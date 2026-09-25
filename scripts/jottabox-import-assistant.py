#!/usr/bin/env python3
import os, sys, json, shutil, subprocess
from pathlib import Path
import pygame

HOME=Path.home()
SRC=Path(sys.argv[1] if len(sys.argv)>1 else HOME/"Downloads"/"rom")
ROMS=HOME/"ROMs"
LOG=HOME/"jottabox-import.log"
QUAR=HOME/".local"/"share"/"jottabox"/"quarantine"/"expanded-archives"

SYSTEMS=[
    ("psp","PSP"),
    ("ps2","PlayStation 2"),
    ("ps3","PlayStation 3"),
    ("psx","PlayStation 1"),
    ("gc","GameCube"),
    ("wii","Wii"),
    ("dreamcast","Dreamcast"),
    ("saturn","Saturn"),
    ("_revisar","Outro / revisar"),
]

IMPORT_EXTS={".iso",".zip",".7z"}

def log(msg):
    with LOG.open("a",encoding="utf-8") as f:
        f.write(msg+"\n")
    print(msg)

def unique_target(dst):
    if not dst.exists():
        return dst

    stem,suf=dst.stem,dst.suffix
    i=2

    while True:
        p=dst.with_name(f"{stem}-{i}{suf}")
        if not p.exists():
            return p
        i+=1

