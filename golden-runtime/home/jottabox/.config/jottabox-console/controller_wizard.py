#!/usr/bin/env python3
import os, sys, time, json, traceback, pygame

pygame.init()
pygame.joystick.init()

HOME=os.path.expanduser("~")
RA_DIR=os.path.join(HOME,".var","app","org.libretro.RetroArch","config","retroarch")
AUTO=os.path.join(RA_DIR,"autoconfig","udev")
CFG=os.path.join(RA_DIR,"retroarch.cfg")
LOG=os.path.join(HOME,"jottabox-controller-wizard.log")
os.makedirs(AUTO,exist_ok=True)

INFO=pygame.display.Info()
W,H=INFO.current_w,INFO.current_h
screen=pygame.display.set_mode((W,H),pygame.FULLSCREEN|pygame.DOUBLEBUF)
pygame.display.set_caption("JottaBox - Configurar controle")
pygame.mouse.set_visible(False)
clock=pygame.time.Clock()

WHITE=(245,249,255); MUTED=(162,187,219); CYAN=(26,213,255)
GREEN=(26,224,121); AMBER=(255,190,72); RED=(255,76,82)
BG=(3,12,28)

def font(sz,b=False):
    return pygame.font.SysFont("DejaVu Sans",sz,bold=b)

F1=font(max(38,int(H*.05)),True)
F2=font(max(24,int(H*.032)),True)
F3=font(max(17,int(H*.022)))
F4=font(max(14,int(H*.018)))

def txt(s,f,c=WHITE): return f.render(str(s),True,c)

def draw_bg():
    screen.fill(BG)
    pygame.draw.circle(screen,(7,39,78),(int(W*.82),int(H*.2)),int(H*.34))
    pygame.draw.circle(screen,(4,24,52),(int(W*.18),int(H*.85)),int(H*.42))

