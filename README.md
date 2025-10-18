# AWS PCI DSS v4.0.1 Continuous Compliance Lab — End‑to‑End Guide

This is a **full lab** that demonstrates how to operationalize **PCI DSS v4.0.1** in a **SaaS‑style AWS account** using a focused toolkit aligned with the **DevOps tools** stack — i.e., **AWS CLI, Terraform, Docker, Jenkins, and Python (Boto3)** — plus a tiny amount of AWS‑native services (**AWS Config, Security Hub, CloudTrail, EventBridge, Lambda**) only where absolutely necessary.

> Why this lab?  
> Hiring managers want proof you can **translate control intent → technical guardrails → continuous evidence**. This lab gives you exactly that: infra as code, guardrails as code, and **automated, auditable artifacts** that map to selected PCI DSS v4.0.1 requirements (focus on **Req. 1, 2, 7, 8, 10, 11, 12**).

---

## What You Will Build (at a glance)

```
+--------------------------------------------------------------+
|                     PCI Continuous Compliance                |
|                                                              |
|  Terraform IaC                                               |
|   ├─ VPC, Subnet, SGs, S3(Log/Evidence), IAM Roles           |
|   ├─ AWS Config (recorder + delivery)                        |
|   └─ Security Hub (PCI standard subscription)                |
|                                                              |
|  Automated Evidence                                          |
|   ├─ EventBridge -> Lambda (daily snapshot to S3)            |
|   └─ Manual Python Collector (MFA, IAM Policies, CloudTrail) |
|                                                              |
|  CI (optional, DevOps-style)                                    |
|   └─ GitHub Actions or Jenkins → Lint & run collectors       |
+--------------------------------------------------------------+
```

**Outcomes you can show in interviews**  
- A repo that reads like a **GRC Engineering portfolio** (WHAT/WHY comments everywhere)  
- A repeatable IaC plan that **bakes in guardrails** (AWS Config / Security Hub)  
- **Timestamped evidence artifacts** in S3 proving ongoing control operation  
- A **mapping & runbook** that reduces audit prep from weeks to hours

---

## Toolkit Alignment (DevOps Focus)

We intentionally keep to the DevOps tooling family — **Terraform, AWS CLI, Docker, Jenkins, Python** — so you stay inside one mental model while you grow the lab. 

> Reference: The DevOps tools overview spans AWS, Terraform, Docker, Jenkins, Python modules, and aligns with our selected tools for this lab. fileciteturn0file0

---

## Prerequisites

- **AWS Account** with permissions to create: VPC, S3, IAM, AWS Config, CloudTrail (enabled by default in most orgs), Security Hub, Lambda, EventBridge.
- **Local tools**
  - **Terraform ≥ 1.5**
  - **AWS CLI v2**, configured (`aws configure sso` or access keys)
  - **Python ≥ 3.11** with `boto3` installed
  - **(Optional) PowerShell 7+** on Windows jump hosts
  - **(Optional) Docker** if you want to containerize collectors (DevOps‑style)
  - **(Optional) Jenkins** if you want to run collectors via CI

- **Clone this repo** (or unzip the provided archive) to your workstation:

```bash
unzip aws_pci_continuous_compliance_lab.zip -d .
cd aws_pci_continuous_compliance_lab
```

---

## Step 0 — Repo Tour (WHAT/WHY)

- `iac/terraform/` — Builds the minimal **foundation** and **guardrails**:
  - S3 buckets (`*-logs`, `*-evidence`) with encryption and public‑access blocks (**WHY**: Req. 10 logging, chain‑of‑custody for evidence)
  - VPC + private subnet (**WHY**: Req. 1 network segmentation/ingress control)
  - AWS Config recorder + delivery to logs bucket (**WHY**: continuous evaluation)
  - Security Hub account + **PCI standard** subscription (**WHY**: rule bundle & findings)
  - IAM role/policy for evidence Lambda (**WHY**: controlled least‑privilege, Req. 7)
- `automation/lambda/evidence_snapshot.py` — Daily snapshot to S3 of **Security Hub** and **AWS Config** summaries (**WHY**: auditor‑friendly, time‑boxed artifacts)
- `evidence/collectors/python/evidence_collect_basic.py` — Manual collector for **MFA status (Req. 8), IAM policy review (Req. 7), CloudTrail events (Req. 10)**
- `evidence/schema/evidence_register.csv` — Evidence catalog you’ll fill in as you go
- `docs/pci_mapping.md` — PCI cross‑walk starter; extend as you add collectors
- `runbooks/audit_evidence_runbook.md` — Scripted retrieval path for audits

---

## Step 1 — Configure AWS Credentials (WHAT/WHY)

**WHAT**: Authenticate the AWS CLI with a role that can create the lab resources.  
**WHY**: Every artifact we create must be traceable to a principal (chain‑of‑custody).

```bash
aws sts get-caller-identity
```

Expected: JSON with your `Account` and `Arn`. Save the role name in your notes.

