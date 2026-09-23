#!/usr/bin/env python3
import os, sys, time, subprocess, shutil
from pathlib import Path
import pygame

HOME=Path.home()
BIN=HOME/".local"/"bin"
STATE=HOME/".local"/"share"/"jottabox"
CFG=HOME/".config"/"jottabox-console"

pygame.init(); pygame.joystick.init()
info=pygame.display.Info(); W,H=info.current_w,info.current_h
screen=pygame.display.set_mode((W,H),pygame.FULLSCREEN|pygame.DOUBLEBUF)
pygame.display.set_caption("JottaBox")
pygame.mouse.set_visible(False)
clock=pygame.time.Clock()

WHITE=(246,249,255); MUTED=(158,184,215); CYAN=(24,213,255)
BG=(2,10,25); PANEL=(5,25,52); PANEL_SEL=(9,48,86); RED=(255,105,115)

def font(sz,b=False): return pygame.font.SysFont("DejaVu Sans",sz,bold=b)
F_LOGO=font(max(42,int(H*.055)),True)
F_TITLE=font(max(25,int(H*.032)),True)
F_CARD=font(max(20,int(H*.026)),True)
F_SMALL=font(max(13,int(H*.017)))

MAIN=[
 ("XBOX CLOUD","Jogar via navegador","xbox-cloud"),
 ("RETRÔ","Abrir ES-DE","gpbox"),
 ("STEAM","Steam Gamepad UI","__steam__"),
 ("BIBLIOTECA","Importar e baixar jogos","__library__"),
 ("CONFIGURAÇÕES","Controles e sistema","__settings__"),
 ("ENERGIA","Desligar ou reiniciar","__power__"),
]
LIBRARY=[
 ("IMPORTAR JOGOS","Organizar arquivos baixados","jottabox-import-roms"),
 ("BAIXAR JOGOS","Navegador e downloads","jottabox-download-roms"),
 ("ORGANIZAR BIBLIOTECA","Verificar biblioteca","jottabox-clean-roms"),
 ("VOLTAR","Retornar à Home","__home__"),
]
SETTINGS=[
 ("CONFIGURAR CONTROLE","Controle ou teclado físico","jottabox-configure-controller"),
 ("ARMAZENAMENTO","Status dos discos","jottabox-storage"),
 ("FERRAMENTAS","Diagnóstico e atualização","__tools__"),
 ("VOLTAR","Retornar à Home","__home__"),
]
TOOLS=[
 ("DIAGNÓSTICO DO CONTROLE","Dispositivos detectados","jottabox-controller-diagnostics"),
 ("REPARAR HOTKEY","SELECT + START","jottabox-repair-hotkey"),
 ("STATUS DO SISTEMA","Diagnóstico geral","jottabox-status"),
 ("ATUALIZAR JOTTABOX","Buscar versão nova","jottabox-update"),
 ("VOLTAR","Retornar","__settings__"),
]
POWER=[
 ("DESLIGAR","Desligar completamente","__shutdown__"),
 ("REINICIAR","Reiniciar o computador","__reboot__"),
 ("SAIR PARA LINUX","Fechar o JottaBox","__desktop__"),
 ("VOLTAR","Retornar à Home","__home__"),
]

page="home"; selected=0

def items():
    return {"home":MAIN,"library":LIBRARY,"settings":SETTINGS,"tools":TOOLS,"power":POWER}[page]

