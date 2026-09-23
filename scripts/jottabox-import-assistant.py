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
    ("psx","PlayStation 1"),
    ("gc","GameCube"),
    ("wii","Wii"),
    ("dreamcast","Dreamcast"),
    ("saturn","Saturn"),
    ("_revisar","Outro / revisar"),
]

def log(msg):
    with LOG.open("a",encoding="utf-8") as f:
        f.write(msg+"\n")
    print(msg)

def fast_move(src,dst):
    """Move sem copiar quando origem/destino estão no mesmo filesystem."""
    src=Path(src); dst=Path(dst)
    dst.parent.mkdir(parents=True,exist_ok=True)
    try:
        # rename/replace no mesmo filesystem: praticamente instantâneo.
        os.replace(src,dst)
        return "rename"
    except OSError as e:
        # EXDEV = filesystems diferentes. shutil.move faz copy+remove com segurança.
        if getattr(e,"errno",None)==18:
            shutil.move(str(src),str(dst))
            return "copy+remove"
        raise

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

def detect_iso(path):
    # Só sugere; o usuário ainda confirma.
    try:
        p=subprocess.run(
            ["7z","l","-ba",str(path)],
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
            text=True,errors="ignore",timeout=30
        )
        out=p.stdout.upper()
        if "PSP_GAME" in out or "UMD_DATA.BIN" in out:
            return "psp"
        if "SYSTEM.CNF" in out:
            # PS1 e PS2 compartilham SYSTEM.CNF; não força sugestão.
            return None
        if "IP.BIN" in out:
            return "dreamcast"
    except Exception:
        pass
    return None

def quarantine_fake_iso_dirs():
    if not SRC.exists():
        return
    QUAR.mkdir(parents=True,exist_ok=True)
    for p in list(SRC.rglob("*")):
        if p.is_dir() and p.name.lower().endswith(".iso"):
            dst=unique_target(QUAR/(p.name+".dir"))
            try:
                fast_move(p,dst)
                log(f"[QUARENTENA] pasta com nome .iso: {p} -> {dst}")
            except Exception as e:
                log(f"[ERRO] quarentena {p}: {e}")

def init_ui():
    pygame.init()
    pygame.joystick.init()
    info=pygame.display.Info()
    w,h=info.current_w,info.current_h
    screen=pygame.display.set_mode((w,h),pygame.FULLSCREEN|pygame.DOUBLEBUF)
    pygame.display.set_caption("JottaBox - Importar Jogos")
    pygame.mouse.set_visible(False)
    return screen,w,h,pygame.time.Clock()

def choose_system(screen,W,H,clock,path,suggested):
    WHITE=(246,249,255); MUTED=(158,184,215); CYAN=(24,213,255)
    BG=(2,10,25); PANEL=(5,25,52)
    def font(sz,b=False): return pygame.font.SysFont("DejaVu Sans",sz,bold=b)
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
        screen.blit(a,(int(W*.06),int(H*.045)))
        screen.blit(b,(int(W*.06)+a.get_width()-3,int(H*.045)))

        title=f_title.render("QUAL É O CONSOLE DESTE ISO?",True,WHITE)
        screen.blit(title,(W//2-title.get_width()//2,int(H*.13)))

        name=path.name
        if len(name)>86: name=name[:83]+"..."
        n=f_body.render(name,True,MUTED)
        screen.blit(n,(W//2-n.get_width()//2,int(H*.18)))

        if suggested:
            label=dict(SYSTEMS).get(suggested,suggested)
            s=f_small.render("Detectado como provável "+label+" — confirme abaixo",True,CYAN)
            screen.blit(s,(W//2-s.get_width()//2,int(H*.215)))

        cols=2
        card_w=int(W*.34); card_h=int(H*.105)
        gap_x=int(W*.035); gap_y=int(H*.025)
        total_w=cols*card_w+(cols-1)*gap_x
        x0=(W-total_w)//2; y0=int(H*.28)

        for i,(key,label) in enumerate(SYSTEMS):
            row=i//cols; col=i%cols
            r=pygame.Rect(x0+col*(card_w+gap_x),y0+row*(card_h+gap_y),card_w,card_h)
            sel=(i==selected)
            pygame.draw.rect(screen,(9,48,86) if sel else PANEL,r,border_radius=16)
            pygame.draw.rect(screen,CYAN if sel else (55,95,135),r,3 if sel else 1,border_radius=16)
            t=f_body.render(label,True,WHITE)
            screen.blit(t,(r.x+22,r.centery-t.get_height()//2))

        ft=f_small.render("D-pad/setas mover • A/ENTER confirmar • B/ESC cancelar este ISO",True,MUTED)
        screen.blit(ft,(W//2-ft.get_width()//2,int(H*.91)))
        pygame.display.flip()

        for e in pygame.event.get():
            if e.type==pygame.QUIT:
                return None
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_ESCAPE: return None
                if e.key==pygame.K_LEFT: selected=(selected-1)%len(SYSTEMS)
                elif e.key==pygame.K_RIGHT: selected=(selected+1)%len(SYSTEMS)
                elif e.key==pygame.K_UP: selected=(selected-2)%len(SYSTEMS)
                elif e.key==pygame.K_DOWN: selected=(selected+2)%len(SYSTEMS)
                elif e.key==pygame.K_RETURN: return SYSTEMS[selected][0]
            elif e.type==pygame.JOYHATMOTION:
                x,y=e.value
                if x<0: selected=(selected-1)%len(SYSTEMS)
                elif x>0: selected=(selected+1)%len(SYSTEMS)
                elif y>0: selected=(selected-2)%len(SYSTEMS)
                elif y<0: selected=(selected+2)%len(SYSTEMS)
            elif e.type==pygame.JOYBUTTONDOWN:
                if e.button==1: return None
                if e.button==0: return SYSTEMS[selected][0]
        clock.tick(60)

def main():
    log("\n=== JottaBox ISO import assistant ===")
    if not SRC.exists():
        return

    quarantine_fake_iso_dirs()

    isos=[p for p in SRC.rglob("*") if p.is_file() and p.suffix.lower()==".iso"]
    if not isos:
        return

    screen,W,H,clock=init_ui()
    try:
        for iso in isos:
            suggested=detect_iso(iso)
            system=choose_system(screen,W,H,clock,iso,suggested)
            if system is None:
                log(f"[ISO] ignorado pelo usuário: {iso}")
                continue

            dest_dir=ROMS/system
            dest_dir.mkdir(parents=True,exist_ok=True)
            dest=unique_target(dest_dir/iso.name)
            mode=fast_move(iso,dest)
            log(f"[ISO] {iso.name} -> {system} -> {dest} [{mode}]")
    finally:
        pygame.quit()

if __name__=="__main__":
    main()
