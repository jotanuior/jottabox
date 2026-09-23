#!/usr/bin/env bash
set -Eeuo pipefail

RAW="https://raw.githubusercontent.com/jotanuior/jottabox/main"
CFG_DIR="$HOME/.config/jottabox-console"
BIN_DIR="$HOME/.local/bin"
STATE_DIR="$HOME/.local/share/jottabox"
BACKUP_DIR="$STATE_DIR/backups/0.10.0-$(date +%Y%m%d-%H%M%S)"
LAUNCHER="$CFG_DIR/launcher.py"

say(){ printf '\n>>> %s\n' "$*"; }
die(){ echo "ERRO: $*" >&2; exit 1; }

mkdir -p "$CFG_DIR" "$BIN_DIR" "$BACKUP_DIR"

[[ -f "$LAUNCHER" ]] || die "launcher.py não encontrado em $LAUNCHER"

say "Criando backup"
cp -a "$LAUNCHER" "$BACKUP_DIR/launcher.py"
[[ -f "$STATE_DIR/jottabox.sh" ]] && cp -a "$STATE_DIR/jottabox.sh" "$BACKUP_DIR/jottabox.sh" || true

say "Instalando configurador de teclado"
curl -fsSL "$RAW/scripts/jottabox-configure-keyboard.py" -o "$CFG_DIR/keyboard_control_config.py"
chmod +x "$CFG_DIR/keyboard_control_config.py"

cat > "$BIN_DIR/jottabox-configure-keyboard" <<EOF
#!/usr/bin/env bash
exec /usr/bin/python3 "$CFG_DIR/keyboard_control_config.py"
EOF
chmod +x "$BIN_DIR/jottabox-configure-keyboard"

say "Atualizando launcher para teclado como controle"
python3 - "$LAUNCHER" <<'PY'
from pathlib import Path
import sys,re
p=Path(sys.argv[1])
s=p.read_text(encoding="utf-8")

if "KEYBOARD_MAP_FILE=" not in s:
    if "import os, time, math, shutil, subprocess, pygame" in s and ", json" not in s.splitlines()[1]:
        s=s.replace("import os, time, math, shutil, subprocess, pygame",
                    "import os, time, math, shutil, subprocess, pygame, json",1)

    anchor='ROM_ROOT=os.path.join(HOME,"ROMs")\n'
    helper='''ROM_ROOT=os.path.join(HOME,"ROMs")
KEYBOARD_MAP_FILE=os.path.join(HOME,".config","jottabox-console","keyboard.json")
DEFAULT_KEYBOARD_MAP={
 "up":pygame.K_UP,"down":pygame.K_DOWN,"left":pygame.K_LEFT,"right":pygame.K_RIGHT,
 "a":pygame.K_RETURN,"b":pygame.K_ESCAPE,"x":pygame.K_SPACE,"y":pygame.K_BACKSPACE,
 "select":pygame.K_RSHIFT,"start":pygame.K_RETURN,"l1":pygame.K_q,"r1":pygame.K_e,
}
def load_keyboard_map():
    m=DEFAULT_KEYBOARD_MAP.copy()
    try:
        raw=json.load(open(KEYBOARD_MAP_FILE,encoding="utf-8"))
        for k,v in raw.items():
            if k in m: m[k]=int(v)
    except Exception:
        pass
    return m
KEYBOARD_MAP=load_keyboard_map()
def keyboard_action(key):
    for action,code in KEYBOARD_MAP.items():
        if key==code: return action
    return None
'''
    if anchor not in s:
        raise SystemExit("estrutura do launcher incompatível: ROM_ROOT")
    s=s.replace(anchor,helper,1)

if '"keyboard":("CONFIGURAR TECLADO"' not in s and "MENU_META={" in s:
    s=s.replace(' "controller":("CONFIGURAR CONTROLE","Assistente automático","🎮"),',
                ' "controller":("CONFIGURAR CONTROLE","Assistente automático","🎮"),\n "keyboard":("CONFIGURAR TECLADO","Usar teclado físico como controle","⌨"),',1)

if '"keyboard":load_img(' not in s and "SET_ART={" in s:
    s=s.replace(' "controller":load_img("settings_gamepad.png"),',
                ' "controller":load_img("settings_gamepad.png"),\n "keyboard":load_img("settings_gamepad.png"),',1)

if '("keyboard",os.path.join(BIN,"jottabox-configure-keyboard"))' not in s:
    s=s.replace(' ("controller",os.path.join(BIN,"jottabox-configure-controller")),',
                ' ("controller",os.path.join(BIN,"jottabox-configure-controller")),\n ("keyboard",os.path.join(BIN,"jottabox-configure-keyboard")),',1)

old='''        elif e.type==pygame.KEYDOWN:
            if e.key in (pygame.K_LEFT,pygame.K_UP,pygame.K_a,pygame.K_w): move(-1)
            elif e.key in (pygame.K_RIGHT,pygame.K_DOWN,pygame.K_d,pygame.K_s): move(1)
            elif e.key in (pygame.K_RETURN,pygame.K_SPACE): launch(active()[selected][1])
            elif e.key in (pygame.K_ESCAPE,pygame.K_BACKSPACE): back()'''
new='''        elif e.type==pygame.KEYDOWN:
            act=keyboard_action(e.key)
            if act in ("left","up"): move(-1)
            elif act in ("right","down"): move(1)
            elif act in ("a","start"): launch(active()[selected][1])
            elif act=="b": back()'''

if old in s:
    s=s.replace(old,new,1)
elif "act=keyboard_action(e.key)" not in s:
    raise SystemExit("estrutura do launcher incompatível: bloco KEYDOWN")

p.write_text(s,encoding="utf-8")
PY

python3 -m py_compile "$LAUNCHER"

say "Instalando atualizador Git"
curl -fsSL "$RAW/updater/jottabox-update.sh" -o "$BIN_DIR/jottabox-update"
chmod +x "$BIN_DIR/jottabox-update"

echo "0.10.0" > "$STATE_DIR/VERSION"

echo
echo "OK: JottaBox atualizado para 0.10.0"
echo "Backup: $BACKUP_DIR"
