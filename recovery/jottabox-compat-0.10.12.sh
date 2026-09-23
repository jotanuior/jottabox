#!/usr/bin/env bash
set -Eeuo pipefail
ROMS="$HOME/ROMs"; DL="$HOME/Downloads/rom"; STATE="$HOME/.local/share/jottabox"
mkdir -p "$ROMS" "$DL" "$STATE"
cmd="${1:-status}"; shift || true
case "$cmd" in
 storage-check)
   [[ -w "$ROMS" && -w "$DL" ]] || { echo "Armazenamento sem permissão de escrita."; exit 1; }
   echo "Armazenamento OK";;
 status)
   echo "JottaBox: 0.10.12+"
   df -h "$HOME" | tail -1
   du -sh "$ROMS" 2>/dev/null || true;;
 storage)
   df -h "$HOME" "$ROMS" "$DL" 2>/dev/null | awk 'NR==1 || !seen[$1]++';;
 clean)
   echo "Verificando arquivos vazios..."
   find "$ROMS" -type f -size 0 -print -delete 2>/dev/null || true
   echo "Concluído.";;
 import)
   SRC="${1:-$DL}"
   [[ -d "$SRC" ]] || exit 0
   echo "Importando de $SRC"
   while IFS= read -r -d '' f; do
      lower="${f,,}"
      [[ "$lower" == *.iso ]] && continue
      case "$lower" in
        *.nes) sys=nes;; *.sfc|*.smc) sys=snes;; *.gb) sys=gb;; *.gbc) sys=gbc;;
        *.gba) sys=gba;; *.nds) sys=nds;; *.z64|*.n64|*.v64) sys=n64;;
        *.md|*.gen|*.smd) sys=megadrive;; *.32x) sys=sega32x;; *.sms) sys=mastersystem;;
        *.gg) sys=gamegear;; *.cso) sys=psp;; *.gdi|*.cdi) sys=dreamcast;;
        *.wbfs) sys=wii;; *.gcm|*.gcz|*.rvz) sys=gc;; *.cue|*.pbp) sys=psx;;
        *) sys=_revisar;;
      esac
      mkdir -p "$ROMS/$sys"
      echo "Movendo: $(basename "$f") -> $sys"
      mv -n -- "$f" "$ROMS/$sys/"
   done < <(find "$SRC" -type f -print0)
   echo "Importação concluída.";;
 *) echo "Comando desconhecido: $cmd"; exit 2;;
esac
