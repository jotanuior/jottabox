# JottaBox Live

Primeira geração da imagem Live/instalável do JottaBox.

## Objetivo

- iniciar pelo pendrive sem alterar o SSD;
- abrir diretamente na sessão JottaBox;
- permitir testar vídeo, áudio, rede, Bluetooth e controles;
- permitir instalação posterior no computador;
- não copiar ROMs, BIOS, downloads, SSH ou dados pessoais;
- levar o runtime validado do golden master;
- atualizar pelo GitHub quando houver rede.

## Fluxo da primeira imagem

1. No micro JottaBox já validado, exporte o runtime:

```bash
cd ~/jottabox
bash iso/export-runtime.sh ~/jottabox-live-runtime.tar.gz
```

2. Baixe uma ISO oficial Linux Mint 64-bit e verifique o SHA256.

3. Instale as ferramentas de remasterização:

```bash
sudo apt update
sudo apt install -y xorriso squashfs-tools rsync
```

4. Gere a ISO:

```bash
sudo bash iso/build-live.sh \
  ~/Downloads/linuxmint.iso \
  ~/jottabox-live-runtime.tar.gz \
  ~/JottaBox-Live-0.1.0.iso
```

5. Grave o arquivo `JottaBox-Live-0.1.0.iso` em um pendrive.

## Instalação posterior

A imagem mantém o instalador da distribuição base. O comando
`jottabox-install-system` detecta `live-installer` e, como compatibilidade,
`ubiquity`.

Após uma instalação normal, o seed em `/opt/jottabox-live` permanece no
sistema instalado e o first-boot prepara o JottaBox para o usuário.

## Observação

A versão 0.1 usa o computador JottaBox já validado como golden master para
congelar a experiência funcional. A evolução seguinte será tornar todo o
runtime reproduzível diretamente a partir do repositório.
