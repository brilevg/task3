import json
import pandas as pd
from collections import defaultdict

INPUT_FILE = "result_task_2.json"
OUTPUT_FILE = "result_task_3.csv"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

rows = []

for dep in data:

    severity_count = defaultdict(int)

    for vuln in dep.get("vulnerabilities", []):
        severity = vuln.get("severity", "unknown").lower()
        severity_count[severity] += 1

    total_vulns = sum(severity_count.values())
    secure_version = dep.get("secure_version")
    has_fix = secure_version is not None

    # ==========================================
    # STRATEGY LOGIC
    # ==========================================

    if total_vulns == 0:
        strategy = "No action required"

    elif severity_count.get("critical", 0) > 0:
        if has_fix:
            strategy = "Immediate upgrade required (critical vulnerability)"
        else:
            strategy = "Critical: no fix available — consider alternative package"

    elif severity_count.get("high", 0) > 0:
        if has_fix:
            strategy = "Urgent update to secure version"
        else:
            strategy = "High severity: no fix available — monitor advisories"

    elif severity_count.get("moderate", 0) > 0:
        if has_fix:
            strategy = "Planned update recommended"
        else:
            strategy = "Moderate: no fix available — monitor advisories"

    else:
        strategy = "Low risk — monitor updates"

    rows.append({
        "name": dep["name"],
        "version": dep["version"],
        "ecosystem": dep["ecosystem"],

        "critical": severity_count.get("critical", 0),
        "high": severity_count.get("high", 0),
        "moderate": severity_count.get("moderate", 0),
        "low": severity_count.get("low", 0),
        "unknown": severity_count.get("unknown", 0),

        "secure_version": secure_version,
        "has_fix": has_fix,

        "strategy": strategy,

        "total_vulnerabilities": total_vulns
    })

df = pd.DataFrame(rows)
df = df.sort_values(by="total_vulnerabilities", ascending=False)

df.to_csv(OUTPUT_FILE, index=False)

print(df.head(10))
print(f"\nSaved to {OUTPUT_FILE}")