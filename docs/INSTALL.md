# Instalação nova do JottaBox

O repositório ainda usa um **runtime seed** para reproduzir exatamente a base
que foi validada no golden master. As atualizações continuam vindo do GitHub.

## Máquina já com JottaBox

```bash
curl -fsSL "https://raw.githubusercontent.com/jotanuior/jottabox/main/install.sh?$(date +%s%N)" | bash
```

## Linux Mint limpo

Copie primeiro o arquivo `jottabox-live-runtime.tar.gz` exportado do golden
master e execute:

```bash
curl -fsSL "https://raw.githubusercontent.com/jotanuior/jottabox/main/install.sh?$(date +%s%N)" -o /tmp/jottabox-install.sh
bash /tmp/jottabox-install.sh ~/jottabox-live-runtime.tar.gz
```

O instalador:

- instala dependências;
- configura Flathub;
- instala RetroArch, PPSSPP, Dolphin, PCSX2 e Steam;
- importa o runtime base;
- adapta caminhos absolutos para o usuário atual;
- instala o updater;
- atualiza para a versão estável atual;
- cria as pastas de ROMs;
- configura autostart sem terminal.

## Live ISO

Na futura ISO, o runtime seed fica em `/opt/jottabox-live`, então não será
necessário fornecer o arquivo manualmente.
