#!/usr/bin/env bash
set -Eeuo pipefail

VERSION_NEW="0.10.15"
HOST="raw.githubusercontent.com"
RAW="https://${HOST}/jotanuior/jottabox/stable"

STATE="$HOME/.local/share/jottabox"
CFG="$HOME/.config/jottabox-console"
BIN="$HOME/.local/bin"

DOWNLOADER="$CFG/downloader_gui.py"
IMPORTER="$CFG/import_assistant.py"
CONTROLLER="$CFG/configure_input.py"
WRAPPER="$BIN/jottabox-import-roms"

BACKUP="$STATE/backups/$VERSION_NEW-$(date +%Y%m%d-%H%M%S)"
TMP="$(mktemp -d)"
COMMITTED=0

mkdir -p "$STATE" "$CFG" "$BIN" "$BACKUP"
trap 'rm -rf "$TMP"' EXIT

backup_file() {
    local src="$1"
    local name="$2"

    if [[ -f "$src" ]]; then
        cp -a "$src" "$BACKUP/$name"
    else
        touch "$BACKUP/$name.missing"
    fi
}

restore_file() {
    local dst="$1"
    local name="$2"

    if [[ -f "$BACKUP/$name" ]]; then
        cp -a "$BACKUP/$name" "$dst"
    elif [[ -f "$BACKUP/$name.missing" ]]; then
        rm -f "$dst"
    fi
}

rollback_on_error() {
    [[ "$COMMITTED" -eq 0 ]] || return 0

    echo
    echo "ERRO: atualização incompleta. Restaurando versão anterior..."

    restore_file "$DOWNLOADER" "downloader_gui.py"
    restore_file "$IMPORTER" "import_assistant.py"
    restore_file "$CONTROLLER" "configure_input.py"
    restore_file "$WRAPPER" "jottabox-import-roms"
    restore_file "$STATE/VERSION" "VERSION"
}

trap rollback_on_error ERR INT TERM

echo ">>> Atualizando JottaBox para $VERSION_NEW"

echo ">>> Criando backup"
backup_file "$DOWNLOADER" "downloader_gui.py"
backup_file "$IMPORTER" "import_assistant.py"
backup_file "$CONTROLLER" "configure_input.py"
backup_file "$WRAPPER" "jottabox-import-roms"
backup_file "$STATE/VERSION" "VERSION"

echo ">>> Baixando componentes"

curl -fsSL \
  "$RAW/scripts/jottabox-downloader.py" \
  -o "$TMP/downloader_gui.py"

curl -fsSL \
  "$RAW/scripts/jottabox-import-assistant.py" \
  -o "$TMP/import_assistant.py"

curl -fsSL \
  "$RAW/scripts/jottabox-configure-input.py" \
  -o "$TMP/configure_input.py"

echo ">>> Validando componentes Python"

python3 -m py_compile \
  "$TMP/downloader_gui.py" \
  "$TMP/import_assistant.py" \
  "$TMP/configure_input.py"

echo ">>> Instalando downloader"
install -m 0755 \
  "$TMP/downloader_gui.py" \
  "$DOWNLOADER"

echo ">>> Instalando assistente de importação"
install -m 0755 \
  "$TMP/import_assistant.py" \
  "$IMPORTER"

echo ">>> Instalando editor de controles"
install -m 0755 \
  "$TMP/configure_input.py" \
  "$CONTROLLER"

echo ">>> Instalando wrapper de importação"

cat > "$WRAPPER" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail

SRC="${1:-$HOME/Downloads/rom}"
ENGINE="$HOME/.local/share/jottabox/jottabox.sh"
ASSIST="$HOME/.config/jottabox-console/import_assistant.py"

"$ENGINE" storage-check || exit 1

python3 "$ASSIST" "$SRC"

# O importador legado processa o que não foi classificado
# pelo assistente visual.
exec "$ENGINE" import "$SRC"
EOF

chmod +x "$WRAPPER"

echo "$VERSION_NEW" > "$STATE/VERSION"

echo ">>> Validação final"

python3 -m py_compile \
  "$DOWNLOADER" \
  "$IMPORTER" \
  "$CONTROLLER"

[[ -x "$WRAPPER" ]]
[[ "$(cat "$STATE/VERSION")" == "$VERSION_NEW" ]]

grep -q 'bar:force:noscroll' "$DOWNLOADER"
grep -q 'run_import_assistant' "$DOWNLOADER"
grep -q 'PlayStation 3' "$IMPORTER"
grep -q 'embedded_isos' "$IMPORTER"

COMMITTED=1
trap - ERR INT TERM

echo
echo "OK: JottaBox $VERSION_NEW instalado."
echo
echo "Novidades:"
echo " - progresso real durante downloads"
echo " - classificação automática após download"
echo " - suporte a ISO, ZIP e 7Z"
echo " - identificação de ISO dentro de ZIP/7Z"
echo " - opção PlayStation 3"
echo " - extração de ISO de arquivos compactados"
echo " - editor visual de controles"
echo
echo "Backup: $BACKUP"
