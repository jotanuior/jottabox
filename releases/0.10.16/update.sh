#!/usr/bin/env bash
set -Eeuo pipefail
RAW="https://raw.githubusercontent.com/jotanuior/jottabox/main"
CFG="$HOME/.config/jottabox-console"
STATE="$HOME/.local/share/jottabox"
BIN="$HOME/.local/bin"
BACKUP="$STATE/backups/0.10.16-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$CFG" "$STATE" "$BIN" "$BACKUP"

[[ -f "$CFG/launcher.py" ]] || { echo "ERRO: launcher.py não encontrado"; exit 1; }
cp -a "$CFG/launcher.py" "$BACKUP/launcher.py"

echo ">>> Migrando launcher legado (modo robusto)"
curl -fsSL -H 'Cache-Control: no-cache, no-store'   "$RAW/scripts/jottabox-migrate-legacy-launcher-robust.py?$(date +%s%N)"   -o "$CFG/migrate_legacy_launcher_robust.py"
python3 -m py_compile "$CFG/migrate_legacy_launcher_robust.py"
python3 "$CFG/migrate_legacy_launcher_robust.py"
python3 -m py_compile "$CFG/launcher.py"

echo ">>> Atualizando assistente de importação"
curl -fsSL -H 'Cache-Control: no-cache, no-store'   "$RAW/scripts/jottabox-import-assistant.py?$(date +%s%N)"   -o "$CFG/import_assistant.py"
python3 -m py_compile "$CFG/import_assistant.py"

echo "0.10.16" > "$STATE/VERSION"
echo
echo "OK: JottaBox 0.10.16 instalado"
echo "Importar/Downloader/Configurar Controle entram antes do terminal legado."
