# Git Upload Guide
## Step-by-Step Instructions for Uploading to GitHub

---

## 📋 Prerequisites

Before starting, ensure you have:
- [ ] Git installed: `git --version`
- [ ] GitHub account created
- [ ] GitHub repository created (or ready to create)
- [ ] Git configured with your name and email

---

## 🚀 Option 1: Upload to New Repository (Recommended)

### Step 1: Configure Git (If Not Already Done)

```bash
# Set your name and email
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Verify configuration
git config --list
```

---

### Step 2: Create GitHub Repository

1. Go to https://github.com
2. Click the **"+"** icon (top right) → **"New repository"**
3. Fill in details:
   - **Repository name:** `aws-pci-continuous-compliance-lab`
   - **Description:** "Automated PCI DSS compliance framework using Terraform, Python, and AWS"
   - **Visibility:** Public (for portfolio) or Private
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
4. Click **"Create repository"**
5. **Copy the repository URL** (e.g., `https://github.com/yourusername/aws-pci-continuous-compliance-lab.git`)

---

### Step 3: Initialize Git in Your Project

```bash
# Navigate to your project directory
cd "/mnt/z/Zero Touch Compliance Engineer/aws_pci_continuous_compliance_lab_FULL"

# Initialize Git repository
git init

# Verify .gitignore exists
ls -la .gitignore
```

---

### Step 4: Review What Will Be Uploaded

```bash
# See what files will be tracked
git status

# Review .gitignore to ensure sensitive files are excluded
cat .gitignore
```

**Important files that should be ignored (already in .gitignore):**
- `*.tfstate` (Terraform state files - contain sensitive data)
- `*.tfstate.backup`
- `.terraform/` (Terraform plugins)
- `terraform.tfvars` (may contain secrets)
- `*.pem`, `*.key` (SSH keys)
- `venv/` (Python virtual environment)
- `__pycache__/` (Python cache)

---

### Step 5: Stage All Files

```bash
# Add all files to staging
git add .

# Verify what's staged
git status

# If you see files that shouldn't be there, remove them:
# git reset HEAD <filename>
```

---

### Step 6: Create Initial Commit

```bash
# Create your first commit
git commit -m "Initial commit: AWS PCI DSS Continuous Compliance Lab

- Complete Terraform infrastructure (VPC, S3, Config, Security Hub)
- Python evidence collectors (baseline and Lambda)
- Comprehensive documentation (README, runbooks, guides)
- CI/CD pipelines (GitHub Actions, Jenkins)
- Interview materials (presentation, talking points, cheat sheet)"

# Verify commit was created
git log --oneline
```

---

### Step 7: Connect to GitHub Repository

```bash
# Add remote repository (replace with your actual URL)
git remote add origin https://github.com/yourusername/aws-pci-continuous-compliance-lab.git

# Verify remote was added
git remote -v
```

---

### Step 8: Push to GitHub

```bash
# Push to GitHub (first time)
git push -u origin main

# If you get an error about 'master' vs 'main', rename the branch:
git branch -M main
git push -u origin main
```

**If prompted for credentials:**
- **Username:** Your GitHub username
- **Password:** Use a Personal Access Token (not your GitHub password)
  - Create token at: https://github.com/settings/tokens
  - Select scopes: `repo` (full control of private repositories)
  - Copy the token and paste it as the password

---

### Step 9: Verify Upload

1. Go to your GitHub repository URL
2. Refresh the page
3. You should see all your files uploaded
4. Check that README.md displays properly
5. Verify sensitive files are NOT uploaded (check for .tfstate files)

---

## 🔄 Option 2: Upload to Existing Repository

### If you already have a repository and want to add this project:

```bash
# Navigate to your project directory
cd "/mnt/z/Zero Touch Compliance Engineer/aws_pci_continuous_compliance_lab_FULL"

# Initialize Git
git init

# Add your existing repository as remote
git remote add origin https://github.com/yourusername/your-existing-repo.git

# Fetch existing branches
git fetch origin

# Create a new branch for this project
git checkout -b pci-compliance-lab

# Add and commit files
git add .
git commit -m "Add PCI DSS Continuous Compliance Lab"

# Push to new branch
git push -u origin pci-compliance-lab
```

Then create a Pull Request on GitHub to merge into main.

---

## 🛡️ Security Checklist (CRITICAL!)

Before pushing, verify these files are NOT in your repository:

```bash
# Check for Terraform state files
find . -name "*.tfstate*"

# Check for AWS credentials
find . -name "credentials" -o -name "config"

# Check for private keys
find . -name "*.pem" -o -name "*.key"

# Check for terraform.tfvars (may contain secrets)
find . -name "terraform.tfvars"
```

**If any of these exist, ensure they're in .gitignore!**

---

## 📝 After Upload: Update README

Update the README.md with your actual GitHub URL:

```bash
# Edit README.md
nano README.md

# Find the placeholder and replace with your actual URL:
# [GitHub Repository](https://github.com/yourusername/aws-pci-continuous-compliance-lab)
```

Then commit and push the change:

```bash
git add README.md
git commit -m "Update GitHub repository URL in README"
git push
```

---

## 🎨 Enhance Your Repository

### Add Repository Topics (Tags)

1. Go to your repository on GitHub
2. Click the gear icon next to "About"
3. Add topics:
   - `aws`
   - `terraform`
   - `pci-dss`
   - `compliance`
   - `security`
   - `automation`
   - `python`
   - `lambda`
   - `devops`
   - `grc`

### Add a Repository Description

In the same "About" section, add:
*"Automated PCI DSS compliance framework using Terraform, Python, and AWS. Reduces audit prep time by 95%."*

