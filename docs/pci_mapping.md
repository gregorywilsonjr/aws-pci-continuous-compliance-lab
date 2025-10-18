# PCI DSS v4.0.1 Control Mapping

This document maps PCI DSS v4.0.1 requirements to technical controls and evidence artifacts.

---

## Requirement 1: Install and Maintain Network Security Controls

### 1.2.1 - Configuration files for NSCs are reviewed at least once every six months

**Control Intent**: Ensure firewall and network security controls are properly configured and reviewed regularly.

**AWS Implementation**:
- **VPC Security Groups**: Defined in Terraform (`iac/terraform/main.tf`)
- **Default-deny ingress**: Security group has no inbound rules by default
- **Explicit HTTPS egress**: Only port 443 outbound for AWS API calls

**Evidence Artifacts**:
- S3 Key: `artifacts/baseline/YYYY-MM-DD/security_groups.json` (to be collected)
- Terraform state: `iac/terraform/terraform.tfstate`
- AWS Config Rule: `vpc-sg-open-only-to-authorized-ports`

**Runbook Section**: See `runbooks/audit_evidence_runbook.md` § Network Controls

---

## Requirement 2: Apply Secure Configurations to All System Components

### 2.2.1 - Configuration standards are defined and implemented

**Control Intent**: Harden systems according to industry standards (CIS, NIST).

**AWS Implementation**:
- **Security Hub PCI Standard**: Automated checks for secure configurations
- **AWS Config Rules**: Continuous monitoring of resource compliance

**Evidence Artifacts**:
- S3 Key: `artifacts/daily/YYYY-MM-DD/securityhub_findings_summary.json`
- S3 Key: `artifacts/daily/YYYY-MM-DD/aws_config_rules_brief.json`

**Runbook Section**: See `runbooks/audit_evidence_runbook.md` § Security Hub Findings

---

## Requirement 7: Restrict Access to System Components and Cardholder Data

### 7.2.1 - Access control systems ensure access based on need to know

**Control Intent**: Implement least privilege access controls.

**AWS Implementation**:
- **IAM Roles with Minimal Policies**: Defined in Terraform
- **Policy Review**: Manual collector captures all role policies for review

**Evidence Artifacts**:
- S3 Key: `artifacts/baseline/YYYY-MM-DD/iam_role_policies.json`
- Terraform code: `iac/terraform/main.tf` (IAM role definitions)

**Runbook Section**: See `runbooks/audit_evidence_runbook.md` § IAM Policy Review

---

## Requirement 8: Identify Users and Authenticate Access

### 8.3.1 - Multi-factor authentication for all non-console administrative access

**Control Intent**: Require MFA for all privileged access.

**AWS Implementation**:
- **IAM User MFA**: Enforced via IAM policies (to be added)
- **MFA Status Collector**: Python script captures current MFA status

**Evidence Artifacts**:
- S3 Key: `artifacts/baseline/YYYY-MM-DD/iam_mfa_status.json`

**Runbook Section**: See `runbooks/audit_evidence_runbook.md` § MFA Verification

**Gap**: Add IAM policy to enforce MFA for console access (future enhancement)

---

## Requirement 10: Log and Monitor All Access to System Components

### 10.2 - Implement automated audit trails

**Control Intent**: Capture all administrative actions and changes.

**AWS Implementation**:
- **CloudTrail**: Enabled by default in AWS accounts
- **S3 Log Bucket**: Terraform creates encrypted bucket for Config/CloudTrail logs
- **Event Collector**: Python script captures recent admin events

**Evidence Artifacts**:
- S3 Key: `artifacts/baseline/YYYY-MM-DD/cloudtrail_recent_events.json`
- CloudTrail logs: `s3://<LOGS_BUCKET>/AWSLogs/`

**Runbook Section**: See `runbooks/audit_evidence_runbook.md` § Audit Log Review

---

## Requirement 11: Test Security of Systems and Networks Regularly

### 11.5.1 - Deploy a change-detection mechanism

**Control Intent**: Detect unauthorized changes to critical files and configurations.

**AWS Implementation**:
- **AWS Config**: Continuous recording of resource configurations
- **Config Rules**: Automated compliance checks

**Evidence Artifacts**:
- S3 Key: `artifacts/daily/YYYY-MM-DD/aws_config_rules_brief.json`
- Config snapshots: `s3://<LOGS_BUCKET>/AWSLogs/<ACCOUNT>/Config/`

**Runbook Section**: See `runbooks/audit_evidence_runbook.md` § Change Detection

**Future Enhancement**: Add AWS Inspector for vulnerability scanning (Req. 11.3)

---

## Requirement 12: Support Information Security with Organizational Policies

### 12.10.1 - Incident response plan is created and implemented

**Control Intent**: Document and test incident response procedures.

**AWS Implementation**:
- **EventBridge Rules**: Automated alerting (to be configured)
- **Lambda Functions**: Automated evidence collection

**Evidence Artifacts**:
- This repository serves as the documented response framework
- Runbook: `runbooks/audit_evidence_runbook.md`

**Runbook Section**: See `runbooks/audit_evidence_runbook.md` § Incident Response

---

## Evidence Traceability Matrix

| PCI Req | Control | AWS Service | Evidence Location | Collection Method |
|---------|---------|-------------|-------------------|-------------------|
| 1.2.1 | Network Controls | VPC, Security Groups | `artifacts/baseline/*/security_groups.json` | Manual collector (TBD) |
| 2.2.1 | Secure Config | Security Hub | `artifacts/daily/*/securityhub_findings_summary.json` | Lambda (daily) |
| 7.2.1 | Least Privilege | IAM | `artifacts/baseline/*/iam_role_policies.json` | Manual collector |
| 8.3.1 | MFA | IAM | `artifacts/baseline/*/iam_mfa_status.json` | Manual collector |
| 10.2 | Audit Logging | CloudTrail | `artifacts/baseline/*/cloudtrail_recent_events.json` | Manual collector |
| 11.5.1 | Change Detection | AWS Config | `artifacts/daily/*/aws_config_rules_brief.json` | Lambda (daily) |

---

## Gaps and Future Enhancements

1. **Req. 11.3 (Vulnerability Scanning)**: Add AWS Inspector integration
2. **Req. 1.2.1 (Network Review)**: Add security group collector to Python script
3. **Req. 8.3.1 (MFA Enforcement)**: Add IAM policy to require MFA for console
4. **Req. 10.6 (Log Review)**: Add automated log analysis with CloudWatch Insights
5. **Req. 12.3 (Risk Assessment)**: Document risk assessment process

---

**Last Updated**: 2024-01-15  
**Maintained By**: GRC Engineering Team  
**Review Frequency**: Quarterly
