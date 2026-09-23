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

    sysnode=None
    for s in root.findall("system"):
        n=s.find("name")
        if n is not None and (n.text or "").strip()=="psp":
            sysnode=s; break
    if sysnode is None:
        sysnode=ET.SubElement(root,"system")
        ET.SubElement(sysnode,"name").text="psp"

    def setv(tag,val):
        e=sysnode.find(tag)
        if e is None: e=ET.SubElement(sysnode,tag)
        e.text=val

    setv("fullname","Sony PlayStation Portable")
    setv("path","%ROMPATH%/psp")
    setv("extension",".iso .ISO .cso .CSO .pbp .PBP")
    for c in list(sysnode.findall("command")):
        sysnode.remove(c)
    c=ET.SubElement(sysnode,"command",{"label":"PPSSPP (JottaBox)"})
    c.text=str(HOME/".local"/"bin"/"jottabox-launch-psp")+" %ROM%"
    setv("platform","psp")
    setv("theme","psp")
    try: ET.indent(tree,space="  ")
    except Exception: pass
    tree.write(path,encoding="utf-8",xml_declaration=True)
    print(path)

for p in paths:
    patch(p)
