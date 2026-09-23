#!/usr/bin/env python3
import os, re, sys, json, time, html, traceback, subprocess
import urllib.parse, urllib.request
import pygame

pygame.init(); pygame.joystick.init()
HOME=os.path.expanduser("~")
CFG=os.path.join(HOME,".config","jottabox-console")
STATE=os.path.join(HOME,".local","share","jottabox")
ASSETS=os.path.join(STATE,"assets")
DEST=os.path.join(HOME,"Downloads","rom")
LOG=os.path.join(HOME,"jottabox-download.log")
GUI_LOG=os.path.join(HOME,"jotabox-downloader-gui.log")
SOURCES=os.path.join(CFG,"download-sources.json")
HISTORY=os.path.join(CFG,"download-history.json")
os.makedirs(CFG,exist_ok=True); os.makedirs(DEST,exist_ok=True)

ALLOWED={".zip",".7z",".nes",".sfc",".smc",".gb",".gbc",".gba",".nds",".n64",".z64",".v64",".md",".gen",".smd",".32x",".sms",".gg",".pce",".a26",".a52",".a78",".lnx",".ngp",".ngc",".ws",".wsc",".cue",".bin",".gdi",".chd",".iso",".cso",".pbp",".cdi",".rvz",".gcm",".gcz",".wbfs"}

def looks_like_file_name(name):
    clean=urllib.parse.unquote(name).rstrip("/")
    return os.path.splitext(clean)[1].lower() in ALLOWED

def force_file_url(url):
    # Alguns servidores (ex.: visualizadores de arquivo) exibem uma URL de .iso/.zip
    # com "/" no fim para permitir navegar dentro do arquivo. Para baixar o arquivo
    # real, removemos apenas essa barra final.
    return url[:-1] if url.endswith("/") and looks_like_file_name(url) else url

def crashhook(t,v,tb):
    try:
        with open(GUI_LOG,"a",encoding="utf-8") as f:
            f.write("\n===== CRASH GUI =====\n"); traceback.print_exception(t,v,tb,file=f)
    except Exception: pass
    sys.__excepthook__(t,v,tb)
sys.excepthook=crashhook

INFO=pygame.display.Info(); W,H=INFO.current_w,INFO.current_h
screen=pygame.display.set_mode((W,H),pygame.FULLSCREEN|pygame.DOUBLEBUF)
pygame.display.set_caption("JottaBox - Downloads"); pygame.mouse.set_visible(False)
clock=pygame.time.Clock()
WHITE=(246,249,255); MUTED=(164,184,210); CYAN=(24,213,255); GREEN=(21,230,126); AMBER=(255,190,84); PANEL=(4,17,38,225)

def font(size,b=False): return pygame.font.SysFont("DejaVu Sans",size,bold=b)
F_LOGO=font(max(44,int(H*.056)),True); F_TITLE=font(max(26,int(H*.032)),True); F_CARD=font(max(19,int(H*.024)),True); F_BODY=font(max(15,int(H*.020))); F_SMALL=font(max(13,int(H*.017)))
def txt(s,f,c=WHITE): return f.render(str(s),True,c)

def load_bg():
    try:
        img=pygame.image.load(os.path.join(ASSETS,"wallpaper.png")).convert(); return pygame.transform.smoothscale(img,(W,H))
    except Exception: return None
BG=load_bg()

def draw_bg():
    if BG: screen.blit(BG,(0,0))
    else: screen.fill((3,12,28))
    ov=pygame.Surface((W,H),pygame.SRCALPHA); ov.fill((0,7,20,95)); screen.blit(ov,(0,0))

def alpha_rect(r,color,radius=20):
    s=pygame.Surface((r.w,r.h),pygame.SRCALPHA); pygame.draw.rect(s,color,s.get_rect(),border_radius=radius); screen.blit(s,r.topleft)

def header(title,subtitle=""):
    m=int(W*.06); a=txt("Jotta",F_LOGO); b=txt("Box",F_LOGO,CYAN)
    screen.blit(a,(m,int(H*.035))); screen.blit(b,(m+a.get_width()-3,int(H*.035)))
    screen.blit(txt(title,F_TITLE),(m,int(H*.14)))
    if subtitle: screen.blit(txt(subtitle,F_BODY,MUTED),(m,int(H*.185)))

