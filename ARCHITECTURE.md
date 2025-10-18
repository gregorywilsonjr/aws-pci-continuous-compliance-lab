# Architecture Overview

Visual representation of the AWS PCI DSS Continuous Compliance Lab architecture.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AWS Account (PCI Environment)               │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    VPC (10.0.0.0/16)                        │    │
│  │  ┌────────────────────────────────────────────────────┐     │    │
│  │  │  Private Subnet (10.0.1.0/24)                      │     │    │
│  │  │  ┌──────────────────────────────────────────┐     │      │    │
│  │  │  │  Security Group (Default-Deny Ingress)   │     │      │    │
│  │  │  │  • No inbound rules                      │     │      │    │
│  │  │  │  • HTTPS outbound only (port 443)        │     │      │    │
│  │  │  └──────────────────────────────────────────┘     │      │    │
│  │  └────────────────────────────────────────────────────┘     │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    S3 Buckets (Encrypted)                   │    │
│  │  ┌─────────────────────┐  ┌─────────────────────────────┐   │    │
│  │  │  Logs Bucket        │  │  Evidence Bucket            │   │    │
│  │  │  • AES256 encrypted │  │  • AES256 encrypted         │   │    │
│  │  │  • Versioning ON    │  │  • Versioning ON            │   │   │
│  │  │  • Public access ✗ │  │  • Public access ✗          │   │   │
│  │  │                     │  │                             │   │   │
│  │  │  Contents:          │  │  Contents:                  │   │   │
│  │  │  • Config logs      │  │  • artifacts/baseline/      │   │   │
│  │  │  • CloudTrail logs  │  │  • artifacts/daily/         │   │   │
│  │  └─────────────────────┘  │  • artifacts/on-demand/     │   │   │
│  │                           └─────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Compliance Services                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │   │
│  │  │ AWS Config   │  │ Security Hub │  │ CloudTrail   │       │   │
│  │  │ • Recorder   │  │ • PCI DSS    │  │ • Enabled    │       │   │
│  │  │ • Rules      │  │   Standard   │  │ • Logging    │       │   │
│  │  │ • Delivery   │  │ • Findings   │  │ • S3 logs    │       │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Automation Layer                         │   │
│  │  ┌────────────────────────────────────────────────────┐     │   │
│  │  │  Lambda: pci-evidence-snapshot                     │     │   │
│  │  │  • Runtime: Python 3.11                            │     │   │
│  │  │  • Trigger: EventBridge (daily 9 AM UTC)           │     │   │
│  │  │  • Actions:                                        │     │   │
│  │  │    - Query Security Hub findings                   │     │   │
│  │  │    - Query Config compliance                       │     │   │
│  │  │    - Upload JSON to S3                             │     │   │
│  │  └────────────────────────────────────────────────────┘     │   │
│  │                            ↓                                │   │
│  │  ┌────────────────────────────────────────────────────┐     │   │
│  │  │  EventBridge Rule: pci-evidence-daily-09utc        │     │   │
│  │  │  • Schedule: cron(0 9 * * ? *)                     │     │   │
│  │  │  • Target: Lambda function                         │     │   │
│  │  └────────────────────────────────────────────────────┘     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    IAM (Least Privilege)                    │   │
│  │  ┌──────────────────────────────────────────────────┐       │   │
│  │  │  Lambda Execution Role                           │       │   │
│  │  │  • S3 PutObject (evidence bucket)                │       │   │
│  │  │  • SecurityHub GetFindings                       │       │   │
│  │  │  • Config DescribeRules                          │       │   │
│  │  │  • CloudWatch Logs                               │       │   │
│  │  └──────────────────────────────────────────────────┘       │   │
│  │  ┌──────────────────────────────────────────────────┐       │   │
│  │  │  Config Service Role                             │       │   │
│  │  │  • S3 PutObject (logs bucket)                    │       │   │
│  │  │  • Config service permissions                    │       │   │
│  │  └──────────────────────────────────────────────────┘       │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         Local Workstation                           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Manual Evidence Collector (Python)                          │   │
│  │  • evidence_collect_basic.py                                 │   │
│  │  • Collects: IAM MFA, Policies, CloudTrail                   │   │
│  │  • Uploads to S3: artifacts/baseline/                        │   │
│  └──────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Terraform (IaC)                                             │   │
│  │  • Provisions all AWS resources                              │   │
│  │  • Maintains state                                           │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Evidence Collection

### Automated Daily Flow

