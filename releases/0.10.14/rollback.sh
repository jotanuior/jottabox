#!/usr/bin/env bash
set -Eeuo pipefail

FROM_VERSION="0.10.14"
TO_VERSION="0.10.13"

STATE="$HOME/.local/share/jottabox"
CFG="$HOME/.config/jottabox-console"

BACKUP="$(
    ls -dt "$STATE"/backups/${FROM_VERSION}-* \
    2>/dev/null |
    head -n1 || true
)"

if [[ -z "$BACKUP" || ! -d "$BACKUP" ]]; then
    echo "ERRO: backup da versão $FROM_VERSION não encontrado."
    exit 1
fi

echo ">>> Rollback JottaBox $FROM_VERSION -> $TO_VERSION"
echo "Backup: $BACKUP"

[[ -f "$BACKUP/configure_input.py" ]] || {
    echo "ERRO: configure_input.py não existe no backup."
    exit 1
}

[[ -f "$BACKUP/VERSION" ]] || {
    echo "ERRO: VERSION não existe no backup."
    exit 1
}

cp -a \
  "$BACKUP/configure_input.py" \
  "$CFG/configure_input.py"

cp -a \
  "$BACKUP/VERSION" \
  "$STATE/VERSION"

python3 -m py_compile \
  "$CFG/configure_input.py"

CURRENT="$(cat "$STATE/VERSION")"

[[ "$CURRENT" == "$TO_VERSION" ]] || {
    echo "ERRO: versão restaurada é $CURRENT."
    exit 1
}

cat > "$STATE/ROLLBACK" <<EOF2
ROLLBACK_FROM=$FROM_VERSION
ROLLBACK_TO=$TO_VERSION
ROLLBACK_AT=$(date -Iseconds)
BACKUP=$BACKUP
EOF2

echo
echo "OK: rollback concluído."
echo "Versão atual: $CURRENT"
