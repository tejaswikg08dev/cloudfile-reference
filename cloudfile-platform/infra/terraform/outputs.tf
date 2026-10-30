output "ecr_repository_urls" {
  description = "ECR repository URLs per service"
  value       = { for k, r in aws_ecr_repository.service : k => r.repository_url }
}

output "s3_bucket_name" {
  description = "Uploads bucket name"
  value       = aws_s3_bucket.uploads.bucket
}

output "rds_endpoint" {
  description = "RDS endpoint address"
  value       = aws_db_instance.main.address
}

output "lambda_function_name" {
  description = "Processor Lambda name"
  value       = aws_lambda_function.processor.function_name
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "eks_cluster_name" {
  description = "EKS cluster name (if enabled)"
  value       = var.enable_eks ? aws_eks_cluster.main[0].name : "disabled"
}
