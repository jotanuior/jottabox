#!/usr/bin/env bash
set -Eeuo pipefail

VERSION_NEW="0.10.16"
HOST="raw.githubusercontent.com"
RAW="https://${HOST}/jotanuior/jottabox/stable"

STATE="$HOME/.local/share/jottabox"
CFG="$HOME/.config/jottabox-console"
BIN="$HOME/.local/bin"

DOWNLOADER="$CFG/downloader_gui.py"
IMPORTER="$CFG/import_assistant.py"
CONTROLLER="$CFG/configure_input.py"
WRAPPER="$BIN/jottabox-import-roms"
PS3_LAUNCHER="$BIN/jottabox-launch-ps3"
PS3_SETUP="$CFG/setup_ps3.py"

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
    restore_file "$PS3_LAUNCHER" "jottabox-launch-ps3"
    restore_file "$PS3_SETUP" "setup_ps3.py"
    restore_file "$STATE/VERSION" "VERSION"
}

on_error() {
    local rc=$?
    echo
    echo "=================================================="
    echo "FALHA NA ATUALIZACAO"
    echo "Linha: $1"
    echo "Comando: $2"
    echo "Codigo: $rc"
    echo "=================================================="
    rollback_on_error
    exit "$rc"
}

trap 'on_error "$LINENO" "$BASH_COMMAND"' ERR
trap rollback_on_error INT TERM

echo ">>> Atualizando JottaBox para $VERSION_NEW"

echo ">>> Criando backup"
backup_file "$DOWNLOADER" "downloader_gui.py"
backup_file "$IMPORTER" "import_assistant.py"
backup_file "$CONTROLLER" "configure_input.py"
backup_file "$WRAPPER" "jottabox-import-roms"
backup_file "$PS3_LAUNCHER" "jottabox-launch-ps3"
backup_file "$PS3_SETUP" "setup_ps3.py"
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


echo ">>> Preparando Flathub do usuário"

flatpak remote-add \
  --user \
  --if-not-exists \
  flathub-jottabox \
  https://dl.flathub.org/repo/flathub.flatpakrepo

echo ">>> Instalando RPCS3"

if ! flatpak info --user net.rpcs3.RPCS3 >/dev/null 2>&1; then
    flatpak install \
      --user \
      --noninteractive \
      -y \
      flathub-jottabox \
      net.rpcs3.RPCS3
fi

flatpak info --user net.rpcs3.RPCS3 >/dev/null

echo ">>> Instalando integração PlayStation 3"

curl -fsSL \
  "$RAW/scripts/jottabox-setup-ps3.py" \
  -o "$TMP/setup_ps3.py"

python3 -m py_compile "$TMP/setup_ps3.py"

install -m 0755 \
  "$TMP/setup_ps3.py" \
  "$CFG/setup_ps3.py"

cat > "$BIN/jottabox-launch-ps3" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail

GAME="${1:?Informe o jogo de PlayStation 3}"

if ! flatpak info --user net.rpcs3.RPCS3 >/dev/null 2>&1; then
    echo "ERRO: RPCS3 não está instalado."
    exit 1
fi

exec flatpak run \
  --user \
  net.rpcs3.RPCS3 \
  "$GAME"
EOF

chmod +x "$BIN/jottabox-launch-ps3"

mkdir -p "$HOME/ROMs/ps3"

python3 "$CFG/setup_ps3.py"

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
