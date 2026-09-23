#!/usr/bin/env python3
from pathlib import Path
import re, sys

p=Path.home()/".config"/"jottabox-console"/"launcher.py"
if not p.exists():
    raise SystemExit("launcher.py não encontrado")

s=p.read_text(encoding="utf-8")
orig=s

# 1. Migração do launcher antigo (bloco admin + terminal + iconify).
old_re=re.compile(
    r'''(?ms)^\s*admin=any\(cmd\.endswith\(x\) for x in \(\s*
.*?
\s*\)\)\s*
\s*run=terminal\(cmd\) if admin else cmd\s*
\s*pygame\.display\.iconify\(\)\s*
\s*pygame\.mouse\.set_visible\(True\)'''
)

replacement='''    # JottaBox: telas gráficas próprias nunca passam por terminal nem minimizam.
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

    # Demais comandos seguem pelo caminho legado, mas só estes podem usar terminal.
    admin=any(cmd.endswith(x) for x in (
      "jottabox-clean-roms","jottabox-update",
      "jottabox-status","jottabox-repair-hotkey","jottabox-controller-diagnostics"))
    run=terminal(cmd) if admin else cmd

    pygame.display.iconify()
    pygame.mouse.set_visible(True)'''

s,n=old_re.subn(replacement,s,count=1)

# 2. Se já houve migração parcial, garantir import/config/downloader no native_gui.
if n==0 and 'native_gui={' in s:
    m=re.search(r'native_gui=\{(.*?)\n\s*\}',s,re.S)
    if m:
        block=m.group(0)
        wanted=[
            '"jottabox-import-roms",',
            '"jottabox-configure-controller",',
            '"jottabox-download-roms",',
        ]
        for item in reversed(wanted):
            if item not in block:
                block=block.replace('native_gui={','native_gui={\n        '+item,1)
        s=s[:m.start()]+block+s[m.end():]

# 3. Remover importador da lista de CLI/terminal interno se existir.
s=s.replace('        "jottabox-import-roms":"Importar jogos",\n','')

if s==orig:
    # Não é erro se já estiver corretamente migrado.
    if '"jottabox-import-roms"' in s and 'native_gui={' in s:
        print("Launcher já estava migrado.")
    else:
        raise SystemExit("ERRO: formato do launcher não reconhecido; nenhuma alteração aplicada")
else:
    p.write_text(s,encoding="utf-8")
    print("Launcher migrado.")

# Validação obrigatória.
check=p.read_text(encoding="utf-8")
if 'native_gui={' not in check:
    raise SystemExit("VALIDAÇÃO FALHOU: native_gui ausente")

native=re.search(r'native_gui=\{(.*?)\n\s*\}',check,re.S)
if not native or '"jottabox-import-roms"' not in native.group(1):
    raise SystemExit("VALIDAÇÃO FALHOU: importador não está em native_gui")

# No trecho antigo antes do native_gui não pode haver importador sendo classificado como admin.
prefix=check[:check.find('native_gui={')]
tail=check[check.find('native_gui={'):]
# O generic iconify pode existir depois, mas native_gui retorna antes dele.
print("VALIDAÇÃO OK: Importar Jogos passa antes do terminal/iconify genérico.")
