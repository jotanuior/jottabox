#!/usr/bin/env python3
from pathlib import Path
import xml.etree.ElementTree as ET
import shutil, time

HOME=Path.home()
paths=[
    HOME/"ES-DE"/"custom_systems"/"es_systems.xml",
    HOME/".emulationstation"/"custom_systems"/"es_systems.xml",
    HOME/".config"/"ES-DE"/"custom_systems"/"es_systems.xml",
]

def patch(path):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        shutil.copy2(path,path.with_name(path.name+f".bak-{int(time.time())}"))
        try:
            tree=ET.parse(path); root=tree.getroot()
        except Exception:
            root=ET.Element("systemList"); tree=ET.ElementTree(root)
    else:
        root=ET.Element("systemList"); tree=ET.ElementTree(root)

    node=None
    for x in root.findall("system"):
        n=x.find("name")
        if n is not None and (n.text or "").strip()=="psp":
            node=x; break
    if node is None:
        node=ET.SubElement(root,"system")
        ET.SubElement(node,"name").text="psp"

    def setv(tag,val):
        e=node.find(tag)
        if e is None: e=ET.SubElement(node,tag)
        e.text=val

    setv("fullname","Sony PlayStation Portable")
    setv("path","%ROMPATH%/psp")
    setv("extension",".iso .ISO .cso .CSO .pbp .PBP")
    for c in list(node.findall("command")):
        node.remove(c)
    c=ET.SubElement(node,"command",{"label":"PPSSPP (JottaBox)"})
    c.text=str(HOME/".local"/"bin"/"jottabox-launch-psp")+" %ROM%"
    setv("platform","psp")
    setv("theme","psp")
    try: ET.indent(tree,space="  ")
    except Exception: pass
    tree.write(path,encoding="utf-8",xml_declaration=True)
    print("PSP:",path)

for path in paths:
    patch(path)
