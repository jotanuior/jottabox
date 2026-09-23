#!/usr/bin/env bash
set -Eeuo pipefail
RAW="https://raw.githubusercontent.com/jotanuior/jottabox/main"
BIN="$HOME/.local/bin"
CFG="$HOME/.config/jottabox-console"
STATE="$HOME/.local/share/jottabox"
BACKUP="$STATE/backups/0.10.1-$(date +%Y%m%d-%H%M%S)"
LAUNCHER="$CFG/launcher.py"

mkdir -p "$BIN" "$CFG" "$BACKUP"
[[ -f "$LAUNCHER" ]] || { echo "ERRO: launcher.py não encontrado"; exit 1; }

echo ">>> Backup"
cp -a "$LAUNCHER" "$BACKUP/launcher.py"
[[ -f "$STATE/jottabox.sh" ]] && cp -a "$STATE/jottabox.sh" "$BACKUP/jottabox.sh" || true

echo ">>> Instalando configurador unificado"
curl -fsSL "$RAW/scripts/jottabox-configure-input.py" -o "$CFG/configure_input.py"
chmod +x "$CFG/configure_input.py"

cat > "$BIN/jottabox-configure-controller" <<EOF
#!/usr/bin/env bash
exec /usr/bin/python3 "$CFG/configure_input.py"
EOF
chmod +x "$BIN/jottabox-configure-controller"

echo ">>> Ajustando menu"
python3 - "$LAUNCHER" <<'PY'
from pathlib import Path
import sys,re
p=Path(sys.argv[1])
s=p.read_text(encoding="utf-8")

# Remove the separate keyboard item introduced in 0.10.0.
s=re.sub(r'\n\s*\("keyboard",os\.path\.join\(BIN,"jottabox-configure-keyboard"\)\),?','',s)

# Make Configurar Controle use the unified external configurator.
s=s.replace('("controller","__controller_native__")',
            '("controller",os.path.join(BIN,"jottabox-configure-controller"))')
s=s.replace('("controller",os.path.join(BIN,"jottabox-configure-controller"))',
            '("controller",os.path.join(BIN,"jottabox-configure-controller"))')

# If the old native handler is still present it becomes harmless/unreferenced.
p.write_text(s,encoding="utf-8")
PY

python3 -m py_compile "$LAUNCHER"
python3 -m py_compile "$CFG/configure_input.py"

# Remove obsolete standalone keyboard launcher if present.
rm -f "$BIN/jottabox-configure-keyboard" "$CFG/keyboard_control_config.py" 2>/dev/null || true

echo "0.10.1" > "$STATE/VERSION"

echo
echo "OK: JottaBox 0.10.1 instalado"
echo "Perfis: $CFG/controllers/"
echo "Backup: $BACKUP"
