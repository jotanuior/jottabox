#!/usr/bin/env python3
from pathlib import Path
import re, sys

HOME=Path.home()
LAUNCHER=HOME/".config"/"jottabox-console"/"launcher.py"

if not LAUNCHER.exists():
    raise SystemExit(f"launcher.py não encontrado: {LAUNCHER}")

s=LAUNCHER.read_text(encoding="utf-8")

marker="# JOTTABOX_NATIVE_GUI_POLICY"
if marker not in s:
    anchor="    run=cmd\n    pygame.display.iconify()"
    if anchor not in s:
        raise SystemExit("Não encontrei o ponto de lançamento externo no launcher.py")

    block='''    # JOTTABOX_NATIVE_GUI_POLICY
    # Telas gráficas do próprio JottaBox não passam por terminal externo
    # nem pelo console textual embutido.
    native_gui={
        "jottabox-configure-controller",
        "jottabox-download-roms",
    }
    native_name=os.path.basename(cmd)
    if native_name in native_gui:
        pygame.display.iconify()
        try:
            subprocess.run([cmd],check=False)
        finally:
            pygame.display.set_mode((W,H),pygame.FULLSCREEN|pygame.DOUBLEBUF)
            pygame.mouse.set_visible(False)
            pygame.event.clear()
        return

'''
    s=s.replace(anchor,block+anchor,1)

LAUNCHER.write_text(s,encoding="utf-8")
print("Política de telas gráficas internas aplicada.")
