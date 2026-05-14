import json
import boto3
import re
import os
import logging
import io

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")
MAX_FILE_SIZE = 5 * 1024 * 1024


def extract_text_from_pdf(pdf_bytes):
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        lines = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                for line in text.split("\n"):
                    line = line.strip()
                    if line:
                        lines.append(line)
        return lines
    except Exception as e:
        logger.error(f"PDF extraction error: {str(e)}")
        return []


def parse_email(lines):
    for line in lines:
        match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", line)
        if match:
            return match.group()
    return None


def parse_phone(lines):
    for line in lines:
        match = re.search(r"(\+?\d[\d\s\-().]{7,}\d)", line)
        if match:
            return match.group().strip()
    return None


def parse_name(lines):
    skip = ["resume", "curriculum", "vitae", "cv", "email", "phone",
            "address", "linkedin", "github", "objective", "summary"]
    for line in lines[:10]:
        clean = line.strip()
        if (len(clean) > 3 and
            not any(s in clean.lower() for s in skip) and
            not re.search(r"[@\d]", clean) and
            len(clean.split()) <= 5):
            return clean
    return None


def parse_skills(lines):
    skill_keywords = [
        "python", "javascript", "typescript", "java", "go", "rust", "c++",
        "react", "next.js", "node.js", "django", "fastapi", "flask",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins",
        "git", "linux", "sql", "postgresql", "mongodb", "redis", "kafka",
        "machine learning", "deep learning", "nlp", "pytorch", "tensorflow",
        "html", "css", "rest", "graphql", "ci/cd", "devops", "devsecops"
    ]
    found = set()
    full_text = " ".join(lines).lower()
    for skill in skill_keywords:
        if skill in full_text:
            found.add(skill)
    return sorted(list(found))


def parse_education(lines):
    education = []
    edu_keywords = ["university", "college", "institute", "school",
                    "bachelor", "master", "b.tech", "bca", "mca",
                    "b.e", "m.e", "phd", "diploma", "degree"]
    for line in lines:
        if any(k in line.lower() for k in edu_keywords):
            education.append(line.strip())
    return education[:5]


def parse_experience(lines):
    experience = []
    exp_keywords = ["engineer", "developer", "intern", "manager",
                    "analyst", "architect", "consultant", "lead",
                    "associate", "trainee", "specialist"]
    for line in lines:
        if any(k in line.lower() for k in exp_keywords):
            experience.append(line.strip())
    return experience[:5]


def validate_file(bucket, key):
    try:
        obj = s3.head_object(Bucket=bucket, Key=key)
        size = obj["ContentLength"]
        if size > MAX_FILE_SIZE:
            return False, f"File too large: {size} bytes. Max 5MB."
        if not key.lower().endswith(".pdf"):
            return False, "Only PDF files are supported."
        return True, None
    except Exception as e:
        return False, str(e)


def lambda_handler(event, context):
    logger.info(f"Event received: {json.dumps(event)}")

    try:
        body = json.loads(event.get("body", "{}"))
        bucket = os.environ.get("BUCKET_NAME")
        key = body.get("key")

        if not key:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Missing 'key' in request body"})
            }

        valid, error = validate_file(bucket, key)
        if not valid:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": error})
            }

        logger.info(f"Downloading s3://{bucket}/{key}")
        response = s3.get_object(Bucket=bucket, Key=key)
        pdf_bytes = response["Body"].read()

        lines = extract_text_from_pdf(pdf_bytes)
        logger.info(f"Extracted {len(lines)} lines")

        result = {
            "name":       parse_name(lines),
            "email":      parse_email(lines),
            "phone":      parse_phone(lines),
            "skills":     parse_skills(lines),
            "education":  parse_education(lines),
            "experience": parse_experience(lines),
            "raw_lines":  len(lines),
            "source":     f"s3://{bucket}/{key}"
        }

        logger.info(f"Parsed result: {json.dumps(result)}")

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(result)
        }

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Internal server error"})
        }
