import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../lambda"))

from parser import (
    parse_email, parse_phone, parse_name,
    parse_skills, parse_education, parse_experience
)


def test_parse_email():
    lines = ["Name: Tayyab", "Email: tayyab@gmail.com", "Phone: 9876543210"]
    assert parse_email(lines) == "tayyab@gmail.com"


def test_parse_email_not_found():
    lines = ["No email here", "Just text"]
    assert parse_email(lines) is None


def test_parse_phone():
    lines = ["tayyab@gmail.com", "+91 9876543210"]
    assert parse_phone(lines) is not None


def test_parse_name():
    lines = ["Tayyab Ahamed", "tayyab@gmail.com", "Software Engineer"]
    assert parse_name(lines) == "Tayyab Ahamed"


def test_parse_skills():
    lines = ["Skills: Python, AWS, Docker, Kubernetes, Terraform"]
    skills = parse_skills(lines)
    assert "python" in skills
    assert "aws" in skills
    assert "docker" in skills


def test_parse_education():
    lines = ["Kristu Jayanti College", "Bachelor of Computer Applications",
             "2022 - 2026", "Bangalore"]
    edu = parse_education(lines)
    assert len(edu) > 0


def test_parse_experience():
    lines = ["Cloud Engineer Intern at Zorvyn FinTech",
             "AWS Cloud Intern at F13 Technologies"]
    exp = parse_experience(lines)
    assert len(exp) > 0


if __name__ == "__main__":
    print("Running tests...")
    test_parse_email()
    test_parse_email_not_found()
    test_parse_phone()
    test_parse_name()
    test_parse_skills()
    test_parse_education()
    test_parse_experience()
    print("All tests passed!")
