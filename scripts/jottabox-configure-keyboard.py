#!/usr/bin/env python3
import json, os, sys, pygame

pygame.init()
pygame.joystick.init()
info=pygame.display.Info()
W,H=info.current_w,info.current_h
screen=pygame.display.set_mode((W,H),pygame.FULLSCREEN|pygame.DOUBLEBUF)
pygame.display.set_caption("JottaBox - Configurar teclado")
clock=pygame.time.Clock()

HOME=os.path.expanduser("~")
CFG=os.path.join(HOME,".config","jottabox-console","keyboard.json")
RETRO=os.path.join(HOME,".var","app","org.libretro.RetroArch","config","retroarch","retroarch.cfg")

WHITE=(246,249,255); MUTED=(166,190,220); CYAN=(24,213,255); BG=(2,10,25)

def font(size,b=False):
    return pygame.font.SysFont("DejaVu Sans",size,bold=b)
F_TITLE=font(max(26,int(H*.032)),True)
F_BODY=font(max(17,int(H*.021)))
F_SMALL=font(max(13,int(H*.016)))

def txt(s,f,c=WHITE):
    return f.render(str(s),True,c)

def draw(title,subtitle,detail=""):
    screen.fill(BG)
    pygame.draw.line(screen,CYAN,(int(W*.14),int(H*.20)),(int(W*.14),int(H*.77)),3)
    a=txt("JottaBox",font(max(42,int(H*.052)),True),WHITE)
    screen.blit(a,(int(W*.08),int(H*.06)))
    t=txt(title,F_TITLE,WHITE)
    screen.blit(t,(W//2-t.get_width()//2,int(H*.36)))
    s=txt(subtitle,F_BODY,CYAN)
    screen.blit(s,(W//2-s.get_width()//2,int(H*.45)))
    if detail:
        d=txt(detail,F_SMALL,MUTED)
        screen.blit(d,(W//2-d.get_width()//2,int(H*.54)))
    h=txt("ESC cancela",F_SMALL,MUTED)
    screen.blit(h,(W//2-h.get_width()//2,int(H*.84)))
    pygame.display.flip()

def retro_name(keycode):
    n=pygame.key.name(keycode).lower().strip()
    aliases={
      "return":"enter","esc":"escape","left shift":"shift","right shift":"rshift",
      "left ctrl":"ctrl","right ctrl":"rctrl","left alt":"alt","right alt":"ralt",
      "page up":"pageup","page down":"pagedown",
    }
    return aliases.get(n,n.replace(" ",""))

def patch_retro(mapping):
    os.makedirs(os.path.dirname(RETRO),exist_ok=True)
    lines=[]
    if os.path.exists(RETRO):
        with open(RETRO,encoding="utf-8",errors="ignore") as f:
            lines=f.read().splitlines()
    bind={
      "input_player1_up":"up","input_player1_down":"down",
      "input_player1_left":"left","input_player1_right":"right",
      "input_player1_b":"a","input_player1_a":"b",
      "input_player1_y":"x","input_player1_x":"y",
      "input_player1_select":"select","input_player1_start":"start",
      "input_player1_l":"l1","input_player1_r":"r1",
    }
    wanted={k:retro_name(mapping[v]) for k,v in bind.items()}
    out=[]; seen=set()
    for line in lines:
        k=line.split("=",1)[0].strip() if "=" in line else ""
        if k in wanted:
            out.append(f'{k} = "{wanted[k]}"'); seen.add(k)
        else:
            out.append(line)
    for k,v in wanted.items():
        if k not in seen:
            out.append(f'{k} = "{v}"')
    with open(RETRO,"w",encoding="utf-8") as f:
        f.write("\n".join(out)+"\n")

steps=[
 ("up","CIMA"),("down","BAIXO"),("left","ESQUERDA"),("right","DIREITA"),
 ("a","BOTÃO A / CONFIRMAR"),("b","BOTÃO B / VOLTAR"),
 ("x","BOTÃO X"),("y","BOTÃO Y"),
 ("select","SELECT / BACK"),("start","START"),
 ("l1","L1"),("r1","R1"),
]

mapping={}
pygame.event.clear()
for action,label in steps:
    captured=None
    while captured is None:
        draw("CONFIGURAR TECLADO",label,"Pressione a tecla física que representará este botão")
        for e in pygame.event.get():
            if e.type==pygame.QUIT:
                pygame.quit(); sys.exit(1)
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_ESCAPE and action!="b":
                    pygame.quit(); sys.exit(0)
                captured=e.key
                break
        clock.tick(60)
    mapping[action]=captured
    pygame.event.clear()

os.makedirs(os.path.dirname(CFG),exist_ok=True)
with open(CFG,"w",encoding="utf-8") as f:
    json.dump(mapping,f,indent=2,ensure_ascii=False)

patch_retro(mapping)

while True:
    draw("TECLADO CONFIGURADO","O teclado físico agora funciona como controle",
         "Mapa aplicado ao JottaBox e ao RetroArch • ENTER ou ESC para voltar")
    for e in pygame.event.get():
        if e.type==pygame.QUIT:
            pygame.quit(); sys.exit(0)
        if e.type==pygame.KEYDOWN and e.key in (pygame.K_RETURN,pygame.K_ESCAPE):
            pygame.quit(); sys.exit(0)
    clock.tick(30)
