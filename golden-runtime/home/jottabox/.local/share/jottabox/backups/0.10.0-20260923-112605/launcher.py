#!/usr/bin/env python3
import os, time, math, shutil, subprocess, pygame, pty, select, re, signal
from collections import deque

pygame.init()
pygame.joystick.init()

INFO=pygame.display.Info()
W,H=INFO.current_w,INFO.current_h
screen=pygame.display.set_mode((W,H),pygame.FULLSCREEN|pygame.DOUBLEBUF)
pygame.display.set_caption("JottaBox")
pygame.mouse.set_visible(False)
clock=pygame.time.Clock()

HOME=os.path.expanduser("~")
BIN=os.path.join(HOME,".local","bin")
ROM_ROOT=os.path.join(HOME,"ROMs")
ASSETS=os.path.join(HOME,".local","share","jottabox","assets")

WHITE=(246,249,255); MUTED=(166,190,220); CYAN=(24,213,255)
GREEN=(27,224,122); AMBER=(255,190,70); RED=(255,72,75)

def font(size,b=False):
    return pygame.font.SysFont("DejaVu Sans",size,bold=b)

F_LOGO=font(max(46,int(H*.058)),True)
F_TAG=font(max(12,int(H*.015)))
F_STATUS=font(max(13,int(H*.017)))
F_TITLE=font(max(25,int(H*.031)),True)
F_BODY=font(max(15,int(H*.019)))
F_SMALL=font(max(12,int(H*.015)))

def txt(s,f,c=WHITE): return f.render(str(s),True,c)

def load_img(name):
    try:
        return pygame.image.load(os.path.join(ASSETS,name)).convert_alpha()
    except Exception:
        return None

wall=load_img("wallpaper.png")
splash=load_img("splash.png")

HOME_ART={
 "cloud":load_img("home_xcloud.png"),
 "retro":load_img("home_retro.png"),
 "steam":load_img("home_steam.png"),
 "library":load_img("home_library.png"),
 "settings":load_img("home_settings.png"),
 "power":load_img("home_power.png"),
}
LIB_ART={
 "import":load_img("library_import.png"),
 "download":load_img("library_download.png"),
 "organize":load_img("library_organize.png"),
 "back":load_img("library_back.png"),
}
SET_ART={
 "controller":load_img("settings_gamepad.png"),
 "testpad":load_img("settings_status.png"),
 "gamepad":load_img("settings_gamepad.png"),
 "storage":load_img("settings_status.png"),
 "tools":load_img("settings_status.png"),
 "status":load_img("settings_status.png"),
 "update":load_img("settings_update.png"),
 "back":load_img("settings_back.png"),
}
POWER_ART={
 "power":load_img("power_power.png"),
 "restart":load_img("power_restart.png"),
 "desktop":load_img("power_back.png"),
 "back":load_img("power_back.png"),
}

MENU_META={
 "controller":("CONFIGURAR CONTROLE","Assistente automático","🎮"),
 "testpad":("DIAGNÓSTICO DO CONTROLE","PS4, Xbox, USB e Bluetooth","✓"),
 "gamepad":("REPARAR HOTKEY","SELECT + START","⌘"),
 "storage":("ARMAZENAMENTO","Escolher disco interno ou externo","▣"),
 "tools":("FERRAMENTAS","Diagnóstico, manutenção e atualização","⚙"),
 "keyboard":("TECLADO VIRTUAL","Abrir teclado na tela","⌨"),
 "status":("STATUS DO SISTEMA","Diagnóstico do JottaBox","⌁"),
 "update":("ATUALIZAR JOTTABOX","Sistema, emuladores e launcher","↻"),
 "power":("DESLIGAR","Desligar completamente","⏻"),
 "restart":("REINICIAR","Reiniciar o JottaBox","↻"),
 "desktop":("SAIR PARA LINUX","Fechar JottaBox e mostrar o desktop","⌂"),
 "back":("VOLTAR","Retornar à Home","←"),
}

