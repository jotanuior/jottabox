#!/usr/bin/env bash
set -Eeuo pipefail
echo "JottaBox 0.11.1: atualização automática da base 0.11.x suspensa."
echo "Esta versão não substitui launcher, ES-DE ou configurações."
echo "Use recovery/restore-golden.sh para restaurar uma instalação validada."
mkdir -p "$HOME/.local/share/jottabox"
echo "0.11.1" > "$HOME/.local/share/jottabox/VERSION"