---

## Step 2 — Deploy the Foundation with Terraform (WHAT/WHY)

**WHAT**: Create S3 (logs/evidence), VPC/subnet, AWS Config, Security Hub, IAM role/policy.  
**WHY**: Encode control intent as **code** so it’s auditable and repeatable.

```bash
cd iac/terraform
terraform init
terraform plan -out plan.tfplan
terraform apply plan.tfplan
```

**Outputs to note**: `evidence_bucket_name`, `logs_bucket`.

**Verify**:
```bash
aws configservice describe-configuration-recorders
aws securityhub get-enabled-standards
aws s3 ls s3://<YOUR-LOGS-BUCKET>
```

> Tip (DevOps style): Add remote state in S3 later (`terraform backend "s3"`), mirroring the “Configure a Shared Remote State” demo project.

---

## Step 3 — Enable the PCI Standard in Security Hub (WHAT/WHY)

Terraform already enables Security Hub and subscribes to the **PCI DSS** standard (lab uses the current ARN available in code).  
**WHY**: You inherit a curated set of checks/findings aligned to PCI, useful for posture KPIs.

**Check it**:
```bash
aws securityhub get-enabled-standards
aws securityhub get-findings --max-results 10
```

Expected: A non‑empty list of `StandardsSubscriptions` and (eventually) findings.

---

## Step 4 — Create the Evidence S3 Folder Structure (WHAT/WHY)

**WHAT**: Keep artifacts in predictable prefixes.  
**WHY**: Auditors love consistent paths and timestamps.

We’ll use these patterns:
- `artifacts/baseline/YYYY-MM-DD/*`
- `artifacts/daily/YYYY-MM-DD/*`
- `artifacts/on-demand/<ticket or incident id>/*`

You don’t need to pre‑create folders in S3; the collectors will write keys.

---

## Step 5 — Seed a Baseline with the Manual Python Collector (WHAT/WHY)

**WHAT**: Capture first proof for **Req. 7/8/10**.  
**WHY**: Establish starting posture; demonstrates that you can pull the exact artifacts assessors ask for.

```bash
cd evidence/collectors/python
python3 -m pip install --user boto3
./evidence_collect_basic.py --region us-west-2 \
  --evidence-bucket <EVIDENCE_BUCKET_FROM_TF_OUTPUT> \
  --prefix baseline/$(date +%F)
```

Expected local files (also uploaded to S3):
- `iam_mfa_status.json` — Who has MFA? (Req. 8)  
- `iam_role_policies.json` — What’s attached? (Req. 7, least privilege review)  
- `cloudtrail_recent_events.json` — Admin/Change events (Req. 10)

**Update the Evidence Register**: edit `evidence/schema/evidence_register.csv` and fill `collected_at` (UTC ISO), `hash` (optional), `reviewer`, `status`.

---

## Step 6 — Automate Daily Snapshots with Lambda + EventBridge (WHAT/WHY)

**WHAT**: Schedule a daily **Security Hub & AWS Config** summary snapshot to S3.  
**WHY**: Demonstrates **continuous** compliance (audit‑ready, every day).

1) **Package/Deploy the Lambda**
   - Environment variables:
     - `EVIDENCE_BUCKET` = your evidence bucket name
     - `REGION` = e.g., `us-west-2`  
   - Role is created by Terraform: `${name_prefix}-evidence-lambda-role`

You can deploy via console to keep it simple, or package with ZIP:

```bash
cd automation/lambda
zip lambda.zip evidence_snapshot.py
# Create function (console or CLI). Example with CLI:
aws lambda create-function \
  --function-name pci-evidence-snapshot \
  --runtime python3.11 \
  --role arn:aws:iam::<ACCOUNT_ID>:role/pci-cc-lab-evidence-lambda-role \
  --handler evidence_snapshot.lambda_handler \
  --timeout 30 \
  --zip-file fileb://lambda.zip \
  --environment Variables="{EVIDENCE_BUCKET=<EVIDENCE_BUCKET>,REGION=us-west-2}"
```

2) **Create an EventBridge (CloudWatch Events) rule** to trigger daily at 09:00 UTC:

```bash
aws events put-rule \
  --name pci-evidence-daily-09utc \
  --schedule-expression "cron(0 9 * * ? *)"

aws lambda add-permission \
  --function-name pci-evidence-snapshot \
  --statement-id ev-perm \
  --action "lambda:InvokeFunction" \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:<REGION>:<ACCOUNT_ID>:rule/pci-evidence-daily-09utc

aws events put-targets \
  --rule pci-evidence-daily-09utc \
  --targets "Id"="1","Arn"="arn:aws:lambda:<REGION>:<ACCOUNT_ID>:function:pci-evidence-snapshot"
```

3) **Validate first run** (invoke once manually):

```bash
aws lambda invoke --function-name pci-evidence-snapshot out.json && cat out.json
aws s3 ls s3://<EVIDENCE_BUCKET>/artifacts/daily/$(date +%F)/
```

