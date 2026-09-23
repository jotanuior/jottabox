#!/usr/bin/env python3
from pathlib import Path
import re, shutil, time

p=Path.home()/".config"/"jottabox-console"/"launcher.py"
if not p.exists():
    raise SystemExit("ERRO: launcher.py não encontrado")

s=p.read_text(encoding="utf-8")
backup=p.with_name("launcher.py.pre-native-"+str(int(time.time())))
shutil.copy2(p,backup)

marker="# JOTTABOX_NATIVE_GUI_ROBUST"
if marker not in s:
    needle='    admin=any(cmd.endswith(x) for x in ('
    pos=s.find(needle)

    if pos < 0:
        # instalação parcialmente migrada: insere antes do run genérico
        needle='    run=cmd'
        pos=s.find(needle)

    if pos < 0:
        raise SystemExit("ERRO: ponto de inserção do launcher não encontrado")

    block='''    # JOTTABOX_NATIVE_GUI_ROBUST
    # Estas telas pertencem ao JottaBox: não usar terminal e não minimizar.
    native_gui={
        "jottabox-import-roms",
        "jottabox-configure-controller",
        "jottabox-download-roms",
    }
    native_name=os.path.basename(cmd)
    if native_name in native_gui:
        try:
            subprocess.run(cmd,shell=True)
        finally:
            pygame.display.set_mode((W,H),pygame.FULLSCREEN|pygame.DOUBLEBUF)
            pygame.mouse.set_visible(False)
            pygame.event.clear()
        return

'''
    s=s[:pos]+block+s[pos:]

# Se existir internal_cli de versões intermediárias, importador não é CLI.
s=s.replace('        "jottabox-import-roms":"Importar jogos",\n','')

p.write_text(s,encoding="utf-8")

# Validação textual simples e determinística.
v=p.read_text(encoding="utf-8")
mpos=v.find(marker)
apos=v.find('admin=any(cmd.endswith(x)')
if mpos < 0:
    raise SystemExit("VALIDAÇÃO FALHOU: bloco native_gui não foi criado")
if apos >= 0 and mpos > apos:
    raise SystemExit("VALIDAÇÃO FALHOU: native_gui ficou depois do admin legado")

for name in ("jottabox-import-roms","jottabox-configure-controller","jottabox-download-roms"):
    if name not in v[mpos:mpos+900]:
        raise SystemExit("VALIDAÇÃO FALHOU: "+name+" ausente")

print("VALIDAÇÃO OK")
print("Backup:",backup)
print("Telas nativas entram antes do terminal/iconify legado.")
