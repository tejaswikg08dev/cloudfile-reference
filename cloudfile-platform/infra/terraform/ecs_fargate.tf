# ECS Fargate cluster + services (the cost-efficient deployment path).
# Tasks run in public subnets with public IPs to avoid NAT Gateway charges.

resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"
}

resource "aws_security_group" "ecs" {
  name_prefix = "${var.project_name}-ecs-"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP to services"
    from_port   = 8001
    to_port     = 8003
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_cloudwatch_log_group" "services" {
  for_each          = toset(local.services)
  name              = "/ecs/${var.project_name}-${each.key}"
  retention_in_days = 3
}

locals {
  service_ports = {
    auth   = 8001
    files  = 8002
    search = 8003
  }

  # Per-service environment. DB URLs use the RDS endpoint.
  # NOTE: RDS provisions exactly ONE database (var.db_name). All services share
  # that single database — their table names (users, files) never collide — so
  # we avoid the "database cloudfile_auth does not exist" failure. (Locally,
  # Docker Compose uses two databases; on AWS we keep it to one for simplicity
  # and free-tier friendliness.)
  service_env = {
    auth = [
      { name = "AUTH_DATABASE_URL", value = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${aws_db_instance.main.address}:5432/${var.db_name}" },
      { name = "JWT_SECRET_KEY", value = var.jwt_secret_key },
    ]
    files = [
      { name = "FILES_DATABASE_URL", value = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${aws_db_instance.main.address}:5432/${var.db_name}" },
      { name = "JWT_SECRET_KEY", value = var.jwt_secret_key },
      { name = "S3_BUCKET_NAME", value = aws_s3_bucket.uploads.bucket },
      { name = "AWS_REGION", value = var.aws_region },
    ]
    search = [
      { name = "SEARCH_DATABASE_URL", value = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${aws_db_instance.main.address}:5432/${var.db_name}" },
      { name = "JWT_SECRET_KEY", value = var.jwt_secret_key },
    ]
  }
}

resource "aws_ecs_task_definition" "service" {
  for_each                 = toset(local.services)
  family                   = "${var.project_name}-${each.key}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = each.key
      image     = "${aws_ecr_repository.service[each.key].repository_url}:latest"
      essential = true
      portMappings = [
        { containerPort = local.service_ports[each.key], protocol = "tcp" }
      ]
      environment = local.service_env[each.key]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.services[each.key].name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "service" {
  for_each        = toset(local.services)
  name            = "${var.project_name}-${each.key}"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.service[each.key].arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true
  }
}
