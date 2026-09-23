#!/usr/bin/env python3
from pathlib import Path
import re, sys

HOME=Path.home()
LAUNCHER=HOME/".config"/"jottabox-console"/"launcher.py"

if not LAUNCHER.exists():
    raise SystemExit(f"launcher.py não encontrado: {LAUNCHER}")

s=LAUNCHER.read_text(encoding="utf-8")

cli_names=[
    "jottabox-import-roms",
    "jottabox-clean-roms",
    "jottabox-update",
    "jottabox-status",
    "jottabox-repair-hotkey",
    "jottabox-storage",
    "jottabox-controller-diagnostics",
]
titles={
    "jottabox-import-roms":"Importar jogos",
    "jottabox-clean-roms":"Organizar biblioteca",
    "jottabox-update":"Atualizar JottaBox",
    "jottabox-status":"Status do sistema",
    "jottabox-repair-hotkey":"Reparar hotkey",
    "jottabox-storage":"Armazenamento",
    "jottabox-controller-diagnostics":"Diagnóstico do controle",
}

# Replace the known legacy admin block with a centralized policy.
pattern=re.compile(
    r'\n\s*admin=any\(cmd\.endswith\(x\) for x in \(.*?\)\)\s*\n\s*if admin:\s*\n\s*titles=\{.*?\}\s*\n\s*name=os\.path\.basename\(cmd\)\s*\n\s*embedded_terminal\(cmd,titles\.get\(name,"JottaBox"\)\)\s*\n\s*pygame\.mouse\.set_visible\(False\)\s*\n\s*pygame\.event\.clear\(\)\s*\n\s*return',
    re.S
)

new_block='''

    # Ferramentas CLI nunca abrem terminal externo.
    # Elas são executadas no PTY/renderizador interno do JottaBox.
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
        return'''

if pattern.search(s):
    s=pattern.sub(new_block,s,count=1)
elif 'internal_cli={' not in s:
    # Fallback: inject immediately before the generic external launch path.
    anchor='    run=cmd\n    pygame.display.iconify()'
    if anchor not in s:
        raise SystemExit("Não encontrei ponto seguro para aplicar política de console interno.")
    s=s.replace(anchor,new_block+'\n\n'+anchor,1)

# Remove any direct terminal-emulator launch patterns that may have survived
# in the launcher. We do not silently rewrite arbitrary commands; fail clearly.
bad=[
    "x-terminal-emulator","gnome-terminal","xfce4-terminal","mate-terminal",
    "konsole","lxterminal","cinnamon-terminal"
]
found=[x for x in bad if x in s]
if found:
    raise SystemExit("Launcher ainda contém terminal externo: "+", ".join(found))

LAUNCHER.write_text(s,encoding="utf-8")
print("Política de console interno aplicada.")
