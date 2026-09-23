#!/usr/bin/env bash
set -Eeuo pipefail

RAW="https://raw.githubusercontent.com/jotanuior/jottabox/main"
BIN="$HOME/.local/bin"
mkdir -p "$BIN"

echo ">>> Instalando atualizador oficial do JottaBox"
curl -fsSL   -H 'Cache-Control: no-cache, no-store, max-age=0'   -H 'Pragma: no-cache'   "$RAW/updater/jottabox-update.sh?cb=$(date +%s%N)"   -o "$BIN/jottabox-update"

chmod +x "$BIN/jottabox-update"

echo ">>> Executando primeira atualização pelo GitHub"
exec "$BIN/jottabox-update"
