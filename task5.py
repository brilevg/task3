import json

with open("sbom_before.json") as f:
    before = json.load(f)

with open("sbom_after.json") as f:
    after = json.load(f)

before_packages = {
    comp["name"]: comp.get("version")
    for comp in before.get("components", [])
}

after_packages = {
    comp["name"]: comp.get("version")
    for comp in after.get("components", [])
}

updated = []
added = []
removed = []

for pkg in before_packages:

    if pkg not in after_packages:
        removed.append(pkg)

    elif before_packages[pkg] != after_packages[pkg]:
        updated.append({
            "name": pkg,
            "before": before_packages[pkg],
            "after": after_packages[pkg]
        })

for pkg in after_packages:

    if pkg not in before_packages:
        added.append(pkg)

print("Updated:", len(updated))
print("Added:", len(added))
print("Removed:", len(removed))