output "api_endpoint" {
  value = "${aws_apigatewayv2_stage.default.invoke_url}/parse"
}

output "bucket_name" {
  value = aws_s3_bucket.resumes.bucket
}

output "lambda_function_name" {
  value = aws_lambda_function.parser.function_name
}
