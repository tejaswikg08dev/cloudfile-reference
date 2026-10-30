# S3 bucket for uploads + event notification that triggers the processor Lambda.

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "uploads" {
  bucket        = "${var.project_name}-uploads-${random_id.bucket_suffix.hex}"
  force_destroy = true # allow destroy even if objects exist (demo convenience)
}

resource "aws_s3_bucket_public_access_block" "uploads" {
  bucket                  = aws_s3_bucket.uploads.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_cors_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id
  cors_rule {
    allowed_methods = ["GET", "PUT"]
    allowed_origins = ["*"] # tighten in production
    allowed_headers = ["*"]
    max_age_seconds = 3000
  }
}

resource "aws_s3_bucket_notification" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.processor.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "uploads/"
  }

  depends_on = [aws_lambda_permission.allow_s3]
}
