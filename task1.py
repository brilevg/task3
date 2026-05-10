import os
import json
import re
from collections import defaultdict

# =========================
# CONFIG
# =========================

REPO_PATH = "./next.js" # ./next.js-12.0.0 
OUTPUT_FILE = "result_task_1.json"

DEPENDENCY_FIELDS = [
    "dependencies",
    "devDependencies",
    "peerDependencies",
    "optionalDependencies"
]

# =========================
# STORAGE
# =========================

seen = set()
results = []
ecosystem_stats = defaultdict(int)

# =========================
# ECOSYSTEM CONFIG
# =========================

ECOSYSTEM_INFO = {
    "npm": {
        "url": "https://www.npmjs.com/package/{}",
        "purl": "pkg:npm/{}@{}"
    },
    "cargo": {
        "url": "https://crates.io/crates/{}",
        "purl": "pkg:cargo/{}@{}"
    },
    "pypi": {
        "url": "https://pypi.org/project/{}",
        "purl": "pkg:pypi/{}@{}"
    },
    "maven": {
        "url": "https://search.maven.org/artifact/{}",
        "purl": "pkg:maven/{}@{}"
    },
    "nuget": {
        "url": "https://www.nuget.org/packages/{}",
        "purl": "pkg:nuget/{}@{}"
    },
    "gem": {
        "url": "https://rubygems.org/gems/{}",
        "purl": "pkg:gem/{}@{}"
    },
    "composer": {
        "url": "https://packagist.org/packages/{}",
        "purl": "pkg:composer/{}@{}"
    },
    "go": {
        "url": "https://pkg.go.dev/{}",
        "purl": "pkg:golang/{}@{}"
    }
}

# =========================
# HELPERS
# =========================

def normalize_version(version: str) -> str:

    if not isinstance(version, str):
        return str(version)

    prefixes = [
        "workspace:",
        "^",
        "~",
        ">=",
        "<=",
        ">",
        "<",
        "="
    ]

    for prefix in prefixes:
        if version.startswith(prefix):
            version = version[len(prefix):]

    return version.strip()


def add_dependency(name, version, ecosystem):

    version = normalize_version(version)

    if version == "" or version.startswith("*"):
        return

    key = (name, version, ecosystem)

    if key in seen:
        return

    seen.add(key)

    ecosystem_data = ECOSYSTEM_INFO.get(ecosystem)

    if ecosystem_data:

        url = ecosystem_data["url"].format(name)
        purl = ecosystem_data["purl"].format(name, version)

    else:
        url = ""
        purl = ""

    results.append({
        "name": name,
        "version": version,
        "ecosystem": ecosystem,
        "url": url,
        "purl": purl
    })

    ecosystem_stats[ecosystem] += 1


# =========================
# PARSE package.json
# =========================

def parse_package_json(filepath):

    try:

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        for field in DEPENDENCY_FIELDS:

            deps = data.get(field, {})

            if isinstance(deps, dict):

                for name, version in deps.items():
                    add_dependency(name, version, "npm")

    except Exception as e:

        print(f"[ERROR] package.json -> {filepath}")
        print(e)


# =========================
# PARSE Cargo.toml
# =========================

def parse_cargo_toml(filepath):

    try:

        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        current_section = None

        cargo_sections = [
            "dependencies",
            "dev-dependencies",
            "build-dependencies"
        ]

        section_pattern = re.compile(r"^\[(.+)]$")
        dep_pattern = re.compile(r'^([A-Za-z0-9_\-]+)\s*=\s*"([^"]+)"')
        dep_table_pattern = re.compile(
            r'^([A-Za-z0-9_\-]+)\s*=\s*\{(.+)\}'
        )

        for line in lines:

            line = line.strip()

            if not line or line.startswith("#"):
                continue

            section_match = section_pattern.match(line)

            if section_match:
                current_section = section_match.group(1)
                continue

            if current_section not in cargo_sections:
                continue

            match_simple = dep_pattern.match(line)

            if match_simple:

                name = match_simple.group(1)
                version = match_simple.group(2)

                add_dependency(name, version, "cargo")
                continue

            match_table = dep_table_pattern.match(line)

            if match_table:

                name = match_table.group(1)
                content = match_table.group(2)

                version_match = re.search(
                    r'version\s*=\s*"([^"]+)"',
                    content
                )

                if version_match:

                    version = version_match.group(1)

                    add_dependency(name, version, "cargo")

    except Exception as e:

        print(f"[ERROR] Cargo.toml -> {filepath}")
        print(e)


