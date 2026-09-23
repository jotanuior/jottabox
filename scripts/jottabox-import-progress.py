#!/usr/bin/env python3
import os, sys, time, pty, select, subprocess, re
from pathlib import Path
import pygame

HOME=Path.home()
SRC=Path(sys.argv[1] if len(sys.argv)>1 else HOME/"Downloads"/"rom")
ENGINE=HOME/".local"/"share"/"jottabox"/"jottabox.sh"
LOG=HOME/"jottabox-import.log"

def clean_line(s):
    s=re.sub(r'\x1b\[[0-9;?]*[ -/]*[@-~]','',s)
    s=s.replace('\r','').strip()
    return s

def main():
    pygame.init()
    pygame.joystick.init()
    info=pygame.display.Info()
    W,H=info.current_w,info.current_h
    screen=pygame.display.set_mode((W,H),pygame.FULLSCREEN|pygame.DOUBLEBUF)
    pygame.display.set_caption("JottaBox - Importar Jogos")
    pygame.mouse.set_visible(False)
    clock=pygame.time.Clock()

    WHITE=(246,249,255); MUTED=(150,176,205); CYAN=(24,213,255)
    GREEN=(72,220,150); RED=(255,100,110); BG=(2,10,25); PANEL=(5,25,52)

    def font(sz,b=False):
        return pygame.font.SysFont("DejaVu Sans",sz,bold=b)

    f_logo=font(max(36,int(H*.048)),True)
    f_title=font(max(25,int(H*.032)),True)
    f_body=font(max(17,int(H*.021)))
    f_small=font(max(14,int(H*.017)))

    lines=[]; current="Preparando importação..."
    started=time.monotonic(); done=False; rc=None

    master,slave=pty.openpty()
    env=os.environ.copy(); env["TERM"]="xterm-256color"
    proc=subprocess.Popen(
        [str(ENGINE),"import",str(SRC)],
        stdin=subprocess.DEVNULL, stdout=slave, stderr=slave,
        env=env, close_fds=True
    )
    os.close(slave)
    os.set_blocking(master,False)
    buf=""

    def append_line(line):
        nonlocal current
        line=clean_line(line)
        if not line:
            return
        current=line
        lines.append(line)
        if len(lines)>10:
            del lines[:-10]
        try:
            with LOG.open("a",encoding="utf-8") as f:
                f.write(line+"\n")
        except Exception:
            pass

    while True:
        for e in pygame.event.get():
            if e.type==pygame.QUIT:
                if proc.poll() is None:
                    proc.terminate()
                pygame.quit(); return
            if done:
                if e.type==pygame.KEYDOWN and e.key in (pygame.K_RETURN,pygame.K_ESCAPE):
                    pygame.quit(); return
                if e.type==pygame.JOYBUTTONDOWN and e.button in (0,1):
                    pygame.quit(); return

        if not done:
            try:
                ready,_,_=select.select([master],[],[],0)
                if ready:
                    chunk=os.read(master,4096).decode("utf-8","ignore")
                    if chunk:
                        buf+=chunk
                        while "\n" in buf:
                            line,buf=buf.split("\n",1)
                            append_line(line)
            except (BlockingIOError,OSError):
                pass

            rc=proc.poll()
            if rc is not None:
                if buf.strip():
                    append_line(buf); buf=""
                done=True
                try: os.close(master)
                except Exception: pass
                current="Importação concluída." if rc==0 else f"Importação terminou com erro ({rc})."

        screen.fill(BG)
        a=f_logo.render("Jotta",True,WHITE)
        b=f_logo.render("Box",True,CYAN)
        screen.blit(a,(int(W*.055),int(H*.045)))
        screen.blit(b,(int(W*.055)+a.get_width()-3,int(H*.045)))

        title=f_title.render("IMPORTANDO JOGOS",True,WHITE)
        screen.blit(title,(int(W*.055),int(H*.145)))

        elapsed=int(time.monotonic()-started)
        status=("CONCLUÍDO" if done and rc==0 else "ERRO" if done else "TRABALHANDO")
        status_color=GREEN if done and rc==0 else RED if done else CYAN
        st=f_small.render(f"{status}   •   {elapsed//60:02d}:{elapsed%60:02d}",True,status_color)
        screen.blit(st,(int(W*.055),int(H*.205)))

        box=pygame.Rect(int(W*.055),int(H*.255),int(W*.89),int(H*.17))
        pygame.draw.rect(screen,PANEL,box,border_radius=18)
        pygame.draw.rect(screen,(40,85,125),box,1,border_radius=18)
        c=f_body.render(current[:110],True,WHITE)
        screen.blit(c,(box.x+28,box.y+28))

        if not done:
            bar=pygame.Rect(box.x+28,box.bottom-45,box.width-56,10)
            pygame.draw.rect(screen,(24,45,70),bar,border_radius=5)
            width=max(90,int(bar.width*.22))
            span=max(1,bar.width-width)
            x=bar.x+int((time.monotonic()*220)%(span*2))
            if x>bar.x+span:
                x=bar.x+span-(x-(bar.x+span))
            pygame.draw.rect(screen,CYAN,(x,bar.y,width,bar.height),border_radius=5)

        hist_title=f_small.render("ÚLTIMAS AÇÕES",True,MUTED)
        screen.blit(hist_title,(int(W*.055),int(H*.47)))
        y=int(H*.515)
        for line in lines[-8:]:
            t=f_small.render(line[:125],True,MUTED)
            screen.blit(t,(int(W*.07),y))
            y+=int(H*.043)

        footer=("A/ENTER para voltar" if done and rc==0 else
                "A/ENTER para voltar • consulte ~/jottabox-import.log" if done else
                "Não desligue o equipamento durante a importação")
        ft=f_small.render(footer,True,MUTED)
        screen.blit(ft,(W//2-ft.get_width()//2,int(H*.93)))

        pygame.display.flip()
        clock.tick(30)

if __name__=="__main__":
    main()
