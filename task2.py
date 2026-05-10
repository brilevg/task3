import json
import requests
import semantic_version

INPUT_FILE = "result_task_1.json"
OUTPUT_FILE = "result_task_2.json"

GITHUB_TOKEN = ""

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}

GRAPHQL_URL = "https://api.github.com/graphql"

ECOSYSTEM_MAPPING = {
    # JS / TS
    "npm": "NPM",
    "yarn": "NPM",

    # Rust
    "cargo": "RUST",

    # Python
    "pypi": "PIP",
    "pip": "PIP",

    # Java
    "maven": "MAVEN",
    "gradle": "MAVEN",

    # .NET
    "nuget": "NUGET",

    # Go
    "go": "GO",

    # Ruby
    "gem": "RUBYGEMS",

    # PHP
    "composer": "COMPOSER",

    # Swift
    "swift": "SWIFT",

    # Dart
    "pub": "PUB"
}

# ======================================================
# GRAPHQL QUERY
# ======================================================

QUERY = """
query($ecosystem: SecurityAdvisoryEcosystem!, $package: String!) {
  securityVulnerabilities(
    first: 100,
    ecosystem: $ecosystem,
    package: $package
  ) {
    nodes {

      vulnerableVersionRange

      firstPatchedVersion {
        identifier
      }

      package {
        name
        ecosystem
      }

      advisory {
        ghsaId
        severity
        permalink
      }
    }
  }
}
"""

# ======================================================
# SEMVER CHECK
# ======================================================

import re

def normalize_range(vuln_range):
    # Сначала убираем пробел между оператором и версией: "< 0.7.0" -> "<0.7.0"
    vuln_range = re.sub(r'([<>=!]+)\s+', r'\1', vuln_range)
    # Затем заменяем пробелы между условиями на запятые: ">=1.0.0 <2.0.0" -> ">=1.0.0,<2.0.0"
    vuln_range = re.sub(r'\s+', ',', vuln_range)
    # Убираем дублирующиеся запятые
    while ',,' in vuln_range:
        vuln_range = vuln_range.replace(',,', ',')
    return vuln_range.strip(',')


def is_vulnerable(version, vuln_range):

    try:

        version = semantic_version.Version.coerce(version)

        normalized = normalize_range(vuln_range)

        spec = semantic_version.NpmSpec(normalized)

        return version in spec

    except Exception:
        return False


def calculate_secure_version(nodes):
    versions = []
    for node in nodes:
        patched = node.get("firstPatchedVersion")
        if not patched:
            continue
        try:
            versions.append(semantic_version.Version.coerce(patched["identifier"]))
        except:
            pass
    if not versions:
        return None
    return str(max(versions))


# ======================================================
# LOAD PACKAGES
# ======================================================

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    dependencies = json.load(f)

results = []

# ======================================================
# PROCESS
# ======================================================

for dep in dependencies:

    ecosystem = dep["ecosystem"]
    dep["name"]=dep["name"].lstrip("@")
    if ecosystem not in ECOSYSTEM_MAPPING:
        continue

    github_ecosystem = ECOSYSTEM_MAPPING[ecosystem]

    variables = {
        "ecosystem": github_ecosystem,
        "package": dep["name"]
    }

    try:

        response = requests.post(
            GRAPHQL_URL,
            headers=HEADERS,
            json={
                "query": QUERY,
                "variables": variables
            },
            timeout=20
        )
        #print(response.json())
        data = response.json()

        nodes = (
            data
            .get("data", {})
            .get("securityVulnerabilities", {})
            .get("nodes", [])
        )

        vulns = []
        for node in nodes:

            vuln_range = node["vulnerableVersionRange"]
            
            if not is_vulnerable(dep["version"], vuln_range):
                continue

            advisory = node["advisory"]

            patched = None

            if node["firstPatchedVersion"]:
                patched = node["firstPatchedVersion"]["identifier"]

            vulns.append({
                "name": advisory["ghsaId"],
                "severity": advisory["severity"],
                "vulnerable_range": vuln_range,
                "first_patched_version": patched
            })

        result = {
            "name": dep["name"],
            "version": dep["version"],
            "ecosystem": dep["ecosystem"],
            "url": dep["url"],
            "purl": dep["purl"],
            "vulnerabilities": vulns,
            "secure_version": calculate_secure_version(nodes)
        }

        results.append(result)

        print(
            f"[+] {dep['name']} "
            f"{dep['version']} "
            f"-> {len(vulns)} vulns"
        )

    except Exception as e:

        print(f"[ERROR] {dep['name']}")
        print(e)

# ======================================================
# SAVE
# ======================================================

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\nSaved to {OUTPUT_FILE}")