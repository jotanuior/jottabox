#!/usr/bin/env python3
from pathlib import Path
import re

p=Path.home()/".config"/"jottabox-console"/"launcher.py"
s=p.read_text(encoding="utf-8")

# Remove Importar Jogos do console textual interno, se ainda estiver lá.
s=s.replace('        "jottabox-import-roms":"Importar jogos",\n','')

# Garante bloco native_gui.
if 'native_gui={' not in s:
    anchor='    run=cmd\n'
    block='''    # Telas gráficas nativas do JottaBox.
    native_gui={
        "jottabox-import-roms",
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
else:
    # Adiciona importador se faltar.
    m=re.search(r'native_gui=\{(.*?)\n\s*\}',s,re.S)
    if m and '"jottabox-import-roms"' not in m.group(1):
        old=m.group(0)
        new=old.replace('native_gui={','native_gui={\n        "jottabox-import-roms",',1)
        s=s.replace(old,new,1)

    # Remove qualquer iconify dentro do bloco native_gui existente.
    start=s.find('native_gui={')
    if start!=-1:
        end=s.find('    run=cmd',start)
        if end==-1: end=len(s)
        block=s[start:end]
        block=block.replace('        pygame.display.iconify()\n','')
        block=block.replace('    pygame.display.iconify()\n','')
        s=s[:start]+block+s[end:]

# Também remove iconify imediatamente antes de subprocess.run([cmd]) para GUIs nativas.
s=re.sub(
    r'(if native_name in native_gui:\n)(?:\s*pygame\.display\.iconify\(\)\n)?',
    r'\1',
    s,
    count=1
)

p.write_text(s,encoding="utf-8")
print("Launcher corrigido: GUIs nativas não minimizam o JottaBox.")