def center(s,y):
    screen.blit(s,((W-s.get_width())//2,y))

def header(title,sub=""):
    draw_bg()
    a=txt("Jotta",F1,WHITE); b=txt("Box",F1,CYAN)
    x=int(W*.06); y=int(H*.04)
    screen.blit(a,(x,y)); screen.blit(b,(x+a.get_width()-3,y))
    center(txt(title,F2,WHITE),int(H*.18))
    if sub: center(txt(sub,F3,MUTED),int(H*.235))

def message(title,body,color=WHITE,footer="ENTER continuar   ESC sair"):
    header(title)
    center(txt(body,F2,color),int(H*.43))
    center(txt(footer,F4,MUTED),int(H*.88))
    pygame.display.flip()

def wait_enter():
    while True:
        for e in pygame.event.get():
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_ESCAPE: return False
                if e.key in (pygame.K_RETURN,pygame.K_SPACE): return True
            elif e.type==pygame.JOYBUTTONDOWN:
                return True
        clock.tick(60)

def refresh_joy():
    pygame.joystick.quit(); pygame.joystick.init()
    arr=[]
    for i in range(pygame.joystick.get_count()):
        j=pygame.joystick.Joystick(i); j.init(); arr.append(j)
    return arr

def choose_joystick():
    joys=refresh_joy()
    if not joys:
        message("Configurar controle","Nenhum controle encontrado",RED,"Conecte o controle e pressione ENTER para tentar novamente")
        if wait_enter():
            joys=refresh_joy()
    if not joys: return None
    if len(joys)==1: return joys[0]

    idx=0
    while True:
        header("Escolha o controle","Use ↑ ↓ e ENTER")
        top=int(H*.34)
        for n,j in enumerate(joys):
            c=CYAN if n==idx else WHITE
            center(txt(("> " if n==idx else "  ")+j.get_name(),F2,c),top+n*55)
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_ESCAPE:return None
                if e.key==pygame.K_UP:idx=(idx-1)%len(joys)
                if e.key==pygame.K_DOWN:idx=(idx+1)%len(joys)
                if e.key in (pygame.K_RETURN,pygame.K_SPACE): return joys[idx]
            elif e.type==pygame.JOYBUTTONDOWN:
                return joys[e.joy] if e.joy < len(joys) else joys[0]
        clock.tick(60)

def neutral_axes(j):
    vals={}
    for a in range(j.get_numaxes()):
        try: vals[a]=j.get_axis(a)
        except: vals[a]=0.0
    return vals

def capture(j,label,allow_hat=True,allow_axis=True):
    base=neutral_axes(j)
    # drain events
    pygame.event.clear()
    started=time.monotonic()
    while True:
        header("Configurar controle",f"Controle: {j.get_name()}")
        center(txt(f"Pressione: {label}",F1,CYAN),int(H*.43))
        center(txt("ESC = cancelar   BACKSPACE = pular",F4,MUTED),int(H*.88))
        pygame.display.flip()

        for e in pygame.event.get():
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_ESCAPE: return "CANCEL",None
                if e.key==pygame.K_BACKSPACE: return "SKIP",None
            elif e.type==pygame.JOYBUTTONDOWN and e.joy==j.get_id():
                return "BTN",e.button
            elif allow_hat and e.type==pygame.JOYHATMOTION and e.joy==j.get_id():
                x,y=e.value
                if y>0:return "HAT","h0up"
                if y<0:return "HAT","h0down"
                if x<0:return "HAT","h0left"
                if x>0:return "HAT","h0right"
            elif allow_axis and e.type==pygame.JOYAXISMOTION and e.joy==j.get_id():
                prev=base.get(e.axis,0.0)
                if abs(e.value-prev)>.65 and abs(e.value)>.65:
                    sign="+" if e.value>0 else "-"
                    return "AXIS",f"{sign}{e.axis}"
        clock.tick(60)

def capture_axis_direction(j,label,axis_hint=None):
    return capture(j,label,allow_hat=False,allow_axis=True)

def cfg_line(key,kind,val):
    if kind=="BTN":
        return f'{key}_btn = "{val}"'
    if kind=="HAT":
        return f'{key}_btn = "{val}"'
    if kind=="AXIS":
        return f'{key}_axis = "{val}"'
    return None

j=choose_joystick()
if not j:
    pygame.quit(); sys.exit(1)

message("Configurar controle",j.get_name(),GREEN,"Pressione qualquer botão para começar")
if not wait_enter():
    pygame.quit(); sys.exit(0)

steps=[
 ("input_b","A / botão inferior",True,True),
 ("input_a","B / botão direito",True,True),
 ("input_y","X / botão esquerdo",True,True),
 ("input_x","Y / botão superior",True,True),
 ("input_select","SELECT / SHARE / BACK",False,False),
 ("input_start","START / OPTIONS",False,False),
 ("input_l","L1 / LB",False,False),
 ("input_r","R1 / RB",False,False),
 ("input_l2","L2 / LT",False,True),
 ("input_r2","R2 / RT",False,True),
 ("input_l3","pressione o analógico esquerdo",False,False),
 ("input_r3","pressione o analógico direito",False,False),
 ("input_up","D-Pad para CIMA",True,True),
 ("input_down","D-Pad para BAIXO",True,True),
 ("input_left","D-Pad para ESQUERDA",True,True),
 ("input_right","D-Pad para DIREITA",True,True),
 ("input_l_x_minus","analógico esquerdo para ESQUERDA",False,True),
 ("input_l_x_plus","analógico esquerdo para DIREITA",False,True),
 ("input_l_y_minus","analógico esquerdo para CIMA",False,True),
 ("input_l_y_plus","analógico esquerdo para BAIXO",False,True),
 ("input_r_x_minus","analógico direito para ESQUERDA",False,True),
 ("input_r_x_plus","analógico direito para DIREITA",False,True),
 ("input_r_y_minus","analógico direito para CIMA",False,True),
 ("input_r_y_plus","analógico direito para BAIXO",False,True),
]

lines=[
 'input_driver = "udev"',
 f'input_device = "{j.get_name()}"',
 f'input_device_display_name = "{j.get_name()} (JottaBox)"',
]

mapped=[]
for key,label,hat,axis in steps:
    kind,val=capture(j,label,allow_hat=hat,allow_axis=axis)
    if kind=="CANCEL":
        pygame.quit(); sys.exit(0)
    if kind=="SKIP":
        continue
    ln=cfg_line(key,kind,val)
    if ln:
        lines.append(ln)
        mapped.append((key,kind,val))

# Keep menu toggle on Guide/Home only if user explicitly maps it later.
safe_name="".join(c if c not in '/\\\0' else "_" for c in j.get_name()).strip() or "JottaBox Controller"
out=os.path.join(AUTO,safe_name+".cfg")
with open(out,"w") as f:
    f.write("\n".join(lines)+"\n")

# Ensure Flatpak RetroArch uses writable autoconfig dir and autodetection.
os.makedirs(RA_DIR,exist_ok=True)
cfg={}
raw=[]
if os.path.exists(CFG):
    with open(CFG,errors="ignore") as f:
        raw=f.readlines()

wanted={
    "joypad_autoconfig_dir": os.path.join(RA_DIR,"autoconfig"),
    "input_autodetect_enable":"true",
    "input_joypad_driver":"udev",
    "input_player1_joypad_index":"0",
}
seen=set()
new=[]
for line in raw:
    m=None
    if "=" in line and not line.lstrip().startswith("#"):
        k=line.split("=",1)[0].strip()
        if k in wanted:
            v=wanted[k]
            if v in ("true","false") or v.isdigit():
                new.append(f'{k} = "{v}"\n')
            else:
                new.append(f'{k} = "{v}"\n')
            seen.add(k)
            continue
    new.append(line)
for k,v in wanted.items():
    if k not in seen:
        new.append(f'{k} = "{v}"\n')
with open(CFG,"w") as f:
    f.writelines(new)

with open(LOG,"a") as f:
    f.write("\n===== PERFIL SALVO =====\n")
    f.write(out+"\n")
    for x in lines:f.write(x+"\n")

message("Controle configurado","Perfil salvo com sucesso",GREEN,"ENTER testar   ESC sair")
test=wait_enter()
if test:
    # Visual test screen
    while True:
        header("Testar controle",j.get_name())
        center(txt("Pressione botões e mova os analógicos",F2,WHITE),int(H*.32))
        yy=int(H*.42)
        vals=[]
        for b in range(j.get_numbuttons()):
            try:
                if j.get_button(b): vals.append(f"B{b}")
            except: pass
        for h in range(j.get_numhats()):
            try:
                v=j.get_hat(h)
                if v!=(0,0): vals.append(f"H{h}:{v}")
            except: pass
        for a in range(j.get_numaxes()):
            try:
                v=j.get_axis(a)
                if abs(v)>.25: vals.append(f"A{a}:{v:+.2f}")
            except: pass
        center(txt("   ".join(vals) if vals else "Aguardando entrada...",F2,CYAN if vals else MUTED),yy)
        center(txt("ESC / B = sair",F4,MUTED),int(H*.88))
        pygame.display.flip()
        leave=False
        for e in pygame.event.get():
            if e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE: leave=True
            if e.type==pygame.JOYBUTTONDOWN and e.button==1: leave=True
        if leave: break
        clock.tick(60)

pygame.quit()