# =========================
# PARSE requirements.txt
# =========================

def parse_requirements_txt(filepath):

    try:

        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line in lines:

            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if "==" in line:

                name, version = line.split("==", 1)

                add_dependency(
                    name.strip(),
                    version.strip(),
                    "pypi"
                )

    except Exception as e:

        print(f"[ERROR] requirements.txt -> {filepath}")
        print(e)


# =========================
# PARSE pom.xml
# =========================

def parse_pom_xml(filepath):

    try:

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        dependency_pattern = re.findall(
            r"<dependency>.*?<groupId>(.*?)</groupId>.*?<artifactId>(.*?)</artifactId>.*?<version>(.*?)</version>.*?</dependency>",
            content,
            re.DOTALL
        )

        for group_id, artifact_id, version in dependency_pattern:

            name = f"{group_id}:{artifact_id}"

            add_dependency(
                name.strip(),
                version.strip(),
                "maven"
            )

    except Exception as e:

        print(f"[ERROR] pom.xml -> {filepath}")
        print(e)


# =========================
# PARSE Gemfile.lock
# =========================

def parse_gemfile_lock(filepath):

    try:

        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        gem_pattern = re.compile(r"^\s{4}([A-Za-z0-9_\-]+)\s\((.*?)\)")

        for line in lines:

            match = gem_pattern.match(line)

            if match:

                name = match.group(1)
                version = match.group(2)

                add_dependency(name, version, "gem")

    except Exception as e:

        print(f"[ERROR] Gemfile.lock -> {filepath}")
        print(e)


# =========================
# PARSE composer.json
# =========================

def parse_composer_json(filepath):

    try:

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        composer_fields = [
            "require",
            "require-dev"
        ]

        for field in composer_fields:

            deps = data.get(field, {})

            if isinstance(deps, dict):

                for name, version in deps.items():

                    add_dependency(
                        name,
                        version,
                        "composer"
                    )

    except Exception as e:

        print(f"[ERROR] composer.json -> {filepath}")
        print(e)


# =========================
# PARSE go.mod
# =========================

def parse_go_mod(filepath):

    try:

        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        require_pattern = re.compile(
            r'^([A-Za-z0-9\.\-\/]+)\s+v?([^\s]+)'
        )

        inside_require = False

        for line in lines:

            line = line.strip()

            if line.startswith("require ("):
                inside_require = True
                continue

            if inside_require and line == ")":
                inside_require = False
                continue

            if inside_require:

                match = require_pattern.match(line)

                if match:

                    name = match.group(1)
                    version = match.group(2)

                    add_dependency(name, version, "go")

    except Exception as e:

        print(f"[ERROR] go.mod -> {filepath}")
        print(e)


# =========================
# WALK REPOSITORY
# =========================

for root, dirs, files in os.walk(REPO_PATH):

    dirs[:] = [
        d for d in dirs
        if d not in [
            "node_modules",
            ".git",
            ".next",
            "target",
            "vendor"
        ]
    ]

    for file in files:

        fullpath = os.path.join(root, file)

        if file == "package.json":
            parse_package_json(fullpath)

        elif file == "Cargo.toml":
            parse_cargo_toml(fullpath)

        elif file == "requirements.txt":
            parse_requirements_txt(fullpath)

        elif file == "pom.xml":
            parse_pom_xml(fullpath)

        elif file == "Gemfile.lock":
            parse_gemfile_lock(fullpath)

        elif file == "composer.json":
            parse_composer_json(fullpath)

        elif file == "go.mod":
            parse_go_mod(fullpath)

# =========================
# SAVE RESULT
# =========================

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

# =========================
# PRINT STATS
# =========================

print("\n=== ECOSYSTEM STATS ===")

for ecosystem, count in ecosystem_stats.items():
    print(f"{ecosystem}: {count}")

print(f"\nTotal unique packages: {len(results)}")
print(f"Saved to: {OUTPUT_FILE}")