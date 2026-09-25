#!/usr/bin/env bash
set -Eeuo pipefail

FROM_VERSION="0.10.17"

STATE="$HOME/.local/share/jottabox"
CFG="$HOME/.config/jottabox-console"
BIN="$HOME/.local/bin"

DOWNLOADER="$CFG/downloader_gui.py"
IMPORTER="$CFG/import_assistant.py"
CONTROLLER="$CFG/configure_input.py"
WRAPPER="$BIN/jottabox-import-roms"
PS3_LAUNCHER="$BIN/jottabox-launch-ps3"
PS3_SETUP="$CFG/setup_ps3.py"
PS3_FW="$BIN/jottabox-rpcs3-firmware"

BACKUP="$(
    ls -dt "$STATE"/backups/${FROM_VERSION}-* 2>/dev/null |
    head -n1 || true
)"

if [[ -z "$BACKUP" || ! -d "$BACKUP" ]]; then
    echo "ERRO: backup da versão $FROM_VERSION não encontrado."
    exit 1
fi

restore_file() {
    local dst="$1"
    local name="$2"

    if [[ -f "$BACKUP/$name" ]]; then
        mkdir -p "$(dirname "$dst")"
        cp -a "$BACKUP/$name" "$dst"

    elif [[ -f "$BACKUP/$name.missing" ]]; then
        rm -f "$dst"

    else
        echo "ERRO: estado anterior de $name não encontrado."
        exit 1
    fi
}

echo ">>> Rollback JottaBox $FROM_VERSION"
echo "Backup: $BACKUP"

restore_file "$DOWNLOADER" "downloader_gui.py"
restore_file "$IMPORTER" "import_assistant.py"
restore_file "$CONTROLLER" "configure_input.py"
restore_file "$WRAPPER" "jottabox-import-roms"
restore_file "$PS3_LAUNCHER" "jottabox-launch-ps3"
restore_file "$PS3_SETUP" "setup_ps3.py"
restore_file "$PS3_FW" "jottabox-rpcs3-firmware"
restore_file "$STATE/VERSION" "VERSION"

[[ -f "$DOWNLOADER" ]] && \
  python3 -m py_compile "$DOWNLOADER" || true

[[ -f "$IMPORTER" ]] && \
  python3 -m py_compile "$IMPORTER" || true

[[ -f "$CONTROLLER" ]] && \
  python3 -m py_compile "$CONTROLLER" || true

CURRENT="$(cat "$STATE/VERSION" 2>/dev/null || echo desconhecida)"

cat > "$STATE/ROLLBACK" <<EOF
ROLLBACK_FROM=$FROM_VERSION
ROLLBACK_TO=$CURRENT
ROLLBACK_AT=$(date -Iseconds)
BACKUP=$BACKUP
EOF

echo
echo "OK: rollback concluído."
echo "Versão restaurada: $CURRENT"
