#!/usr/bin/env bash
set -Eeuo pipefail

RAW="https://raw.githubusercontent.com/jotanuior/jottabox/main"
CFG="$HOME/.config/jottabox-console"
STATE="$HOME/.local/share/jottabox"
BACKUP="$STATE/backups/0.10.5-$(date +%Y%m%d-%H%M%S)"
TARGET="$CFG/downloader_gui.py"

mkdir -p "$CFG" "$BACKUP"

echo ">>> Backup do downloader atual"
[[ -f "$TARGET" ]] && cp -a "$TARGET" "$BACKUP/downloader_gui.py" || true

echo ">>> Instalando navegador de downloads unificado"
curl -fsSL "$RAW/scripts/jottabox-downloader.py" -o "$TARGET.new"
python3 -m py_compile "$TARGET.new"
mv -f "$TARGET.new" "$TARGET"
chmod +x "$TARGET"

echo "0.10.5" > "$STATE/VERSION"

echo
echo "OK: JottaBox 0.10.5 instalado"
echo "Downloader agora usa um único navegador de pastas/arquivos."
echo "Links salvos continuam em: $CFG/download-sources.json"
echo "Backup: $BACKUP"
