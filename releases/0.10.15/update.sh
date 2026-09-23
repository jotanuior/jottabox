#!/usr/bin/env bash
set -Eeuo pipefail

RAW="https://raw.githubusercontent.com/jotanuior/jottabox/main"
CFG="$HOME/.config/jottabox-console"
STATE="$HOME/.local/share/jottabox"
BIN="$HOME/.local/bin"
BACKUP="$STATE/backups/0.10.15-$(date +%Y%m%d-%H%M%S)"
LAUNCHER="$CFG/launcher.py"

mkdir -p "$CFG" "$STATE" "$BIN" "$BACKUP"

[[ -f "$LAUNCHER" ]] || { echo "ERRO: launcher.py não encontrado"; exit 1; }
cp -a "$LAUNCHER" "$BACKUP/launcher.py"

echo ">>> Migrando launcher antigo"
curl -fsSL -H 'Cache-Control: no-cache, no-store'   "$RAW/scripts/jottabox-migrate-legacy-launcher.py?$(date +%s%N)"   -o "$CFG/migrate_legacy_launcher.py"

python3 -m py_compile "$CFG/migrate_legacy_launcher.py"
python3 "$CFG/migrate_legacy_launcher.py"
python3 -m py_compile "$LAUNCHER"

echo ">>> Atualizando assistente de importação"
curl -fsSL -H 'Cache-Control: no-cache, no-store'   "$RAW/scripts/jottabox-import-assistant.py?$(date +%s%N)"   -o "$CFG/import_assistant.py"
python3 -m py_compile "$CFG/import_assistant.py"

echo ">>> Atualizando updater"
curl -fsSL -H 'Cache-Control: no-cache, no-store'   "$RAW/updater/jottabox-update.sh?$(date +%s%N)"   -o "$BIN/jottabox-update"
chmod +x "$BIN/jottabox-update"

# Só grava VERSION depois de todas as validações.
echo "0.10.15" > "$STATE/VERSION"

echo
echo "OK: JottaBox 0.10.15 instalado e validado"
echo "Launcher legado migrado com sucesso."
echo "Backup: $BACKUP"
