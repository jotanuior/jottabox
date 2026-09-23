#!/usr/bin/env python3
from pathlib import Path
import re

p=Path.home()/".config"/"jottabox-console"/"launcher.py"
s=p.read_text(encoding="utf-8")

# Importar jogos é fluxo gráfico: seletor ISO + processamento em background.
# Não deve passar pelo terminal embutido.
s=s.replace(
    '        "jottabox-import-roms":"Importar jogos",\n',
    ''
)

# Garante que o importador esteja na categoria GUI nativa.
m=re.search(r'native_gui=\{(.*?)\n\s*\}',s,re.S)
if m and '"jottabox-import-roms"' not in m.group(1):
    old=m.group(0)
    new=old.replace('native_gui={','native_gui={\n        "jottabox-import-roms",',1)
    s=s.replace(old,new,1)

# Em instalações antigas onde não existe o bloco native_gui, cria antes do launch genérico.
if 'native_gui={' not in s:
    anchor='    run=cmd\n    pygame.display.iconify()'
    block='''    # Fluxos gráficos do JottaBox: nunca expor terminal.
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

p.write_text(s,encoding="utf-8")
print("Importar Jogos classificado como GUI nativa.")
