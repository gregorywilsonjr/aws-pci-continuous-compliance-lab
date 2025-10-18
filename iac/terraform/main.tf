# ============================================================================
# AWS PCI DSS v4.0.1 Continuous Compliance Lab — Terraform Foundation
# ============================================================================
# WHAT: Core infrastructure for PCI compliance monitoring
# WHY: Encode control intent as code for auditability and repeatability
# ============================================================================

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "PCI-Continuous-Compliance-Lab"
      ManagedBy   = "Terraform"
      Environment = var.environment
      Purpose     = "GRC-Engineering-Portfolio"
    }
  }
}

# ============================================================================
# Data Sources
# ============================================================================

data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}

# ============================================================================
# S3 Buckets for Logs and Evidence
# WHY: Req. 10 (logging), chain-of-custody for evidence artifacts
# ============================================================================

resource "aws_s3_bucket" "logs" {
  bucket = "${var.name_prefix}-logs-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name    = "${var.name_prefix}-logs"
    Purpose = "PCI-Req-10-Audit-Logs"
  }
}

resource "aws_s3_bucket_versioning" "logs" {
  bucket = aws_s3_bucket.logs.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "logs" {
  bucket = aws_s3_bucket.logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "logs" {
  bucket = aws_s3_bucket.logs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AWSConfigBucketPermissionsCheck"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
        Action   = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.logs.arn
      },
      {
        Sid    = "AWSConfigBucketExistenceCheck"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
        Action   = "s3:ListBucket"
        Resource = aws_s3_bucket.logs.arn
      },
      {
        Sid    = "AWSConfigBucketPutObject"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.logs.arn}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
          }
        }
      }
    ]
  })
}

resource "aws_s3_bucket" "evidence" {
  bucket = "${var.name_prefix}-evidence-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name    = "${var.name_prefix}-evidence"
    Purpose = "PCI-Evidence-Artifacts"
  }
}

resource "aws_s3_bucket_versioning" "evidence" {
  bucket = aws_s3_bucket.evidence.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "evidence" {
  bucket = aws_s3_bucket.evidence.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "evidence" {
  bucket = aws_s3_bucket.evidence.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ============================================================================
# VPC and Networking
# WHY: Req. 1 (network segmentation, ingress control)
# ============================================================================

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name    = "${var.name_prefix}-vpc"
    Purpose = "PCI-Req-1-Network-Segmentation"
  }
}

resource "aws_subnet" "private" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "${var.aws_region}a"

  tags = {
    Name    = "${var.name_prefix}-private-subnet"
    Purpose = "PCI-CDE-Isolation"
  }
}

resource "aws_security_group" "default" {
  name        = "${var.name_prefix}-default-sg"
  description = "Default security group with minimal access"
  vpc_id      = aws_vpc.main.id

  # No ingress rules by default (deny all inbound)
  # WHY: Req. 1.2.1 - Restrict inbound traffic to necessary protocols

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS for AWS API calls"
  }

  tags = {
    Name    = "${var.name_prefix}-default-sg"
    Purpose = "PCI-Req-1-Firewall-Rules"
  }
}

# ============================================================================
# IAM Role for Lambda Evidence Collection
# WHY: Req. 7 (least privilege access control)
# ============================================================================

resource "aws_iam_role" "evidence_lambda" {
  name = "${var.name_prefix}-evidence-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Purpose = "PCI-Req-7-Least-Privilege"
  }
}

resource "aws_iam_role_policy" "evidence_lambda" {
  name = "${var.name_prefix}-evidence-lambda-policy"
  role = aws_iam_role.evidence_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:${data.aws_partition.current.partition}:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl"
        ]
        Resource = "${aws_s3_bucket.evidence.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "securityhub:GetFindings",
          "securityhub:GetEnabledStandards"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "config:DescribeConfigRules",
          "config:DescribeComplianceByConfigRule"
        ]
        Resource = "*"
      }
    ]
  })
}

# ============================================================================
# AWS Config - Configuration Recorder
# WHY: Continuous evaluation of resource compliance
# ============================================================================

resource "aws_iam_role" "config" {
  name = "${var.name_prefix}-config-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "config" {
  role       = aws_iam_role.config.name
  policy_arn = "arn:${data.aws_partition.current.partition}:iam::aws:policy/service-role/AWS_ConfigRole"
}

resource "aws_iam_role_policy" "config_s3" {
  name = "${var.name_prefix}-config-s3-policy"
  role = aws_iam_role.config.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetBucketVersioning",
          "s3:GetBucketAcl",
          "s3:ListBucket",
          "s3:PutObject",
          "s3:GetObject"
        ]
        Resource = [
          aws_s3_bucket.logs.arn,
          "${aws_s3_bucket.logs.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_config_configuration_recorder" "main" {
  name     = "${var.name_prefix}-recorder"
  role_arn = aws_iam_role.config.arn

  recording_group {
    all_supported = true
  }
}

resource "aws_config_delivery_channel" "main" {
  name           = "${var.name_prefix}-delivery-channel"
  s3_bucket_name = aws_s3_bucket.logs.id

  depends_on = [aws_config_configuration_recorder.main, aws_s3_bucket_policy.logs]
}

resource "aws_config_configuration_recorder_status" "main" {
  name       = aws_config_configuration_recorder.main.name
  is_enabled = true

  depends_on = [aws_config_delivery_channel.main]
}

# ============================================================================
# Security Hub - PCI DSS Standard
# WHY: Curated set of checks aligned to PCI requirements
# ============================================================================

resource "aws_securityhub_account" "main" {}

resource "aws_securityhub_standards_subscription" "pci_dss" {
  standards_arn = "arn:${data.aws_partition.current.partition}:securityhub:${var.aws_region}::standards/pci-dss/v/3.2.1"

  depends_on = [aws_securityhub_account.main]
}

# ============================================================================
# Outputs
# ============================================================================

output "evidence_bucket_name" {
  description = "S3 bucket for evidence artifacts"
  value       = aws_s3_bucket.evidence.id
}

output "logs_bucket_name" {
  description = "S3 bucket for audit logs"
  value       = aws_s3_bucket.logs.id
}

output "vpc_id" {
  description = "VPC ID for PCI environment"
  value       = aws_vpc.main.id
}

output "private_subnet_id" {
  description = "Private subnet ID"
  value       = aws_subnet.private.id
}

output "evidence_lambda_role_arn" {
  description = "IAM role ARN for evidence Lambda"
  value       = aws_iam_role.evidence_lambda.arn
}

output "aws_account_id" {
  description = "AWS Account ID"
  value       = data.aws_caller_identity.current.account_id
}
