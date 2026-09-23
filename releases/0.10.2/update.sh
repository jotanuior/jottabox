#!/usr/bin/env bash
set -Eeuo pipefail

RAW="https://raw.githubusercontent.com/jotanuior/jottabox/main"
CFG="$HOME/.config/jottabox-console"
STATE="$HOME/.local/share/jottabox"
BACKUP="$STATE/backups/0.10.2-$(date +%Y%m%d-%H%M%S)"
TARGET="$CFG/downloader_gui.py"

mkdir -p "$CFG" "$BACKUP"

echo ">>> Backup do downloader atual"
if [[ -f "$TARGET" ]]; then
  cp -a "$TARGET" "$BACKUP/downloader_gui.py"
fi

echo ">>> Instalando downloader 0.10.2"
curl -fsSL "$RAW/scripts/jottabox-downloader.py" -o "$TARGET.new"
python3 -m py_compile "$TARGET.new"
mv -f "$TARGET.new" "$TARGET"
chmod +x "$TARGET"

echo "0.10.2" > "$STATE/VERSION"

echo
echo "OK: JottaBox 0.10.2 instalado"
echo "Downloader atualizado com:"
echo " - baixar pasta"
echo " - baixar arquivo"
echo " - links salvos"
echo " - histórico"
echo "Backup: $BACKUP"
