#!/usr/bin/env bash
set -Eeuo pipefail

ROOTS=(
  "$HOME/.config/jottabox-console"
  "$HOME/.local/bin"
  "$HOME/.local/share/jottabox"
)

PATTERN='x-terminal-emulator|gnome-terminal|xfce4-terminal|mate-terminal|konsole|lxterminal|cinnamon-terminal|terminator'

echo "=== Auditoria de terminais externos do JottaBox ==="
FOUND=0

for root in "${ROOTS[@]}"; do
  [[ -e "$root" ]] || continue
  while IFS= read -r hit; do
    [[ -n "$hit" ]] || continue
    # Ignore backups and binary/art blobs.
    case "$hit" in
      */backups/*|*/assets/*) continue ;;
    esac
    echo "$hit"
    FOUND=1
  done < <(grep -RniE --binary-files=without-match "$PATTERN" "$root" 2>/dev/null || true)
done

if [[ "$FOUND" -eq 0 ]]; then
  echo "OK: nenhuma chamada de terminal externo encontrada."
else
  echo
  echo "ATENÇÃO: foram encontradas referências a terminal externo."
  exit 2
fi
