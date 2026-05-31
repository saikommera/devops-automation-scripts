#!/usr/bin/env bash
# Automated Incident Response Triage Script
# Author: Sai Babji Kommera
# Usage: ./incident_response.sh --severity P1 --service payment-api --region us-east-1

set -euo pipefail

SEVERITY=""
SERVICE=""
REGION="us-east-1"
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"
RUNBOOK_BASE="https://runbooks.internal"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
alert() { echo "🚨 $*"; }
info()  { echo "ℹ️  $*"; }
ok()    { echo "✅ $*"; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --severity) SEVERITY="$2"; shift 2 ;;
    --service)  SERVICE="$2";  shift 2 ;;
    --region)   REGION="$2";   shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

[[ -z "$SERVICE" ]] && { echo "ERROR: --service required"; exit 1; }
[[ -z "$SEVERITY" ]] && SEVERITY="P2"

INCIDENT_ID="INC-$(date +%Y%m%d%H%M%S)"
log "=== Incident Response: $INCIDENT_ID ==="
log "Service: $SERVICE | Severity: $SEVERITY | Region: $REGION"

# 1. Capture current state
log "--- Capturing system state ---"
info "Checking pod status..."
kubectl get pods -A -l app="$SERVICE" --sort-by='.status.phase' 2>/dev/null || true

info "Recent pod logs (last 100 lines)..."
kubectl logs -l app="$SERVICE" --tail=100 --all-containers 2>/dev/null | tail -50 || true

info "Checking recent deployments..."
kubectl rollout history deployment/"$SERVICE" 2>/dev/null || true

info "Checking HPA status..."
kubectl get hpa "$SERVICE" 2>/dev/null || true

# 2. Check AWS health
log "--- Checking AWS service health ---"
aws health describe-events   --filter "services=${SERVICE^^},eventStatusCodes=open"   --region "$REGION" 2>/dev/null || true

# 3. Check recent CloudWatch alarms
log "--- Active CloudWatch alarms ---"
aws cloudwatch describe-alarms   --state-value ALARM   --region "$REGION"   --query 'MetricAlarms[?contains(AlarmName, `'"$SERVICE"'`)].{Name:AlarmName,State:StateValue,Reason:StateReason}'   --output table 2>/dev/null || true

# 4. Notify team
if [[ -n "$SLACK_WEBHOOK" ]]; then
  log "--- Notifying team via Slack ---"
  PAYLOAD=$(cat <<JSON
{
  "attachments": [{
    "color": "danger",
    "title": "🚨 ${SEVERITY} Incident: ${SERVICE}",
    "fields": [
      {"title": "Incident ID", "value": "${INCIDENT_ID}", "short": true},
      {"title": "Severity",    "value": "${SEVERITY}",    "short": true},
      {"title": "Service",     "value": "${SERVICE}",     "short": true},
      {"title": "Region",      "value": "${REGION}",      "short": true},
      {"title": "Runbook",     "value": "${RUNBOOK_BASE}/${SERVICE}"}
    ],
    "footer": "Incident Response Automation"
  }]
}
JSON
  )
  curl -s -X POST -H "Content-type: application/json" --data "$PAYLOAD" "$SLACK_WEBHOOK"
  ok "Slack notification sent"
fi

log "=== Triage complete: $INCIDENT_ID ==="
log "Next steps: Check runbook at ${RUNBOOK_BASE}/${SERVICE}"
