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
      # psycopg2 DSN for the files DB. The handler only updates the DB if this
      # is set AND psycopg2 is available in the package/layer; otherwise it
      # safely skips the DB update (see services/processor/handler.py).
      PROCESSOR_DATABASE_URL = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.main.address}:5432/${var.db_name}"
    }
  }
}

# IMPORTANT: handler.py imports Pillow and psycopg2. The zip above contains only
# source files, so those libraries are NOT present by default and the Lambda
# will skip thumbnails/DB updates (it degrades gracefully, it does not crash).
# To enable them, attach a Lambda layer that provides Pillow + psycopg2, or
# build a zip that includes dependencies (see services/processor/README.md).

resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.uploads.arn
}