def draw():
    screen.fill(BG)
    x=int(W*.055); y=int(H*.04)
    a=F_LOGO.render("Jotta",True,WHITE); b=F_LOGO.render("Box",True,CYAN)
    screen.blit(a,(x,y)); screen.blit(b,(x+a.get_width()-3,y))

    title={"home":"INÍCIO","library":"BIBLIOTECA","settings":"CONFIGURAÇÕES","tools":"FERRAMENTAS","power":"ENERGIA"}[page]
    t=F_TITLE.render(title,True,WHITE); screen.blit(t,(x,int(H*.145)))

    arr=items()
    cols=3 if page=="home" else 2
    card_w=int(W*(.26 if cols==3 else .36)); card_h=int(H*.18 if page=="home" else H*.14)
    gapx=int(W*.035); gapy=int(H*.035)
    total=cols*card_w+(cols-1)*gapx; x0=(W-total)//2; y0=int(H*.245)
    for i,(name,sub,cmd) in enumerate(arr):
        row=i//cols; col=i%cols
        r=pygame.Rect(x0+col*(card_w+gapx),y0+row*(card_h+gapy),card_w,card_h)
        sel=i==selected
        pygame.draw.rect(screen,PANEL_SEL if sel else PANEL,r,border_radius=18)
        pygame.draw.rect(screen,CYAN if sel else (55,95,135),r,3 if sel else 1,border_radius=18)
        tn=F_CARD.render(name,True,WHITE); ts=F_SMALL.render(sub,True,MUTED)
        screen.blit(tn,(r.x+22,r.y+24)); screen.blit(ts,(r.x+22,r.y+66))
    foot=F_SMALL.render("D-pad/setas mover   A/ENTER selecionar   B/ESC voltar",True,MUTED)
    screen.blit(foot,(W//2-foot.get_width()//2,int(H*.93)))
    pygame.display.flip()

def restore_display():
    global screen
    pygame.display.quit(); pygame.display.init()
    screen=pygame.display.set_mode((W,H),pygame.FULLSCREEN|pygame.DOUBLEBUF)
    pygame.mouse.set_visible(False)
    pygame.event.clear()

def run_native(name):
    cmd=str(BIN/name)
    if not os.path.exists(cmd): return
    try:
        subprocess.run([cmd],check=False)
    finally:
        restore_display()

def run_external(cmd,shell=False):
    pygame.display.iconify(); pygame.mouse.set_visible(True)
    try:
        subprocess.run(cmd,shell=shell,check=False)
    finally:
        restore_display()

def activate(cmd):
    global page,selected
    if cmd=="__home__": page="home"; selected=0; return
    if cmd=="__library__": page="library"; selected=0; return
    if cmd=="__settings__": page="settings"; selected=0; return
    if cmd=="__tools__": page="tools"; selected=0; return
    if cmd=="__power__": page="power"; selected=0; return
    if cmd=="__shutdown__": subprocess.run(["systemctl","poweroff"]); return
    if cmd=="__reboot__": subprocess.run(["systemctl","reboot"]); return
    if cmd=="__desktop__": pygame.quit(); raise SystemExit
    if cmd=="__steam__": run_external(["flatpak","run","com.valvesoftware.Steam","-gamepadui"]); return

    if cmd in ("jottabox-import-roms","jottabox-download-roms","jottabox-configure-controller"):
        run_native(cmd); return
    if cmd in ("gpbox","xbox-cloud"):
        run_external([str(BIN/cmd)]); return

    runner=CFG/"console_runner.py"
    if runner.exists():
        run_native("jottabox-console-runner-"+cmd) if (BIN/("jottabox-console-runner-"+cmd)).exists() else subprocess.run(["python3",str(runner),str(BIN/cmd)],check=False)
        restore_display()
    else:
        run_external([str(BIN/cmd)])

while True:
    draw()
    arr=items(); cols=3 if page=="home" else 2
    for e in pygame.event.get():
        if e.type==pygame.QUIT:
            pygame.quit(); raise SystemExit
        if e.type==pygame.KEYDOWN:
            if e.key==pygame.K_ESCAPE:
                if page=="home": continue
                page="home"; selected=0
            elif e.key==pygame.K_LEFT: selected=(selected-1)%len(arr)
            elif e.key==pygame.K_RIGHT: selected=(selected+1)%len(arr)
            elif e.key==pygame.K_UP: selected=(selected-cols)%len(arr)
            elif e.key==pygame.K_DOWN: selected=(selected+cols)%len(arr)
            elif e.key==pygame.K_RETURN: activate(arr[selected][2])
        elif e.type==pygame.JOYHATMOTION:
            x,y=e.value
            if x<0: selected=(selected-1)%len(arr)
            elif x>0: selected=(selected+1)%len(arr)
            elif y>0: selected=(selected-cols)%len(arr)
            elif y<0: selected=(selected+cols)%len(arr)
        elif e.type==pygame.JOYBUTTONDOWN:
            if e.button==1:
                if page!="home": page="home"; selected=0
            elif e.button==0:
                activate(arr[selected][2])
    clock.tick(60)