```
┌─────────────┐
│ EventBridge │  Triggers daily at 9 AM UTC
│    Rule     │
└──────┬──────┘
       │
       ↓
┌─────────────────────────────────────────────────────────┐
│ Lambda: pci-evidence-snapshot                           │
│                                                         │
│  1. Query Security Hub                                  │
│     ├─ Get active findings                             │
│     ├─ Aggregate by severity                           │
│     └─ Aggregate by compliance status                  │
│                                                         │
│  2. Query AWS Config                                    │
│     ├─ List all rules                                  │
│     ├─ Get compliance status per rule                  │
│     └─ Aggregate by compliance type                    │
│                                                         │
│  3. Generate JSON artifacts                             │
│     ├─ securityhub_findings_summary.json               │
│     └─ aws_config_rules_brief.json                     │
│                                                         │
│  4. Upload to S3                                        │
│     └─ s3://evidence-bucket/artifacts/daily/YYYY-MM-DD/ │
└─────────────────────────────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────────────────────┐
│ S3 Evidence Bucket                                      │
│  artifacts/daily/2024-01-15/                            │
│    ├─ securityhub_findings_summary.json                 │
│    └─ aws_config_rules_brief.json                       │
└─────────────────────────────────────────────────────────┘
```

### Manual Baseline Collection Flow

```
┌─────────────────────────────────────────────────────────┐
│ Local Workstation                                       │
│  $ python3 evidence_collect_basic.py                    │
│    --region us-west-2                                   │
│    --evidence-bucket <BUCKET>                           │
│    --prefix baseline/2024-01-15                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│ AWS API Calls (via boto3)                              │
│                                                         │
│  1. IAM.list_users()                                    │
│     └─ For each user: list_mfa_devices()               │
│                                                         │
│  2. IAM.list_roles()                                    │
│     ├─ For each role: list_attached_role_policies()    │
│     └─ For each role: list_role_policies()             │
│                                                         │
│  3. CloudTrail.lookup_events()                          │
│     └─ Filter: ReadOnly=false (write events)           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│ Generate Local JSON Files                              │
│  ├─ iam_mfa_status.json                                 │
│  ├─ iam_role_policies.json                              │
│  ├─ cloudtrail_recent_events.json                       │
│  └─ collection_summary.json                             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│ Upload to S3                                            │
│  s3://evidence-bucket/artifacts/baseline/2024-01-15/    │
│    ├─ iam_mfa_status.json                               │
│    ├─ iam_role_policies.json                            │
│    ├─ cloudtrail_recent_events.json                     │
│    └─ collection_summary.json                           │
└─────────────────────────────────────────────────────────┘
```

---

## PCI Requirement to AWS Service Mapping

```
┌─────────────────────────────────────────────────────────────────┐
│                    PCI DSS Requirements                         │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ↓                     ↓                     ↓
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  Req. 1       │    │  Req. 2       │    │  Req. 7       │
│  Network      │    │  Secure       │    │  Least        │
│  Security     │    │  Config       │    │  Privilege    │
└───────┬───────┘    └───────┬───────┘    └───────┬───────┘
        │                    │                    │
        ↓                    ↓                    ↓
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ VPC           │    │ Security Hub  │    │ IAM Roles     │
│ Security      │    │ AWS Config    │    │ IAM Policies  │
│ Groups        │    │               │    │               │
└───────┬───────┘    └───────┬───────┘    └───────┬───────┘
        │                    │                    │
        ↓                    ↓                    ↓
┌───────────────────────────────────────────────────────────┐
│              Evidence Artifacts in S3                     │
│  • security_groups.json                                   │
│  • securityhub_findings_summary.json                      │
│  • aws_config_rules_brief.json                            │
│  • iam_role_policies.json                                 │
└───────────────────────────────────────────────────────────┘

        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ↓                     ↓                     ↓
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  Req. 8       │    │  Req. 10      │    │  Req. 11      │
│  MFA          │    │  Audit        │    │  Change       │
│  Required     │    │  Logging      │    │  Detection    │
└───────┬───────┘    └───────┬───────┘    └───────┬───────┘
        │                    │                    │
        ↓                    ↓                    ↓
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ IAM MFA       │    │ CloudTrail    │    │ AWS Config    │
│ Devices       │    │               │    │ Recorder      │
└───────┬───────┘    └───────┬───────┘    └───────┬───────┘
        │                    │                    │
        ↓                    ↓                    ↓
┌───────────────────────────────────────────────────────────┐
│              Evidence Artifacts in S3                     │
│  • iam_mfa_status.json                                    │
│  • cloudtrail_recent_events.json                          │
│  • aws_config_rules_brief.json                            │
└───────────────────────────────────────────────────────────┘
```

---

## CI/CD Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Developer Commits Code                                     │
│  $ git push origin main                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  GitHub / GitLab / Bitbucket                                │
│  • Webhook triggered                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ↓                         ↓
┌───────────────┐         ┌───────────────┐
│ GitHub Actions│         │   Jenkins     │
└───────┬───────┘         └───────┬───────┘
        │                         │
        ↓                         ↓
