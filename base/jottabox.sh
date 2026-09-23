#!/usr/bin/env bash
set -Eeuo pipefail
HOME="${HOME:?}"
ROMS="$HOME/ROMs"
DL="$HOME/Downloads/rom"
STATE="$HOME/.local/share/jottabox"
mkdir -p "$ROMS" "$DL" "$STATE"

unique_dest() {
  local d="$1"
  [[ ! -e "$d" ]] && { printf '%s' "$d"; return; }
  local dir base stem ext n=2
  dir="$(dirname "$d")"; base="$(basename "$d")"
  if [[ "$base" == *.* ]]; then stem="${base%.*}"; ext=".${base##*.}"; else stem="$base"; ext=""; fi
  while [[ -e "$dir/$stem-$n$ext" ]]; do ((n++)); done
  printf '%s' "$dir/$stem-$n$ext"
}

move_file() {
  local src="$1" system="$2" dst
  mkdir -p "$ROMS/$system"
  dst="$(unique_dest "$ROMS/$system/$(basename "$src")")"
  echo "Movendo: $(basename "$src") -> $system"
  mv -- "$src" "$dst"
}

detect_system() {
  local f="${1,,}"
  case "$f" in
    *.nes) echo nes;; *.sfc|*.smc) echo snes;;
    *.gb) echo gb;; *.gbc) echo gbc;; *.gba) echo gba;; *.nds) echo nds;;
    *.z64|*.n64|*.v64) echo n64;;
    *.md|*.gen|*.smd) echo megadrive;; *.32x) echo sega32x;; *.sms) echo mastersystem;; *.gg) echo gamegear;;
    *.pce) echo pcengine;; *.a26) echo atari2600;; *.a52) echo atari5200;; *.a78) echo atari7800;;
    *.lnx) echo atarilynx;; *.ngp) echo ngp;; *.ngc) echo ngpc;; *.ws) echo wonderswan;; *.wsc) echo wonderswancolor;;
    *.cso) echo psp;; *.wbfs) echo wii;; *.gcm|*.gcz) echo gc;;
    *.gdi|*.cdi) echo dreamcast;;
    *.cue|*.pbp) echo psx;;
    *.chd|*.rvz|*.bin|*.zip|*.7z) echo _revisar;;
    *) echo _revisar;;
  esac
}

cmd="${1:-status}"; shift || true
case "$cmd" in
  storage-check)
    mkdir -p "$ROMS" "$DL"
    [[ -w "$ROMS" && -w "$DL" ]] || { echo "Armazenamento sem permissão de escrita."; exit 1; }
    echo "Armazenamento OK"
    ;;
  import)
    src="${1:-$DL}"
    [[ -d "$src" ]] || { echo "Origem inexistente: $src"; exit 1; }
    echo "Importando de: $src"
    count=0
    while IFS= read -r -d '' f; do
      [[ "${f,,}" == *.iso ]] && continue
      system="$(detect_system "$f")"
      move_file "$f" "$system"
      ((count++)) || true
    done < <(find "$src" -type f -print0)
    echo "Importação concluída: $count arquivo(s)."
    ;;
  clean)
    echo "Verificando biblioteca..."
    find "$ROMS" -type f -size 0 -print -delete 2>/dev/null || true
    echo "Verificação concluída."
    ;;
  status)
    echo "JottaBox: $(cat "$STATE/VERSION" 2>/dev/null || echo desconhecida)"
    echo "ROMs: $ROMS"
    du -sh "$ROMS" 2>/dev/null || true
    df -h "$HOME" | tail -1
    ;;
  storage)
    echo "Armazenamento atual:"
    df -h "$HOME" "$ROMS" "$DL" 2>/dev/null | awk 'NR==1 || !seen[$1]++'
    ;;
  *)
    echo "Comando desconhecido: $cmd"; exit 2;;
esac
