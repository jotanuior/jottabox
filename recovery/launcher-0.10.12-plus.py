#!/usr/bin/env python3
import os, time, shutil, socket, subprocess, pty, select, re
from pathlib import Path
import pygame

HOME=Path.home()
BIN=HOME/".local"/"bin"
STATE=HOME/".local"/"share"/"jottabox"
ASSETS=STATE/"assets"

pygame.init(); pygame.joystick.init()
info=pygame.display.Info(); W,H=info.current_w,info.current_h
screen=pygame.display.set_mode((W,H),pygame.FULLSCREEN|pygame.DOUBLEBUF)
pygame.display.set_caption("JottaBox 0.10.12+")
pygame.mouse.set_visible(False)
clock=pygame.time.Clock()

BG=(3,9,20); PANEL=(10,20,36); PANEL2=(16,31,52)
WHITE=(245,248,253); MUTED=(142,162,187); CYAN=(31,205,255)
GREEN=(55,214,147); RED=(245,91,104); BORDER=(45,67,92)

def font(sz,b=False): return pygame.font.SysFont("DejaVu Sans",sz,bold=b)
F_LOGO=font(max(40,int(H*.052)),True)
F_TITLE=font(max(23,int(H*.028)),True)
F_CARD=font(max(19,int(H*.024)),True)
F_SMALL=font(max(12,int(H*.015)))
F_TINY=font(max(11,int(H*.013)))

def load_bg():
    for p in [ASSETS/"wallpaper.png",ASSETS/"background.png",ASSETS/"bg.png"]:
        try:
            if p.exists():
                im=pygame.image.load(str(p)).convert()
                return pygame.transform.smoothscale(im,(W,H))
        except Exception: pass
    return None
BGIMG=load_bg()

MAIN=[
 ("cloud",str(BIN/"xbox-cloud")),
 ("retro",str(BIN/"gpbox")),
 ("steam","flatpak run com.valvesoftware.Steam -gamepadui"),
 ("library","__library__"),
 ("settings","__settings__"),
 ("power","__power__"),
]
LIBRARY=[
 ("import",str(BIN/"jottabox-import-roms")),
 ("download",str(BIN/"jottabox-download-roms")),
 ("organize",str(BIN/"jottabox-clean-roms")),
 ("back","__back__"),
]
SETTINGS=[
 ("controller",str(BIN/"jottabox-configure-controller")),
 ("storage",str(BIN/"jottabox-storage")),
 ("tools","__tools__"),
 ("back","__back__"),
]
TOOLS=[
 ("testpad",str(BIN/"jottabox-controller-diagnostics")),
 ("gamepad",str(BIN/"jottabox-repair-hotkey")),
 ("status",str(BIN/"jottabox-status")),
 ("update",str(BIN/"jottabox-update")),
 ("back","__settings__"),
]
POWER=[
 ("shutdown","__shutdown__"),
 ("restart","__reboot__"),
 ("desktop","__desktop__"),
 ("back","__back__"),
]

META={
 "cloud":("XBOX CLOUD","Jogue na nuvem"),
 "retro":("RETRÔ","EmulationStation / ES-DE"),
 "steam":("STEAM","Modo Gamepad"),
 "library":("BIBLIOTECA","Jogos, downloads e importação"),
 "settings":("CONFIGURAÇÕES","Controle, armazenamento e sistema"),
 "power":("ENERGIA","Desligar, reiniciar ou sair"),
 "import":("IMPORTAR JOGOS","Organizar jogos baixados"),
 "download":("BAIXAR JOGOS","Navegar por pastas e baixar"),
 "organize":("ORGANIZAR BIBLIOTECA","Limpar e revisar arquivos"),
 "controller":("CONFIGURAR CONTROLE","Gamepad ou teclado físico"),
 "storage":("ARMAZENAMENTO","Discos e espaço livre"),
 "tools":("FERRAMENTAS","Diagnóstico, status e atualização"),
 "testpad":("DIAGNÓSTICO DO CONTROLE","Ver controles detectados"),
 "gamepad":("REPARAR HOTKEY","SELECT + START"),
 "status":("STATUS DO SISTEMA","Versão e diagnóstico"),
 "update":("ATUALIZAR JOTTABOX","Buscar atualização"),
 "shutdown":("DESLIGAR","Desligar completamente"),
 "restart":("REINICIAR","Reiniciar o computador"),
 "desktop":("SAIR PARA LINUX","Fechar o JottaBox"),
 "back":("VOLTAR","Retornar"),
}

page="home"; selected=0
last_status=0; status_cache={}

def internet_ok():
    try:
        s=socket.create_connection(("1.1.1.1",53),.35); s.close(); return True
    except Exception: return False

def disk_free():
    try:
        return shutil.disk_usage(HOME).free/1024/1024/1024
    except Exception: return 0

