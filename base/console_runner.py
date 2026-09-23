#!/usr/bin/env python3
import os,sys,pty,select,subprocess,time,re,pygame
cmd=sys.argv[1:]
if not cmd: raise SystemExit(2)
pygame.init(); pygame.joystick.init()
i=pygame.display.Info(); W,H=i.current_w,i.current_h
screen=pygame.display.set_mode((W,H),pygame.FULLSCREEN|pygame.DOUBLEBUF)
pygame.mouse.set_visible(False); clock=pygame.time.Clock()
F=pygame.font.SysFont("DejaVu Sans Mono",max(14,int(H*.019)))
FT=pygame.font.SysFont("DejaVu Sans",max(25,int(H*.032)),bold=True)
lines=["Executando: "+" ".join(cmd)]; done=False; rc=None; buf=""
master,slave=pty.openpty()
p=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=slave,stderr=slave,close_fds=True)
os.close(slave); os.set_blocking(master,False)
ansi=re.compile(r'\x1b\[[0-9;?]*[ -/]*[@-~]')
while True:
    for e in pygame.event.get():
        if done and ((e.type==pygame.KEYDOWN and e.key in (pygame.K_RETURN,pygame.K_ESCAPE)) or (e.type==pygame.JOYBUTTONDOWN and e.button in (0,1))):
            pygame.quit(); raise SystemExit(rc or 0)
    if not done:
        try:
            r,_,_=select.select([master],[],[],0)
            if r:
                chunk=os.read(master,4096).decode("utf-8","ignore")
                buf+=chunk
                while "\n" in buf:
                    line,buf=buf.split("\n",1)
                    line=ansi.sub("",line).replace("\r","").strip()
                    if line: lines.append(line)
                    lines=lines[-18:]
        except (OSError,BlockingIOError): pass
        rc=p.poll()
        if rc is not None:
            if buf.strip(): lines.append(ansi.sub("",buf).replace("\r","").strip())
            done=True
    screen.fill((2,10,25))
    t=FT.render("JottaBox • Sistema",True,(246,249,255)); screen.blit(t,(int(W*.05),int(H*.06)))
    y=int(H*.15)
    for line in lines[-16:]:
        tx=F.render(line[:145],True,(170,195,220)); screen.blit(tx,(int(W*.05),y)); y+=int(H*.045)
    footer="A/ENTER para voltar" if done else "Aguarde..."
    tx=F.render(footer,True,(24,213,255)); screen.blit(tx,(W//2-tx.get_width()//2,int(H*.93)))
    pygame.display.flip(); clock.tick(30)
