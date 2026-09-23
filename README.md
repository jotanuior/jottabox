# JottaBox

JottaBox é uma interface de console para Linux voltada a uso em TV, com suporte a emulação, Steam, Xbox Cloud, controles e armazenamento interno/externo.

## Atualizações

O JottaBox usa este repositório como fonte oficial de atualizações.

A versão atual é definida em:

- `VERSION`
- `manifest.json`

O sistema instalado compara sua versão local com a versão publicada aqui e pode atualizar pela própria interface.

## Estrutura prevista

```text
jottabox/
├── VERSION
├── manifest.json
├── jottabox.sh
├── launcher/
├── assets/
├── updater/
└── docs/
```

## Segurança do repositório

Não devem ser versionados:

- ROMs
- BIOS
- credenciais
- tokens
- imagens de disco
- arquivos pessoais

Esses itens já estão cobertos pelo `.gitignore`.

## Canais

- `stable`: versões testadas
- `beta`: versões em desenvolvimento

## Repositório oficial

`git@github.com:jotanuior/jottabox.git`
