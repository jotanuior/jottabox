#!/usr/bin/env bash
set -Eeuo pipefail

RAW="https://raw.githubusercontent.com/jotanuior/jottabox/main"
BIN="$HOME/.local/bin"
STATE="$HOME/.local/share/jottabox"
BACKUP="$STATE/backups/0.10.3-$(date +%Y%m%d-%H%M%S)"

mkdir -p "$BIN" "$STATE" "$BACKUP"

echo ">>> Backup do atualizador"
[[ -f "$BIN/jottabox-update" ]] && cp -a "$BIN/jottabox-update" "$BACKUP/jottabox-update" || true

echo ">>> Instalando atualizador com reinício automático"
curl -fsSL "$RAW/updater/jottabox-update.sh" -o "$BIN/jottabox-update.new"
bash -n "$BIN/jottabox-update.new"
chmod +x "$BIN/jottabox-update.new"
mv -f "$BIN/jottabox-update.new" "$BIN/jottabox-update"

echo "0.10.3" > "$STATE/VERSION"

echo
echo "OK: JottaBox 0.10.3 instalado"
echo "A partir de agora, atualizações concluídas reiniciam o JottaBox automaticamente."
echo "Backup: $BACKUP"
