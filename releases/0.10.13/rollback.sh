#!/usr/bin/env bash
set -Eeuo pipefail

FROM_VERSION="0.10.13"
TO_VERSION="0.10.12"
STATE="$HOME/.local/share/jottabox"
BIN="$HOME/.local/bin"

BACKUP="$(ls -dt "$STATE"/backups/${FROM_VERSION}-* 2>/dev/null | head -n1 || true)"

if [[ -z "$BACKUP" || ! -d "$BACKUP" ]]; then
  echo "ERRO: nenhum backup de $FROM_VERSION foi encontrado."
  echo "Esperado em: $STATE/backups/${FROM_VERSION}-*"
  exit 1
fi

echo ">>> Rollback JottaBox $FROM_VERSION -> $TO_VERSION"
echo "Backup: $BACKUP"

[[ -f "$BACKUP/jottabox-update" ]] || {
  echo "ERRO: backup do updater não encontrado."
  exit 1
}

[[ -f "$BACKUP/VERSION" ]] || {
  echo "ERRO: backup do VERSION não encontrado."
  exit 1
}

cp -a "$BACKUP/jottabox-update" "$BIN/jottabox-update"
chmod +x "$BIN/jottabox-update"
cp -a "$BACKUP/VERSION" "$STATE/VERSION"

bash -n "$BIN/jottabox-update"

CURRENT="$(cat "$STATE/VERSION" 2>/dev/null || true)"
if [[ "$CURRENT" != "$TO_VERSION" ]]; then
  echo "ERRO: VERSION restaurado como '$CURRENT', esperado '$TO_VERSION'."
  exit 1
fi

cat > "$STATE/ROLLBACK" <<EOF
ROLLBACK_FROM=$FROM_VERSION
ROLLBACK_TO=$TO_VERSION
ROLLBACK_AT=$(date -Iseconds)
BACKUP=$BACKUP
EOF

echo
echo "OK: rollback concluído."
echo "Versão atual: $CURRENT"
echo "Registro: $STATE/ROLLBACK"
