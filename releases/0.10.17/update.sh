#!/usr/bin/env bash
set -Eeuo pipefail

RAW="https://raw.githubusercontent.com/jotanuior/jottabox/main"
CFG="$HOME/.config/jottabox-console"
BIN="$HOME/.local/bin"
STATE="$HOME/.local/share/jottabox"
BACKUP="$STATE/backups/0.10.17-$(date +%Y%m%d-%H%M%S)"
WRAPPER="$BIN/jottabox-import-roms"

mkdir -p "$CFG" "$BIN" "$STATE" "$BACKUP"

[[ -f "$WRAPPER" ]] && cp -a "$WRAPPER" "$BACKUP/jottabox-import-roms" || true

echo ">>> Instalando tela gráfica de progresso da importação"
curl -fsSL -H 'Cache-Control: no-cache, no-store'   "$RAW/scripts/jottabox-import-progress.py?$(date +%s%N)"   -o "$CFG/import_progress.py"
python3 -m py_compile "$CFG/import_progress.py"
chmod +x "$CFG/import_progress.py"

echo ">>> Atualizando assistente de ISO"
curl -fsSL -H 'Cache-Control: no-cache, no-store'   "$RAW/scripts/jottabox-import-assistant.py?$(date +%s%N)"   -o "$CFG/import_assistant.py"
python3 -m py_compile "$CFG/import_assistant.py"
chmod +x "$CFG/import_assistant.py"

cat > "$WRAPPER" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail

SRC="${1:-$HOME/Downloads/rom}"
ENGINE="$HOME/.local/share/jottabox/jottabox.sh"
ASSIST="$HOME/.config/jottabox-console/import_assistant.py"
PROGRESS="$HOME/.config/jottabox-console/import_progress.py"

"$ENGINE" storage-check || exit 1

python3 "$ASSIST" "$SRC"
exec python3 "$PROGRESS" "$SRC"
EOF

chmod +x "$WRAPPER"
echo "0.10.17" > "$STATE/VERSION"

echo
echo "OK: JottaBox 0.10.17 instalado"
echo "Importar Jogos agora mostra progresso em tela cheia, sem terminal."
echo "Backup: $BACKUP"
