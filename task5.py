import json
from collections import defaultdict
from packaging.version import parse as parse_version

# =========================================================
# FILES
# =========================================================

SBOM_BEFORE = "sbom_before.json"
SBOM_AFTER = "sbom_after.json"

OSV_BEFORE = "osv_before.json"
#OSV_AFTER = "osv_after.json"

# =========================================================
# HELPERS
# =========================================================

def load_json(path):

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_sbom_packages(sbom):

    packages = {}

    for comp in sbom.get("components", []):

        name = comp.get("name")

        if not name:
            continue

        packages[name] = {
            "version": comp.get("version"),
            "purl": comp.get("purl"),
            "type": comp.get("type"),
            "bom-ref": comp.get("bom-ref")
        }

    return packages


def extract_vulnerabilities(osv_data):

    vulns_by_package = defaultdict(list)

    results = osv_data.get("results", [])

    for result in results:

        packages = result.get("packages", [])

        vulns = result.get("vulnerabilities", [])

        for pkg in packages:

            pkg_name = pkg.get("package", {}).get("name")

            if not pkg_name:
                continue

            for vuln in vulns:

                vulns_by_package[pkg_name].append({
                    "id": vuln.get("id"),
                    "summary": vuln.get("summary"),
                    "severity": vuln.get("severity", [])
                })

    return vulns_by_package


def compare_packages(before, after):

    added = []
    removed = []
    updated = []
    unchanged = []

    for pkg in before:

        if pkg not in after:

            removed.append(pkg)

        else:

            before_version = before[pkg]["version"]
            after_version = after[pkg]["version"]

            if before_version != after_version:

                updated.append({
                    "name": pkg,
                    "before_version": before_version,
                    "after_version": after_version
                })

            else:

                unchanged.append(pkg)

    for pkg in after:

        if pkg not in before:
            added.append(pkg)

    return {
        "added": added,
        "removed": removed,
        "updated": updated,
        "unchanged": unchanged
    }


def compare_vulnerabilities(before_vulns, after_vulns):

    fixed = []
    new = []
    unchanged = []

    before_ids = set()
    after_ids = set()

    for pkg, vulns in before_vulns.items():

        for vuln in vulns:

            before_ids.add((pkg, vuln["id"]))

    for pkg, vulns in after_vulns.items():

        for vuln in vulns:

            after_ids.add((pkg, vuln["id"]))

    for vuln in before_ids:

        if vuln not in after_ids:
            fixed.append(vuln)

    for vuln in after_ids:

        if vuln not in before_ids:
            new.append(vuln)

    for vuln in before_ids:

        if vuln in after_ids:
            unchanged.append(vuln)

    return {
        "fixed": fixed,
        "new": new,
        "unchanged": unchanged
    }


def count_severity(vulns):

    severity_stats = defaultdict(int)

    for pkg, items in vulns.items():

        for vuln in items:

            severities = vuln.get("severity", [])

            if not severities:
                severity_stats["unknown"] += 1
                continue

            for sev in severities:

                sev_type = sev.get("type", "unknown")

                severity_stats[sev_type] += 1

    return dict(severity_stats)

# =========================================================
# LOAD DATA
# =========================================================

sbom_before = load_json(SBOM_BEFORE)
sbom_after = load_json(SBOM_AFTER)

osv_before = load_json(OSV_BEFORE)
#osv_after = load_json(OSV_AFTER)

# =========================================================
# EXTRACT PACKAGES
# =========================================================

packages_before = extract_sbom_packages(sbom_before)
packages_after = extract_sbom_packages(sbom_after)

# =========================================================
# EXTRACT VULNERABILITIES
# =========================================================

vulns_before = extract_vulnerabilities(osv_before)
vulns_after = extract_vulnerabilities(osv_before) # osv_after, но он пустой

# =========================================================
# COMPARE PACKAGES
# =========================================================

package_diff = compare_packages(
    packages_before,
    packages_after
)

# =========================================================
# COMPARE VULNERABILITIES
# =========================================================

vuln_diff = compare_vulnerabilities(
    vulns_before,
    vulns_after
)

# =========================================================
# SEVERITY STATS
# =========================================================

severity_before = count_severity(vulns_before)
severity_after = count_severity(vulns_after)

# =========================================================
# REPORT
# =========================================================

report = {
    "packages": {
        "before_total": len(packages_before),
        "after_total": len(packages_after),

        "added": len(package_diff["added"]),
        "removed": len(package_diff["removed"]),
        "updated": len(package_diff["updated"]),
        "unchanged": len(package_diff["unchanged"]),

        "updated_packages": package_diff["updated"]
    },

    "vulnerabilities": {
        "before_total_packages": len(vulns_before),
        "after_total_packages": len(vulns_after),

        "fixed_vulnerabilities": len(vuln_diff["fixed"]),
        "new_vulnerabilities": len(vuln_diff["new"]),
        "unchanged_vulnerabilities": len(vuln_diff["unchanged"]),

        "fixed_list": list(vuln_diff["fixed"]),
        "new_list": list(vuln_diff["new"])
    },

    "severity": {
        "before": severity_before,
        "after": severity_after
    }
}

# =========================================================
# SAVE REPORT
# =========================================================

with open(
    "result_task_5_analysis.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        report,
        f,
        indent=2,
        ensure_ascii=False
    )

# =========================================================
# PRINT SUMMARY
# =========================================================

print("\n==============================")
print("PACKAGE ANALYSIS")
print("==============================")

print(f"Before packages: {len(packages_before)}")
print(f"After packages: {len(packages_after)}")

print(f"Updated packages: {len(package_diff['updated'])}")
print(f"Added packages: {len(package_diff['added'])}")
print(f"Removed packages: {len(package_diff['removed'])}")

print("\n==============================")
print("VULNERABILITY ANALYSIS")
print("==============================")

print(f"Fixed vulnerabilities: {len(vuln_diff['fixed'])}")
print(f"New vulnerabilities: {len(vuln_diff['new'])}")
print(f"Unchanged vulnerabilities: {len(vuln_diff['unchanged'])}")

print("\n==============================")
print("SEVERITY ANALYSIS")
print("==============================")

print("Before:")
for k, v in severity_before.items():
    print(f"  {k}: {v}")

print("\nAfter:")
for k, v in severity_after.items():
    print(f"  {k}: {v}")

print("\nSaved: result_task_5_analysis.json")