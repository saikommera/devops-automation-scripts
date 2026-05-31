# ⚙️ DevOps Automation Scripts

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python)](https://python.org)
[![AWS](https://img.shields.io/badge/AWS-Automation-FF9900?style=flat-square&logo=amazonaws)](https://aws.amazon.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

Production-grade Python and Bash automation scripts for AWS cost reporting, EKS cluster health monitoring, Terraform drift detection, and incident response automation.

## 📁 Scripts

| Script | Language | Purpose |
|---|---|---|
| `aws/cost_report.py` | Python | Weekly AWS cost breakdown by service + email report |
| `aws/eks_health_check.py` | Python | EKS cluster health, node status, unhealthy pod detection |
| `aws/terraform_drift.py` | Python | Detect and report Terraform state drift |
| `aws/ec2_rightsizing.py` | Python | Identify oversized EC2 instances for FinOps |
| `bash/incident_response.sh` | Bash | Automated incident triage and Slack notification |
| `bash/log_cleanup.sh` | Bash | Automated log rotation and S3 archival |

## 🚀 Setup

```bash
git clone https://github.com/saikommera/devops-automation-scripts.git
cd devops-automation-scripts
pip install -r requirements.txt

# Configure AWS credentials
export AWS_PROFILE=your-profile
export AWS_DEFAULT_REGION=us-east-1
```

## 💰 AWS Cost Report

```bash
# Generate weekly cost report and email to team
python aws/cost_report.py --days 7 --email team@company.com --threshold 1000
```

## 🏥 EKS Health Check

```bash
# Check all clusters in account
python aws/eks_health_check.py --region us-east-1 --alert-slack

# Output example:
# ✅ prod-cluster: 15/15 nodes healthy, 0 pods crashing
# ⚠️  staging-cluster: 1 node not ready, 2 pods in CrashLoopBackOff
```

## 🔍 Terraform Drift Detection

```bash
# Detect drift and post to Slack
python aws/terraform_drift.py --workspace prod --slack-webhook $SLACK_WEBHOOK
```

## 🧑‍💻 Author

**Sai Babji Kommera** — Senior DevOps / SRE Engineer
[LinkedIn](https://www.linkedin.com/in/sai-babji-kommera-a3b953396/) · saibabji1@gmail.com
