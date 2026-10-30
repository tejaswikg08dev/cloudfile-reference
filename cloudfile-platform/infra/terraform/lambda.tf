# Packages and deploys the processor Lambda.
# NOTE: This zips only handler.py + image_utils.py. For Pillow/psycopg2 you must
# attach a Lambda layer or build a zip with dependencies. See processor/README.

data "archive_file" "processor" {
  type        = "zip"
  source_dir  = "${path.module}/../../services/processor"
  output_path = "${path.module}/processor.zip"
  excludes    = ["README.md", "requirements.txt"]
}

resource "aws_lambda_function" "processor" {
  function_name    = "${var.project_name}-processor"
  role             = aws_iam_role.lambda.arn
  handler          = "handler.handler"
  runtime          = "python3.11"
  filename         = data.archive_file.processor.output_path
  source_code_hash = data.archive_file.processor.output_base64sha256
  timeout          = 30
  memory_size      = 256

  environment {
    variables = {
      # Set PROCESSOR_DATABASE_URL after RDS is known if DB updates are desired.
      PROCESSOR_DATABASE_URL = ""
    }
  }
}

resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.uploads.arn
}
