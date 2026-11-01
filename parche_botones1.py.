import os, sys, shutil, time
try:
    from PIL import Image
except Exception:
    print("ABORTO: falta Pillow"); sys.exit(1)
RAIZ = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato"
carpeta = None
for dp, dn, fn in os.walk(RAIZ):
    if "propina.png" in fn and "bak" not in dp:
        carpeta = dp; break
if not carpeta:
    print("ABORTO: no encuentro la carpeta de imagenes (propina.png)"); sys.exit(1)
print("Carpeta de imagenes:", carpeta)
cp = carpeta.rstrip("/") + "_bak_" + time.strftime("%Y%m%d%H%M%S")
shutil.copytree(carpeta, cp)
import math, time
from PIL import Image, ImageDraw, ImageChops, ImageFilter, ImageFont
DIRS=("/usr/share/fonts/truetype/dejavu/","/usr/share/fonts/dejavu/","/usr/share/fonts/TTF/")
def F(n,s):
    for D in DIRS:
        try: return ImageFont.truetype(D+n,s)
        except Exception: pass
    return ImageFont.load_default()
sans=lambda s,b=True:F("DejaVuSans-Bold.ttf" if b else "DejaVuSans.ttf",s)
mono=lambda s:F("DejaVuSansMono.ttf",s)
serb=lambda s:F("DejaVuSerif-Bold.ttf",s)
W,H=1280,720
def pill(img,xy,txt,font,fg,line,fill,pad=22):
    lay=Image.new("RGBA",img.size,(0,0,0,0)); d=ImageDraw.Draw(lay)
    w=d.textlength(txt,font=font); h=font.size+20; x,y=xy
    d.rounded_rectangle((x,y,x+w+2*pad,y+h),radius=h//2,fill=fill,outline=line,width=2)
    d.text((x+pad,y+h/2),txt,font=font,fill=fg,anchor="lm"); img.alpha_composite(lay); return x+w+2*pad
def star(d,c,R,fill):
    pts=[]
    for i in range(10):
        r=R if i%2==0 else R*0.42; a=-math.pi/2+i*math.pi/5
        pts.append((c[0]+r*math.cos(a),c[1]+r*math.sin(a)))
    d.polygon(pts,fill=fill)
def icono(d,tipo,c,R,col):
    x,y=c
    if tipo=="star": star(d,c,R*0.8,col)
    elif tipo=="bag":
        d.rounded_rectangle((x-R*.62,y-R*.35,x+R*.62,y+R*.7),radius=14,outline=col,width=10)
        d.arc((x-R*.32,y-R*.8,x+R*.32,y-R*.05),180,360,fill=col,width=10)
    elif tipo=="menu":
        for i in (-1,0,1): d.rounded_rectangle((x-R*.6,y+i*R*.42-9,x+R*.6,y+i*R*.42+9),radius=9,fill=col)
    elif tipo=="bubble":
        d.rounded_rectangle((x-R*.7,y-R*.55,x+R*.7,y+R*.35),radius=22,fill=col)
        d.polygon([(x-R*.3,y+R*.3),(x-R*.5,y+R*.8),(x+R*.05,y+R*.3)],fill=col)
        for k in (-1,0,1): d.ellipse((x+k*R*.32-9,y-R*.12-9,x+k*R*.32+9,y-R*.12+9),fill=(8,10,16,255))
    elif tipo=="funnel":
        d.polygon([(x-R*.75,y-R*.65),(x+R*.75,y-R*.65),(x+R*.12,y+R*.05),(x+R*.12,y+R*.7),(x-R*.12,y+R*.55),(x-R*.12,y+R*.05)],fill=col)
    elif tipo=="bars":
        for k,hh in enumerate((.5,.95,.7,1.2)):
            xx=x-R*.7+k*R*.46; d.rounded_rectangle((xx,y+R*.7-R*hh*1.1,xx+R*.3,y+R*.7),radius=6,fill=col)
    elif tipo=="bolt":
        d.polygon([(x+R*.15,y-R*.9),(x-R*.55,y+R*.1),(x-R*.05,y+R*.1),(x-R*.2,y+R*.9),(x+R*.6,y-R*.2),(x+R*.05,y-R*.2)],fill=col)
    elif tipo=="pct":
        d.text((x,y+2),"%",font=serb(int(R*1.7)),fill=col,anchor="mm")
    elif tipo=="bellx":
        icono(d,"bell",c,R,col); d.line((x-R*.85,y-R*.85,x+R*.85,y+R*.85),fill=(8,10,16,255),width=26); d.line((x-R*.85,y-R*.85,x+R*.85,y+R*.85),fill=col,width=12)
    elif tipo=="help":
        d.text((x,y+4),"?",font=serb(int(R*1.7)),fill=col,anchor="mm")
    elif tipo=="bell":
        d.pieslice((x-R*.55,y-R*.75,x+R*.55,y+R*.35),180,360,fill=col)
        d.rectangle((x-R*.55,y-R*.2,x+R*.55,y+R*.4),fill=col)
        d.rounded_rectangle((x-R*.75,y+R*.3,x+R*.75,y+R*.48),radius=9,fill=col)
        d.ellipse((x-R*.16,y+R*.5,x+R*.16,y+R*.8),fill=col)
def tarjeta(ruta,tag,titulo,sub,pills,nav,icon,acc,hora="",cmd="/menu"):
    base=Image.new("RGBA",(W,H),(5,6,10,255))
    M=28; ww,wh=W-2*M,H-2*M
    # fondo estudio con foco a la derecha
    cx,cy=int(ww*0.76),int(wh*0.50)
    g=Image.radial_gradient("L").resize((ww,wh)); 
    spot=Image.new("L",(ww,wh),0); sd=ImageDraw.Draw(spot)
    sd.ellipse((cx-420,cy-330,cx+420,cy+330),fill=255); spot=spot.filter(ImageFilter.GaussianBlur(140))
    col=Image.new("RGB",(ww,wh),(9,11,17))
    tint=Image.new("RGB",(ww,wh),tuple(int(v*0.55) for v in acc))
    win=Image.composite(tint,col,spot.point(lambda v:int(v*0.55))).convert("RGBA")
    gris=Image.composite(Image.new("RGB",(ww,wh),(120,126,140)),Image.new("RGB",(ww,wh),(0,0,0)),spot.point(lambda v:int(v*0.16)))
    win=ImageChops.add(win.convert("RGB"),gris).convert("RGBA")
    # cono de luz
    cone=Image.new("L",(ww,wh),0); ImageDraw.Draw(cone).polygon([(cx-60,0),(cx+60,0),(cx+300,wh),(cx-300,wh)],fill=60)
    cone=cone.filter(ImageFilter.GaussianBlur(45))
    win=ImageChops.add(win.convert("RGB"),Image.merge("RGB",[cone.point(lambda v:int(v*.3))]*3)).convert("RGBA")
    # disco de cristal con icono
    R=150
    glow=Image.new("RGBA",(ww,wh),(0,0,0,0)); gd=ImageDraw.Draw(glow)
    gd.ellipse((cx-R-40,cy-R-40,cx+R+40,cy+R+40),fill=acc+(110,)); glow=glow.filter(ImageFilter.GaussianBlur(50)); win.alpha_composite(glow)
    lay=Image.new("RGBA",(ww,wh),(0,0,0,0)); d=ImageDraw.Draw(lay)
    d.ellipse((cx-R,cy-R,cx+R,cy+R),fill=(8,10,16,225),outline=acc+(255,),width=5)
    d.ellipse((cx-R+22,cy-R+22,cx+R-22,cy+R-22),outline=(255,255,255,40),width=2)
    icono(d,icon,(cx,cy),R*0.62,acc+(255,))
    win.alpha_composite(lay)
    # suelo reflejo
    ref=Image.new("RGBA",(ww,wh),(0,0,0,0)); ImageDraw.Draw(ref).ellipse((cx-R*1.1,cy+R+30,cx+R*1.1,cy+R+60),fill=acc+(90,)); win.alpha_composite(ref.filter(ImageFilter.GaussianBlur(14)))
    # degradado a negro a la izquierda para legibilidad
    sh=Image.new("RGBA",(ww,wh),(0,0,0,0)); sdd=ImageDraw.Draw(sh)
    for x in range(0,int(ww*0.62)):
        sdd.line((x,0,x,wh),fill=(9,11,17,int(215*(1-x/(ww*0.62))**1.2)))
    win.alpha_composite(sh)
    d=ImageDraw.Draw(win)
    pill(win,(26,24),tag,mono(21),(240,242,248),(255,255,255,120),(8,10,16,190))
    d.text((ww-28,38),"CHIVATO DE OFERTAS · %s"%cmd.upper(),font=mono(19),fill=(215,220,232),anchor="rm")
    d.line((26,92,ww-26,92),fill=(70,74,86),width=1)
    nx=ww-28
    for l in reversed(nav):
        d.text((nx,116),l,font=mono(16),fill=(205,210,224),anchor="rm"); nx-=d.textlength(l,font=mono(16))+28
    # titulo
    tf=serb(86); y=250
    for i,l in enumerate(titulo):
        d.text((40,y+i*98),l,font=tf,fill=(255,255,255),anchor="lm")
    ys=y+len(titulo)*98+10
    for i,l in enumerate(sub):
        d.text((42,ys+i*38),l,font=sans(27,False),fill=(170,178,196),anchor="lm")
    x=40; yp=wh-120
    for k,(t,es) in enumerate(pills):
        if es: x=pill(win,(x,yp),t,sans(25),acc,acc+(170,),tuple(int(v*0.22) for v in acc)+(150,))+12
        else: x=pill(win,(x,yp),t,sans(25,False),(235,236,244),(255,255,255,90),(14,18,28,190))+12
    d=ImageDraw.Draw(win)
    d.text((40,wh-30),"CHIVATO DE OFERTAS · Todo el bot es gratis para todos.",font=sans(16,False),fill=(120,128,146),anchor="lm")
    m=Image.new("L",win.size,0); ImageDraw.Draw(m).rounded_rectangle((0,0,ww-1,wh-1),40,fill=255)
    base.paste(win,(M,M),m); ImageDraw.Draw(base).rounded_rectangle((M,M,W-M,H-M),40,outline=(46,50,62),width=2)
    base.convert("RGB").save(ruta)

MINT=(120,255,214); GOLD=(255,196,70); BLUE=(120,160,255); PINK=(255,110,200); RED=(255,95,110); VIO=(180,140,255); ORA=(255,150,80)
CARDS={
"inicio":("BIENVENIDA",["Chivato","de Ofertas"],["Te aviso de ofertas reales en Amazon.","Gratis y sin spam."],[("/menu",1),("Gratis",0),("Sin spam",0)],["OFERTAS","AVISOS","AHORRO"],"bell",MINT,"/start"),
"menu":("MENÚ",["Tu centro","de ofertas"],["Filtros, avisos, segunda mano y más.","Todo a un toque."],[("Ofertas",1),("Segunda mano",0),("Ayuda",0)],["OFERTAS","FILTRO","AVISOS","AYUDA"],"menu",MINT,"/menu"),
"ayuda":("AYUDA",["¿Cómo","funciona?"],["Recibes avisos de ofertas con descuento","real y precio mínimo histórico."],[("Guía rápida",1),("Contacto",0),("FAQ",0)],["AVISOS","FILTRO","SOPORTE"],"help",PINK,"/ayuda"),
"propina":("PROPINA",["Apoya el","proyecto"],["Opcional y voluntaria. Si el bot te ahorra","dinero, puedes invitarnos a un café."],[("300 ★ Stars",1),("o cripto (SOL)",0),("Gracias",0)],["STARS","CRIPTO","GRACIAS"],"star",GOLD,"/propina"),
"contacto":("CONTACTO",["Habla","con nosotros"],["Dudas, ideas o problemas.","Te respondemos lo antes posible."],[("Escríbenos",1),("Sugerencias",0),("Soporte",0)],["DUDAS","IDEAS","SOPORTE"],"bubble",BLUE,"/contacto"),
"suscribir":("SUSCRIPCIÓN",["Activa","los avisos"],["Recibe las mejores ofertas","en cuanto aparecen."],[("Suscribirme",1),("Gratis",0)],["AVISOS","OFERTAS","GRATIS"],"bell",MINT,"/suscribir"),
"parar":("AVISOS",["Pausar","los avisos"],["Deja de recibir ofertas.","Puedes volver cuando quieras."],[("Parar avisos",1),("Volver a activar",0)],["PAUSA","REACTIVAR"],"bellx",RED,"/parar"),
"umbral":("UMBRAL",["Tu descuento","mínimo"],["Elige a partir de qué descuento","quieres recibir avisos."],[("Ajustar %",1),("Más ofertas",0),("Más calidad",0)],["DESCUENTO","AVISOS"],"pct",ORA,"/umbral"),
"filtro":("FILTRO",["Tu filtro","a medida"],["Filtra por palabras o categorías","y no te pierdas nada útil."],[("Activar filtro",1),("Quitar filtro",0)],["PALABRAS","CATEGORÍAS"],"funnel",VIO,"/filtro"),
"ultimas":("ÚLTIMAS",["Las últimas","ofertas"],["Lo más reciente detectado,","con precio y valoraciones."],[("Ver ahora",1),("Mínimo histórico",0)],["HOY","RECIENTES"],"bolt",GOLD,"/ultimas"),
"estado":("ESTADO",["Tu estado","en el bot"],["Tus ajustes: avisos, filtro y umbral.","Todo de un vistazo."],[("Mi estado",1),("Ajustes",0)],["AVISOS","FILTRO","UMBRAL"],"bars",MINT,"/estado"),
}
def generar(carpeta):
    import os
    for nombre,(tag,tit,sub,pills,nav,icon,acc,cmd) in CARDS.items():
        tarjeta(os.path.join(carpeta,nombre+".png"),tag,tit,sub,pills,nav,icon,acc,cmd=cmd)

generar(carpeta)
print("Listo: 11 imagenes nuevas. Copia de las antiguas en", cp)
print("No hace falta reiniciar. Prueba /menu, /propina, /ayuda...")
print("Deshacer: rm -r", carpeta, "&& mv", cp, carpeta)