def archive_listing(path):
    try:
        p=subprocess.run(
            ["7z","l","-ba",str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="ignore",
            timeout=60
        )
        return p.stdout.upper()
    except Exception as e:
        log(f"[ERRO] lendo conteúdo de {path}: {e}")
        return ""

def detect_system(path):
    out=archive_listing(path)
    name=path.name.lower()

    # Estrutura direta de PS3
    if (
        "PS3_GAME" in out
        or "PARAM.SFO" in out
        or "PS3_DISC.SFB" in out
    ):
        return "ps3"

    # ZIP/7Z contendo uma ISO de PS3.
    # O nome é apenas uma sugestão; o usuário ainda confirma.
    if path.suffix.lower() in (".zip",".7z"):
        iso_lines=[
            line for line in out.splitlines()
            if ".ISO" in line.upper()
        ]

        if iso_lines:
            joined="\n".join(iso_lines).upper()

            if (
                "PLAYSTATION 3" in joined
                or "PS3" in joined
                or "PLAYSTATION 3" in name.upper()
                or "PS3" in name.upper()
            ):
                return "ps3"

    # PSP
    if (
        "PSP_GAME" in out
        or "UMD_DATA.BIN" in out
    ):
        return "psp"

    # Dreamcast
    if "IP.BIN" in out:
        return "dreamcast"

    # PS1/PS2 compartilham SYSTEM.CNF
    if "SYSTEM.CNF" in out:
        return None

    return None


def embedded_isos(path):
    """Retorna nomes das ISOs contidas em ZIP/7Z."""
    if path.suffix.lower() not in (".zip",".7z"):
        return []

    try:
        p=subprocess.run(
            ["7z","l","-slt",str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="ignore",
            timeout=60
        )

        result=[]

        for line in p.stdout.splitlines():
            if not line.startswith("Path = "):
                continue

            name=line[7:].strip()

            if name.lower().endswith(".iso"):
                result.append(name)

        return result

    except Exception as e:
        log(f"[ERRO] procurando ISO em {path}: {e}")
        return []


def install_item(item,system):
    dest_dir=ROMS/system
    dest_dir.mkdir(parents=True,exist_ok=True)

    # ISO já solta: apenas mover.
    if item.suffix.lower()==".iso":
        dest=unique_target(dest_dir/item.name)
        shutil.move(str(item),str(dest))
        return dest

    # ZIP/7Z: se houver uma ISO dentro, extrair somente a ISO.
    if item.suffix.lower() in (".zip",".7z"):
        isos=embedded_isos(item)

        if len(isos)==1:
            inner=isos[0]

            tmp=HOME/".cache"/"jottabox-import"
            tmp.mkdir(parents=True,exist_ok=True)

            log(
                f"[EXTRACAO] {item.name}: "
                f"extraindo {inner}"
            )

            result=subprocess.run(
                [
                    "7z",
                    "e",
                    "-y",
                    f"-o{tmp}",
                    str(item),
                    inner
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                errors="ignore"
            )

            if result.returncode != 0:
                log(result.stdout)
                raise RuntimeError(
                    f"Falha extraindo ISO de {item.name}"
                )

            extracted=tmp/Path(inner).name

            if not extracted.exists():
                raise RuntimeError(
                    f"ISO extraída não encontrada: {extracted}"
                )

            dest=unique_target(
                dest_dir/extracted.name
            )

            shutil.move(
                str(extracted),
                str(dest)
            )

            # Só remove o arquivo compactado quando a ISO foi
            # instalada com sucesso.
            item.unlink()

            return dest

        # Arquivo compactado sem uma única ISO reconhecível:
        # preserva o arquivo para revisão/classificação manual.
        dest=unique_target(dest_dir/item.name)
        shutil.move(str(item),str(dest))
        return dest

    dest=unique_target(dest_dir/item.name)
    shutil.move(str(item),str(dest))
    return dest


def quarantine_fake_iso_dirs():
    if not SRC.exists():
        return

    QUAR.mkdir(parents=True,exist_ok=True)

    for p in list(SRC.rglob("*")):
        if p.is_dir() and p.name.lower().endswith(".iso"):
            dst=unique_target(QUAR/(p.name+".dir"))

            try:
                shutil.move(str(p),str(dst))
                log(f"[QUARENTENA] pasta com nome .iso: {p} -> {dst}")
            except Exception as e:
                log(f"[ERRO] quarentena {p}: {e}")

def init_ui():
    pygame.init()
    pygame.joystick.init()

    info=pygame.display.Info()
    w,h=info.current_w,info.current_h

    screen=pygame.display.set_mode(
        (w,h),
        pygame.FULLSCREEN|pygame.DOUBLEBUF
    )

    pygame.display.set_caption(
        "JottaBox - Importar Jogos"
    )

    pygame.mouse.set_visible(False)

    return screen,w,h,pygame.time.Clock()

def choose_system(screen,W,H,clock,path,suggested):
    WHITE=(246,249,255)
    MUTED=(158,184,215)
    CYAN=(24,213,255)
    BG=(2,10,25)
    PANEL=(5,25,52)

    def font(sz,b=False):
        return pygame.font.SysFont(
            "DejaVu Sans",
            sz,
            bold=b
        )

    f_logo=font(max(38,int(H*.050)),True)
    f_title=font(max(24,int(H*.030)),True)
    f_body=font(max(17,int(H*.021)))
    f_small=font(max(13,int(H*.016)))

    selected=0

    if suggested:
        for i,(key,_) in enumerate(SYSTEMS):
            if key==suggested:
                selected=i
                break

    while True:
        screen.fill(BG)

        a=f_logo.render("Jotta",True,WHITE)
        b=f_logo.render("Box",True,CYAN)

        screen.blit(
            a,
            (int(W*.06),int(H*.045))
        )

        screen.blit(
            b,
            (
                int(W*.06)+a.get_width()-3,
                int(H*.045)
            )
        )

        title=f_title.render(
            "QUAL É O CONSOLE DESTE JOGO?",
            True,
            WHITE
        )

        screen.blit(
            title,
            (
                W//2-title.get_width()//2,
                int(H*.13)
            )
        )

        name=path.name

        if len(name)>86:
            name=name[:83]+"..."

        n=f_body.render(
            name,
            True,
            MUTED
        )

        screen.blit(
            n,
            (
                W//2-n.get_width()//2,
                int(H*.18)
            )
        )

        if suggested:
            label=dict(SYSTEMS).get(
                suggested,
                suggested
            )

            s=f_small.render(
                "Detectado como provável "+label+" — confirme abaixo",
                True,
                CYAN
            )

            screen.blit(
                s,
                (
                    W//2-s.get_width()//2,
                    int(H*.215)
                )
            )

        cols=2
        card_w=int(W*.34)
        card_h=int(H*.090)
        gap_x=int(W*.035)
        gap_y=int(H*.018)

        total_w=cols*card_w+(cols-1)*gap_x
        x0=(W-total_w)//2
        y0=int(H*.27)

        for i,(key,label) in enumerate(SYSTEMS):
            row=i//cols
            col=i%cols

            r=pygame.Rect(
                x0+col*(card_w+gap_x),
                y0+row*(card_h+gap_y),
                card_w,
                card_h
            )

            sel=(i==selected)

            pygame.draw.rect(
                screen,
                (9,48,86) if sel else PANEL,
                r,
                border_radius=16
            )

            pygame.draw.rect(
                screen,
                CYAN if sel else (55,95,135),
                r,
                3 if sel else 1,
                border_radius=16
            )

            t=f_body.render(
                label,
                True,
                WHITE
            )

            screen.blit(
                t,
                (
                    r.x+22,
                    r.centery-t.get_height()//2
                )
            )

        ft=f_small.render(
            "D-pad/setas mover • A/ENTER confirmar • B/ESC cancelar",
            True,
            MUTED
        )

        screen.blit(
            ft,
            (
                W//2-ft.get_width()//2,
                int(H*.92)
            )
        )

        pygame.display.flip()

        for e in pygame.event.get():
            if e.type==pygame.QUIT:
                return None

            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_ESCAPE:
                    return None

                if e.key==pygame.K_LEFT:
                    selected=(selected-1)%len(SYSTEMS)

                elif e.key==pygame.K_RIGHT:
                    selected=(selected+1)%len(SYSTEMS)

                elif e.key==pygame.K_UP:
                    selected=(selected-2)%len(SYSTEMS)

                elif e.key==pygame.K_DOWN:
                    selected=(selected+2)%len(SYSTEMS)

                elif e.key==pygame.K_RETURN:
                    return SYSTEMS[selected][0]

            elif e.type==pygame.JOYHATMOTION:
                x,y=e.value

                if x<0:
                    selected=(selected-1)%len(SYSTEMS)

                elif x>0:
                    selected=(selected+1)%len(SYSTEMS)

                elif y>0:
                    selected=(selected-2)%len(SYSTEMS)

                elif y<0:
                    selected=(selected+2)%len(SYSTEMS)

            elif e.type==pygame.JOYBUTTONDOWN:
                if e.button==1:
                    return None

                if e.button==0:
                    return SYSTEMS[selected][0]

        clock.tick(60)

def main():
    log("\n=== JottaBox import assistant ===")

    if not SRC.exists():
        return

    quarantine_fake_iso_dirs()

    candidates=[
        p for p in SRC.rglob("*")
        if p.is_file()
        and p.suffix.lower() in IMPORT_EXTS
    ]

    if not candidates:
        return

    screen,W,H,clock=init_ui()

    try:
        for item in candidates:
            suggested=detect_system(item)

            system=choose_system(
                screen,
                W,
                H,
                clock,
                item,
                suggested
            )

            if system is None:
                log(
                    f"[IMPORT] ignorado pelo usuário: {item}"
                )
                continue

            try:
                dest=install_item(
                    item,
                    system
                )

                log(
                    f"[IMPORT] {item.name} -> "
                    f"{system} -> {dest}"
                )

            except Exception as e:
                log(
                    f"[ERRO] importando {item}: {e}"
                )

    finally:
        pygame.quit()

if __name__=="__main__":
    main()
