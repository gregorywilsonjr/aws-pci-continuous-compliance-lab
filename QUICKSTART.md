# Quick Start Guide

Get the PCI DSS Continuous Compliance Lab running in 15 minutes.

---

## Prerequisites Check

```bash
# Verify tools are installed
terraform --version    # Should be >= 1.5
aws --version         # Should be AWS CLI v2
python3 --version     # Should be >= 3.11

# Verify AWS credentials
aws sts get-caller-identity
```

---

## Step 1: Deploy Infrastructure (5 minutes)

```bash
cd iac/terraform

# Initialize Terraform
terraform init

# Review the plan
terraform plan -out plan.tfplan

# Apply (creates S3, VPC, Config, Security Hub, IAM)
terraform apply plan.tfplan

# Save outputs
terraform output > ../../terraform_outputs.txt
```

**Note the outputs**: `evidence_bucket_name` and `logs_bucket_name`

---

## Step 2: Verify AWS Services (2 minutes)

```bash
# Check AWS Config
aws configservice describe-configuration-recorders

# Check Security Hub
aws securityhub get-enabled-standards

# List S3 buckets
aws s3 ls | grep pci-cc-lab
```

---

## Step 3: Collect Baseline Evidence (3 minutes)

```bash
cd evidence/collectors/python

# Install dependencies
pip install boto3

# Run collector (replace <BUCKET> with your evidence_bucket_name)
python3 evidence_collect_basic.py \
  --region us-west-2 \
  --evidence-bucket <YOUR_EVIDENCE_BUCKET> \
  --prefix baseline/$(date +%F)
```

**Expected output**: 3 JSON files uploaded to S3

---

## Step 4: Deploy Lambda for Daily Snapshots (5 minutes)

```bash
cd automation/lambda

# Package Lambda
zip lambda.zip evidence_snapshot.py

# Get your account ID and evidence bucket from Terraform outputs
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
EVIDENCE_BUCKET=$(terraform output -raw evidence_bucket_name)
REGION="us-west-2"

# Create Lambda function
aws lambda create-function \
  --function-name pci-evidence-snapshot \
  --runtime python3.11 \
  --role arn:aws:iam::${ACCOUNT_ID}:role/pci-cc-lab-evidence-lambda-role \
  --handler evidence_snapshot.lambda_handler \
  --timeout 30 \
  --zip-file fileb://lambda.zip \
  --environment Variables="{EVIDENCE_BUCKET=${EVIDENCE_BUCKET},REGION=${REGION}}"

# Test Lambda
aws lambda invoke --function-name pci-evidence-snapshot output.json
cat output.json
```

---

## Step 5: Schedule Daily Execution (Optional)

```bash
# Create EventBridge rule for daily 9 AM UTC
aws events put-rule \
  --name pci-evidence-daily-09utc \
  --schedule-expression "cron(0 9 * * ? *)"

# Grant permission
aws lambda add-permission \
  --function-name pci-evidence-snapshot \
  --statement-id ev-perm \
  --action "lambda:InvokeFunction" \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:${REGION}:${ACCOUNT_ID}:rule/pci-evidence-daily-09utc

# Add target
aws events put-targets \
  --rule pci-evidence-daily-09utc \
  --targets "Id"="1","Arn"="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:pci-evidence-snapshot"
```

---

## Verify Everything Works

```bash
# List evidence artifacts
aws s3 ls s3://${EVIDENCE_BUCKET}/artifacts/ --recursive

# Check Security Hub findings
aws securityhub get-findings --max-results 5

# Check Config compliance
aws configservice describe-compliance-by-config-rule
```

---

## Next Steps

1. **Review Evidence**: Check `evidence/schema/evidence_register.csv`
2. **Update Mapping**: Edit `docs/pci_mapping.md` with your findings
3. **Run Runbook**: Follow `runbooks/audit_evidence_runbook.md`
4. **Customize**: Adjust Terraform variables in `iac/terraform/terraform.tfvars`

---

## Cleanup

When you're done with the lab:

```bash
# Delete Lambda and EventBridge rule
aws lambda delete-function --function-name pci-evidence-snapshot
aws events remove-targets --rule pci-evidence-daily-09utc --ids 1
aws events delete-rule --name pci-evidence-daily-09utc

# Destroy Terraform resources
cd iac/terraform
terraform destroy
```

**Warning**: This will delete all S3 buckets and evidence artifacts!

---

## Troubleshooting

**Issue**: Terraform apply fails with "bucket already exists"
- **Fix**: Bucket names must be globally unique. Edit `iac/terraform/variables.tf` and change `name_prefix`

**Issue**: Lambda can't write to S3
- **Fix**: Check IAM role permissions. Verify `EVIDENCE_BUCKET` environment variable is set correctly

**Issue**: Security Hub shows no findings
- **Fix**: Wait 15-30 minutes for initial scan. Verify standard is enabled: `aws securityhub get-enabled-standards`

**Issue**: Python collector fails with "boto3 not found"
- **Fix**: Install boto3: `pip install boto3`

---

## Support

For detailed instructions, see the main [README.md](README.md)

For audit procedures, see [runbooks/audit_evidence_runbook.md](runbooks/audit_evidence_runbook.md)
