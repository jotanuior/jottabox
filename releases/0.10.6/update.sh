#!/usr/bin/env bash
set -Eeuo pipefail

RAW="https://raw.githubusercontent.com/jotanuior/jottabox/main"
BIN="$HOME/.local/bin"
CFG="$HOME/.config/jottabox-console"
STATE="$HOME/.local/share/jottabox"
BACKUP="$STATE/backups/0.10.6-$(date +%Y%m%d-%H%M%S)"
WRAPPER="$BIN/jottabox-import-roms"

mkdir -p "$BIN" "$CFG" "$BACKUP"

echo ">>> Backup do importador"
[[ -f "$WRAPPER" ]] && cp -a "$WRAPPER" "$BACKUP/jottabox-import-roms" || true

echo ">>> Instalando assistente de ISO"
curl -fsSL "$RAW/scripts/jottabox-import-assistant.py" -o "$CFG/import_assistant.py"
python3 -m py_compile "$CFG/import_assistant.py"
chmod +x "$CFG/import_assistant.py"

cat > "$WRAPPER" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
SRC="${1:-$HOME/Downloads/rom}"
ENGINE="$HOME/.local/share/jottabox/jottabox.sh"
ASSIST="$HOME/.config/jottabox-console/import_assistant.py"

"$ENGINE" storage-check || exit 1

# Todo .iso é classificado pelo usuário antes do importador legado.
python3 "$ASSIST" "$SRC"

# Os demais formatos continuam usando o importador estável já existente.
exec "$ENGINE" import "$SRC"
EOF

chmod +x "$WRAPPER"
echo "0.10.6" > "$STATE/VERSION"

echo
echo "OK: JottaBox 0.10.6 instalado"
echo "Todo .iso agora pergunta o console antes da importação."
echo "Log: $HOME/jottabox-import.log"
echo "Backup: $BACKUP"
