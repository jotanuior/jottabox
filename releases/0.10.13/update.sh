#!/usr/bin/env bash
set -Eeuo pipefail

RAW="https://raw.githubusercontent.com/jotanuior/jottabox/main"
BIN="$HOME/.local/bin"
CFG="$HOME/.config/jottabox-console"
STATE="$HOME/.local/share/jottabox"
BACKUP="$STATE/backups/0.10.13-$(date +%Y%m%d-%H%M%S)"
LAUNCHER="$CFG/launcher.py"

mkdir -p "$BIN" "$CFG" "$BACKUP"

[[ -f "$LAUNCHER" ]] && cp -a "$LAUNCHER" "$BACKUP/launcher.py" || true
[[ -f "$CFG/import_assistant.py" ]] && cp -a "$CFG/import_assistant.py" "$BACKUP/" || true

echo ">>> Corrigindo fluxo Importar Jogos"
curl -fsSL "$RAW/scripts/jottabox-import-native-gui.py?$(date +%s%N)" -o "$CFG/import_native_gui.py"
python3 -m py_compile "$CFG/import_native_gui.py"
python3 "$CFG/import_native_gui.py"
python3 -m py_compile "$LAUNCHER"

echo ">>> Atualizando assistente de importação"
curl -fsSL "$RAW/scripts/jottabox-import-assistant.py?$(date +%s%N)" -o "$CFG/import_assistant.py"
python3 -m py_compile "$CFG/import_assistant.py"
chmod +x "$CFG/import_assistant.py"

echo "0.10.13" > "$STATE/VERSION"

echo
echo "OK: JottaBox 0.10.13 instalado"
echo "Importar Jogos não deve mais revelar terminal."
echo "ISO usa rename instantâneo quando origem e destino estão no mesmo filesystem."
