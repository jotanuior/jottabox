#!/usr/bin/env python3
from pathlib import Path
import re

HOME=Path.home()
p=HOME/".config"/"jottabox-console"/"launcher.py"
s=p.read_text(encoding="utf-8")

# Native GUI tools: keep parent fullscreen behind child. Never iconify,
# because on this installation the launcher itself is running inside gnome-terminal.
old='''    if native_name in native_gui:
        pygame.display.iconify()
        try:
            subprocess.run([cmd],check=False)
        finally:
            pygame.display.set_mode((W,H),pygame.FULLSCREEN|pygame.DOUBLEBUF)
            pygame.mouse.set_visible(False)
            pygame.event.clear()
        return'''
new='''    if native_name in native_gui:
        try:
            subprocess.run([cmd],check=False)
        finally:
            pygame.display.set_mode((W,H),pygame.FULLSCREEN|pygame.DOUBLEBUF)
            pygame.mouse.set_visible(False)
            pygame.event.clear()
        return'''
if old in s:
    s=s.replace(old,new,1)

# Ensure controller/downloader are classified as native GUI even on installations
# that skipped a previous release.
if 'native_gui={' not in s:
    anchor='    run=cmd\n    pygame.display.iconify()'
    block='''    # JOTTABOX_NATIVE_GUI_POLICY
    native_gui={
        "jottabox-configure-controller",
        "jottabox-download-roms",
    }
    native_name=os.path.basename(cmd)
    if native_name in native_gui:
        try:
            subprocess.run([cmd],check=False)
        finally:
            pygame.display.set_mode((W,H),pygame.FULLSCREEN|pygame.DOUBLEBUF)
            pygame.mouse.set_visible(False)
            pygame.event.clear()
        return

'''
    if anchor in s:
        s=s.replace(anchor,block+anchor,1)

# Ensure admin CLI tools use embedded console, for skipped-version installs.
if 'internal_cli={' not in s:
    anchor='    # JOTTABOX_NATIVE_GUI_POLICY'
    block='''    # Ferramentas CLI usam o console interno do JottaBox.
    internal_cli={
        "jottabox-import-roms":"Importar jogos",
        "jottabox-clean-roms":"Organizar biblioteca",
        "jottabox-update":"Atualizar JottaBox",
        "jottabox-status":"Status do sistema",
        "jottabox-repair-hotkey":"Reparar hotkey",
        "jottabox-storage":"Armazenamento",
        "jottabox-controller-diagnostics":"Diagnóstico do controle",
    }
    name=os.path.basename(cmd)
    if name in internal_cli:
        embedded_terminal(cmd,internal_cli[name])
        pygame.mouse.set_visible(False)
        pygame.event.clear()
        return

'''
    if anchor in s:
        s=s.replace(anchor,block+anchor,1)

p.write_text(s,encoding="utf-8")
print("launcher corrigido")
