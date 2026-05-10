import os
import platform
import subprocess

def parse_os_release():

    os_info = {}

    if os.path.exists("/etc/os-release"):

        with open("/etc/os-release", "r", encoding="utf-8") as f:

            for line in f:

                line = line.strip()

                if "=" not in line:
                    continue

                key, value = line.split("=", 1)

                os_info[key] = value.strip().strip('"')

    # kernel version
    kernel_version = subprocess.check_output(
        ["uname", "-r"],
        text=True
    ).strip()

    # boot cmdline
    description = None

    if os.path.exists("/proc/cmdline"):

        with open("/proc/cmdline", "r", encoding="utf-8") as f:
            description = f.read().strip()

    if not description:
        description = (
            os_info.get("PRETTY_NAME")
            or os_info.get("NAME")
        )

    result = {
        "name": os_info.get("NAME", "Unknown Linux"),
        "version": kernel_version,
        "arch": platform.machine(),
        "id": os_info.get("ID"),
        "description": description
    }

    if os_info.get("BUILD_ID"):
        result["version_id"] = os_info["BUILD_ID"]

    return result