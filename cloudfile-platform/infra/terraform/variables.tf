variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefix for resource names"
  type        = string
  default     = "cloudfile"
}

variable "db_name" {
  description = "Initial database name"
  type        = string
  default     = "cloudfile_files"
}

variable "db_username" {
  description = "RDS master username"
  type        = string
  default     = "cloudfile"
}

variable "db_password" {
  description = "RDS master password (pass via -var or TF_VAR_db_password)"
  type        = string
  sensitive   = true
}

variable "jwt_secret_key" {
  description = "Shared JWT signing secret"
  type        = string
  sensitive   = true
  default     = "change-me-use-a-long-random-string"
}

variable "enable_eks" {
  description = "Set true only for a short EKS demo (costs money)."
  type        = bool
  default     = false
}

variable "service_desired_count" {
  description = <<-EOT
    Number of tasks per ECS service.
    Use 0 for the FIRST apply (creates infra + ECR without trying to run
    containers before images exist). After pushing images, apply again with
    1 to start the services.
  EOT
  type    = number
  default = 0
}
