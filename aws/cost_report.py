#!/usr/bin/env python3
"""
AWS Cost Report Generator
Fetches cost breakdown by service and sends email/Slack summary.
Author: Sai Babji Kommera
"""

import boto3
import json
import argparse
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List


def get_cost_by_service(days: int = 7) -> Dict:
    """Fetch AWS cost breakdown by service for the past N days."""
    client = boto3.client("ce", region_name="us-east-1")

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    response = client.get_cost_and_usage(
        TimePeriod={"Start": start_date, "End": end_date},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
        GroupBy=[
            {"Type": "DIMENSION", "Key": "SERVICE"},
            {"Type": "TAG", "Key": "Environment"},
        ],
    )

    services = {}
    for result in response["ResultsByTime"]:
        for group in result["Groups"]:
            service = group["Keys"][0]
            env = group["Keys"][1] if len(group["Keys"]) > 1 else "untagged"
            cost = float(group["Metrics"]["UnblendedCost"]["Amount"])
            if cost > 0:
                services[f"{service} ({env})"] = round(cost, 2)

    return dict(sorted(services.items(), key=lambda x: x[1], reverse=True))


def get_cost_anomalies() -> List[Dict]:
    """Detect cost anomalies using AWS Cost Anomaly Detection."""
    client = boto3.client("ce", region_name="us-east-1")
    response = client.get_anomalies(
        DateInterval={
            "StartDate": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
            "EndDate": datetime.now().strftime("%Y-%m-%d"),
        }
    )
    return response.get("Anomalies", [])


def format_report(costs: Dict, anomalies: List, threshold: float) -> str:
    """Format the cost report as HTML."""
    total = sum(costs.values())
    alert = "🚨 OVER BUDGET" if total > threshold else "✅ Within Budget"

    rows = "".join(
        f"<tr><td>{svc}</td><td>${cost:,.2f}</td>"
        f"<td>{'🔴' if cost > threshold * 0.3 else '🟡' if cost > threshold * 0.1 else '🟢'}</td></tr>"
        for svc, cost in list(costs.items())[:15]
    )

    anomaly_section = ""
    if anomalies:
        anomaly_section = f"<h3>⚠️ Cost Anomalies Detected ({len(anomalies)})</h3><ul>"
        for a in anomalies[:5]:
            anomaly_section += f"<li>{a.get('RootCauses', [{}])[0].get('Service', 'Unknown')}: ${a['Impact']['TotalImpact']:,.2f} impact</li>"
        anomaly_section += "</ul>"

    return f"""
    <html><body>
    <h2>AWS Cost Report — {datetime.now().strftime('%Y-%m-%d')} {alert}</h2>
    <p><strong>Total: ${total:,.2f}</strong> | Budget: ${threshold:,.2f}</p>
    <table border='1' cellpadding='5'>
    <tr><th>Service</th><th>Cost</th><th>Status</th></tr>
    {rows}
    </table>
    {anomaly_section}
    </body></html>
    """


def main():
    parser = argparse.ArgumentParser(description="AWS Cost Report Generator")
    parser.add_argument("--days", type=int, default=7, help="Days to report on")
    parser.add_argument("--email", type=str, help="Email recipient")
    parser.add_argument("--threshold", type=float, default=5000, help="Budget threshold USD")
    parser.add_argument("--output", choices=["print", "json"], default="print")
    args = parser.parse_args()

    print(f"Fetching AWS costs for last {args.days} days...")
    costs = get_cost_by_service(args.days)
    anomalies = get_cost_anomalies()

    if args.output == "json":
        print(json.dumps({"costs": costs, "total": sum(costs.values())}, indent=2))
        return

    total = sum(costs.values())
    print(f"\nTotal AWS spend: ${total:,.2f}")
    print(f"Budget threshold: ${args.threshold:,.2f}")
    print(f"Status: {'OVER BUDGET 🚨' if total > args.threshold else 'Within Budget ✅'}")
    print("\nTop 10 services:")
    for svc, cost in list(costs.items())[:10]:
        print(f"  {svc:<50} ${cost:>10,.2f}")

    if anomalies:
        print(f"\n⚠️  {len(anomalies)} cost anomalies detected!")

    if args.email:
        report_html = format_report(costs, anomalies, args.threshold)
        print(f"\nReport would be emailed to {args.email}")


if __name__ == "__main__":
    main()