def controller_name():
    try:
        pygame.joystick.quit(); pygame.joystick.init()
        if pygame.joystick.get_count():
            j=pygame.joystick.Joystick(0); j.init(); return j.get_name()
    except Exception: pass
    return "Sem controle"

def get_status():
    global last_status,status_cache
    if time.monotonic()-last_status>2:
        status_cache={"net":internet_ok(),"disk":disk_free(),"pad":controller_name()}
        last_status=time.monotonic()
    return status_cache

def active():
    return {"home":MAIN,"library":LIBRARY,"settings":SETTINGS,"tools":TOOLS,"power":POWER}[page]

def title():
    return {"home":"INÍCIO","library":"BIBLIOTECA","settings":"CONFIGURAÇÕES","tools":"FERRAMENTAS","power":"ENERGIA"}[page]

def draw_background():
    if BGIMG: screen.blit(BGIMG,(0,0))
    else:
        screen.fill(BG)
        for i in range(12):
            r=pygame.Rect(0,int(H*i/12),W,int(H/12)+1)
            c=8+i
            pygame.draw.rect(screen,(2,7+c//3,16+c),r)
    shade=pygame.Surface((W,H),pygame.SRCALPHA); shade.fill((0,5,14,95)); screen.blit(shade,(0,0))

def draw_header():
    x=int(W*.055); y=int(H*.035)
    a=F_LOGO.render("Jotta",True,WHITE); b=F_LOGO.render("Box",True,CYAN)
    screen.blit(a,(x,y)); screen.blit(b,(x+a.get_width()-3,y))
    ver=F_TINY.render("Launcher 0.10.12+",True,MUTED)
    screen.blit(ver,(x,y+a.get_height()+2))

    now=time.localtime()
    t=F_TITLE.render(time.strftime("%H:%M",now),True,WHITE)
    d=F_SMALL.render(time.strftime("%d/%m/%Y",now),True,MUTED)
    screen.blit(t,(W-int(W*.055)-t.get_width(),y))
    screen.blit(d,(W-int(W*.055)-d.get_width(),y+t.get_height()+3))

def draw_status():
    st=get_status()
    y=int(H*.905); x=int(W*.055)
    bits=[
      ("ONLINE" if st.get("net") else "OFFLINE",GREEN if st.get("net") else RED),
      (st.get("pad","Sem controle")[:34],WHITE),
      (f'{st.get("disk",0):.0f} GB LIVRES',WHITE),
    ]
    for text,c in bits:
        t=F_SMALL.render(text,True,c); screen.blit(t,(x,y)); x+=t.get_width()+int(W*.025)

def draw_cards():
    arr=active()
    cols=3 if page=="home" else 2
    rows=(len(arr)+cols-1)//cols
    card_w=int(W*(.265 if cols==3 else .39))
    card_h=int(H*(.245 if page=="home" else .155))
    gx=int(W*.028); gy=int(H*.03)
    total=cols*card_w+(cols-1)*gx; x0=(W-total)//2
    y0=int(H*.22 if page=="home" else H*.25)

    for i,(key,cmd) in enumerate(arr):
        row=i//cols; col=i%cols
        r=pygame.Rect(x0+col*(card_w+gx),y0+row*(card_h+gy),card_w,card_h)
        sel=i==selected
        shadow=r.move(0,8)
        s=pygame.Surface((shadow.w,shadow.h),pygame.SRCALPHA)
        pygame.draw.rect(s,(0,0,0,75),s.get_rect(),border_radius=20); screen.blit(s,shadow.topleft)
        pygame.draw.rect(screen,PANEL2 if sel else PANEL,r,border_radius=20)
        pygame.draw.rect(screen,CYAN if sel else BORDER,r,3 if sel else 1,border_radius=20)

        # faixa lateral simples, aproxima o launcher clássico sem depender de emoji/fonts.
        pygame.draw.rect(screen,CYAN if sel else (28,54,80),(r.x,r.y,7,r.h),border_radius=4)
        name,sub=META[key]
        tn=F_CARD.render(name,True,WHITE)
        ts=F_SMALL.render(sub,True,CYAN if sel else MUTED)
        screen.blit(tn,(r.x+24,r.y+int(r.h*.30)))
        screen.blit(ts,(r.x+24,r.y+int(r.h*.58)))

def draw():
    draw_background(); draw_header()
    h=F_TITLE.render(title(),True,WHITE); screen.blit(h,(int(W*.055),int(H*.15)))
    draw_cards(); draw_status()
    help_=F_TINY.render("D-PAD / SETAS   •   A / ENTER SELECIONAR   •   B / ESC VOLTAR",True,MUTED)
    screen.blit(help_,(W-int(W*.055)-help_.get_width(),int(H*.91)))
    pygame.display.flip()

def restore_display():
    global screen
    try: pygame.display.quit()
    except Exception: pass
    pygame.display.init()
    screen=pygame.display.set_mode((W,H),pygame.FULLSCREEN|pygame.DOUBLEBUF)
    pygame.mouse.set_visible(False); pygame.event.clear()

def embedded_terminal(cmd,label):
    master,slave=pty.openpty()
    p=subprocess.Popen([cmd],stdin=subprocess.DEVNULL,stdout=slave,stderr=slave,close_fds=True)
    os.close(slave); os.set_blocking(master,False)
    lines=[]; buf=""; done=False; rc=None
    ansi=re.compile(r'\x1b\[[0-9;?]*[ -/]*[@-~]')
    mono=pygame.font.SysFont("DejaVu Sans Mono",max(13,int(H*.017)))
    while True:
        for e in pygame.event.get():
            if done and ((e.type==pygame.KEYDOWN and e.key in (pygame.K_RETURN,pygame.K_ESCAPE)) or (e.type==pygame.JOYBUTTONDOWN and e.button in (0,1))):
                return
        if not done:
            try:
                rr,_,_=select.select([master],[],[],0)
                if rr:
                    chunk=os.read(master,4096).decode("utf-8","ignore"); buf+=chunk
                    while "\n" in buf:
                        ln,buf=buf.split("\n",1); ln=ansi.sub("",ln).replace("\r","").strip()
                        if ln: lines.append(ln)
                        lines=lines[-15:]
            except (OSError,BlockingIOError): pass
            rc=p.poll()
            if rc is not None: done=True
        draw_background(); draw_header()
        ttl=F_TITLE.render(label.upper(),True,WHITE); screen.blit(ttl,(int(W*.055),int(H*.16)))
        y=int(H*.24)
        for ln in lines[-14:]:
            t=mono.render(ln[:150],True,MUTED); screen.blit(t,(int(W*.06),y)); y+=int(H*.045)
        f=F_SMALL.render("A / ENTER para voltar" if done else "Aguarde...",True,CYAN)
        screen.blit(f,(W//2-f.get_width()//2,int(H*.91)))
        pygame.display.flip(); clock.tick(30)

def launch(cmd):
    global page,selected
    if cmd=="__library__": page="library"; selected=0; return
    if cmd=="__settings__": page="settings"; selected=0; return
    if cmd=="__tools__": page="tools"; selected=0; return
    if cmd=="__power__": page="power"; selected=0; return
    if cmd=="__back__": page="home"; selected=0; return
    if cmd=="__shutdown__": subprocess.run(["systemctl","poweroff"]); return
    if cmd=="__reboot__": subprocess.run(["systemctl","reboot"]); return
    if cmd=="__desktop__": pygame.quit(); raise SystemExit

    name=os.path.basename(cmd)
    native_gui={"jottabox-configure-controller","jottabox-download-roms","jottabox-import-roms"}
    internal_cli={
      "jottabox-clean-roms":"Organizar biblioteca",
      "jottabox-update":"Atualizar JottaBox",
      "jottabox-status":"Status do sistema",
      "jottabox-repair-hotkey":"Reparar hotkey",
      "jottabox-storage":"Armazenamento",
      "jottabox-controller-diagnostics":"Diagnóstico do controle",
    }

    if name in native_gui:
        try: subprocess.run([cmd],check=False)
        finally: restore_display()
        return
    if name in internal_cli:
        embedded_terminal(cmd,internal_cli[name]); pygame.event.clear(); return

    pygame.display.iconify(); pygame.mouse.set_visible(True)
    try: subprocess.run(cmd,shell=True,check=False)
    finally: restore_display()

def move(delta):
    global selected
    arr=active(); selected=(selected+delta)%len(arr)

def back():
    global page,selected
    if page=="home": return
    if page=="tools": page="settings"
    else: page="home"
    selected=0

while True:
    draw(); arr=active(); cols=3 if page=="home" else 2
    for e in pygame.event.get():
        if e.type==pygame.QUIT: pygame.quit(); raise SystemExit
        if e.type==pygame.KEYDOWN:
            if e.key in (pygame.K_LEFT,pygame.K_a): move(-1)
            elif e.key in (pygame.K_RIGHT,pygame.K_d): move(1)
            elif e.key in (pygame.K_UP,pygame.K_w): move(-cols)
            elif e.key in (pygame.K_DOWN,pygame.K_s): move(cols)
            elif e.key in (pygame.K_RETURN,pygame.K_SPACE): launch(active()[selected][1])
            elif e.key in (pygame.K_ESCAPE,pygame.K_BACKSPACE): back()
        elif e.type==pygame.JOYHATMOTION:
            x,y=e.value
            if x<0: move(-1)
            elif x>0: move(1)
            elif y>0: move(-cols)
            elif y<0: move(cols)
        elif e.type==pygame.JOYBUTTONDOWN:
            if e.button==0: launch(active()[selected][1])
            elif e.button==1: back()
    clock.tick(60)