MAIN=[
 ("cloud",os.path.join(BIN,"xbox-cloud")),
 ("retro",os.path.join(BIN,"gpbox")),
 ("steam","flatpak run com.valvesoftware.Steam -gamepadui"),
 ("library","__library__"),
 ("settings","__settings__"),
 ("power","__power__"),
]
LIBRARY=[
 ("import",os.path.join(BIN,"jottabox-import-roms")),
 ("download",os.path.join(BIN,"jottabox-download-roms")),
 ("organize",os.path.join(BIN,"jottabox-clean-roms")),
 ("back","__back__"),
]
SETTINGS=[
 ("controller","__controller_native__"),
 ("storage",os.path.join(BIN,"jottabox-storage")),
 ("tools","__tools__"),
 ("back","__back__"),
]

TOOLS=[
 ("keyboard","__keyboard__"),
 ("testpad",os.path.join(BIN,"jottabox-controller-diagnostics")),
 ("gamepad",os.path.join(BIN,"jottabox-repair-hotkey")),
 ("status",os.path.join(BIN,"jottabox-status")),
 ("update",os.path.join(BIN,"jottabox-update")),
 ("back","__back__"),
]
POWER=[
 ("power","__shutdown__"),
 ("restart","__reboot__"),
 ("desktop","__desktop__"),
 ("back","__back__"),
]

page="home"; selected=0; last_nav=0; status_time=0; status={}

joysticks=[]
def refresh_joy():
    global joysticks
    pygame.joystick.quit(); pygame.joystick.init()
    joysticks=[]
    for i in range(pygame.joystick.get_count()):
        try:
            j=pygame.joystick.Joystick(i); j.init(); joysticks.append(j)
        except Exception: pass
refresh_joy()

def net_ok():
    return subprocess.run(["bash","-lc","ip route | grep -q '^default '"],
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0

def rom_count():
    n=0
    try:
        for root,dirs,files in os.walk(ROM_ROOT):
            dirs[:]=[d for d in dirs if not d.startswith("_")]
            n+=len(files)
    except Exception: pass
    return n

def update_status():
    global status_time,status
    if time.monotonic()-status_time<4: return
    status_time=time.monotonic()
    try: disk=f"{shutil.disk_usage(HOME).free/(1024**3):.0f} GB livres"
    except Exception: disk="-- GB livres"
    status={"net":net_ok(),"disk":disk,"roms":rom_count()}

def background():
    if wall:
        screen.blit(pygame.transform.smoothscale(wall,(W,H)),(0,0))
    else:
        screen.fill((2,10,25))
    shade=pygame.Surface((W,H),pygame.SRCALPHA); shade.fill((0,6,18,48)); screen.blit(shade,(0,0))

def header():
    update_status()
    m=int(W*.06)
    a=txt("Jotta",F_LOGO,WHITE); b=txt("Box",F_LOGO,CYAN)
    screen.blit(a,(m,int(H*.034))); screen.blit(b,(m+a.get_width()-3,int(H*.034)))
    screen.blit(txt("MAIS JOGOS.  MAIS MOMENTOS.",F_TAG,(131,191,230)),(m+3,int(H*.108)))

    now=txt(time.strftime("%H:%M"),F_TITLE,WHITE)
    date=txt(time.strftime("%d/%m/%Y"),F_SMALL,WHITE)
    screen.blit(now,(W-m-now.get_width(),int(H*.036)))
    screen.blit(date,(W-m-date.get_width(),int(H*.079)))

    y=int(H*.118); x=int(W*.38)
    vals=[
      ("●  Controle conectado" if joysticks else "●  Controle desconectado",GREEN if joysticks else AMBER),
      ("●  Internet" if status.get("net") else "●  Sem internet",GREEN if status.get("net") else AMBER),
      (status.get("disk","-- GB livres"),WHITE),
    ]
    for label,c in vals:
        s=txt(label,F_STATUS,c); screen.blit(s,(x,y)); x+=s.get_width()+int(W*.035)

def alpha_rect(rect,color,radius=22,width=0):
    surf=pygame.Surface((rect.w,rect.h),pygame.SRCALPHA)
    pygame.draw.rect(surf,color,surf.get_rect(),width=width,border_radius=radius)
    screen.blit(surf,rect.topleft)

def glow(rect):
    for n,a in ((18,20),(10,42),(5,90)):
        rr=rect.inflate(n,n)
        s=pygame.Surface((rr.w,rr.h),pygame.SRCALPHA)
        pygame.draw.rect(s,(*CYAN,a),s.get_rect(),3,border_radius=26)
        screen.blit(s,rr.topleft)

def draw_art(art,rect):
    if not art:
        alpha_rect(rect,(8,22,48,235),22)
        return
    img=pygame.transform.smoothscale(art,(rect.w,rect.h))
    # rounded mask
    mask=pygame.Surface((rect.w,rect.h),pygame.SRCALPHA)
    pygame.draw.rect(mask,(255,255,255,255),mask.get_rect(),border_radius=22)
    img.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MIN)
    screen.blit(img,rect.topleft)