def footer(s):
    r=txt(s,F_SMALL,MUTED); screen.blit(r,((W-r.get_width())//2,H-int(H*.05)))

def load_json(path,default):
    try:
        with open(path,encoding="utf-8") as f: return json.load(f)
    except Exception: return default

def save_json(path,data):
    tmp=path+".tmp"
    with open(tmp,"w",encoding="utf-8") as f: json.dump(data,f,indent=2,ensure_ascii=False)
    os.replace(tmp,path)

def sources():
    data=load_json(SOURCES,[]); return data if isinstance(data,list) else []

def history():
    data=load_json(HISTORY,[]); return data if isinstance(data,list) else []

def add_history(url,name,status="ok"):
    data=history(); item={"url":url,"name":name,"status":status,"timestamp":int(time.time())}
    data=[x for x in data if x.get("url")!=url]; data.insert(0,item); save_json(HISTORY,data[:50])

def normalize_folder(url):
    url=url.strip(); p=urllib.parse.urlparse(url)
    if p.scheme not in ("http","https") or not p.netloc: raise ValueError("URL inválida")
    if not url.endswith("/"): url+="/"
    return url

def normalize_file(url):
    url=url.strip(); p=urllib.parse.urlparse(url)
    if p.scheme not in ("http","https") or not p.netloc: raise ValueError("URL inválida")
    clean_path=p.path.rstrip("/")
    name=urllib.parse.unquote(os.path.basename(clean_path))
    if not name: raise ValueError("A URL não aponta para um arquivo")
    if os.path.splitext(name)[1].lower() not in ALLOWED: raise ValueError("Extensão não reconhecida pelo JottaBox")
    if p.path.endswith("/"):
        url=urllib.parse.urlunparse((p.scheme,p.netloc,clean_path,p.params,p.query,p.fragment))
    return url,name

def get_html(url):
    req=urllib.request.Request(url,headers={"User-Agent":"JottaBox/1.0"})
    with urllib.request.urlopen(req,timeout=30) as r: return r.read().decode("utf-8","ignore")

def parent_url(url):
    p=urllib.parse.urlparse(url)
    path=p.path.rstrip("/")
    if not path or path=="/": return None
    parent=path.rsplit("/",1)[0] or "/"
    if not parent.endswith("/"): parent+="/"
    return urllib.parse.urlunparse((p.scheme,p.netloc,parent,"","",""))

def fetch_entries(root):
    data=get_html(root); hrefs=re.findall(r'href=["\']([^"\']+)["\']',data,re.I); rp=urllib.parse.urlparse(root)
    result=[]; seen=set()
    for href in hrefs:
        href=html.unescape(href)
        if href in ("../","./","/") or href.startswith("?"): continue
        full=urllib.parse.urljoin(root,href); p=urllib.parse.urlparse(full)
        if p.netloc!=rp.netloc or not full.startswith(root): continue
        rel=urllib.parse.unquote(full[len(root):]).strip("/")
        if not rel or "/" in rel: continue
        name=urllib.parse.unquote(rel)
        # Extensão conhecida tem prioridade sobre "/" final. Isso impede que
        # Archive.org trate .iso/.zip como pasta navegável dentro do arquivo.
        file_by_ext=looks_like_file_name(name)
        is_dir=href.endswith("/") and not file_by_ext
        if not is_dir and not file_by_ext: continue
        item_url=force_file_url(full) if file_by_ext else (full if full.endswith("/") else full+"/")
        item={"name":name.rstrip("/"),"url":item_url,"kind":"file" if file_by_ext else "dir"}
        key=(item["url"],item["kind"])
        if key not in seen: seen.add(key); result.append(item)
    result.sort(key=lambda e:(0 if e["kind"]=="dir" else 1,e["name"].lower())); return result

def crawl_files(folder_url,base_root,progress_cb=None):
    todo=[folder_url]; seen_dirs=set(); files=[]; seen_files=set(); root_host=urllib.parse.urlparse(base_root).netloc
    while todo:
        url=todo.pop()
        if url in seen_dirs: continue
        seen_dirs.add(url)
        if progress_cb: progress_cb("Lendo pasta "+urllib.parse.unquote(url.rstrip("/").split("/")[-1])+"...")
        try: data=get_html(url)
        except Exception as e:
            with open(LOG,"a",encoding="utf-8") as log: log.write(f"\nERRO listando {url}: {e}\n")
            continue
        for href in re.findall(r'href=["\']([^"\']+)["\']',data,re.I):
            href=html.unescape(href)
            if href in ("../","./","/") or href.startswith("?"): continue
            full=urllib.parse.urljoin(url,href); p=urllib.parse.urlparse(full)
            if p.netloc!=root_host or not full.startswith(folder_url): continue
            name=urllib.parse.unquote(p.path.rstrip("/").rsplit("/",1)[-1])
            if looks_like_file_name(name):
                file_url=force_file_url(full)
                if file_url not in seen_files:
                    seen_files.add(file_url); files.append(file_url)
            elif href.endswith("/"):
                if full not in seen_dirs: todo.append(full)
    return files

def dest_for_url(url,base_root=None,direct=False):
    up=urllib.parse.urlparse(url)
    if direct or not base_root:
        name=urllib.parse.unquote(os.path.basename(up.path.rstrip("/"))).replace("..","_"); return os.path.join(DEST,name)
    rp=urllib.parse.urlparse(base_root); base_path=rp.path
    rel=urllib.parse.unquote(up.path[len(base_path):]).lstrip("/") if up.path.startswith(base_path) else urllib.parse.unquote(up.path).lstrip("/")
    return os.path.join(DEST,rel.replace("..","_"))

def progress_screen(label,done=0,total=0):
    draw_bg(); header("Downloads",label); w=int(W*.68); h=36; x=(W-w)//2; y=int(H*.5)
    alpha_rect(pygame.Rect(x,y,w,h),(4,18,40,220),18); pct=(done/total) if total else 0
    pygame.draw.rect(screen,CYAN,(x,y,int(w*max(0,min(1,pct))),h),border_radius=18)
    if total:
        s=txt(f"{done}/{total}",F_BODY); screen.blit(s,((W-s.get_width())//2,y+55))
    pygame.display.flip(); pygame.event.pump()

def download_one(url,base_root=None,direct=False):
    dest=dest_for_url(url,base_root,direct); os.makedirs(os.path.dirname(dest),exist_ok=True)
    progress_screen("Baixando "+os.path.basename(dest))
    cmd=["wget","--continue","--tries=3","--timeout=30","--read-timeout=30","--waitretry=5","-O",dest,url]
    with open(LOG,"a",encoding="utf-8") as log:
        log.write(f"\n===== ARQUIVO {url} =====\n"); p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
    add_history(url,os.path.basename(dest),"ok" if p.returncode == 0 else "error")
    return p.returncode,dest

def run_folder_download(root,chosen):
    allfiles=[]
    for e in chosen:
        if e["kind"]=="file": allfiles.append(e["url"])
        else: allfiles.extend(crawl_files(e["url"],root,lambda s:progress_screen(s)))
    allfiles=list(dict.fromkeys(allfiles))
    if not allfiles: return False,"Nenhum arquivo compatível encontrado."
    errors=[]
    for i,url in enumerate(allfiles,1):
        progress_screen("Baixando "+urllib.parse.unquote(url.rsplit("/",1)[-1]),i-1,len(allfiles))
        rc,_=download_one(url,root,False)
        if rc != 0: errors.append(url)
    progress_screen("Downloads finalizados",len(allfiles),len(allfiles))
    return (not errors, f"{len(allfiles)-len(errors)}/{len(allfiles)} arquivo(s) concluído(s).")

def input_text(title,current="",subtitle="Use o teclado físico para digitar ou colar"):
    val=current
    while True:
        draw_bg(); header(title,subtitle); r=pygame.Rect(int(W*.08),int(H*.38),int(W*.84),int(H*.10)); alpha_rect(r,(4,18,40,230))
        screen.blit(txt(val[-110:] if val else "Digite aqui...",F_BODY,WHITE if val else MUTED),(r.x+20,r.y+25)); footer("ENTER Confirmar    ESC Cancelar")
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_RETURN: return val
                if e.key==pygame.K_ESCAPE: return None
                if e.key==pygame.K_BACKSPACE: val=val[:-1]
                elif e.unicode and e.unicode.isprintable(): val+=e.unicode
            elif e.type==pygame.JOYBUTTONDOWN and e.button==1: return None
        clock.tick(60)

def choose_list(title,items,render,footer_text="A/ENTER selecionar    B/ESC voltar"):
    if not items: return None
    cur=0; scroll=0
    while True:
        draw_bg(); header(title); top=int(H*.24); rh=int(H*.09); shown=7
        if cur<scroll: scroll=cur
        if cur>=scroll+shown: scroll=cur-shown+1
        for line,idx in enumerate(range(scroll,min(len(items),scroll+shown))):
            r=pygame.Rect(int(W*.10),top+line*rh,int(W*.80),rh-8); sel=idx==cur
            alpha_rect(r,(8,29,57,235) if sel else (4,18,40,215)); pygame.draw.rect(screen,CYAN if sel else (55,95,135),r,3 if sel else 1,border_radius=18)
            title1,sub=render(items[idx]); screen.blit(txt(title1,F_CARD),(r.x+18,r.y+10)); screen.blit(txt(sub,F_SMALL,MUTED),(r.x+18,r.y+42))
        footer(footer_text); pygame.display.flip()
        for e in pygame.event.get():
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_ESCAPE: return None
                if e.key==pygame.K_UP: cur=(cur-1)%len(items)
                elif e.key==pygame.K_DOWN: cur=(cur+1)%len(items)
                elif e.key==pygame.K_RETURN: return cur
            elif e.type==pygame.JOYHATMOTION:
                if e.value[1]>0: cur=(cur-1)%len(items)
                elif e.value[1]<0: cur=(cur+1)%len(items)
            elif e.type==pygame.JOYBUTTONDOWN:
                if e.button==1: return None
                if e.button==0: return cur
        clock.tick(60)

def save_source(url,kind):
    name=input_text("Salvar link","","Digite um nome para este link")
    if not name: return False
    data=sources(); data=[x for x in data if x.get("url")!=url]; data.insert(0,{"name":name.strip(),"url":url,"type":kind}); save_json(SOURCES,data[:100]); return True

def browser_mode(initial=""):
    current=initial.strip()
    message=""
    entries=[]
    selected=set()
    cursor=0
    scroll=0
    stage="url"

    def open_current():
        nonlocal current,entries,cursor,scroll,message,stage,selected
        p=urllib.parse.urlparse(current.strip())
        if p.scheme not in ("http","https") or not p.netloc:
            message="Erro: URL inválida"; return
        # If user pasted a direct file URL, download that one file.
        clean_name=urllib.parse.unquote(os.path.basename(p.path.rstrip("/")))
        if looks_like_file_name(clean_name):
            try:
                file_url,name=normalize_file(current)
                rc,dest=download_one(file_url,None,True)
                message=("Concluído: " if rc == 0 else "Falha: ")+os.path.basename(dest)
            except Exception as ex:
                message="Erro: "+str(ex)
            return
        current=normalize_folder(current)
        progress_screen("Lendo lista...")
        entries=fetch_entries(current)
        cursor=scroll=0
        selected.clear()
        message=f"{len(entries)} item(ns)"
        stage="browse"

    def enter_dir(url):
        nonlocal current,entries,cursor,scroll,message,stage,selected
        current=normalize_folder(url)
        progress_screen("Lendo pasta...")
        entries=fetch_entries(current)
        cursor=scroll=0
        selected.clear()
        message=f"{len(entries)} item(ns)"
        stage="browse"

    while True:
        draw_bg()
        if stage=="url":
            header("NAVEGAR / BAIXAR","Cole uma URL raiz, de pasta ou de arquivo")
            r=pygame.Rect(int(W*.08),int(H*.37),int(W*.84),int(H*.10)); alpha_rect(r,PANEL)
            screen.blit(txt(current or "Informe a URL...",F_BODY),(r.x+20,r.y+25))
            if message: screen.blit(txt(message,F_SMALL,AMBER),(r.x,r.bottom+24))
            footer("A/ENTER editar    START/F10 abrir    Y/S salvar link    B/ESC voltar")
        else:
            short=urllib.parse.unquote(urllib.parse.urlparse(current).path.rstrip("/") or "/")
            header("NAVEGAR / BAIXAR",short)
            top=int(H*.235); rh=int(H*.071); shown=8
            if entries:
                if cursor<scroll: scroll=cursor
                if cursor>=scroll+shown: scroll=cursor-shown+1
            for line,idx in enumerate(range(scroll,min(len(entries),scroll+shown))):
                e=entries[idx]
                r=pygame.Rect(int(W*.08),top+line*rh,int(W*.84),rh-7)
                alpha_rect(r,(8,29,57,235) if idx==cursor else (4,18,40,215))
                if idx==cursor: pygame.draw.rect(screen,CYAN,r,3,border_radius=18)
                if e["kind"]=="dir":
                    prefix="▸  PASTA"
                else:
                    prefix=("☑" if e["url"] in selected else "☐")+"  ARQUIVO"
                label=f'{prefix}  {e["name"]}'
                screen.blit(txt(label,F_CARD),(r.x+18,r.y+12))
            if message:
                m=txt(message,F_SMALL,AMBER); screen.blit(m,(int(W*.08),int(H*.84)))
            footer("A abrir pasta/marcar arquivo • X marcar todos • Y salvar URL • START baixar • B voltar")

        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type==pygame.KEYDOWN:
                if stage=="url":
                    if ev.key in (pygame.K_RETURN,pygame.K_SPACE):
                        v=input_text("NAVEGAR / BAIXAR",current,"Digite ou cole uma URL")
                        if v is not None: current=v
                    elif ev.key==pygame.K_F10:
                        try: open_current()
                        except Exception as ex: message="Erro: "+str(ex)
                    elif ev.key==pygame.K_s:
                        try:
                            p=urllib.parse.urlparse(current.strip())
                            kind="file" if looks_like_file_name(os.path.basename(p.path.rstrip("/"))) else "folder"
                            normalized=normalize_file(current)[0] if kind=="file" else normalize_folder(current)
                            message="Link salvo." if save_source(normalized,kind) else "Cancelado."
                        except Exception as ex: message="Erro: "+str(ex)
                    elif ev.key==pygame.K_ESCAPE:
                        return
                else:
                    if ev.key==pygame.K_ESCAPE:
                        parent=parent_url(current)
                        if parent:
                            try: enter_dir(parent)
                            except Exception as ex: message="Erro: "+str(ex)
                        else:
                            stage="url"
                    elif ev.key==pygame.K_UP and entries:
                        cursor=(cursor-1)%len(entries)
                    elif ev.key==pygame.K_DOWN and entries:
                        cursor=(cursor+1)%len(entries)
                    elif ev.key in (pygame.K_RETURN,pygame.K_SPACE) and entries:
                        e=entries[cursor]
                        if e["kind"]=="dir":
                            try: enter_dir(e["url"])
                            except Exception as ex: message="Erro: "+str(ex)
                        else:
                            if e["url"] in selected: selected.remove(e["url"])
                            else: selected.add(e["url"])
                    elif ev.key==pygame.K_x:
                        selected={e["url"] for e in entries if e["kind"]=="file"}
                    elif ev.key==pygame.K_y:
                        message="Link salvo." if save_source(current,"folder") else "Cancelado."
                    elif ev.key==pygame.K_F10:
                        chosen=[e for e in entries if e["kind"]=="file" and e["url"] in selected]
                        if chosen:
                            ok,msg=run_folder_download(current,chosen)
                            message=("Concluído. " if ok else "Falha. ")+msg
                        else:
                            message="Marque pelo menos um arquivo."
            elif ev.type==pygame.JOYHATMOTION and stage=="browse" and entries:
                if ev.value[1]>0: cursor=(cursor-1)%len(entries)
                elif ev.value[1]<0: cursor=(cursor+1)%len(entries)
            elif ev.type==pygame.JOYBUTTONDOWN:
                if stage=="url":
                    if ev.button==0:
                        v=input_text("NAVEGAR / BAIXAR",current,"Digite ou cole uma URL")
                        if v is not None: current=v
                    elif ev.button in (7,9):
                        try: open_current()
                        except Exception as ex: message="Erro: "+str(ex)
                    elif ev.button==3:
                        try:
                            p=urllib.parse.urlparse(current.strip())
                            kind="file" if looks_like_file_name(os.path.basename(p.path.rstrip("/"))) else "folder"
                            normalized=normalize_file(current)[0] if kind=="file" else normalize_folder(current)
                            message="Link salvo." if save_source(normalized,kind) else "Cancelado."
                        except Exception as ex: message="Erro: "+str(ex)
                    elif ev.button==1:
                        return
                else:
                    if ev.button==1:
                        parent=parent_url(current)
                        if parent:
                            try: enter_dir(parent)
                            except Exception as ex: message="Erro: "+str(ex)
                        else:
                            stage="url"
                    elif ev.button==0 and entries:
                        e=entries[cursor]
                        if e["kind"]=="dir":
                            try: enter_dir(e["url"])
                            except Exception as ex: message="Erro: "+str(ex)
                        else:
                            if e["url"] in selected: selected.remove(e["url"])
                            else: selected.add(e["url"])
                    elif ev.button==2:
                        selected={e["url"] for e in entries if e["kind"]=="file"}
                    elif ev.button==3:
                        message="Link salvo." if save_source(current,"folder") else "Cancelado."
                    elif ev.button in (7,9):
                        chosen=[e for e in entries if e["kind"]=="file" and e["url"] in selected]
                        if chosen:
                            ok,msg=run_folder_download(current,chosen)
                            message=("Concluído. " if ok else "Falha. ")+msg
                        else:
                            message="Marque pelo menos um arquivo."
        clock.tick(60)

def saved_mode():
    while True:
        data=sources()
        if not data:
            draw_bg(); header("LINKS SALVOS","Nenhum link salvo ainda"); footer("B/ESC voltar"); pygame.display.flip()
            while True:
                for e in pygame.event.get():
                    if e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE: return
                    if e.type==pygame.JOYBUTTONDOWN and e.button==1: return
                clock.tick(60)
        idx=choose_list("LINKS SALVOS",data,lambda x:(x.get("name","Sem nome"),("PASTA" if x.get("type")=="folder" else "ARQUIVO")+" • "+x.get("url","")))
        if idx is None: return
        item=data[idx]
        browser_mode(item.get("url",""))

def history_mode():
    while True:
        data=history()
        if not data:
            draw_bg(); header("HISTÓRICO","Nenhum download realizado ainda"); footer("B/ESC voltar"); pygame.display.flip()
            while True:
                for e in pygame.event.get():
                    if e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE: return
                    if e.type==pygame.JOYBUTTONDOWN and e.button==1: return
                clock.tick(60)
        idx=choose_list("HISTÓRICO",data,lambda x:(x.get("name","Arquivo"),time.strftime("%d/%m/%Y %H:%M",time.localtime(x.get("timestamp",0)))+" • "+x.get("status","")))
        if idx is None: return
        browser_mode(data[idx].get("url",""))

MENU=[("NAVEGAR / BAIXAR","Entrar em pastas, marcar arquivos e baixar"),("LINKS SALVOS","Abrir fontes e arquivos favoritos"),("HISTÓRICO","Reabrir downloads recentes"),("VOLTAR","Retornar ao JottaBox")]
selected=0; running=True
while running:
    draw_bg(); header("DOWNLOADS","Escolha como deseja baixar"); left=int(W*.18); width=int(W*.68); top=int(H*.24); rh=int(H*.105); gap=int(H*.017)
    for i,(name,sub) in enumerate(MENU):
        r=pygame.Rect(left,top+i*(rh+gap),width,rh); sel=i==selected; alpha_rect(r,(8,42,78,240) if sel else PANEL); pygame.draw.rect(screen,CYAN if sel else (55,95,135),r,3 if sel else 1,border_radius=18)
        screen.blit(txt(name,F_CARD),(r.x+24,r.y+14)); screen.blit(txt(sub,F_SMALL,MUTED),(r.x+24,r.y+48))
    footer("D-pad/setas mover    A/ENTER selecionar    B/ESC voltar"); pygame.display.flip()
    for e in pygame.event.get():
        if e.type==pygame.QUIT: running=False
        elif e.type==pygame.KEYDOWN:
            if e.key==pygame.K_ESCAPE: running=False
            elif e.key==pygame.K_UP: selected=(selected-1)%len(MENU)
            elif e.key==pygame.K_DOWN: selected=(selected+1)%len(MENU)
            elif e.key==pygame.K_RETURN:
                if selected==0: browser_mode()
                elif selected==1: saved_mode()
                elif selected==2: history_mode()
                else: running=False
        elif e.type==pygame.JOYHATMOTION:
            if e.value[1]>0: selected=(selected-1)%len(MENU)
            elif e.value[1]<0: selected=(selected+1)%len(MENU)
        elif e.type==pygame.JOYBUTTONDOWN:
            if e.button==1: running=False
            elif e.button==0:
                if selected==0: browser_mode()
                elif selected==1: saved_mode()
                elif selected==2: history_mode()
                else: running=False
    clock.tick(60)
pygame.quit()
