# Deployment Checklist

Use this checklist to ensure successful deployment of the PCI DSS Continuous Compliance Lab.

---

## Pre-Deployment

### AWS Account Setup
- [ ] AWS account with admin permissions available
- [ ] AWS CLI v2 installed and configured
- [ ] Verified credentials: `aws sts get-caller-identity`
- [ ] Noted AWS Account ID: ___________________
- [ ] Selected deployment region: ___________________

### Local Tools
- [ ] Terraform >= 1.5 installed: `terraform --version`
- [ ] Python >= 3.11 installed: `python3 --version`
- [ ] Git installed (for version control)
- [ ] Text editor or IDE ready

### Optional Tools
- [ ] Docker installed (for containerized collector)
- [ ] Jenkins configured (for CI/CD pipeline)

---

## Phase 1: Infrastructure Deployment

### Terraform Setup
- [ ] Navigate to `iac/terraform/` directory
- [ ] Review `main.tf` to understand resources
- [ ] Copy `terraform.tfvars.example` to `terraform.tfvars`
- [ ] Customize variables if needed (region, name_prefix)
- [ ] Run `terraform init`
- [ ] Run `terraform plan -out plan.tfplan`
- [ ] Review plan output for correctness
- [ ] Run `terraform apply plan.tfplan`
- [ ] Save outputs: `terraform output > ../../terraform_outputs.txt`

### Record Terraform Outputs
- [ ] Evidence bucket name: ___________________
- [ ] Logs bucket name: ___________________
- [ ] VPC ID: ___________________
- [ ] Lambda role ARN: ___________________

### Verify AWS Resources
- [ ] S3 buckets created: `aws s3 ls | grep pci-cc-lab`
- [ ] VPC created: `aws ec2 describe-vpcs --filters "Name=tag:Name,Values=pci-cc-lab-vpc"`
- [ ] Config recorder enabled: `aws configservice describe-configuration-recorder-status`
- [ ] Security Hub enabled: `aws securityhub get-enabled-standards`

---

## Phase 2: Evidence Collection Setup

### Python Collector
- [ ] Navigate to `evidence/collectors/python/`
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Make script executable: `chmod +x evidence_collect_basic.py` (Linux/Mac)
- [ ] Test help: `python3 evidence_collect_basic.py --help`

### Baseline Collection
- [ ] Run baseline collection:
  ```bash
  python3 evidence_collect_basic.py \
    --region <YOUR_REGION> \
    --evidence-bucket <YOUR_EVIDENCE_BUCKET> \
    --prefix baseline/$(date +%F)
  ```
- [ ] Verify local files created:
  - [ ] `iam_mfa_status.json`
  - [ ] `iam_role_policies.json`
  - [ ] `cloudtrail_recent_events.json`
  - [ ] `collection_summary.json`
- [ ] Verify S3 upload: `aws s3 ls s3://<EVIDENCE_BUCKET>/artifacts/baseline/`

### Update Evidence Register
- [ ] Open `evidence/schema/evidence_register.csv`
- [ ] Update `collected_at` with current timestamp
- [ ] Update `s3_key` with actual paths
- [ ] Add `reviewer` name
- [ ] Set `status` to "collected"

---

## Phase 3: Lambda Automation

### Package Lambda
- [ ] Navigate to `automation/lambda/`
- [ ] Create deployment package: `zip lambda.zip evidence_snapshot.py`
- [ ] Verify zip contents: `unzip -l lambda.zip`

### Deploy Lambda Function
- [ ] Get account ID: `ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)`
- [ ] Get evidence bucket: `EVIDENCE_BUCKET=<from terraform output>`
- [ ] Set region: `REGION=<your region>`
- [ ] Create Lambda function:
  ```bash
  aws lambda create-function \
    --function-name pci-evidence-snapshot \
    --runtime python3.11 \
    --role arn:aws:iam::${ACCOUNT_ID}:role/pci-cc-lab-evidence-lambda-role \
    --handler evidence_snapshot.lambda_handler \
    --timeout 30 \
    --zip-file fileb://lambda.zip \
    --environment Variables="{EVIDENCE_BUCKET=${EVIDENCE_BUCKET},REGION=${REGION}}"
  ```

### Test Lambda
- [ ] Invoke manually: `aws lambda invoke --function-name pci-evidence-snapshot output.json`
- [ ] Check output: `cat output.json`
- [ ] Verify S3 artifacts: `aws s3 ls s3://${EVIDENCE_BUCKET}/artifacts/daily/$(date +%F)/`
- [ ] Expected files:
  - [ ] `securityhub_findings_summary.json`
  - [ ] `aws_config_rules_brief.json`

### Schedule Daily Execution
- [ ] Create EventBridge rule:
  ```bash
  aws events put-rule \
    --name pci-evidence-daily-09utc \
    --schedule-expression "cron(0 9 * * ? *)"
  ```