def draw_home():
    margin=int(W*.085); top=int(H*.198); gap=int(W*.016)
    cw=int((W-2*margin-2*gap)/3); ch=int(H*.252); rg=int(H*.022)
    for i,(kind,cmd) in enumerate(MAIN):
        row,col=divmod(i,3)
        r=pygame.Rect(margin+col*(cw+gap),top+row*(ch+rg),cw,ch)
        if i==selected: glow(r)
        draw_art(HOME_ART.get(kind),r)
        pygame.draw.rect(screen,CYAN if i==selected else (65,98,137),r,3 if i==selected else 1,border_radius=22)

def section_title(title):
    x=int(W*.074); y=int(H*.225)
    pygame.draw.line(screen,CYAN,(x,y-20),(x,y+62),3)
    screen.blit(txt(title,F_BODY,(165,205,236)),(x+22,y))
    pygame.draw.line(screen,CYAN,(x+22,y+38),(x+50,y+38),3)

def draw_native_card(kind,r,is_selected):
    label,sub,icon=MENU_META.get(kind,(kind.upper(),"","•"))

    if is_selected:
        glow(r)

    panel=pygame.Surface((r.w,r.h),pygame.SRCALPHA)
    panel.fill((4,23,52,218 if is_selected else 190))
    screen.blit(panel,r.topleft)

    pygame.draw.rect(
        screen,
        CYAN if is_selected else (62,101,145),
        r,
        3 if is_selected else 1,
        border_radius=max(12,int(r.h*.16))
    )

    icon_r=max(20,int(r.h*.27))
    icon_c=(r.x+int(r.h*.58),r.centery)
    pygame.draw.circle(screen,(22,91,147),icon_c,icon_r)
    pygame.draw.circle(screen,CYAN if is_selected else (108,181,225),icon_c,icon_r,2)

    it=txt(icon,F_BODY,WHITE)
    screen.blit(it,(icon_c[0]-it.get_width()//2,icon_c[1]-it.get_height()//2))

    tx=r.x+int(r.h*1.15)
    title_font=F_BODY if r.h < int(H*.105) else F_TITLE
    screen.blit(txt(label,title_font,WHITE),(tx,r.y+int(r.h*.17)))
    screen.blit(txt(sub,F_SMALL,(100,202,247)),(tx,r.y+int(r.h*.57)))

    ar=txt("›",F_TITLE,CYAN if is_selected else WHITE)
    screen.blit(ar,(r.right-ar.get_width()-22,r.centery-ar.get_height()//2))

def draw_list(title,items,arts):
    section_title(title)
    left=int(W*.225); top=int(H*.202); width=int(W*.64)

    if len(items)>=7:
        rh=int(H*.083); gap=int(H*.007)
    elif len(items)>4:
        rh=int(H*.108); gap=int(H*.010)
    else:
        rh=int(H*.137); gap=int(H*.015)

    for i,(kind,cmd) in enumerate(items):
        r=pygame.Rect(left,top+i*(rh+gap),width,rh)

        if page in ("settings","tools","power"):
            draw_native_card(kind,r,i==selected)
        else:
            if i==selected:
                glow(r)
            draw_art(arts.get(kind),r)
            pygame.draw.rect(
                screen,
                CYAN if i==selected else (61,91,128),
                r,
                3 if i==selected else 1,
                border_radius=22
            )

def footer():
    s=txt("A  Selecionar     B  Voltar     SELECT + START  Sair do jogo",F_SMALL,MUTED)
    screen.blit(s,((W-s.get_width())//2,H-int(H*.048)))

def active():
    return {"home":MAIN,"library":LIBRARY,"settings":SETTINGS,"tools":TOOLS,"power":POWER}[page]


def virtual_keyboard(initial=""):
    value=initial
    rows=[
        list("1234567890"),
        list("QWERTYUIOP"),
        list("ASDFGHJKL"),
        list("ZXCVBNM.-_"),
        [":","/","@","?","&","=","SPACE","BKSP"],
        ["CLEAR","OK","CANCEL"],
    ]
    rr=cc=0

    def clamp():
        nonlocal cc
        cc=max(0,min(cc,len(rows[rr])-1))

    while True:
        background(); header(); section_title("TECLADO VIRTUAL")

        field=pygame.Rect(int(W*.12),int(H*.19),int(W*.76),int(H*.09))
        fs=pygame.Surface((field.w,field.h),pygame.SRCALPHA)
        fs.fill((0,10,25,235)); screen.blit(fs,field.topleft)
        pygame.draw.rect(screen,CYAN,field,2,border_radius=14)
        shown=value[-90:] if value else "Digite..."
        screen.blit(txt(shown,F_BODY,WHITE if value else MUTED),(field.x+20,field.y+20))

        top=int(H*.33); row_h=int(H*.083)
        for r,row in enumerate(rows):
            gap=8
            usable=int(W*.76)
            kw=max(58,int((usable-gap*(len(row)-1))/len(row)))
            x0=(W-(kw*len(row)+gap*(len(row)-1)))//2
            for c,key in enumerate(row):
                kr=pygame.Rect(x0+c*(kw+gap),top+r*row_h,kw,row_h-10)
                sel=(r==rr and c==cc)
                ps=pygame.Surface((kr.w,kr.h),pygame.SRCALPHA)
                ps.fill((9,49,88,245) if sel else (4,25,51,225))
                screen.blit(ps,kr.topleft)
                pygame.draw.rect(screen,CYAN if sel else (60,105,150),kr,2 if sel else 1,border_radius=12)
                label="⌫" if key=="BKSP" else ("ESPAÇO" if key=="SPACE" else key)
                kt=txt(label,F_SMALL if len(label)>4 else F_BODY,WHITE)
                screen.blit(kt,(kr.centerx-kt.get_width()//2,kr.centery-kt.get_height()//2))

        hint=txt("D-pad mover  •  A selecionar  •  B cancelar",F_SMALL,MUTED)
        screen.blit(hint,(W//2-hint.get_width()//2,int(H*.91)))
        pygame.display.flip()

        for e in pygame.event.get():
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_ESCAPE:
                    return None
                if e.key==pygame.K_UP: rr=(rr-1)%len(rows); clamp(); continue
                if e.key==pygame.K_DOWN: rr=(rr+1)%len(rows); clamp(); continue
                if e.key==pygame.K_LEFT: cc=(cc-1)%len(rows[rr]); continue
                if e.key==pygame.K_RIGHT: cc=(cc+1)%len(rows[rr]); continue
                if e.key==pygame.K_BACKSPACE: value=value[:-1]; continue
                if e.key==pygame.K_RETURN:
                    key=rows[rr][cc]
                elif e.unicode and e.unicode.isprintable():
                    value+=e.unicode
                    continue
                else:
                    continue
            elif e.type==pygame.JOYHATMOTION:
                x,y=e.value
                if y>0: rr=(rr-1)%len(rows); clamp()
                elif y<0: rr=(rr+1)%len(rows); clamp()
                elif x<0: cc=(cc-1)%len(rows[rr])
                elif x>0: cc=(cc+1)%len(rows[rr])
                continue
            elif e.type==pygame.JOYBUTTONDOWN:
                if e.button==1:
                    return None
                if e.button!=0:
                    continue
                key=rows[rr][cc]
            else:
                continue

            if key=="OK": return value
            if key=="CANCEL": return None
            if key=="CLEAR": value=""
            elif key=="BKSP": value=value[:-1]
            elif key=="SPACE": value+=" "
            else: value+=key

        clock.tick(60)

def controller_wizard_native():
    pygame.joystick.quit()
    pygame.joystick.init()

    joys=[]
    for i in range(pygame.joystick.get_count()):
        try:
            j=pygame.joystick.Joystick(i); j.init(); joys.append(j)
        except Exception:
            pass

    if not joys:
        while True:
            background(); header(); section_title("CONFIGURAR CONTROLE")
            msg=txt("Nenhum controle encontrado",F_TITLE,WHITE)
            sub=txt("Conecte o controle e pressione A/ENTER para tentar novamente",F_BODY,MUTED)
            screen.blit(msg,(W//2-msg.get_width()//2,int(H*.42)))
            screen.blit(sub,(W//2-sub.get_width()//2,int(H*.49)))
            pygame.display.flip()
            for e in pygame.event.get():
                if e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE: return
                if e.type==pygame.JOYBUTTONDOWN and e.button==1: return
                if (e.type==pygame.KEYDOWN and e.key==pygame.K_RETURN) or (e.type==pygame.JOYBUTTONDOWN and e.button==0):
                    return controller_wizard_native()
            clock.tick(30)

    j=joys[0]
    steps=[
        ("input_b_btn","BOTÃO INFERIOR / A / X"),
        ("input_a_btn","BOTÃO DIREITO / B / CÍRCULO"),
        ("input_y_btn","BOTÃO ESQUERDO / X / QUADRADO"),
        ("input_x_btn","BOTÃO SUPERIOR / Y / TRIÂNGULO"),
        ("input_select_btn","SELECT / SHARE / BACK"),
        ("input_start_btn","START / OPTIONS / MENU"),
        ("input_l_btn","L1 / LB"),
        ("input_r_btn","R1 / RB"),
    ]
    mapping={}

    pygame.event.clear()
    for key,label in steps:
        captured=None
        while captured is None:
            background(); header(); section_title("CONFIGURAR CONTROLE")
            t=txt(label,F_TITLE,WHITE)
            s=txt("Pressione o botão correspondente",F_BODY,CYAN)
            esc=txt("B/ESC para cancelar",F_SMALL,MUTED)
            screen.blit(t,(W//2-t.get_width()//2,int(H*.40)))
            screen.blit(s,(W//2-s.get_width()//2,int(H*.48)))
            screen.blit(esc,(W//2-esc.get_width()//2,int(H*.80)))
            pygame.display.flip()

            for e in pygame.event.get():
                if e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE:
                    return
                if e.type==pygame.JOYBUTTONDOWN:
                    if e.button==1 and label.startswith("BOTÃO") is False:
                        # B can be a legitimate mapping, only cancel later stages via ESC
                        pass
                    captured=e.button
                    break
            clock.tick(60)
        mapping[key]=captured
        time.sleep(.12)
        pygame.event.clear()

    # D-pad
    hatmap={}
    for name,want in [("up",(0,1)),("down",(0,-1)),("left",(-1,0)),("right",(1,0))]:
        done=False
        while not done:
            background(); header(); section_title("CONFIGURAR CONTROLE")
            t=txt("D-PAD "+name.upper(),F_TITLE,WHITE)
            screen.blit(t,(W//2-t.get_width()//2,int(H*.43)))
            screen.blit(txt("Pressione a direção",F_BODY,CYAN),(int(W*.40),int(H*.51)))
            pygame.display.flip()
            for e in pygame.event.get():
                if e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE: return
                if e.type==pygame.JOYHATMOTION and e.value==want:
                    hatmap[name]=f"h0{name}"
                    done=True
                    break
            clock.tick(60)

    cfgdir=os.path.expanduser("~/.var/app/org.libretro.RetroArch/config/retroarch/autoconfig/udev")
    os.makedirs(cfgdir,exist_ok=True)
    safe="".join(c if c.isalnum() or c in " ._-" else "_" for c in j.get_name()).strip() or "JottaBox Controller"
    cfg=os.path.join(cfgdir,safe+".cfg")
    with open(cfg,"w",encoding="utf-8") as f:
        f.write('input_driver = "udev"\n')
        f.write(f'input_device = "{j.get_name()}"\n')
        f.write(f'input_device_display_name = "{j.get_name()} (JottaBox)"\n')
        for k,v in mapping.items():
            f.write(f'{k} = "{v}"\n')
        for name,val in hatmap.items():
            f.write(f'input_{name}_btn = "{val}"\n')

    retro=os.path.expanduser("~/.var/app/org.libretro.RetroArch/config/retroarch/retroarch.cfg")
    os.makedirs(os.path.dirname(retro),exist_ok=True)
    lines=[]
    if os.path.exists(retro):
        lines=open(retro,encoding="utf-8",errors="ignore").read().splitlines()
    wanted={
      "joypad_autoconfig_dir":os.path.expanduser("~/.var/app/org.libretro.RetroArch/config/retroarch/autoconfig"),
      "input_autodetect_enable":"true",
      "input_joypad_driver":"udev",
      "input_player1_joypad_index":"0",
    }
    out=[]
    seen=set()
    for line in lines:
        k=line.split("=",1)[0].strip() if "=" in line else ""
        if k in wanted:
            out.append(f'{k} = "{wanted[k]}"'); seen.add(k)
        else:
            out.append(line)
    for k,v in wanted.items():
        if k not in seen: out.append(f'{k} = "{v}"')
    open(retro,"w",encoding="utf-8").write("\n".join(out)+"\n")

    while True:
        background(); header(); section_title("CONFIGURAR CONTROLE")
        a=txt("Controle configurado com sucesso",F_TITLE,WHITE)
        b=txt(j.get_name(),F_BODY,CYAN)
        c=txt("A / ENTER / B / ESC para voltar",F_SMALL,MUTED)
        screen.blit(a,(W//2-a.get_width()//2,int(H*.42)))
        screen.blit(b,(W//2-b.get_width()//2,int(H*.50)))
        screen.blit(c,(W//2-c.get_width()//2,int(H*.72)))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type==pygame.KEYDOWN and e.key in (pygame.K_RETURN,pygame.K_ESCAPE): return
            if e.type==pygame.JOYBUTTONDOWN and e.button in (0,1): return
        clock.tick(30)

ANSI_RE=re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")

def _clean_term(s):
    s=ANSI_RE.sub("",s)
    s=s.replace("\r\n","\n").replace("\r","\n")
    return "".join(ch for ch in s if ch in "\n\t" or ord(ch)>=32)

def embedded_terminal(cmd,title="JottaBox"):
    master,slave=pty.openpty()
    env=os.environ.copy()
    env["TERM"]="xterm-256color"
    env["COLUMNS"]="108"
    env["LINES"]="28"

    proc=subprocess.Popen(
        ["bash","-lc",cmd],
        stdin=slave,
        stdout=slave,
        stderr=slave,
        env=env,
        start_new_session=True,
        close_fds=True
    )
    os.close(slave)
    os.set_blocking(master,False)

    lines=deque(maxlen=30)
    partial=""
    finished=False

    def feed(data):
        nonlocal partial
        partial += _clean_term(data)
        parts=partial.split("\n")
        partial=parts.pop() if parts else ""
        for line in parts:
            lines.append(line[-150:])

    def send(data):
        try:
            os.write(master,data)
        except Exception:
            pass

    while True:
        try:
            while True:
                ready,_,_=select.select([master],[],[],0)
                if not ready:
                    break
                chunk=os.read(master,8192)
                if not chunk:
                    break
                feed(chunk.decode("utf-8","replace"))
        except (BlockingIOError,OSError):
            pass

        rc=proc.poll()
        if rc is not None and not finished:
            finished=True
            if partial:
                lines.append(partial[-150:])
                partial=""
            lines.append("")
            lines.append("Concluído." if rc==0 else f"Processo encerrado (código {rc}).")
            lines.append("A / ENTER / B / ESC para voltar ao JottaBox")

        background()
        header()
        section_title(title.upper())

        box=pygame.Rect(int(W*.12),int(H*.18),int(W*.76),int(H*.69))
        surf=pygame.Surface((box.w,box.h),pygame.SRCALPHA)
        surf.fill((0,8,20,240))
        screen.blit(surf,box.topleft)
        pygame.draw.rect(screen,CYAN,box,2,border_radius=18)

        head=pygame.Rect(box.x,box.y,box.w,int(H*.065))
        pygame.draw.rect(screen,(7,35,67),head,border_radius=18)
        pygame.draw.rect(screen,(7,35,67),(head.x,head.bottom-18,head.w,18))
        screen.blit(txt("JottaBox • Console interno",F_BODY,WHITE),(head.x+22,head.y+16))

        font_term=font(max(13,int(H*.017)))
        lh=max(20,int(H*.026))
        y=head.bottom+18

        visible=list(lines)
        if partial:
            visible.append(partial[-150:])

        max_rows=max(1,int((box.bottom-y-38)/lh))
        visible=visible[-max_rows:]

        for ln in visible:
            color=(210,231,245)
            up=ln.upper()
            if "ERRO" in up or "ERROR" in up:
                color=(255,115,115)
            elif ln.startswith("OK:") or "Concluído." in ln:
                color=(104,238,164)
            screen.blit(txt(ln,font_term,color),(box.x+22,y))
            y+=lh

        hint=("Teclado físico disponível • A = ENTER • B = interromper"
              if not finished else
              "A / ENTER / B / ESC = voltar")
        hs=txt(hint,F_SMALL,MUTED)
        screen.blit(hs,(box.x+22,box.bottom-hs.get_height()-14))

        pygame.display.flip()

        for e in pygame.event.get():
            if e.type==pygame.QUIT:
                if not finished:
                    try:
                        os.killpg(proc.pid,signal.SIGTERM)
                    except Exception:
                        pass
                try:
                    os.close(master)
                except Exception:
                    pass
                return

            if e.type==pygame.KEYDOWN:
                if finished and e.key in (pygame.K_RETURN,pygame.K_ESCAPE):
                    try:
                        os.close(master)
                    except Exception:
                        pass
                    pygame.event.clear()
                    return

                if not finished:
                    if e.key==pygame.K_RETURN:
                        send(b"\n")
                    elif e.key==pygame.K_BACKSPACE:
                        send(b"\x7f")
                    elif e.key==pygame.K_UP:
                        send(b"\x1b[A")
                    elif e.key==pygame.K_DOWN:
                        send(b"\x1b[B")
                    elif e.key==pygame.K_RIGHT:
                        send(b"\x1b[C")
                    elif e.key==pygame.K_LEFT:
                        send(b"\x1b[D")
                    elif e.key==pygame.K_ESCAPE:
                        send(b"\x03")
                    elif e.unicode and e.unicode.isprintable():
                        send(e.unicode.encode("utf-8"))

            elif e.type==pygame.JOYBUTTONDOWN:
                if finished and e.button in (0,1):
                    try:
                        os.close(master)
                    except Exception:
                        pass
                    pygame.event.clear()
                    return

                if not finished:
                    if e.button==0:
                        send(b"\n")
                    elif e.button==1:
                        send(b"\x03")

            elif e.type==pygame.JOYHATMOTION and not finished:
                x,yh=e.value
                if yh>0:
                    send(b"\x1b[A")
                elif yh<0:
                    send(b"\x1b[B")
                elif x>0:
                    send(b"\x1b[C")
                elif x<0:
                    send(b"\x1b[D")

        clock.tick(30)

def launch(cmd):
    global page,selected
    if cmd=="__library__": page,selected="library",0; return
    if cmd=="__settings__": page,selected="settings",0; return
    if cmd=="__tools__": page,selected="tools",0; return
    if cmd=="__power__": page,selected="power",0; return
    if cmd=="__keyboard__":
        virtual_keyboard("")
        pygame.event.clear()
        return
    if cmd=="__controller_native__":
        controller_wizard_native()
        pygame.event.clear()
        return
    if cmd=="__back__":
        if page=="tools":
            page,selected="settings",0
        else:
            page,selected="home",0
        return
    if cmd=="__shutdown__": subprocess.run(["systemctl","poweroff"]); return
    if cmd=="__reboot__": subprocess.run(["systemctl","reboot"]); return
    if cmd=="__desktop__":
        pygame.quit()
        raise SystemExit(0)

    admin=any(cmd.endswith(x) for x in (
      "jottabox-import-roms","jottabox-clean-roms","jottabox-update",
      "jottabox-status","jottabox-repair-hotkey","jottabox-storage",
      "jottabox-controller-diagnostics"))

    if admin:
        titles={
          "jottabox-import-roms":"Importar jogos",
          "jottabox-clean-roms":"Organizar biblioteca",
          "jottabox-update":"Atualizar JottaBox",
          "jottabox-status":"Status do sistema",
          "jottabox-repair-hotkey":"Reparar hotkey",
          "jottabox-storage":"Armazenamento",
          "jottabox-controller-diagnostics":"Diagnóstico do controle",
        }
        name=os.path.basename(cmd)
        embedded_terminal(cmd,titles.get(name,"JottaBox"))
        pygame.mouse.set_visible(False)
        pygame.event.clear()
        return

    run=cmd
    pygame.display.iconify()
    pygame.mouse.set_visible(True)

    try:
        if cmd.endswith("xbox-cloud"):
            # Chromium/Edge pode retornar do comando inicial antes da janela fechar.
            # Inicia o XCloud e mantém o JottaBox escondido enquanto existir
            # qualquer processo usando o perfil exclusivo jottabox-edge-xcloud.
            subprocess.Popen(run, shell=True)

            # Dá tempo para o Edge criar o processo real.
            time.sleep(1.5)

            deadline=time.monotonic()+15
            seen_edge=False

            while True:
                edge_alive = subprocess.run(
                    ["pgrep","-f","jottabox-edge-xcloud"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                ).returncode == 0

                if edge_alive:
                    seen_edge=True
                elif seen_edge:
                    break
                elif time.monotonic() > deadline:
                    break

                pygame.event.pump()
                time.sleep(.35)

        else:
            subprocess.run(run,shell=True)

    except Exception:
        pass

    pygame.mouse.set_visible(False)
    pygame.display.set_mode((W,H),pygame.FULLSCREEN|pygame.DOUBLEBUF)

def move(d):
    global selected
    selected=(selected+d)%len(active())

def back():
    global page,selected
    if page=="home":
        page,selected="power",0
    elif page=="tools":
        page,selected="settings",0
    else:
        page,selected="home",0

def draw():
    background(); header()
    if page=="home": draw_home()
    elif page=="library": draw_list("BIBLIOTECA",LIBRARY,LIB_ART)
    elif page=="settings": draw_list("CONFIGURAÇÕES",SETTINGS,SET_ART)
    elif page=="tools": draw_list("FERRAMENTAS",TOOLS,SET_ART)
    elif page=="power": draw_list("ENERGIA",POWER,POWER_ART)
    footer(); pygame.display.flip()

if splash:
    screen.blit(pygame.transform.smoothscale(splash,(W,H)),(0,0)); pygame.display.flip()
    t=time.monotonic()
    while time.monotonic()-t<2.1:
        pygame.event.pump(); clock.tick(60)

running=True
while running:
    now=time.monotonic()
    for e in pygame.event.get():
        if e.type==pygame.QUIT: running=False
        elif e.type in (pygame.JOYDEVICEADDED,pygame.JOYDEVICEREMOVED): refresh_joy()
        elif e.type==pygame.KEYDOWN:
            if e.key in (pygame.K_LEFT,pygame.K_UP,pygame.K_a,pygame.K_w): move(-1)
            elif e.key in (pygame.K_RIGHT,pygame.K_DOWN,pygame.K_d,pygame.K_s): move(1)
            elif e.key in (pygame.K_RETURN,pygame.K_SPACE): launch(active()[selected][1])
            elif e.key in (pygame.K_ESCAPE,pygame.K_BACKSPACE): back()
        elif e.type==pygame.JOYBUTTONDOWN:
            # SELECT + Y abre o teclado virtual dentro do JottaBox.
            try:
                if e.button==3 and any(j.get_numbuttons()>6 and (j.get_button(6) or (j.get_numbuttons()>8 and j.get_button(8))) for j in joysticks):
                    virtual_keyboard("")
                    pygame.event.clear()
                    continue
            except Exception:
                pass
            if e.button==0: launch(active()[selected][1])
            elif e.button==1: back()
        elif e.type==pygame.JOYHATMOTION:
            if e.value[0]<0 or e.value[1]>0: move(-1)
            elif e.value[0]>0 or e.value[1]<0: move(1)

    if joysticks and now-last_nav>.23:
        try:
            x=joysticks[0].get_axis(0); y=joysticks[0].get_axis(1)
            if x<-.72 or y<-.72: move(-1); last_nav=now
            elif x>.72 or y>.72: move(1); last_nav=now
        except Exception: pass
    draw(); clock.tick(60)

pygame.quit()
