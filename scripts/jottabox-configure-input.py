#!/usr/bin/env python3
import json, os, re, sys, time, pygame

pygame.init()
pygame.joystick.init()

info=pygame.display.Info()
W,H=info.current_w,info.current_h
screen=pygame.display.set_mode((W,H),pygame.FULLSCREEN|pygame.DOUBLEBUF)
pygame.display.set_caption("JottaBox - Configurar controle")
clock=pygame.time.Clock()

HOME=os.path.expanduser("~")
CFG_ROOT=os.path.join(HOME,".config","jottabox-console")
PROFILE_DIR=os.path.join(CFG_ROOT,"controllers")
RETRO_ROOT=os.path.join(HOME,".var","app","org.libretro.RetroArch","config","retroarch")
RETRO_CFG=os.path.join(RETRO_ROOT,"retroarch.cfg")
AUTO_DIR=os.path.join(RETRO_ROOT,"autoconfig","udev")
os.makedirs(PROFILE_DIR,exist_ok=True)
os.makedirs(AUTO_DIR,exist_ok=True)

BG=(2,10,25); PANEL=(5,26,55); WHITE=(246,249,255)
MUTED=(150,180,215); CYAN=(24,213,255); GREEN=(70,235,150)
RED=(255,110,110)

def font(size,b=False):
    return pygame.font.SysFont("DejaVu Sans",size,bold=b)

F_LOGO=font(max(34,int(H*.050)),True)
F_TITLE=font(max(24,int(H*.031)),True)
F_BODY=font(max(17,int(H*.021)))
F_SMALL=font(max(13,int(H*.016)))

def txt(s,f,c=WHITE):
    return f.render(str(s),True,c)

