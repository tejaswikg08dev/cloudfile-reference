# ECR repositories for each service image.

locals {
  services = ["auth", "files", "search"]
}

resource "aws_ecr_repository" "service" {
  for_each             = toset(local.services)
  name                 = "${var.project_name}-${each.key}"
  image_tag_mutability = "MUTABLE"
  force_delete         = true # allow `terraform destroy` to remove images

  image_scanning_configuration {
    scan_on_push = true
  }
}
