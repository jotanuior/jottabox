#!/usr/bin/env python3
import os, re, sys, json, time, html, traceback, subprocess
import urllib.parse, urllib.request
import pygame

pygame.init()
pygame.joystick.init()

HOME=os.path.expanduser("~")
CFG=os.path.join(HOME,".config","jottabox-console")
STATE=os.path.join(HOME,".local","share","jottabox")
ASSETS=os.path.join(STATE,"assets")
DEST=os.path.join(HOME,"Downloads","rom")
LOG=os.path.join(HOME,"jotabox-download.log")
GUI_LOG=os.path.join(HOME,"jotabox-downloader-gui.log")
LAST=os.path.join(CFG,"last-download.json")
os.makedirs(CFG,exist_ok=True)
os.makedirs(DEST,exist_ok=True)

def crashhook(t,v,tb):
    try:
        with open(GUI_LOG,"a") as f:
            f.write("\n===== CRASH GUI =====\n")
            traceback.print_exception(t,v,tb,file=f)
    except Exception:
        pass
    sys.__excepthook__(t,v,tb)
sys.excepthook=crashhook

INFO=pygame.display.Info()
W,H=INFO.current_w,INFO.current_h
screen=pygame.display.set_mode((W,H),pygame.FULLSCREEN|pygame.DOUBLEBUF)
pygame.display.set_caption("JottaBox - Downloads")
pygame.mouse.set_visible(False)
clock=pygame.time.Clock()

WHITE=(246,249,255); MUTED=(164,184,210); CYAN=(24,213,255)
GREEN=(21,230,126); RED=(255,70,78); AMBER=(255,190,84)
PANEL=(4,17,38,225)

def font(size,b=False): return pygame.font.SysFont("DejaVu Sans",size,bold=b)
F_LOGO=font(max(44,int(H*.056)),True)
F_TITLE=font(max(26,int(H*.032)),True)
F_CARD=font(max(19,int(H*.024)),True)
F_BODY=font(max(15,int(H*.020)))
F_SMALL=font(max(13,int(H*.017)))
def txt(s,f,c=WHITE): return f.render(str(s),True,c)

def load_bg():
    try:
        img=pygame.image.load(os.path.join(ASSETS,"wallpaper.png")).convert()
        return pygame.transform.smoothscale(img,(W,H))
    except Exception: return None
BG=load_bg()

def draw_bg():
    if BG: screen.blit(BG,(0,0))
    else: screen.fill((3,12,28))
    ov=pygame.Surface((W,H),pygame.SRCALPHA); ov.fill((0,7,20,95)); screen.blit(ov,(0,0))

def alpha_rect(r,color,radius=20):
    s=pygame.Surface((r.w,r.h),pygame.SRCALPHA)
    pygame.draw.rect(s,color,s.get_rect(),border_radius=radius); screen.blit(s,r.topleft)

def header(title,subtitle=""):
    m=int(W*.06)
    a=txt("Jotta",F_LOGO); b=txt("Box",F_LOGO,CYAN)
    screen.blit(a,(m,int(H*.035))); screen.blit(b,(m+a.get_width()-3,int(H*.035)))
    screen.blit(txt(title,F_TITLE),(m,int(H*.14)))
    if subtitle: screen.blit(txt(subtitle,F_BODY,MUTED),(m,int(H*.185)))

