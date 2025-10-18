# ============================================================================
# Variables for PCI Compliance Lab
# ============================================================================

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-west-2"
}

variable "environment" {
  description = "Environment name (lab, dev, prod)"
  type        = string
  default     = "lab"
}

variable "name_prefix" {
  description = "Prefix for all resource names"
  type        = string
  default     = "pci-cc-lab"
}
