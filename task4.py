import json
import os
import platform
import subprocess

OUTPUT_FILE = "result_task_4.json"

# ==========================================
# OS INFO
# ==========================================

def parse_os_release():

    os_info = {}

    if os.path.exists("/etc/os-release"):

        with open("/etc/os-release", "r", encoding="utf-8") as f:

            for line in f:

                line = line.strip()

                if "=" not in line:
                    continue

                key, value = line.split("=", 1)

                value = value.strip().strip('"')

                os_info[key] = value

    return {
        "name": os_info.get("NAME"),
        "version": os_info.get("VERSION"),
        "arch": platform.machine(),
        "id": os_info.get("ID"),
        "version_id": os_info.get("VERSION_ID"),
        "description": (
            os_info.get("PRETTY_NAME")
            or f"{os_info.get('NAME', '')} {os_info.get('VERSION', '')}".strip()
        ),
        "codename": os_info.get("VERSION_CODENAME")
    }

# ==========================================
# PACKAGE INVENTORY (PACMAN)
# ==========================================

def get_installed_packages():

    packages = []

    # Получаем список пакетов
    result = subprocess.run(
        ["pacman", "-Qi"],
        capture_output=True,
        text=True
    )

    output = result.stdout

    blocks = output.split("\n\n")

    for block in blocks:

        package = {}

        lines = block.splitlines()

        for line in lines:

            if ":" not in line:
                continue

            key, value = line.split(":", 1)

            key = key.strip()
            value = value.strip()

            if key == "Name":
                package["name"] = value

            elif key == "Version":
                package["version"] = value

            elif key == "Architecture":
                package["arch"] = value

            elif key == "Description":

                description = value.split(".")[0].strip()

                if description:
                    package["description"] = description

            elif key == "Installed Size":
                package["size"] = value

        if "name" in package:
            packages.append(package)

    return packages

# ==========================================
# MAIN
# ==========================================

result = {
    "OS": parse_os_release(),
    "packages": get_installed_packages()
}

# ==========================================
# SAVE
# ==========================================

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"Saved to {OUTPUT_FILE}")
print(f"Packages found: {len(result['packages'])}")