#!/usr/bin/env bash
set -Eeuo pipefail

VERSION_NEW="0.10.13"
RAW_STABLE="https://raw.githubusercontent.com/jotanuior/jottabox/stable"
STATE="$HOME/.local/share/jottabox"
BIN="$HOME/.local/bin"
BACKUP="$STATE/backups/$VERSION_NEW-$(date +%Y%m%d-%H%M%S)"
TMP="$(mktemp -d)"
COMMITTED=0

mkdir -p "$STATE" "$BIN" "$BACKUP"
trap 'rm -rf "$TMP"' EXIT

rollback() {
  [[ "$COMMITTED" -eq 0 ]] || return 0
  echo
  echo "ERRO: atualização não concluída. Restaurando arquivos anteriores..."
  if [[ -f "$BACKUP/jottabox-update" ]]; then
    cp -a "$BACKUP/jottabox-update" "$BIN/jottabox-update"
    chmod +x "$BIN/jottabox-update" 2>/dev/null || true
  else
    rm -f "$BIN/jottabox-update"
  fi
  if [[ -f "$BACKUP/VERSION" ]]; then
    cp -a "$BACKUP/VERSION" "$STATE/VERSION"
  else
    rm -f "$STATE/VERSION"
  fi
}
trap rollback ERR INT TERM

echo ">>> Preparando migração segura para o canal stable"

[[ -f "$BIN/jottabox-update" ]] && cp -a "$BIN/jottabox-update" "$BACKUP/jottabox-update"
[[ -f "$STATE/VERSION" ]] && cp -a "$STATE/VERSION" "$BACKUP/VERSION"

echo ">>> Baixando atualizador oficial do canal stable"
curl -fsSL "$RAW_STABLE/updater/jottabox-update.sh" -o "$TMP/jottabox-update"

echo ">>> Validando atualizador"
bash -n "$TMP/jottabox-update"
grep -q 'jotanuior/jottabox/stable' "$TMP/jottabox-update"
grep -q 'channels/stable.json' "$TMP/jottabox-update"

install -m 0755 "$TMP/jottabox-update" "$BIN/jottabox-update"

echo "$VERSION_NEW" > "$STATE/VERSION"

# Validação final antes de considerar a migração concluída.
bash -n "$BIN/jottabox-update"
grep -q 'jotanuior/jottabox/stable' "$BIN/jottabox-update"
grep -q 'channels/stable.json' "$BIN/jottabox-update"
[[ "$(cat "$STATE/VERSION")" == "$VERSION_NEW" ]]

COMMITTED=1
trap - ERR INT TERM

echo
echo "OK: JottaBox $VERSION_NEW instalado."
echo "Canal de atualizações: stable"
echo "Backup desta migração: $BACKUP"
echo "A branch main não controla mais as atualizações deste equipamento."