┌─────────────────────────────────────────────────────────────┐
│  Stage 1: Terraform Validation                              │
│  • terraform fmt -check                                     │
│  • terraform init -backend=false                            │
│  • terraform validate                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  Stage 2: Python Linting                                    │
│  • ruff check *.py                                          │
│  • python -m py_compile *.py                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  Stage 3: Security Scanning                                 │
│  • Trivy vulnerability scan                                 │
│  • Upload SARIF to GitHub Security                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  Stage 4: Documentation Validation                          │
│  • Check required files exist                               │
│  • Validate CSV format                                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  ✅ Pipeline Success                                         │
│  • All checks passed                                        │
│  • Ready for deployment                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Audit Evidence Retrieval Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Auditor Request: "Provide evidence for PCI Req. 7, 8, 10"  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Consult PCI Mapping Document                       │
│  • docs/pci_mapping.md                                      │
│  • Identify required artifacts                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 2: Check Evidence Register                            │
│  • evidence/schema/evidence_register.csv                    │
│  • Find S3 keys for required artifacts                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 3: Download from S3                                   │
│  $ aws s3 sync s3://evidence-bucket/artifacts/ ./evidence/  │
│                                                             │
│  Retrieved:                                                 │
│  • artifacts/baseline/2024-01-15/iam_role_policies.json     │
│  • artifacts/baseline/2024-01-15/iam_mfa_status.json        │
│  • artifacts/baseline/2024-01-15/cloudtrail_events.json     │
│  • artifacts/daily/2024-01-15/securityhub_findings.json     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 4: Package for Auditor                                │
│  • Create evidence package directory                        │
│  • Include PCI mapping document                             │
│  • Include evidence register                                │
│  • Include runbook                                          │
│  • Generate checksums                                       │
│  • Compress and deliver                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  ✅ Evidence Package Delivered                               │
│  • pci_audit_evidence_2024-01-15.tar.gz                     │
│  • SHA256 checksum included                                 │
│  • Chain of custody documented                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Interactions

```
┌──────────────┐
│  Terraform   │──────┐
└──────────────┘      │
                      ↓
              ┌───────────────┐
              │  AWS Account  │
              └───────┬───────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ↓             ↓             ↓
┌──────────┐  ┌──────────┐  ┌──────────┐
│   VPC    │  │   S3     │  │   IAM    │
└──────────┘  └────┬─────┘  └──────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
        ↓          ↓          ↓
┌──────────┐  ┌──────────┐  ┌──────────┐
│  Config  │  │ Security │  │CloudTrail│
│          │  │   Hub    │  │          │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     └─────────────┼─────────────┘
                   │
                   ↓
         ┌─────────────────┐
         │  Lambda         │
         │  (Evidence      │
         │   Collector)    │
         └────────┬────────┘
                  │
                  ↓
         ┌─────────────────┐
         │  S3 Evidence    │
         │  Bucket         │
         └────────┬────────┘
                  │
                  ↓
         ┌─────────────────┐
         │  Auditor        │
         │  (Evidence      │
         │   Consumer)     │
         └─────────────────┘
```

---

## Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Network Security (Req. 1)                         │
│  • VPC isolation                                            │
│  • Private subnets                                          │
│  • Security groups (default-deny)                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Data Protection (Req. 3, 4)                       │
│  • S3 encryption at rest (AES256)                           │
│  • S3 versioning                                            │
│  • Public access blocked                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Access Control (Req. 7, 8)                        │
│  • IAM least privilege policies                             │
│  • MFA enforcement                                          │
│  • Role-based access                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: Monitoring & Logging (Req. 10)                    │
│  • CloudTrail enabled                                       │
│  • Config recording                                         │
│  • Security Hub findings                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 5: Change Detection (Req. 11)                        │
│  • AWS Config rules                                         │
│  • Continuous compliance checks                             │
│  • Automated alerting                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Development Layer                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   Git    │  │  VS Code │  │  Python  │  │ Terraform│   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                    CI/CD Layer                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  GitHub  │  │ Jenkins  │  │  Docker  │  │   Ruff   │   │
│  │ Actions  │  │          │  │          │  │  (Lint)  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   VPC    │  │    S3    │  │   IAM    │  │  Lambda  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                    Compliance Layer                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Config  │  │ Security │  │CloudTrail│  │EventBridge│  │
│  │          │  │   Hub    │  │          │  │          │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                    Evidence Layer                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Baseline │  │  Daily   │  │On-Demand │  │ Evidence │   │
│  │ Artifacts│  │Snapshots │  │Collection│  │ Register │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

**Architecture Version**: 1.0  
**Last Updated**: 2024-01-15  
**Maintained By**: GRC Engineering Team
