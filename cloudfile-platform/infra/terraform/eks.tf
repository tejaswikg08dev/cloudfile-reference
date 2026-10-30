# Optional EKS cluster for a SHORT demo only. Disabled by default.
# Enable with: terraform apply -var="enable_eks=true"
# REMEMBER: EKS control plane costs ~$0.10/hour. Destroy promptly.

data "aws_iam_policy_document" "eks_assume" {
  count = var.enable_eks ? 1 : 0
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["eks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "eks_cluster" {
  count              = var.enable_eks ? 1 : 0
  name               = "${var.project_name}-eks-cluster"
  assume_role_policy = data.aws_iam_policy_document.eks_assume[0].json
}

resource "aws_iam_role_policy_attachment" "eks_cluster" {
  count      = var.enable_eks ? 1 : 0
  role       = aws_iam_role.eks_cluster[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
}

resource "aws_eks_cluster" "main" {
  count    = var.enable_eks ? 1 : 0
  name     = "${var.project_name}-eks"
  role_arn = aws_iam_role.eks_cluster[0].arn
  version  = "1.30"

  vpc_config {
    subnet_ids = aws_subnet.public[*].id
  }

  depends_on = [aws_iam_role_policy_attachment.eks_cluster]
}
