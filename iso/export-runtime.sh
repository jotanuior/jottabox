#!/usr/bin/env bash
set -Eeuo pipefail

OUT="${1:-$HOME/jottabox-live-runtime.tar.gz}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

SRC_HOME="$HOME"
DST="$TMP/runtime-home"
mkdir -p "$DST"

copy_item() {
  local src="$1" rel="$2"
  [[ -e "$src" ]] || return 0

  if [[ -d "$src" ]]; then
    mkdir -p "$DST/$rel"
    rsync -a --copy-links "$src/" "$DST/$rel/"
  else
    mkdir -p "$DST/$(dirname "$rel")"
    rsync -a --copy-links "$src" "$DST/$rel"
  fi
}

echo ">>> Exportando runtime JottaBox de $SRC_HOME"

copy_item "$HOME/.local/share/jottabox" ".local/share/jottabox"
copy_item "$HOME/.config/jottabox-console" ".config/jottabox-console"
copy_item "$HOME/.emulationstation" ".emulationstation"
copy_item "$HOME/ES-DE" "ES-DE"

mkdir -p "$DST/.local/bin"
while IFS= read -r -d '' f; do
  cp -aL "$f" "$DST/.local/bin/$(basename "$f")"
done < <(find "$HOME/.local/bin" -maxdepth 1 -type f \( -name 'jottabox-*' -o -name 'gpbox' -o -name 'xbox-cloud' \) -print0 2>/dev/null)

# Configurações e cores que já foram validados.
copy_item "$HOME/.var/app/org.libretro.RetroArch/config/retroarch" ".var/app/org.libretro.RetroArch/config/retroarch"
copy_item "$HOME/.var/app/org.ppsspp.PPSSPP/config" ".var/app/org.ppsspp.PPSSPP/config"

# ES-DE AppImage, se estiver no diretório comum.
mkdir -p "$DST/Applications"
for f in "$HOME"/Applications/ES-DE*.AppImage "$HOME"/Applications/es-de*.AppImage; do
  [[ -f "$f" ]] && cp -a "$f" "$DST/Applications/"
done

# Nunca carregar conteúdo pessoal/jogos para a ISO.
rm -rf   "$DST/ROMs"   "$DST/Downloads"   "$DST/.local/share/jottabox/backups"   "$DST/.local/share/jottabox/logs"   "$DST/.config/google-chrome"   "$DST/.config/microsoft-edge"   "$DST/.ssh" 2>/dev/null || true

printf '%s\n' "$SRC_HOME" > "$TMP/source-home.txt"
printf '%s\n' "$(cat "$HOME/.local/share/jottabox/VERSION" 2>/dev/null || echo unknown)" > "$TMP/jottabox-version.txt"

tar -C "$TMP" -czf "$OUT" runtime-home source-home.txt jottabox-version.txt

echo
echo "OK: $OUT"
du -h "$OUT"
echo "ROMs, BIOS, downloads, SSH e dados do navegador não foram incluídos."
