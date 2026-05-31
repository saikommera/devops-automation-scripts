#!/usr/bin/env python3
"""
EKS Cluster Health Check
Checks node status, pod health, HPA scaling, and posts alerts.
Author: Sai Babji Kommera
"""

import boto3
import subprocess
import json
import argparse
import requests
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ClusterHealth:
    name: str
    region: str
    nodes_total: int
    nodes_ready: int
    pods_running: int
    pods_crashing: int
    pods_pending: int
    hpa_maxed: List[str]
    issues: List[str]

    @property
    def healthy(self) -> bool:
        return len(self.issues) == 0

    @property
    def summary(self) -> str:
        icon = "✅" if self.healthy else "⚠️"
        return (
            f"{icon} {self.name}: {self.nodes_ready}/{self.nodes_total} nodes ready | "
            f"{self.pods_crashing} crashing | {self.pods_pending} pending"
        )


def get_eks_clusters(region: str) -> List[str]:
    client = boto3.client("eks", region_name=region)
    return client.list_clusters()["clusters"]


def check_cluster(cluster_name: str, region: str) -> ClusterHealth:
    """Run kubectl checks against an EKS cluster."""
    issues = []
    hpa_maxed = []

    def kubectl(cmd: str) -> dict:
        result = subprocess.run(
            f"kubectl --context=arn:aws:eks:{region}:*:cluster/{cluster_name} {cmd} -o json",
            shell=True, capture_output=True, text=True
        )
        return json.loads(result.stdout) if result.returncode == 0 else {"items": []}

    # Check nodes
    nodes = kubectl("get nodes")["items"]
    nodes_ready = sum(
        1 for n in nodes
        if any(c["type"] == "Ready" and c["status"] == "True"
               for c in n["status"].get("conditions", []))
    )
    if nodes_ready < len(nodes):
        issues.append(f"{len(nodes) - nodes_ready} nodes not ready")

    # Check pods
    pods = kubectl("get pods --all-namespaces")["items"]
    crashing = [p for p in pods if p["status"].get("phase") == "Failed" or
                any(c.get("state", {}).get("waiting", {}).get("reason") == "CrashLoopBackOff"
                    for c in p["status"].get("containerStatuses", []))]
    pending = [p for p in pods if p["status"].get("phase") == "Pending"]
    running = [p for p in pods if p["status"].get("phase") == "Running"]

    if crashing:
        issues.append(f"{len(crashing)} pods in CrashLoopBackOff")
    if len(pending) > 5:
        issues.append(f"{len(pending)} pods pending (possible resource pressure)")

    # Check HPA
    hpas = kubectl("get hpa --all-namespaces")["items"]
    for hpa in hpas:
        current = hpa["status"].get("currentReplicas", 0)
        max_r = hpa["spec"]["maxReplicas"]
        if current >= max_r:
            ns = hpa["metadata"]["namespace"]
            name = hpa["metadata"]["name"]
            hpa_maxed.append(f"{ns}/{name}")
            issues.append(f"HPA {ns}/{name} at max replicas ({max_r})")

    return ClusterHealth(
        name=cluster_name, region=region,
        nodes_total=len(nodes), nodes_ready=nodes_ready,
        pods_running=len(running), pods_crashing=len(crashing),
        pods_pending=len(pending), hpa_maxed=hpa_maxed, issues=issues
    )


def post_to_slack(webhook_url: str, health_checks: List[ClusterHealth]):
    """Post health summary to Slack."""
    unhealthy = [h for h in health_checks if not h.healthy]
    color = "danger" if unhealthy else "good"
    text = "\n".join(h.summary for h in health_checks)

    payload = {
        "attachments": [{
            "color": color,
            "title": f"EKS Health Check — {len(unhealthy)} clusters with issues",
            "text": text,
            "footer": "DevOps Automation | EKS Health Monitor"
        }]
    }
    requests.post(webhook_url, json=payload)


def main():
    parser = argparse.ArgumentParser(description="EKS Cluster Health Check")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--cluster", help="Specific cluster name (default: all)")
    parser.add_argument("--slack-webhook", help="Slack webhook URL for alerts")
    parser.add_argument("--fail-on-issues", action="store_true")
    args = parser.parse_args()

    clusters = [args.cluster] if args.cluster else get_eks_clusters(args.region)
    results = []

    for cluster in clusters:
        print(f"Checking {cluster}...")
        health = check_cluster(cluster, args.region)
        results.append(health)
        print(f"  {health.summary}")
        for issue in health.issues:
            print(f"    ⚠️  {issue}")

    if args.slack_webhook:
        post_to_slack(args.slack_webhook, results)
        print("\nPosted to Slack")

    if args.fail_on_issues and any(not h.healthy for h in results):
        exit(1)


if __name__ == "__main__":
    main()
