#!/usr/bin/env bash
set -Eeuo pipefail

RAW="https://raw.githubusercontent.com/jotanuior/jottabox/main"
CFG="$HOME/.config/jottabox-console"
STATE="$HOME/.local/share/jottabox"
BACKUP="$STATE/backups/0.10.14-$(date +%Y%m%d-%H%M%S)"
LAUNCHER="$CFG/launcher.py"

mkdir -p "$CFG" "$BACKUP"

[[ -f "$LAUNCHER" ]] && cp -a "$LAUNCHER" "$BACKUP/launcher.py" || true

echo ">>> Corrigindo telas nativas cumulativamente"
curl -fsSL -H 'Cache-Control: no-cache'   "$RAW/scripts/jottabox-fix-native-gui-cumulative.py?$(date +%s%N)"   -o "$CFG/fix_native_gui_cumulative.py"

python3 -m py_compile "$CFG/fix_native_gui_cumulative.py"
python3 "$CFG/fix_native_gui_cumulative.py"
python3 -m py_compile "$LAUNCHER"

echo ">>> Atualizando assistente de importação"
curl -fsSL -H 'Cache-Control: no-cache'   "$RAW/scripts/jottabox-import-assistant.py?$(date +%s%N)"   -o "$CFG/import_assistant.py"
python3 -m py_compile "$CFG/import_assistant.py"

echo "0.10.14" > "$STATE/VERSION"

echo
echo "OK: JottaBox 0.10.14 instalado"
echo "Importar Jogos, Downloader e Configurar Controle não minimizam mais o JottaBox."
echo "Backup: $BACKUP"