Expected S3 keys:
- `securityhub_findings_summary.json`
- `aws_config_rules_brief.json`

---

## Step 7 — Optional DevOps‑Style CI Hooks (Lint & Collectors)

Keeping with the DevOps spirit, you can use **Jenkins** or **GitHub Actions** to run basic checks on every PR:

- **GitHub Actions** (already included): `.github/workflows/compliance-ci.yml`
  - `terraform fmt -check`
  - Python lint via `ruff`
- **Jenkins**: mirror the CI stages and add a simple stage that runs the Python collector in **read‑only** mode (no S3 upload) as a smoke test.

**WHY**: Treat compliance like software. Everything changes through PRs, everything is tested.

---

## Step 8 — Map Controls to Evidence (WHAT/WHY)

Open `docs/pci_mapping.md` and extend it as you add more checks. For each row:
- **PCI Requirement** → **Control intent** → **AWS service/config** → **Evidence path**
- Link to the **exact S3 key** and the **runbook** section

**WHY**: This is what makes your lab interview‑ready — it mirrors an assessor’s traceability matrix.

---

## Step 9 — Runbook: How to Hand Evidence to an Assessor

1. Validate caller identity (`aws sts get-caller-identity`) and note role in the package.  
2. Export the day’s artifact list from the `artifacts/daily/YYYY-MM-DD/` prefix.  
3. Provide the Evidence Register CSV with the rows referencing those keys.  
4. Attach the latest `securityhub_findings_summary.json` and `aws_config_rules_brief.json`.  
5. Include `iam_mfa_status.json` and `iam_role_policies.json` from your latest baseline/on‑demand run.  
6. Provide `docs/pci_mapping.md` so the assessor can navigate requirement → evidence.

---

## Step 10 — Troubleshooting & Common Pitfalls

- **Security Hub shows no findings yet**  
  It can take minutes to populate. Verify the standard is enabled. Run:
  ```bash
  aws securityhub get-enabled-standards
  aws securityhub get-findings --max-results 10
  ```

- **Lambda cannot write to S3**  
  Check the function environment variables and the IAM policy attached to the Lambda role. The Terraform policy grants `s3:PutObject` to `*` in the lab for simplicity.

- **Config recorder is `STOPPED`**  
  Ensure the **delivery channel** exists and the recorder status is set to **enabled**. Re‑run:
  ```bash
  aws configservice describe-configuration-recorder-status
  ```

- **MFA list is empty**  
  Your account may be using AWS SSO/Identity Center. For the lab, the MFA collector looks at classic IAM users. That’s OK — include a note in `docs/pci_mapping.md` about IdP‑backed MFA and attach screenshots/policy references if needed.

---

## Next Expansions (only when necessary)

- **Req. 11 (Vuln scans)**: Add **AWS Inspector** and export findings JSON daily.  
- **Req. 2 (Secure config)**: Add **SSM State Manager** associations (CIS hardening) and export compliance reports.  
- **Req. 10 (Log retention)**: Export CloudTrail retention & bucket lifecycle policies as artifacts.  
- **Dashboards**: Use **QuickSight** or **Grafana** to trend Security Hub counts and Config rule health.

Keep your toolkit disciplined — only add services when a control needs them.

---

## Deliverables Checklist (portfolio‑ready)

- ✅ Terraform plan/apply output (PDF or text)  
- ✅ S3 evidence prefix with **daily** JSONs and **baseline** JSONs  
- ✅ Completed rows in `evidence_register.csv`  
- ✅ Updated `docs/pci_mapping.md` with links to S3 keys  
- ✅ Screenshot of **Security Hub** standards enabled & sample findings  
- ✅ Screenshot of **Config recorder** enabled  
- ✅ Runbook (`runbooks/audit_evidence_runbook.md`) followed successfully

---

## Security & Cost Notes

- **Costs** should be minimal in a single region with low data volume (S3 storage, Config recording, Security Hub). Clean up when done.  
- **Never** keep real secrets or cardholder data in this lab. Evidence JSON contains metadata only.  
- Tighten IAM policies to least privilege if you lift this into production.

---

## Clean Up

```bash
cd iac/terraform
terraform destroy
# Also delete the Lambda function & EventBridge rule if you created them outside TF.
```

---

### Appendix A — Commands Reference

- **List S3 evidence keys**  
  `aws s3 ls s3://<EVIDENCE_BUCKET>/artifacts/ --recursive`
- **Manual Lambda run**  
  `aws lambda invoke --function-name pci-evidence-snapshot out.json`
- **Config status**  
  `aws configservice describe-configuration-recorder-status`
- **Security Hub quick check**  
  `aws securityhub get-findings --max-results 5`

---

**Author’s note**: This lab is designed to “cement a hiring decision” by proving you can *operationalize* PCI requirements with a DevOps toolkit — a small set of tools, high leverage, lots of automation.
