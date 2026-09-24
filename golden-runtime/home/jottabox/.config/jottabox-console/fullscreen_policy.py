#!/usr/bin/env python3
from pathlib import Path
import configparser, re

HOME=Path.home()

def patch_kv_file(path, updates):
    path.parent.mkdir(parents=True, exist_ok=True)
    lines=[]
    if path.exists():
        lines=path.read_text(encoding="utf-8",errors="ignore").splitlines()
    seen=set(); out=[]
    for line in lines:
        stripped=line.strip()
        key=stripped.split("=",1)[0].strip() if "=" in stripped else ""
        if key in updates:
            out.append(f'{key} = "{updates[key]}"')
            seen.add(key)
        else:
            out.append(line)
    for k,v in updates.items():
        if k not in seen:
            out.append(f'{k} = "{v}"')
    path.write_text("\n".join(out)+"\n",encoding="utf-8")

def patch_ini(path, section, updates):
    path.parent.mkdir(parents=True,exist_ok=True)
    cp=configparser.ConfigParser(strict=False)
    cp.optionxform=str
    if path.exists():
        try: cp.read(path,encoding="utf-8")
        except Exception: cp=configparser.ConfigParser(strict=False); cp.optionxform=str
    if not cp.has_section(section):
        cp.add_section(section)
    for k,v in updates.items():
        cp.set(section,k,v)
    with path.open("w",encoding="utf-8") as f:
        cp.write(f,space_around_delimiters=True)

# RetroArch
patch_kv_file(
    HOME/".var"/"app"/"org.libretro.RetroArch"/"config"/"retroarch"/"retroarch.cfg",
    {
        "video_fullscreen":"true",
        "video_windowed_fullscreen":"true",
    }
)

# PPSSPP Flatpak
ppsspp_candidates=[
    HOME/".var"/"app"/"org.ppsspp.PPSSPP"/"config"/"ppsspp"/"PSP"/"SYSTEM"/"ppsspp.ini",
    HOME/".config"/"ppsspp"/"PSP"/"SYSTEM"/"ppsspp.ini",
]
for p in ppsspp_candidates:
    if p.exists() or "org.ppsspp.PPSSPP" in str(p):
        patch_ini(p,"Graphics",{"FullScreen":"True"})

# Dolphin Flatpak / native
dolphin_candidates=[
    HOME/".var"/"app"/"org.DolphinEmu.dolphin-emu"/"config"/"dolphin-emu"/"Dolphin.ini",
    HOME/".config"/"dolphin-emu"/"Dolphin.ini",
]
for p in dolphin_candidates:
    if p.exists():
        patch_ini(p,"Display",{"Fullscreen":"True"})

# PCSX2 Flatpak / native, modern Qt.
pcsx2_candidates=[
    HOME/".var"/"app"/"net.pcsx2.PCSX2"/"config"/"PCSX2"/"inis"/"PCSX2.ini",
    HOME/".config"/"PCSX2"/"inis"/"PCSX2.ini",
]
for p in pcsx2_candidates:
    if p.exists():
        patch_ini(p,"UI",{"StartFullscreen":"true"})

print("Fullscreen padrão aplicado.")