- [ ] Grant Lambda permission:
  ```bash
  aws lambda add-permission \
    --function-name pci-evidence-snapshot \
    --statement-id ev-perm \
    --action "lambda:InvokeFunction" \
    --principal events.amazonaws.com \
    --source-arn arn:aws:events:${REGION}:${ACCOUNT_ID}:rule/pci-evidence-daily-09utc
  ```
- [ ] Add target:
  ```bash
  aws events put-targets \
    --rule pci-evidence-daily-09utc \
    --targets "Id"="1","Arn"="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:pci-evidence-snapshot"
  ```
- [ ] Verify rule: `aws events describe-rule --name pci-evidence-daily-09utc`

---

## Phase 4: Documentation & Validation

### Update Documentation
- [ ] Review `docs/pci_mapping.md`
- [ ] Update S3 keys with actual paths
- [ ] Add any custom controls or gaps
- [ ] Document current date as "Last Updated"

### Test Runbook
- [ ] Follow `runbooks/audit_evidence_runbook.md`
- [ ] Complete "Pre-Audit Checklist" section
- [ ] Test evidence retrieval commands
- [ ] Verify all artifacts are accessible

### CI/CD Setup (Optional)
- [ ] If using GitHub:
  - [ ] Push code to GitHub repository
  - [ ] Verify `.github/workflows/compliance-ci.yml` runs
  - [ ] Check Actions tab for results
- [ ] If using Jenkins:
  - [ ] Configure Jenkins job with `Jenkinsfile`
  - [ ] Run pipeline manually
  - [ ] Verify all stages pass

---

## Phase 5: Monitoring & Maintenance

### Set Up Monitoring
- [ ] Configure CloudWatch alarms for Lambda failures
- [ ] Set up SNS topic for notifications (optional)
- [ ] Create CloudWatch dashboard for compliance metrics (optional)

### Schedule Regular Reviews
- [ ] Calendar reminder: Review evidence register monthly
- [ ] Calendar reminder: Update PCI mapping quarterly
- [ ] Calendar reminder: Test runbook quarterly
- [ ] Calendar reminder: Review IAM policies quarterly

### Documentation Maintenance
- [ ] Add this lab to your portfolio/resume
- [ ] Take screenshots of:
  - [ ] Terraform apply output
  - [ ] Security Hub dashboard
  - [ ] AWS Config compliance
  - [ ] S3 evidence artifacts
- [ ] Document lessons learned

---

## Validation Tests

### End-to-End Test
- [ ] Verify complete workflow:
  1. [ ] Terraform deployed successfully
  2. [ ] Manual collector ran successfully
  3. [ ] Lambda deployed and tested
  4. [ ] Daily schedule configured
  5. [ ] Evidence artifacts in S3
  6. [ ] Documentation updated

### Security Validation
- [ ] S3 buckets have encryption enabled
- [ ] S3 buckets block public access
- [ ] IAM roles follow least privilege
- [ ] Security groups have default-deny ingress
- [ ] CloudTrail is logging
- [ ] Config recorder is enabled

### Compliance Validation
- [ ] Security Hub PCI standard enabled
- [ ] At least one Config rule active
- [ ] Evidence register has entries
- [ ] PCI mapping document complete
- [ ] Runbook tested successfully

---

## Troubleshooting Completed

If you encountered issues during deployment, document them here:

### Issue 1
- **Problem**: ___________________
- **Solution**: ___________________
- **Prevention**: ___________________

### Issue 2
- **Problem**: ___________________
- **Solution**: ___________________
- **Prevention**: ___________________

---

## Sign-Off

### Deployment Completed By
- **Name**: ___________________
- **Date**: ___________________
- **AWS Account**: ___________________
- **Region**: ___________________

### Verification
- [ ] All checklist items completed
- [ ] Evidence artifacts verified in S3
- [ ] Documentation updated
- [ ] Screenshots captured for portfolio
- [ ] Lab ready for demonstration

---

## Next Steps

1. **Practice**: Run through the audit runbook multiple times
2. **Extend**: Add more collectors (Inspector, GuardDuty, etc.)
3. **Customize**: Tailor to specific PCI requirements for your use case
4. **Present**: Prepare to discuss in interviews
5. **Maintain**: Keep evidence current with regular collections

---

## Cleanup Instructions

When you're ready to tear down the lab:

- [ ] Delete Lambda function: `aws lambda delete-function --function-name pci-evidence-snapshot`
- [ ] Delete EventBridge rule:
  ```bash
  aws events remove-targets --rule pci-evidence-daily-09utc --ids 1
  aws events delete-rule --name pci-evidence-daily-09utc
  ```
- [ ] Download evidence artifacts for safekeeping
- [ ] Run Terraform destroy: `cd iac/terraform && terraform destroy`
- [ ] Verify all resources deleted in AWS Console

**Warning**: Terraform destroy will delete S3 buckets and all evidence artifacts!

---

**Checklist Version**: 1.0  
**Last Updated**: 2024-01-15