def footer(s):
    r=txt(s,F_SMALL,MUTED); screen.blit(r,((W-r.get_width())//2,H-int(H*.05)))

ALLOWED={
 ".zip",".7z",".nes",".sfc",".smc",".gb",".gbc",".gba",".nds",
 ".n64",".z64",".v64",".md",".gen",".smd",".32x",".sms",".gg",
 ".pce",".a26",".a52",".a78",".lnx",".ngp",".ngc",".ws",".wsc",
 ".cue",".bin",".gdi",".chd",".iso",".cso",".pbp",".cdi",
 ".rvz",".gcm",".gcz",".wbfs"
}

def normalize_root(url):
    url=url.strip()
    if not url.endswith("/"): url+="/"
    p=urllib.parse.urlparse(url)
    if p.scheme not in ("http","https") or not p.netloc:
        raise ValueError("URL inválida")
    return url

def get_html(url):
    req=urllib.request.Request(url,headers={"User-Agent":"JottaBox/1.0"})
    with urllib.request.urlopen(req,timeout=30) as r:
        return r.read().decode("utf-8","ignore")

def fetch_entries(root):
    data=get_html(root)
    hrefs=re.findall(r'href=["\']([^"\']+)["\']',data,re.I)
    rp=urllib.parse.urlparse(root)
    result=[]; seen=set()
    for href in hrefs:
        href=html.unescape(href)
        if href in ("../","./","/"): continue
        full=urllib.parse.urljoin(root,href)
        p=urllib.parse.urlparse(full)
        if p.netloc!=rp.netloc: continue
        if not full.startswith(root): continue
        rel=urllib.parse.unquote(full[len(root):]).strip("/")
        if not rel or "/" in rel: continue
        is_dir=href.endswith("/")
        name=urllib.parse.unquote(rel)
        if not is_dir and os.path.splitext(name)[1].lower() not in ALLOWED:
            continue
        item={"name":name,"url":full if not is_dir or full.endswith("/") else full+"/",
              "kind":"dir" if is_dir else "file"}
        key=(item["url"],item["kind"])
        if key not in seen:
            seen.add(key); result.append(item)
    result.sort(key=lambda e:(0 if e["kind"]=="dir" else 1,e["name"].lower()))
    return result

def crawl_files(folder_url, base_root, progress_cb=None):
    """Recursively parse directory indexes and return concrete file URLs."""
    todo=[folder_url]; seen_dirs=set(); files=[]; seen_files=set()
    root_host=urllib.parse.urlparse(base_root).netloc
    while todo:
        url=todo.pop()
        if url in seen_dirs: continue
        seen_dirs.add(url)
        if progress_cb: progress_cb(f"Lendo pasta {urllib.parse.unquote(url.rstrip('/').split('/')[-1])}...")
        try: data=get_html(url)
        except Exception as e:
            with open(LOG,"a") as log: log.write(f"\nERRO listando {url}: {e}\n")
            continue
        for href in re.findall(r'href=["\']([^"\']+)["\']',data,re.I):
            href=html.unescape(href)
            if href in ("../","./","/") or href.startswith("?"): continue
            full=urllib.parse.urljoin(url,href)
            p=urllib.parse.urlparse(full)
            if p.netloc!=root_host: continue
            # nunca sobe para fora da pasta selecionada
            if not full.startswith(folder_url): continue
            if href.endswith("/"):
                if full not in seen_dirs: todo.append(full)
            else:
                name=urllib.parse.unquote(p.path.rsplit("/",1)[-1])
                if os.path.splitext(name)[1].lower() in ALLOWED and full not in seen_files:
                    seen_files.add(full); files.append(full)
    return files

def dest_for_url(url, base_root):
    rp=urllib.parse.urlparse(base_root)
    up=urllib.parse.urlparse(url)
    base_path=rp.path
    rel=urllib.parse.unquote(up.path[len(base_path):]).lstrip("/") if up.path.startswith(base_path) else urllib.parse.unquote(up.path).lstrip("/")
    rel=rel.replace("..","_")
    return os.path.join(DEST,rel)

def download_file(url, base_root, label_cb=None):
    dest=dest_for_url(url,base_root)
    os.makedirs(os.path.dirname(dest),exist_ok=True)
    if label_cb: label_cb("Baixando "+os.path.basename(dest))
    cmd=["wget","--continue","--tries=3","--timeout=30","--read-timeout=30","--waitretry=5","-O",dest,url]
    with open(LOG,"a") as log:
        log.write(f"\n===== ARQUIVO {url} =====\n")
        p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
    return p.returncode

def progress_screen(label,done=0,total=0):
    draw_bg(); header("Downloads",label)
    w=int(W*.68); h=36; x=(W-w)//2; y=int(H*.5)
    alpha_rect(pygame.Rect(x,y,w,h),(4,18,40,220),18)
    pct=(done/total) if total else 0
    pygame.draw.rect(screen,CYAN,(x,y,int(w*max(0,min(1,pct))),h),border_radius=18)
    if total:
        s=txt(f"{done}/{total}",F_BODY); screen.blit(s,((W-s.get_width())//2,y+55))
    pygame.display.flip(); pygame.event.pump()

def run_download(root,selected):
    allfiles=[]
    for e in selected:
        if e["kind"]=="file":
            allfiles.append(e["url"])
        else:
            found=crawl_files(e["url"],root,lambda s:progress_screen(s))
            allfiles.extend(found)
    # preserva ordem e remove duplicatas
    allfiles=list(dict.fromkeys(allfiles))
    if not allfiles:
        return False,"Nenhum arquivo compatível encontrado."

    errors=[]
    for i,url in enumerate(allfiles,1):
        progress_screen("Baixando "+urllib.parse.unquote(url.rsplit("/",1)[-1]),i-1,len(allfiles))
        rc=download_file(url,root)
        if rc not in (0,8):
            errors.append((url,rc))
    progress_screen("Downloads finalizados",len(allfiles),len(allfiles))
    if errors:
        return False,f"{len(errors)} arquivo(s) falharam. Veja o log."
    return True,f"{len(allfiles)} arquivo(s) processados."

def load_last():
    try: return json.load(open(LAST))
    except Exception: return {"root_url":"","selected":[]}

def save_last(root,selected):
    try:
        with open(LAST,"w") as f: json.dump({"root_url":root,"selected":selected},f)
    except Exception: pass

def keyboard_url(current):
    val=current; active=True
    while active:
        draw_bg(); header("Downloads","Digite a URL da fonte autorizada")
        r=pygame.Rect(int(W*.08),int(H*.38),int(W*.84),int(H*.10))
        alpha_rect(r,(4,18,40,230))
        screen.blit(txt(val[-110:],F_BODY),(r.x+20,r.y+25))
        footer("ENTER Confirmar    ESC Cancelar")
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_RETURN: active=False
                elif e.key==pygame.K_ESCAPE: return current
                elif e.key==pygame.K_BACKSPACE: val=val[:-1]
                elif e.unicode and e.unicode.isprintable(): val+=e.unicode
        clock.tick(60)
    return val

state=load_last()
root=state.get("root_url","")
selected_names=set(state.get("selected",[]))
entries=[]; cursor=0; scroll=0; message=""; mode="url"

def load_entries():
    global entries,cursor,scroll,message,mode,root
    try:
        root=normalize_root(root)
        progress_screen("Lendo lista...")
        entries=fetch_entries(root)
        cursor=scroll=0
        message=f"{sum(e['kind']=='dir' for e in entries)} pasta(s), {sum(e['kind']=='file' for e in entries)} arquivo(s)"
        mode="browse"
    except Exception as e:
        message=f"Erro: {e}"
        mode="url"

running=True
while running:
    draw_bg()
    if mode=="url":
        header("Downloads","Tudo será salvo em ~/Downloads/rom. Depois use Importar Jogos.")
        r=pygame.Rect(int(W*.08),int(H*.38),int(W*.84),int(H*.10))
        alpha_rect(r,PANEL)
        screen.blit(txt(root or "Informe a URL...",F_BODY),(r.x+20,r.y+25))
        if message: screen.blit(txt(message,F_SMALL,AMBER),(r.x,r.bottom+25))
        footer("ENTER Editar URL    F10 Continuar    ESC Voltar")
    else:
        header("Downloads",message or "Selecione o que deseja baixar")
        top=int(H*.245); rh=int(H*.072); shown=7
        if cursor<scroll: scroll=cursor
        if cursor>=scroll+shown: scroll=cursor-shown+1
        for line,idx in enumerate(range(scroll,min(len(entries),scroll+shown))):
            e=entries[idx]; r=pygame.Rect(int(W*.10),top+line*rh,int(W*.80),rh-8)
            alpha_rect(r,(8,29,57,235) if idx==cursor else (4,18,40,215))
            if idx==cursor: pygame.draw.rect(screen,CYAN,r,3,border_radius=18)
            mark="☑" if e["name"] in selected_names else "☐"
            kind="PASTA" if e["kind"]=="dir" else "ARQUIVO"
            screen.blit(txt(f"{mark}  {kind}  {e['name']}",F_CARD),(r.x+18,r.y+13))
        footer("ENTER Marcar    X Todos    Y Limpar    F10 Baixar    ESC Voltar")
    pygame.display.flip()

    for ev in pygame.event.get():
        if ev.type==pygame.QUIT: running=False
        elif ev.type==pygame.KEYDOWN:
            if mode=="url":
                if ev.key in (pygame.K_RETURN,pygame.K_SPACE):
                    root=keyboard_url(root)
                elif ev.key==pygame.K_F10:
                    load_entries()
                elif ev.key==pygame.K_ESCAPE:
                    running=False
            else:
                if ev.key in (pygame.K_UP,pygame.K_LEFT):
                    cursor=(cursor-1)%len(entries) if entries else 0
                elif ev.key in (pygame.K_DOWN,pygame.K_RIGHT):
                    cursor=(cursor+1)%len(entries) if entries else 0
                elif ev.key in (pygame.K_RETURN,pygame.K_SPACE) and entries:
                    n=entries[cursor]["name"]
                    if n in selected_names: selected_names.remove(n)
                    else: selected_names.add(n)
                elif ev.key==pygame.K_x:
                    selected_names={e["name"] for e in entries}
                elif ev.key==pygame.K_y:
                    selected_names.clear()
                elif ev.key==pygame.K_F10:
                    chosen=[e for e in entries if e["name"] in selected_names]
                    if chosen:
                        save_last(root,list(selected_names))
                        ok,msg=run_download(root,chosen)
                        message=("Concluído. Agora use IMPORTAR JOGOS. " if ok else "Falha. ")+msg
                    else:
                        message="Marque pelo menos um item."
                elif ev.key==pygame.K_ESCAPE:
                    mode="url"

        elif ev.type==pygame.JOYBUTTONDOWN:
            # A=0, B=1, X=2, Y=3, START geralmente 7
            if mode=="url":
                if ev.button==0: root=keyboard_url(root)
                elif ev.button in (7,9): load_entries()
                elif ev.button==1: running=False
            else:
                if ev.button==0 and entries:
                    n=entries[cursor]["name"]
                    if n in selected_names: selected_names.remove(n)
                    else: selected_names.add(n)
                elif ev.button==2:
                    selected_names={e["name"] for e in entries}
                elif ev.button==3:
                    selected_names.clear()
                elif ev.button in (7,9):
                    chosen=[e for e in entries if e["name"] in selected_names]
                    if chosen:
                        save_last(root,list(selected_names))
                        ok,msg=run_download(root,chosen)
                        message=("Concluído. Agora use IMPORTAR JOGOS. " if ok else "Falha. ")+msg
                elif ev.button==1:
                    mode="url"

        elif ev.type==pygame.JOYHATMOTION and mode=="browse" and entries:
            if ev.value[1]>0: cursor=(cursor-1)%len(entries)
            elif ev.value[1]<0: cursor=(cursor+1)%len(entries)

    clock.tick(60)

pygame.quit()
