#!/usr/bin/env bash
set -Eeuo pipefail

RAW="https://raw.githubusercontent.com/jotanuior/jottabox/main"
CFG="$HOME/.config/jottabox-console"
STATE="$HOME/.local/share/jottabox"
BACKUP="$STATE/backups/0.10.4-$(date +%Y%m%d-%H%M%S)"
TARGET="$CFG/downloader_gui.py"

mkdir -p "$CFG" "$BACKUP"

echo ">>> Backup do downloader atual"
[[ -f "$TARGET" ]] && cp -a "$TARGET" "$BACKUP/downloader_gui.py" || true

echo ">>> Corrigindo downloader"
curl -fsSL "$RAW/scripts/jottabox-downloader.py" -o "$TARGET.new"
python3 -m py_compile "$TARGET.new"
mv -f "$TARGET.new" "$TARGET"
chmod +x "$TARGET"

# Mantém o log antigo, se existir, mas passa a usar o nome padronizado.
if [[ -f "$HOME/jotabox-download.log" && ! -f "$HOME/jottabox-download.log" ]]; then
  mv "$HOME/jotabox-download.log" "$HOME/jottabox-download.log"
fi

echo "0.10.4" > "$STATE/VERSION"

echo
echo "OK: JottaBox 0.10.4 instalado"
echo "Correção: ISO/ZIP/7Z/CHD/RVZ e afins agora são tratados como arquivos,"
echo "mesmo quando o servidor permite navegar dentro deles."
echo "Log: $HOME/jottabox-download.log"
echo "Backup: $BACKUP"
