#!/usr/bin/env python3

from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

HOME = Path.home()
ROMS = HOME / "ROMs"
PS3 = ROMS / "ps3"

ES_PATHS = [
    HOME / "ES-DE" / "custom_systems" / "es_systems.xml",
    HOME / ".emulationstation" / "custom_systems" / "es_systems.xml",
    HOME / ".config" / "ES-DE" / "custom_systems" / "es_systems.xml",
]

PS3.mkdir(parents=True, exist_ok=True)

def ensure_system(path):
    if not path.exists():
        return False

    backup = path.with_suffix(path.suffix + ".before-ps3")
    if not backup.exists():
        shutil.copy2(path, backup)

    tree = ET.parse(path)
    root = tree.getroot()

    systems = root
    if root.tag != "systemList":
        found = root.find("systemList")
        if found is not None:
            systems = found

    target = None

    for node in systems.findall("system"):
        name = node.find("name")
        if name is not None and (name.text or "").strip() == "ps3":
            target = node
            break

    if target is None:
        target = ET.SubElement(systems, "system")

    def setv(tag, value):
        node = target.find(tag)
        if node is None:
            node = ET.SubElement(target, tag)
        node.text = value

    setv("name", "ps3")
    setv("fullname", "Sony PlayStation 3")
    setv("path", str(PS3))
    setv("extension", ".iso .ISO .pkg .PKG .ps3 .PS3")

    for cmd in list(target.findall("command")):
        target.remove(cmd)

    cmd = ET.SubElement(
        target,
        "command",
        {"label": "RPCS3 (JottaBox)"}
    )
    cmd.text = str(HOME / ".local" / "bin" / "jottabox-launch-ps3") + " %ROM%"

    setv("platform", "ps3")
    setv("theme", "ps3")

    ET.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=True)

    return True

changed = []

for path in ES_PATHS:
    try:
        if ensure_system(path):
            changed.append(str(path))
    except Exception as e:
        print(f"ERRO em {path}: {e}")

print("PS3 ROM:", PS3)

if changed:
    for path in changed:
        print("ES-DE atualizado:", path)
else:
    print("Nenhum es_systems.xml existente encontrado.")