def bg(title,sub=""):
    screen.fill(BG)
    pygame.draw.line(screen,CYAN,(int(W*.12),int(H*.18)),(int(W*.12),int(H*.84)),3)
    screen.blit(txt("JottaBox",F_LOGO,WHITE),(int(W*.07),int(H*.055)))
    t=txt(title,F_TITLE,WHITE)
    screen.blit(t,(W//2-t.get_width()//2,int(H*.105)))
    if sub:
        s=txt(sub,F_SMALL,MUTED)
        screen.blit(s,(W//2-s.get_width()//2,int(H*.15)))

def footer(s):
    t=txt(s,F_SMALL,MUTED)
    screen.blit(t,(W//2-t.get_width()//2,int(H*.92)))

def safe_name(s):
    s=re.sub(r'[^A-Za-z0-9 ._-]+','_',s).strip()
    return s or "Controller"

def joy_guid(j):
    try:
        return j.get_guid()
    except Exception:
        return f"index-{j.get_id()}"

def profile_path_for_guid(guid):
    return os.path.join(PROFILE_DIR,guid+".json")

def keyboard_profile_path():
    return os.path.join(PROFILE_DIR,"keyboard.json")

def configured(kind,guid=None):
    if kind=="keyboard":
        return os.path.isfile(keyboard_profile_path())
    return bool(guid and os.path.isfile(profile_path_for_guid(guid)))

def list_devices():
    pygame.joystick.quit(); pygame.joystick.init()
    out=[]
    for i in range(pygame.joystick.get_count()):
        try:
            j=pygame.joystick.Joystick(i); j.init()
            out.append({
                "kind":"gamepad",
                "name":j.get_name(),
                "guid":joy_guid(j),
                "index":i
            })
        except Exception:
            pass
    out.append({"kind":"keyboard","name":"Teclado físico","guid":"keyboard","index":None})
    return out

def device_menu():
    selected=0
    while True:
        devices=list_devices()
        if selected>=len(devices): selected=0

        bg("CONFIGURAR CONTROLE","Cada dispositivo possui seu próprio perfil")

        left=int(W*.20); width=int(W*.64); top=int(H*.23)
        rh=int(H*.105); gap=int(H*.018)

        for i,d in enumerate(devices):
            r=pygame.Rect(left,top+i*(rh+gap),width,rh)
            sel=i==selected
            pygame.draw.rect(screen,(8,48,86) if sel else PANEL,r,border_radius=16)
            pygame.draw.rect(screen,CYAN if sel else (55,95,135),r,3 if sel else 1,border_radius=16)

            label=("⌨  "+d["name"]) if d["kind"]=="keyboard" else ("🎮  "+d["name"])
            screen.blit(txt(label,F_BODY,WHITE),(r.x+24,r.y+int(r.h*.20)))

            ok=configured(d["kind"],d.get("guid"))
            status="✓ Configurado" if ok else "Não configurado"
            screen.blit(txt(status,F_SMALL,GREEN if ok else MUTED),(r.x+24,r.y+int(r.h*.59)))

            if d["kind"]=="gamepad":
                g=txt(d["guid"][:18]+"…",F_SMALL,MUTED)
                screen.blit(g,(r.right-g.get_width()-22,r.y+int(r.h*.20)))

        footer("D-pad/setas mover • A/ENTER configurar • B/ESC voltar")
        pygame.display.flip()

        for e in pygame.event.get():
            if e.type==pygame.QUIT:
                return None
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_ESCAPE: return None
                if e.key==pygame.K_UP: selected=(selected-1)%len(devices)
                elif e.key==pygame.K_DOWN: selected=(selected+1)%len(devices)
                elif e.key==pygame.K_RETURN: return devices[selected]
            elif e.type==pygame.JOYHATMOTION:
                if e.value[1]>0: selected=(selected-1)%len(devices)
                elif e.value[1]<0: selected=(selected+1)%len(devices)
            elif e.type==pygame.JOYBUTTONDOWN:
                if e.button==1: return None
                if e.button==0: return devices[selected]
        clock.tick(60)

def wait_key(label):
    pygame.event.clear()
    while True:
        bg("CONFIGURAR TECLADO",label)
        m=txt("Pressione a tecla física correspondente",F_BODY,CYAN)
        screen.blit(m,(W//2-m.get_width()//2,int(H*.46)))
        footer("ESC cancela")
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_ESCAPE: return None
                return e.key
            if e.type==pygame.QUIT: return None
        clock.tick(60)

def retro_key_name(keycode):
    n=pygame.key.name(keycode).lower().strip()
    aliases={
      "return":"enter","esc":"escape","left shift":"shift","right shift":"rshift",
      "left ctrl":"ctrl","right ctrl":"rctrl","left alt":"alt","right alt":"ralt",
      "page up":"pageup","page down":"pagedown",
    }
    return aliases.get(n,n.replace(" ",""))

def patch_retro_keyboard(mapping):
    lines=[]
    if os.path.isfile(RETRO_CFG):
        lines=open(RETRO_CFG,encoding="utf-8",errors="ignore").read().splitlines()

    bindings={
      "input_player1_up":"up","input_player1_down":"down",
      "input_player1_left":"left","input_player1_right":"right",
      "input_player1_b":"a","input_player1_a":"b",
      "input_player1_y":"x","input_player1_x":"y",
      "input_player1_select":"select","input_player1_start":"start",
      "input_player1_l":"l1","input_player1_r":"r1",
    }
    wanted={k:retro_key_name(mapping[v]) for k,v in bindings.items()}
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
    os.makedirs(os.path.dirname(RETRO_CFG),exist_ok=True)
    open(RETRO_CFG,"w",encoding="utf-8").write("\n".join(out)+"\n")

def configure_keyboard():
    steps=[
      ("up","CIMA"),("down","BAIXO"),("left","ESQUERDA"),("right","DIREITA"),
      ("a","A / CONFIRMAR"),("b","B / VOLTAR"),("x","X"),("y","Y"),
      ("select","SELECT / BACK"),("start","START"),
      ("l1","L1"),("r1","R1"),
    ]
    mapping={}
    for key,label in steps:
        code=wait_key(label)
        if code is None: return
        mapping[key]=code
        time.sleep(.08)

    with open(keyboard_profile_path(),"w",encoding="utf-8") as f:
        json.dump({
          "type":"keyboard",
          "name":"Teclado físico",
          "mapping":mapping,
          "updated_at":time.time()
        },f,indent=2,ensure_ascii=False)

    patch_retro_keyboard(mapping)
    done_screen("Teclado físico configurado","Perfil salvo separadamente")

def axis_or_hat_value(e, direction):
    if e.type==pygame.JOYHATMOTION:
        x,y=e.value
        names={(0,1):"h0up",(0,-1):"h0down",(-1,0):"h0left",(1,0):"h0right"}
        if (x,y) in names:
            return {"kind":"hat","retro":names[(x,y)]}
    if e.type==pygame.JOYAXISMOTION and abs(e.value)>.72:
        sign="+" if e.value>0 else "-"
        return {"kind":"axis","retro":f"{sign}{e.axis}"}
    if e.type==pygame.JOYBUTTONDOWN:
        return {"kind":"button","retro":str(e.button)}
    return None

def capture_gamepad(j,label,allow_axis=True):
    pygame.event.clear()
    while True:
        bg("CONFIGURAR CONTROLE",label)
        screen.blit(txt("Pressione/mova o comando correspondente",F_BODY,CYAN),
                    (int(W*.31),int(H*.46)))
        footer("ESC no teclado cancela")
        pygame.display.flip()

        for e in pygame.event.get():
            if e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE:
                return None
            if e.type==pygame.QUIT:
                return None
            if e.type==pygame.JOYBUTTONDOWN:
                return {"kind":"button","retro":str(e.button)}
            if e.type==pygame.JOYHATMOTION:
                v=axis_or_hat_value(e,label)
                if v: return v
            if allow_axis and e.type==pygame.JOYAXISMOTION:
                v=axis_or_hat_value(e,label)
                if v: return v
        clock.tick(60)

def retro_line(action,capture):
    # RetroArch autoconfig convention
    suffix={
      "up":"up","down":"down","left":"left","right":"right",
      "a":"b","b":"a","x":"y","y":"x",
      "select":"select","start":"start","l1":"l","r1":"r",
      "l2":"l2","r2":"r2","l3":"l3","r3":"r3",
      "ls_up":"l_y_minus","ls_down":"l_y_plus",
      "ls_left":"l_x_minus","ls_right":"l_x_plus",
      "rs_up":"r_y_minus","rs_down":"r_y_plus",
      "rs_left":"r_x_minus","rs_right":"r_x_plus",
    }[action]
    k=capture["kind"]
    if k=="button":
        return f'input_{suffix}_btn = "{capture["retro"]}"'
    if k=="axis":
        return f'input_{suffix}_axis = "{capture["retro"]}"'
    if k=="hat":
        return f'input_{suffix}_btn = "{capture["retro"]}"'
    return None


CONTROLLER_TYPES = [
    ("dualshock4", "DualShock 4"),
    ("dualsense", "DualSense"),
    ("xbox360", "Xbox 360"),
    ("xboxseries", "Xbox One / Series"),
    ("switchpro", "Nintendo Switch Pro"),
    ("generic", "Controle genérico"),
]

BASE_ACTIONS = [
    "a","b","x","y",
    "select","start",
    "l1","r1","l2","r2",
    "l3","r3",
    "up","down","left","right",
    "ls_up","ls_down","ls_left","ls_right",
    "rs_up","rs_down","rs_left","rs_right",
]

TYPE_LABELS = {
    "dualshock4": {
        "a":"X / CONFIRMAR", "b":"CÍRCULO / VOLTAR",
        "x":"QUADRADO", "y":"TRIÂNGULO",
        "select":"SHARE", "start":"OPTIONS",
        "l1":"L1","r1":"R1","l2":"L2","r2":"R2",
        "l3":"L3","r3":"R3",
    },
    "dualsense": {
        "a":"X / CONFIRMAR", "b":"CÍRCULO / VOLTAR",
        "x":"QUADRADO", "y":"TRIÂNGULO",
        "select":"CREATE", "start":"OPTIONS",
        "l1":"L1","r1":"R1","l2":"L2","r2":"R2",
        "l3":"L3","r3":"R3",
    },
    "xbox360": {
        "a":"A / CONFIRMAR", "b":"B / VOLTAR",
        "x":"X", "y":"Y",
        "select":"BACK", "start":"START",
        "l1":"LB","r1":"RB","l2":"LT","r2":"RT",
        "l3":"L3","r3":"R3",
    },
    "xboxseries": {
        "a":"A / CONFIRMAR", "b":"B / VOLTAR",
        "x":"X", "y":"Y",
        "select":"VIEW", "start":"MENU",
        "l1":"LB","r1":"RB","l2":"LT","r2":"RT",
        "l3":"L3","r3":"R3",
    },
    "switchpro": {
        "a":"A / CONFIRMAR", "b":"B / VOLTAR",
        "x":"X", "y":"Y",
        "select":"-", "start":"+",
        "l1":"L","r1":"R","l2":"ZL","r2":"ZR",
        "l3":"L3","r3":"R3",
    },
    "generic": {
        "a":"A / CONFIRMAR", "b":"B / VOLTAR",
        "x":"X", "y":"Y",
        "select":"SELECT", "start":"START",
        "l1":"L1","r1":"R1","l2":"L2","r2":"R2",
        "l3":"L3","r3":"R3",
    },
}

COMMON_LABELS = {
    "up":"D-PAD CIMA",
    "down":"D-PAD BAIXO",
    "left":"D-PAD ESQUERDA",
    "right":"D-PAD DIREITA",

    "ls_up":"ANALÓGICO ESQ. CIMA",
    "ls_down":"ANALÓGICO ESQ. BAIXO",
    "ls_left":"ANALÓGICO ESQ. ESQUERDA",
    "ls_right":"ANALÓGICO ESQ. DIREITA",

    "rs_up":"ANALÓGICO DIR. CIMA",
    "rs_down":"ANALÓGICO DIR. BAIXO",
    "rs_left":"ANALÓGICO DIR. ESQUERDA",
    "rs_right":"ANALÓGICO DIR. DIREITA",
}

def controller_type_menu(device, current=None):
    selected = 0

    if current:
        for i, (key, _) in enumerate(CONTROLLER_TYPES):
            if key == current:
                selected = i
                break

    while True:
        bg(
            "TIPO DE CONTROLE",
            device["name"]
        )

        left = int(W * .25)
        width = int(W * .50)
        top = int(H * .23)
        rh = int(H * .075)
        gap = int(H * .012)

        for i, (key, label) in enumerate(CONTROLLER_TYPES):
            r = pygame.Rect(
                left,
                top + i * (rh + gap),
                width,
                rh
            )

            sel = i == selected

            pygame.draw.rect(
                screen,
                (8,48,86) if sel else PANEL,
                r,
                border_radius=14
            )

            pygame.draw.rect(
                screen,
                CYAN if sel else (55,95,135),
                r,
                3 if sel else 1,
                border_radius=14
            )

            screen.blit(
                txt(label, F_BODY, WHITE),
                (r.x + 25, r.centery - F_BODY.get_height() // 2)
            )

        footer("Setas/D-pad mover • A/ENTER selecionar • B/ESC voltar")
        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return None

            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return None
                if e.key == pygame.K_UP:
                    selected = (selected - 1) % len(CONTROLLER_TYPES)
                elif e.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(CONTROLLER_TYPES)
                elif e.key == pygame.K_RETURN:
                    return CONTROLLER_TYPES[selected][0]

            elif e.type == pygame.JOYHATMOTION:
                if e.value[1] > 0:
                    selected = (selected - 1) % len(CONTROLLER_TYPES)
                elif e.value[1] < 0:
                    selected = (selected + 1) % len(CONTROLLER_TYPES)

            elif e.type == pygame.JOYBUTTONDOWN:
                if e.button == 1:
                    return None
                if e.button == 0:
                    return CONTROLLER_TYPES[selected][0]

        clock.tick(60)


def action_label(controller_type, action):
    return (
        TYPE_LABELS.get(controller_type, {}).get(action)
        or COMMON_LABELS.get(action)
        or action.upper()
    )


def capture_text(cap):
    if not cap:
        return "NÃO CONFIGURADO"

    if cap["kind"] == "button":
        return "BOTÃO " + cap["retro"]

    if cap["kind"] == "axis":
        return "EIXO " + cap["retro"]

    if cap["kind"] == "hat":
        return "HAT " + cap["retro"]

    return str(cap)


def wait_axis_neutral(j, timeout=2.0):
    start = time.monotonic()

    while time.monotonic() - start < timeout:
        neutral = True

        for i in range(j.get_numaxes()):
            try:
                if abs(j.get_axis(i)) > .25:
                    neutral = False
                    break
            except Exception:
                pass

        pygame.event.pump()

        if neutral:
            return

        time.sleep(.03)


def capture_one_mapping(j, label):
    pygame.event.clear()

    while True:
        bg("MAPEAR COMANDO", label)

        m = txt(
            "Pressione ou mova o comando físico correspondente",
            F_BODY,
            CYAN
        )

        screen.blit(
            m,
            (W // 2 - m.get_width() // 2, int(H * .45))
        )

        footer("ESC cancela esta alteração")
        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return None

            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return None

            cap = None

            if e.type == pygame.JOYBUTTONDOWN:
                cap = {
                    "kind":"button",
                    "retro":str(e.button)
                }

            elif e.type == pygame.JOYHATMOTION:
                cap = axis_or_hat_value(e, label)

            elif e.type == pygame.JOYAXISMOTION:
                cap = axis_or_hat_value(e, label)

            if cap:
                if cap["kind"] == "axis":
                    wait_axis_neutral(j)

                pygame.event.clear()
                return cap

        clock.tick(60)


def mapping_conflicts(mapping):
    used = {}
    conflicts = set()

    for action, cap in mapping.items():
        if not cap:
            continue

        sig = (
            cap.get("kind"),
            cap.get("retro")
        )

        if sig in used:
            conflicts.add(action)
            conflicts.add(used[sig])
        else:
            used[sig] = action

    return conflicts


def test_controller(j, mapping, controller_type):
    while True:
        bg(
            "TESTAR CONTROLE",
            "Pressione os comandos físicos para conferir o mapeamento"
        )

        active = set()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return

            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return

            if e.type == pygame.JOYBUTTONDOWN and e.button == 1:
                return

        for action, cap in mapping.items():
            if not cap:
                continue

            try:
                if cap["kind"] == "button":
                    if j.get_button(int(cap["retro"])):
                        active.add(action)

                elif cap["kind"] == "axis":
                    v = cap["retro"]
                    sign = v[0]
                    idx = int(v[1:])
                    value = j.get_axis(idx)

                    if sign == "+" and value > .65:
                        active.add(action)

                    if sign == "-" and value < -.65:
                        active.add(action)

                elif cap["kind"] == "hat":
                    hat = j.get_hat(0)

                    expected = {
                        "h0up":(0,1),
                        "h0down":(0,-1),
                        "h0left":(-1,0),
                        "h0right":(1,0),
                    }.get(cap["retro"])

                    if expected == hat:
                        active.add(action)

            except Exception:
                pass

        cols = 2
        rows = (len(BASE_ACTIONS) + 1) // 2

        left = int(W * .18)
        top = int(H * .22)
        cw = int(W * .31)
        rh = int(H * .045)

        for i, action in enumerate(BASE_ACTIONS):
            col = i // rows
            row = i % rows

            x = left + col * int(W * .37)
            y = top + row * rh

            label = action_label(controller_type, action)

            color = GREEN if action in active else MUTED

            screen.blit(
                txt(label, F_SMALL, color),
                (x, y)
            )

        footer("Os comandos ficam verdes quando detectados • B/ESC voltar")

        pygame.display.flip()
        clock.tick(60)


def save_gamepad_profile(j, controller_type, mapping):
    guid = joy_guid(j)

    profile = {
        "type":"gamepad",
        "controller_type":controller_type,
        "name":j.get_name(),
        "guid":guid,
        "mapping":mapping,
        "updated_at":time.time()
    }

    with open(
        profile_path_for_guid(guid),
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            profile,
            f,
            indent=2,
            ensure_ascii=False
        )

    fname = safe_name(j.get_name()) + "-" + guid[:8] + ".cfg"
    path = os.path.join(AUTO_DIR, fname)

    lines = [
        'input_driver = "udev"',
        f'input_device = "{j.get_name()}"',
        f'input_device_display_name = "{j.get_name()} (JottaBox)"',
    ]

    for action in BASE_ACTIONS:
        cap = mapping.get(action)

        if not cap:
            continue

        line = retro_line(action, cap)

        if line:
            lines.append(line)

    open(
        path,
        "w",
        encoding="utf-8"
    ).write("\n".join(lines) + "\n")

    cfg = []

    if os.path.isfile(RETRO_CFG):
        cfg = open(
            RETRO_CFG,
            encoding="utf-8",
            errors="ignore"
        ).read().splitlines()

    wanted = {
        "joypad_autoconfig_dir":os.path.join(
            RETRO_ROOT,
            "autoconfig"
        ),
        "input_autodetect_enable":"true",
        "input_joypad_driver":"udev",
    }

    out = []
    seen = set()

    for line in cfg:
        k = line.split("=",1)[0].strip() if "=" in line else ""

        if k in wanted:
            out.append(f'{k} = "{wanted[k]}"')
            seen.add(k)
        else:
            out.append(line)

    for k, v in wanted.items():
        if k not in seen:
            out.append(f'{k} = "{v}"')

    open(
        RETRO_CFG,
        "w",
        encoding="utf-8"
    ).write("\n".join(out) + "\n")


def configure_gamepad(device):
    pygame.joystick.quit()
    pygame.joystick.init()

    j = pygame.joystick.Joystick(device["index"])
    j.init()

    guid = joy_guid(j)
    existing = None
    mapping = {}
    controller_type = None

    profile_file = profile_path_for_guid(guid)

    if os.path.isfile(profile_file):
        try:
            existing = json.load(
                open(profile_file, encoding="utf-8")
            )

            mapping = existing.get("mapping", {})
            controller_type = existing.get("controller_type")
        except Exception:
            pass

    controller_type = controller_type_menu(
        device,
        controller_type
    )

    if controller_type is None:
        return

    selected = 0
    scroll = 0

    while True:
        conflicts = mapping_conflicts(mapping)

        bg(
            "MAPEAMENTO DO CONTROLE",
            TYPE_LABELS.get(controller_type, {}).get(
                "name",
                dict(CONTROLLER_TYPES).get(
                    controller_type,
                    controller_type
                )
            )
            + "  •  "
            + j.get_name()
        )

        visible_rows = 11

        if selected < scroll:
            scroll = selected

        if selected >= scroll + visible_rows:
            scroll = selected - visible_rows + 1

        left = int(W * .16)
        top = int(H * .215)
        width = int(W * .68)
        rh = int(H * .055)

        for row, idx in enumerate(
            range(
                scroll,
                min(len(BASE_ACTIONS), scroll + visible_rows)
            )
        ):
            action = BASE_ACTIONS[idx]

            r = pygame.Rect(
                left,
                top + row * rh,
                width,
                int(rh * .86)
            )

            sel = idx == selected

            pygame.draw.rect(
                screen,
                (8,48,86) if sel else PANEL,
                r,
                border_radius=11
            )

            pygame.draw.rect(
                screen,
                CYAN if sel else (50,85,120),
                r,
                2 if sel else 1,
                border_radius=11
            )

            label = action_label(controller_type, action)
            cap = mapping.get(action)

            value = capture_text(cap)

            if action in conflicts:
                value_color = RED
            elif cap:
                value_color = GREEN
            else:
                value_color = MUTED

            screen.blit(
                txt(label, F_SMALL, WHITE),
                (r.x + 18, r.centery - F_SMALL.get_height() // 2)
            )

            value_surface = txt(
                value,
                F_SMALL,
                value_color
            )

            screen.blit(
                value_surface,
                (
                    r.right - value_surface.get_width() - 18,
                    r.centery - value_surface.get_height() // 2
                )
            )

        footer(
            "A/ENTER editar • X/T apagar • Y testar • START/S salvar • B/ESC cancelar"
        )

        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return

            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return

                if e.key == pygame.K_UP:
                    selected = (selected - 1) % len(BASE_ACTIONS)

                elif e.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(BASE_ACTIONS)

                elif e.key == pygame.K_RETURN:
                    action = BASE_ACTIONS[selected]
                    cap = capture_one_mapping(
                        j,
                        action_label(controller_type, action)
                    )

                    if cap is not None:
                        mapping[action] = cap

                elif e.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
                    mapping.pop(BASE_ACTIONS[selected], None)

                elif e.key == pygame.K_t:
                    test_controller(
                        j,
                        mapping,
                        controller_type
                    )

                elif e.key == pygame.K_s:
                    if conflicts:
                        done_screen(
                            "Existem comandos duplicados",
                            "Corrija os itens vermelhos antes de salvar"
                        )
                    else:
                        save_gamepad_profile(
                            j,
                            controller_type,
                            mapping
                        )

                        done_screen(
                            "Controle configurado",
                            dict(CONTROLLER_TYPES)[controller_type]
                        )
                        return

            elif e.type == pygame.JOYHATMOTION:
                if e.value[1] > 0:
                    selected = (selected - 1) % len(BASE_ACTIONS)

                elif e.value[1] < 0:
                    selected = (selected + 1) % len(BASE_ACTIONS)

            elif e.type == pygame.JOYBUTTONDOWN:

                # Botão físico 0 = editar item selecionado.
                if e.button == 0:
                    action = BASE_ACTIONS[selected]

                    cap = capture_one_mapping(
                        j,
                        action_label(controller_type, action)
                    )

                    if cap is not None:
                        mapping[action] = cap

                # Botão físico 1 = voltar sem salvar.
                elif e.button == 1:
                    return

                # Botão físico 2 = apagar campo.
                elif e.button == 2:
                    mapping.pop(
                        BASE_ACTIONS[selected],
                        None
                    )

                # Botão físico 3 = testar.
                elif e.button == 3:
                    test_controller(
                        j,
                        mapping,
                        controller_type
                    )

                # Start comum em vários controles.
                elif e.button in (7, 9):
                    if conflicts:
                        done_screen(
                            "Existem comandos duplicados",
                            "Corrija os itens vermelhos antes de salvar"
                        )
                    else:
                        save_gamepad_profile(
                            j,
                            controller_type,
                            mapping
                        )

                        done_screen(
                            "Controle configurado",
                            dict(CONTROLLER_TYPES)[controller_type]
                        )
                        return

        clock.tick(60)

def done_screen(title,sub):
    while True:
        bg("CONFIGURAÇÃO CONCLUÍDA",title)
        s=txt(sub,F_SMALL,GREEN)
        screen.blit(s,(W//2-s.get_width()//2,int(H*.50)))
        footer("A / ENTER / B / ESC para voltar")
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type==pygame.KEYDOWN and e.key in (pygame.K_RETURN,pygame.K_ESCAPE): return
            if e.type==pygame.JOYBUTTONDOWN and e.button in (0,1): return
            if e.type==pygame.QUIT: return
        clock.tick(60)

while True:
    d=device_menu()
    if d is None:
        break
    if d["kind"]=="keyboard":
        configure_keyboard()
    else:
        configure_gamepad(d)

pygame.quit()