### Enable GitHub Pages (Optional)

If you want to host documentation:
1. Go to Settings → Pages
2. Source: Deploy from a branch
3. Branch: main, folder: /docs or /root
4. Save

---

## 🔄 Future Updates: Git Workflow

### Making Changes

```bash
# 1. Check current status
git status

# 2. Pull latest changes (if working with others)
git pull origin main

# 3. Make your changes (edit files)

# 4. Stage changes
git add <filename>
# Or stage all changes:
git add .

# 5. Commit with descriptive message
git commit -m "Add: Description of what you added"
# Or for fixes:
git commit -m "Fix: Description of what you fixed"

# 6. Push to GitHub
git push origin main
```

### Commit Message Best Practices

Use conventional commit format:

```bash
# New features
git commit -m "feat: Add GuardDuty integration to Lambda collector"

# Bug fixes
git commit -m "fix: Correct S3 bucket policy for Config access"

# Documentation
git commit -m "docs: Update runbook with new evidence types"

# Refactoring
git commit -m "refactor: Simplify IAM policy structure"

# Tests
git commit -m "test: Add unit tests for evidence collector"
```

---

## 🌿 Branching Strategy (For Larger Changes)

```bash
# Create a new branch for a feature
git checkout -b feature/add-guardduty

# Make changes and commit
git add .
git commit -m "feat: Add GuardDuty threat detection"

# Push branch to GitHub
git push -u origin feature/add-guardduty

# Create Pull Request on GitHub
# After review and approval, merge to main
```

---

## 🔍 Useful Git Commands

### Check Status
```bash
git status                    # See what's changed
git log --oneline            # See commit history
git log --oneline --graph    # See branch history visually
```

### View Changes
```bash
git diff                     # See unstaged changes
git diff --staged            # See staged changes
git diff HEAD~1              # Compare with previous commit
```

### Undo Changes
```bash
git checkout -- <filename>   # Discard changes to a file
git reset HEAD <filename>    # Unstage a file
git reset --soft HEAD~1      # Undo last commit (keep changes)
git reset --hard HEAD~1      # Undo last commit (discard changes)
```

### Branch Management
```bash
git branch                   # List local branches
git branch -a                # List all branches (including remote)
git branch -d <branch-name>  # Delete local branch
git push origin --delete <branch-name>  # Delete remote branch
```

---

## 🚨 Troubleshooting

### Problem: "Permission denied (publickey)"

**Solution:** Set up SSH key or use HTTPS with Personal Access Token

```bash
# Switch to HTTPS
git remote set-url origin https://github.com/yourusername/repo.git

# Or set up SSH key
ssh-keygen -t ed25519 -C "your.email@example.com"
cat ~/.ssh/id_ed25519.pub
# Copy the output and add to GitHub: Settings → SSH and GPG keys
```

---

### Problem: "fatal: refusing to merge unrelated histories"

**Solution:** Force merge if you're sure

```bash
git pull origin main --allow-unrelated-histories
```

---

### Problem: Accidentally committed sensitive file

**Solution:** Remove from history

```bash
# Remove file from Git but keep locally
git rm --cached <filename>

# Add to .gitignore
echo "<filename>" >> .gitignore

# Commit the removal
git commit -m "Remove sensitive file from tracking"

# If already pushed, you need to rewrite history (DANGEROUS!)
# Only do this if no one else has pulled the repository
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch <filename>" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (WARNING: This rewrites history!)
git push origin --force --all
```

**Better approach:** Delete the repository and create a new one if sensitive data was exposed.

---

### Problem: Large files causing push to fail

**Solution:** Use Git LFS or remove large files

```bash
# Check file sizes
find . -type f -size +50M

# If you have large files, consider Git LFS
git lfs install
git lfs track "*.zip"
git add .gitattributes
```

---

## ✅ Final Checklist

Before considering your upload complete:

- [ ] All files uploaded successfully
- [ ] README.md displays correctly on GitHub
- [ ] No sensitive files in repository (.tfstate, credentials, keys)
- [ ] Repository has description and topics
- [ ] Repository is public (if you want it in your portfolio)
- [ ] Links in documentation point to correct GitHub URL
- [ ] License file is present (MIT)
- [ ] .gitignore is working correctly

---

## 🎯 Next Steps After Upload

1. **Add GitHub Repository URL to your resume/LinkedIn**
   ```
   GitHub: github.com/yourusername/aws-pci-continuous-compliance-lab
   ```

2. **Pin the repository on your GitHub profile**
   - Go to your profile
   - Click "Customize your pins"
   - Select this repository

3. **Share on LinkedIn**
   ```
   Excited to share my latest project: An automated PCI DSS compliance 
   framework that reduces audit prep time by 95%! 
   
   Built with Terraform, Python, AWS Lambda, and more.
   
   Check it out: [GitHub URL]
   
   #CloudSecurity #Compliance #DevOps #AWS #Terraform
   ```

4. **Create a GitHub Actions badge for README**
   ```markdown
   ![CI](https://github.com/yourusername/aws-pci-continuous-compliance-lab/workflows/PCI%20Compliance%20CI/badge.svg)
   ```

---

## 📚 Additional Resources

**Git Documentation:**
- https://git-scm.com/doc
- https://docs.github.com/en/get-started

**Git Tutorials:**
- https://learngitbranching.js.org/ (interactive)
- https://www.atlassian.com/git/tutorials

**GitHub Best Practices:**
- https://docs.github.com/en/repositories/creating-and-managing-repositories/best-practices-for-repositories

---

**Ready to upload? Follow the steps above and you'll have your project on GitHub in 10-15 minutes!** 🚀
