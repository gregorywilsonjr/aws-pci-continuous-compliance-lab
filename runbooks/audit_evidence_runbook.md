# PCI DSS Audit Evidence Runbook

**Purpose**: Step-by-step guide for retrieving and packaging evidence artifacts for PCI DSS assessments.

**Audience**: GRC Engineers, Auditors, Compliance Teams

**Last Updated**: 2024-01-15

---

## Table of Contents

1. [Pre-Audit Checklist](#pre-audit-checklist)
2. [Evidence Retrieval Process](#evidence-retrieval-process)
3. [Network Controls (Req. 1)](#network-controls-req-1)
4. [Security Hub Findings (Req. 2)](#security-hub-findings-req-2)
5. [IAM Policy Review (Req. 7)](#iam-policy-review-req-7)
6. [MFA Verification (Req. 8)](#mfa-verification-req-8)
7. [Audit Log Review (Req. 10)](#audit-log-review-req-10)
8. [Change Detection (Req. 11)](#change-detection-req-11)
9. [Incident Response (Req. 12)](#incident-response-req-12)
10. [Packaging Evidence for Assessor](#packaging-evidence-for-assessor)

---

## Pre-Audit Checklist

Before beginning evidence collection:

- [ ] Verify AWS CLI credentials: `aws sts get-caller-identity`
- [ ] Note your IAM role/user ARN for chain-of-custody
- [ ] Confirm evidence bucket exists: `aws s3 ls s3://<EVIDENCE_BUCKET>/`
- [ ] Verify date range for audit period (e.g., last 12 months)
- [ ] Review `evidence/schema/evidence_register.csv` for completeness
- [ ] Ensure all automated collectors have run successfully

---

## Evidence Retrieval Process

### Step 1: Validate Caller Identity

```bash
aws sts get-caller-identity > caller_identity.json
```

**Purpose**: Establish chain-of-custody for who retrieved evidence.

**Save**: Include `caller_identity.json` in evidence package.

---

### Step 2: List Available Artifacts

```bash
# List all evidence artifacts
aws s3 ls s3://<EVIDENCE_BUCKET>/artifacts/ --recursive > artifact_inventory.txt

# List daily snapshots for audit period
aws s3 ls s3://<EVIDENCE_BUCKET>/artifacts/daily/ --recursive | grep "2024-"
```

**Purpose**: Create inventory of available evidence.

---

### Step 3: Download Evidence Package

```bash
# Create local evidence directory
mkdir -p audit_evidence_package/$(date +%F)
cd audit_evidence_package/$(date +%F)

# Download baseline artifacts
aws s3 sync s3://<EVIDENCE_BUCKET>/artifacts/baseline/ ./baseline/

# Download daily artifacts for audit period
aws s3 sync s3://<EVIDENCE_BUCKET>/artifacts/daily/ ./daily/

# Download on-demand artifacts (if any)
aws s3 sync s3://<EVIDENCE_BUCKET>/artifacts/on-demand/ ./on-demand/
```

---

## Network Controls (Req. 1)

**PCI Requirement**: 1.2.1 - Configuration files for NSCs are reviewed at least once every six months

### Evidence to Collect

1. **Security Group Configurations**
   ```bash
   aws ec2 describe-security-groups --region us-west-2 > security_groups_$(date +%F).json
   ```

2. **VPC Configuration**
   ```bash
   aws ec2 describe-vpcs --region us-west-2 > vpcs_$(date +%F).json
   aws ec2 describe-subnets --region us-west-2 > subnets_$(date +%F).json
   ```

3. **Network ACLs**
   ```bash
   aws ec2 describe-network-acls --region us-west-2 > network_acls_$(date +%F).json
   ```

### Verification Steps

- [ ] Confirm default-deny ingress rules
- [ ] Verify no 0.0.0.0/0 inbound rules (except for specific approved services)
- [ ] Check for unused security groups

### Evidence Location

- Terraform code: `iac/terraform/main.tf` (lines defining security groups)
- Runtime config: `security_groups_YYYY-MM-DD.json`

---

## Security Hub Findings (Req. 2)

**PCI Requirement**: 2.2.1 - Configuration standards are defined and implemented

### Evidence to Collect

1. **Daily Security Hub Snapshots**
   ```bash
   # Already collected by Lambda
   ls -l daily/*/securityhub_findings_summary.json
   ```

2. **Current Security Hub Status**
   ```bash
   aws securityhub get-enabled-standards > securityhub_standards_$(date +%F).json
   aws securityhub get-findings --max-results 100 > securityhub_findings_$(date +%F).json
   ```

### Verification Steps

- [ ] Confirm PCI DSS standard is enabled
- [ ] Review CRITICAL and HIGH severity findings
- [ ] Document remediation status for failed checks

### Evidence Location

- Daily snapshots: `artifacts/daily/YYYY-MM-DD/securityhub_findings_summary.json`
- Current state: `securityhub_findings_YYYY-MM-DD.json`

---

## IAM Policy Review (Req. 7)

**PCI Requirement**: 7.2.1 - Access control systems ensure access based on need to know

### Evidence to Collect

1. **IAM Role Policies** (already collected)
   ```bash
   # Review baseline collection
   cat baseline/*/iam_role_policies.json | jq '.total_roles'
   ```

2. **IAM Users and Groups**
   ```bash
   aws iam list-users > iam_users_$(date +%F).json
   aws iam list-groups > iam_groups_$(date +%F).json
   ```

3. **Policy Simulator (sample check)**
   ```bash
   # Example: Check if role can perform sensitive action
   aws iam simulate-principal-policy \
     --policy-source-arn arn:aws:iam::ACCOUNT:role/ROLE_NAME \
     --action-names s3:DeleteBucket \
     --resource-arns arn:aws:s3:::*
   ```

### Verification Steps

- [ ] Review each role for least privilege
- [ ] Identify roles with `*` permissions
- [ ] Verify no inline policies with excessive permissions
- [ ] Check for unused roles (no activity in 90 days)

### Evidence Location

- Baseline: `artifacts/baseline/YYYY-MM-DD/iam_role_policies.json`
- Terraform: `iac/terraform/main.tf` (IAM role definitions)

---

## MFA Verification (Req. 8)

**PCI Requirement**: 8.3.1 - Multi-factor authentication for all non-console administrative access

### Evidence to Collect

1. **MFA Status** (already collected)
   ```bash
   # Review baseline collection
   cat baseline/*/iam_mfa_status.json | jq '.users_without_mfa'
   ```

2. **Current MFA Status**
   ```bash
   # Re-run collector for current state
   cd evidence/collectors/python
   python3 evidence_collect_basic.py \
     --region us-west-2 \
     --evidence-bucket <BUCKET> \
     --prefix on-demand/audit-$(date +%F) \
     --local-only
   ```

### Verification Steps

- [ ] Confirm all users have MFA enabled
- [ ] Document exceptions (service accounts, break-glass)
- [ ] Verify MFA enforcement policy exists

### Evidence Location

- Baseline: `artifacts/baseline/YYYY-MM-DD/iam_mfa_status.json`
- Current: `on-demand/audit-YYYY-MM-DD/iam_mfa_status.json`

---

## Audit Log Review (Req. 10)

**PCI Requirement**: 10.2 - Implement automated audit trails

### Evidence to Collect

1. **CloudTrail Events** (already collected)
   ```bash
   # Review baseline collection
   cat baseline/*/cloudtrail_recent_events.json | jq '.total_events'
   ```

2. **CloudTrail Configuration**
   ```bash
   aws cloudtrail describe-trails > cloudtrail_config_$(date +%F).json
   aws cloudtrail get-trail-status --name <TRAIL_NAME> > cloudtrail_status_$(date +%F).json
   ```

3. **Sample Log Entries**
   ```bash
   # Download recent CloudTrail logs from S3
   aws s3 sync s3://<LOGS_BUCKET>/AWSLogs/<ACCOUNT>/CloudTrail/ ./cloudtrail_logs/ \
     --exclude "*" --include "*.json.gz"
   ```

### Verification Steps

- [ ] Confirm CloudTrail is enabled and logging
- [ ] Verify log file validation is enabled
- [ ] Check S3 bucket has encryption and versioning
- [ ] Review sample admin events (Create, Delete, Update)

### Evidence Location

- Events: `artifacts/baseline/YYYY-MM-DD/cloudtrail_recent_events.json`
- Logs: `s3://<LOGS_BUCKET>/AWSLogs/<ACCOUNT>/CloudTrail/`
- Config: `cloudtrail_config_YYYY-MM-DD.json`

---

## Change Detection (Req. 11)

**PCI Requirement**: 11.5.1 - Deploy a change-detection mechanism

### Evidence to Collect

1. **AWS Config Compliance** (already collected)
   ```bash
   # Review daily snapshots
   cat daily/*/aws_config_rules_brief.json | jq '.by_compliance'
   ```

2. **Config Recorder Status**
   ```bash
   aws configservice describe-configuration-recorders > config_recorders_$(date +%F).json
   aws configservice describe-configuration-recorder-status > config_status_$(date +%F).json
   ```

3. **Config Rule Details**
   ```bash
   aws configservice describe-config-rules > config_rules_$(date +%F).json
   ```

### Verification Steps

- [ ] Confirm Config recorder is enabled and recording
- [ ] Review non-compliant resources
- [ ] Verify Config delivery channel is working
- [ ] Check for configuration changes in audit period

### Evidence Location

- Daily snapshots: `artifacts/daily/YYYY-MM-DD/aws_config_rules_brief.json`
- Config snapshots: `s3://<LOGS_BUCKET>/AWSLogs/<ACCOUNT>/Config/`

---

## Incident Response (Req. 12)

**PCI Requirement**: 12.10.1 - Incident response plan is created and implemented

### Evidence to Collect

1. **Incident Response Documentation**
   - This repository serves as the IR framework
   - Runbook: `runbooks/audit_evidence_runbook.md`
   - Automation: `automation/lambda/evidence_snapshot.py`

2. **EventBridge Rules** (if configured)
   ```bash
   aws events list-rules > eventbridge_rules_$(date +%F).json
   ```

3. **Lambda Functions**
   ```bash
   aws lambda list-functions > lambda_functions_$(date +%F).json
   aws lambda get-function --function-name pci-evidence-snapshot > lambda_config_$(date +%F).json
   ```

### Verification Steps

- [ ] Document IR procedures
- [ ] Verify automated alerting is configured
- [ ] Test evidence collection process
- [ ] Review incident logs (if any incidents occurred)

### Evidence Location

- Documentation: This repository
- Lambda config: `lambda_config_YYYY-MM-DD.json`

---

## Packaging Evidence for Assessor

### Step 1: Create Evidence Package

```bash
# Create package directory
mkdir pci_audit_evidence_$(date +%F)
cd pci_audit_evidence_$(date +%F)

# Copy all collected artifacts
cp -r ../audit_evidence_package/$(date +%F)/* .

# Copy documentation
cp ../evidence/schema/evidence_register.csv .
cp ../docs/pci_mapping.md .
cp ../runbooks/audit_evidence_runbook.md .

# Copy Terraform code (infrastructure as code)
cp -r ../iac/terraform ./infrastructure_code/

# Add caller identity
cp ../caller_identity.json .
```

### Step 2: Create Evidence Index

```bash
# Generate file listing with checksums
find . -type f -exec sha256sum {} \; > evidence_checksums.txt

# Create README for assessor
cat > README_FOR_ASSESSOR.md << 'EOF'
# PCI DSS v4.0.1 Evidence Package

**Audit Period**: [START_DATE] to [END_DATE]
**Prepared By**: [YOUR_NAME]
**Date Prepared**: $(date +%F)
**AWS Account**: [ACCOUNT_ID]

## Contents

- `baseline/` - Initial baseline evidence collection
- `daily/` - Automated daily snapshots
- `on-demand/` - On-demand collections for audit
- `infrastructure_code/` - Terraform IaC definitions
- `evidence_register.csv` - Evidence catalog
- `pci_mapping.md` - Control mapping document
- `audit_evidence_runbook.md` - This runbook
- `caller_identity.json` - Chain of custody
- `evidence_checksums.txt` - File integrity hashes

## How to Navigate

1. Start with `pci_mapping.md` to understand control mappings
2. Review `evidence_register.csv` for artifact inventory
3. Cross-reference S3 keys to files in this package
4. Verify checksums using `evidence_checksums.txt`

## Contact

For questions: [YOUR_EMAIL]
EOF
```

### Step 3: Compress and Deliver

```bash
# Create compressed archive
cd ..
tar -czf pci_audit_evidence_$(date +%F).tar.gz pci_audit_evidence_$(date +%F)/

# Or create ZIP for Windows assessors
zip -r pci_audit_evidence_$(date +%F).zip pci_audit_evidence_$(date +%F)/

# Generate final checksum
sha256sum pci_audit_evidence_$(date +%F).tar.gz > pci_audit_evidence_$(date +%F).tar.gz.sha256
```

### Step 4: Secure Delivery

- [ ] Upload to secure file transfer (SFTP, S3 presigned URL)
- [ ] Encrypt if sending via email (GPG, 7-Zip with password)
- [ ] Document delivery method and recipient
- [ ] Retain copy for records

---

## Troubleshooting

### Issue: Missing Artifacts

**Symptom**: Expected S3 keys are not present

**Resolution**:
1. Check Lambda execution logs: `aws logs tail /aws/lambda/pci-evidence-snapshot --follow`
2. Verify EventBridge rule is enabled: `aws events describe-rule --name pci-evidence-daily-09utc`
3. Manually invoke Lambda: `aws lambda invoke --function-name pci-evidence-snapshot out.json`

### Issue: Config Recorder Stopped

**Symptom**: AWS Config status shows "STOPPED"

**Resolution**:
```bash
aws configservice start-configuration-recorder --configuration-recorder-name <NAME>
aws configservice describe-configuration-recorder-status
```

### Issue: Security Hub No Findings

**Symptom**: Security Hub shows zero findings

**Resolution**:
- Wait 15-30 minutes after enabling (initial scan takes time)
- Verify standard is enabled: `aws securityhub get-enabled-standards`
- Check if resources exist to evaluate

---

## Appendix: Quick Reference Commands

```bash
# Verify AWS credentials
aws sts get-caller-identity

# List evidence artifacts
aws s3 ls s3://<EVIDENCE_BUCKET>/artifacts/ --recursive

# Download specific artifact
aws s3 cp s3://<EVIDENCE_BUCKET>/artifacts/daily/2024-01-15/securityhub_findings_summary.json .

# Manual Lambda invocation
aws lambda invoke --function-name pci-evidence-snapshot output.json && cat output.json

# Check Config status
aws configservice describe-configuration-recorder-status

# Check Security Hub
aws securityhub get-findings --max-results 5

# Re-run manual collector
cd evidence/collectors/python
python3 evidence_collect_basic.py --region us-west-2 --evidence-bucket <BUCKET> --prefix on-demand/$(date +%F)
```

---

**Document Version**: 1.0  
**Last Reviewed**: 2024-01-15  
**Next Review**: 2024-04-15
