# Project Structure

Complete directory layout for the AWS PCI DSS v4.0.1 Continuous Compliance Lab.

```
aws_pci_continuous_compliance_lab_FULL/
│
├── README.md                          # Main documentation (comprehensive guide)
├── QUICKSTART.md                      # 15-minute quick start guide
├── LICENSE                            # MIT License
├── Dockerfile                         # Container for evidence collector
├── .dockerignore                      # Docker build exclusions
├── .gitignore                         # Git exclusions
├── Jenkinsfile                        # Jenkins CI/CD pipeline (TWN-style)
│
├── .github/
│   └── workflows/
│       └── compliance-ci.yml          # GitHub Actions CI workflow
│
├── iac/
│   └── terraform/
│       ├── main.tf                    # Core infrastructure (VPC, S3, Config, Security Hub, IAM)
│       ├── variables.tf               # Terraform variables
│       ├── terraform.tfvars.example   # Example variable values
│       └── .gitignore                 # Terraform-specific ignores
│
├── automation/
│   └── lambda/
│       ├── evidence_snapshot.py       # Lambda function for daily snapshots
│       └── requirements.txt           # Python dependencies (boto3)
│
├── evidence/
│   ├── collectors/
│   │   └── python/
│   │       ├── evidence_collect_basic.py  # Manual evidence collector
│   │       └── requirements.txt           # Python dependencies
│   │
│   └── schema/
│       └── evidence_register.csv      # Evidence catalog/register
│
├── docs/
│   └── pci_mapping.md                 # PCI DSS control mapping document
│
└── runbooks/
    └── audit_evidence_runbook.md      # Step-by-step audit procedures
```

---

## File Purposes

### Root Level

- **README.md**: Comprehensive lab guide with detailed explanations
- **QUICKSTART.md**: Fast-track setup in 15 minutes
- **LICENSE**: MIT License for open source use
- **Dockerfile**: Containerize the evidence collector (TWN Docker approach)
- **Jenkinsfile**: CI/CD pipeline for Jenkins (TWN automation)

### Infrastructure as Code (`iac/terraform/`)

- **main.tf**: Creates all AWS resources:
  - S3 buckets (logs, evidence) with encryption
  - VPC and private subnet
  - Security groups (default-deny)
  - AWS Config recorder and delivery channel
  - Security Hub with PCI standard
  - IAM roles and policies (least privilege)

- **variables.tf**: Configurable parameters (region, environment, naming)
- **terraform.tfvars.example**: Template for customization

### Automation (`automation/lambda/`)

- **evidence_snapshot.py**: Lambda function that runs daily to:
  - Collect Security Hub findings summary
  - Collect AWS Config compliance status
  - Upload JSON artifacts to S3 with timestamps

### Evidence Collection (`evidence/`)

- **collectors/python/evidence_collect_basic.py**: Manual collector for:
  - IAM MFA status (Req. 8)
  - IAM role policies (Req. 7)
  - CloudTrail events (Req. 10)

- **schema/evidence_register.csv**: Evidence catalog tracking:
  - Artifact IDs
  - PCI requirements
  - S3 locations
  - Collection timestamps
  - Review status

### Documentation (`docs/`)

- **pci_mapping.md**: Maps PCI DSS requirements to:
  - Technical controls
  - AWS services
  - Evidence artifacts
  - Runbook sections

### Runbooks (`runbooks/`)

- **audit_evidence_runbook.md**: Complete audit procedures:
  - Pre-audit checklist
  - Evidence retrieval steps
  - Verification procedures
  - Packaging for assessors
  - Troubleshooting guide

### CI/CD (`.github/workflows/`)

- **compliance-ci.yml**: GitHub Actions workflow:
  - Terraform format and validation
  - Python linting (ruff)
  - Security scanning (Trivy)
  - Documentation checks

---

## Key Design Principles

1. **WHAT/WHY Comments**: Every file explains what it does and why it exists
2. **TWN Toolkit Alignment**: Uses Terraform, AWS CLI, Python, Docker, Jenkins
3. **Audit-Ready**: All artifacts are timestamped and traceable
4. **Repeatable**: Infrastructure as Code ensures consistency
5. **Portfolio-Ready**: Demonstrates GRC engineering skills

---

## Workflow Overview

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Deploy Infrastructure (Terraform)                        │
│    → VPC, S3, AWS Config, Security Hub, IAM                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Collect Baseline Evidence (Python Script)                │
│    → IAM MFA, Policies, CloudTrail Events                   │
│    → Upload to S3: artifacts/baseline/YYYY-MM-DD/           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Deploy Lambda + EventBridge (Automation)                 │
│    → Daily snapshots of Security Hub & Config               │
│    → Upload to S3: artifacts/daily/YYYY-MM-DD/              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Continuous Monitoring (Automated)                        │
│    → Lambda runs daily at 9 AM UTC                          │
│    → Config records all changes                             │
│    → Security Hub evaluates compliance                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Audit Preparation (Runbook)                              │
│    → Follow audit_evidence_runbook.md                       │
│    → Package artifacts for assessor                         │
│    → Provide PCI mapping and evidence register              │
└─────────────────────────────────────────────────────────────┘
```

---

## Evidence Artifact Structure in S3

```
s3://<EVIDENCE_BUCKET>/
└── artifacts/
    ├── baseline/
    │   └── YYYY-MM-DD/
    │       ├── iam_mfa_status.json
    │       ├── iam_role_policies.json
    │       ├── cloudtrail_recent_events.json
    │       └── collection_summary.json
    │
    ├── daily/
    │   └── YYYY-MM-DD/
    │       ├── securityhub_findings_summary.json
    │       └── aws_config_rules_brief.json
    │
    └── on-demand/
        └── <ticket-or-incident-id>/
            └── (ad-hoc collections)
```

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| IaC | Terraform 1.5+ | Infrastructure provisioning |
| Cloud | AWS | PCI compliance environment |
| Scripting | Python 3.11+ | Evidence collectors |
| Containers | Docker | Portable collector runtime |
| CI/CD | Jenkins / GitHub Actions | Automated testing |
| AWS Services | Config, Security Hub, CloudTrail, Lambda, EventBridge | Compliance monitoring |

---

## Next Steps After Setup

1. **Customize**: Edit `terraform.tfvars` with your preferences
2. **Extend**: Add more collectors (Inspector, GuardDuty, etc.)
3. **Integrate**: Connect to your SIEM or ticketing system
4. **Document**: Update `pci_mapping.md` as you add controls
5. **Test**: Run through the audit runbook quarterly

---

## Interview Talking Points

When presenting this lab in interviews:

1. **Control Intent**: "I translated PCI requirements into technical guardrails"
2. **Automation**: "Daily evidence collection proves continuous compliance"
3. **Auditability**: "Every artifact is timestamped and traceable to a principal"
4. **Repeatability**: "Infrastructure as Code ensures consistent deployments"
5. **Efficiency**: "This reduces audit prep from weeks to hours"

---

**Last Updated**: 2024-01-15  
**Maintained By**: GRC Engineering Team
