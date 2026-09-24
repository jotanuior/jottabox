#!/usr/bin/env python3
from pathlib import Path
import xml.etree.ElementTree as ET
import shutil, time

HOME=Path.home()
candidates=[
    HOME/".emulationstation"/"custom_systems"/"es_systems.xml",
    HOME/".config"/"ES-DE"/"custom_systems"/"es_systems.xml",
]

def ensure_parent(p):
    p.parent.mkdir(parents=True,exist_ok=True)

def patch_file(path):
    ensure_parent(path)
    if path.exists():
        backup=path.with_name(path.name+f".bak-{int(time.time())}")
        shutil.copy2(path,backup)
        try:
            tree=ET.parse(path)
            root=tree.getroot()
        except Exception:
            root=ET.Element("systemList")
            tree=ET.ElementTree(root)
    else:
        root=ET.Element("systemList")
        tree=ET.ElementTree(root)

    target=None
    for system in root.findall("system"):
        name=system.find("name")
        if name is not None and (name.text or "").strip()=="psp":
            target=system
            break

    if target is None:
        target=ET.SubElement(root,"system")
        ET.SubElement(target,"name").text="psp"

    def set_child(tag,value):
        e=target.find(tag)
        if e is None:
            e=ET.SubElement(target,tag)
        e.text=value

    set_child("fullname","Sony PlayStation Portable")
    set_child("path","%ROMPATH%/psp")
    set_child("extension",".iso .ISO .cso .CSO .pbp .PBP")

    # Remove old commands that may point PSP to RetroArch.
    for cmd in list(target.findall("command")):
        target.remove(cmd)

    cmd=ET.SubElement(target,"command",{"label":"PPSSPP (Standalone)"})
    cmd.text="flatpak run org.ppsspp.PPSSPP %ROM%"

    set_child("platform","psp")
    set_child("theme","psp")

    try:
        ET.indent(tree,space="  ")
    except AttributeError:
        pass
    tree.write(path,encoding="utf-8",xml_declaration=True)
    return path

written=[]
for p in candidates:
    # Patch the primary ES-DE path always; patch alternate path only if it already exists.
    if p==candidates[0] or p.exists():
        written.append(patch_file(p))

for p in written:
    print(p)
