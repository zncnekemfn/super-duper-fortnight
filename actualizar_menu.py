import os, sys, math
from PIL import Image, ImageDraw, ImageFont

RUTA_BOT = "/opt/chivato/bot.py"
IMG_DIR = "/opt/chivato/img"
if len(sys.argv) > 2:
    RUTA_BOT, IMG_DIR = sys.argv[1], sys.argv[2]

# ---------------------------------------------------------------- imágenes
W, H = 960, 540
FUENTES = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
           "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
           "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]

def fuente(tam):
    for f in FUENTES:
        if os.path.exists(f):
            return ImageFont.truetype(f, tam)
    return ImageFont.load_default()

BLANCO = (255, 255, 255)

def fondo(c1, c2):
    im = Image.new("RGB", (W, H))
    px = im.load()
    for y in range(H):
        t = y / H
        c = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
        for x in range(W):
            px[x, y] = c
    return im

def estrella(d, cx, cy, R, r, col):
    pts = []
    for i in range(10):
        a = math.pi * i / 5 - math.pi / 2
        rr = R if i % 2 == 0 else r
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=col)

def icono(d, nombre, cx, cy, col):
    if nombre == "propina":
        estrella(d, cx, cy + 4, 85, 36, col)
    elif nombre == "contacto":
        d.rounded_rectangle((cx - 85, cy - 65, cx + 85, cy + 40), radius=26, fill=col)
        d.polygon([(cx - 40, cy + 35), (cx - 70, cy + 80), (cx - 5, cy + 35)], fill=col)
        for k in (-40, 0, 40):
            d.ellipse((cx + k - 9, cy - 23, cx + k + 9, cy - 5), fill=(255, 255, 255))
    elif nombre in ("suscribir", "parar"):
        d.ellipse((cx - 38, cy - 80, cx + 38, cy - 10), fill=col)
        d.polygon([(cx - 38, cy - 40), (cx + 38, cy - 40), (cx + 78, cy + 38), (cx - 78, cy + 38)], fill=col)
        d.rounded_rectangle((cx - 85, cy + 30, cx + 85, cy + 48), radius=9, fill=col)
        d.ellipse((cx - 17, cy + 52, cx + 17, cy + 84), fill=col)
        if nombre == "parar":
            d.line((cx - 90, cy - 80, cx + 90, cy + 85), fill=(255, 255, 255), width=24)
            d.line((cx - 90, cy - 80, cx + 90, cy + 85), fill=(200, 40, 40), width=12)
    elif nombre == "ultimas":
        for k, y in enumerate((-55, 0, 55)):
            d.ellipse((cx - 85, cy + y - 11, cx - 63, cy + y + 11), fill=col)
            d.rounded_rectangle((cx - 45, cy + y - 11, cx + 85 - k * 20, cy + y + 11), radius=11, fill=col)
    elif nombre == "estado":
        d.rounded_rectangle((cx - 80, cy + 10, cx - 40, cy + 75), radius=8, fill=col)
        d.rounded_rectangle((cx - 20, cy - 40, cx + 20, cy + 75), radius=8, fill=col)
        d.rounded_rectangle((cx + 40, cy - 80, cx + 80, cy + 75), radius=8, fill=col)
    elif nombre == "umbral":
        d.rounded_rectangle((cx - 90, cy - 8, cx + 90, cy + 8), radius=8, fill=col)
        d.ellipse((cx + 10, cy - 34, cx + 78, cy + 34), fill=col)
        d.ellipse((cx - 78, cy - 24, cx - 30, cy + 24), outline=col, width=10)
    elif nombre == "filtro":
        d.polygon([(cx - 90, cy - 75), (cx + 90, cy - 75), (cx + 22, cy + 5), (cx + 22, cy + 75),
                   (cx - 22, cy + 52), (cx - 22, cy + 5)], fill=col)
    elif nombre == "ayuda":
        f = fuente(190)
        w = d.textlength("?", font=f)
        d.text((cx - w / 2, cy - 112), "?", font=f, fill=col)
    elif nombre == "menu":
        for dx in (-50, 8):
            for dy in (-50, 8):
                d.rounded_rectangle((cx + dx - 6, cy + dy - 6, cx + dx + 48, cy + dy + 48), radius=14, fill=col)
    elif nombre == "inicio":
        pts = []
        for i in range(32):
            a = math.pi * i / 16 - math.pi / 2
            rr = 98 if i % 2 == 0 else 82
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        d.polygon(pts, fill=col)
        f = fuente(46)
        w = d.textlength("-80%", font=f)
        d.text((cx - w / 2, cy - 30), "-80%", font=f, fill=(255, 255, 255))

BANNERS = {
    "inicio":    ("CHIVATO DE OFERTAS", "Chollos y errores de precio", (14, 26, 70), (30, 20, 100), (238, 62, 38)),
    "menu":      ("MENÚ", "Elige una opción", (16, 32, 76), (20, 70, 130), (30, 90, 160)),
    "ayuda":     ("AYUDA", "Cómo funciona el bot", (50, 60, 90), (90, 110, 150), (60, 80, 125)),
    "propina":   ("PROPINA", "Hazte apoyante desde 500 Stars", (150, 70, 10), (235, 150, 30), (225, 130, 20)),
    "contacto":  ("CONTACTO", "Escribe directamente al creador", (14, 70, 140), (40, 140, 220), (25, 105, 190)),
    "suscribir": ("SUSCRIBIRSE", "Activa los avisos de chollos", (14, 100, 60), (40, 175, 100), (25, 140, 80)),
    "parar":     ("PARAR AVISOS", "Puedes volver cuando quieras", (110, 20, 30), (200, 60, 60), (175, 40, 45)),
    "ultimas":   ("ÚLTIMOS CHOLLOS", "Lo más reciente que he encontrado", (150, 40, 20), (240, 100, 40), (225, 80, 30)),
    "estado":    ("TU ESTADO", "Plan y configuración", (60, 30, 120), (130, 80, 210), (105, 60, 185)),
    "umbral":    ("DESCUENTO MÍNIMO", "Elige a partir de qué % te aviso", (10, 90, 100), (30, 170, 180), (20, 135, 150)),
    "filtro":    ("FILTROS", "Solo lo que te interesa", (40, 40, 130), (90, 100, 215), (65, 75, 190)),
}

def crear_imagen(clave):
    titulo, sub, c1, c2, ccol = BANNERS[clave]
    im = fondo(c1, c2)
    d = ImageDraw.Draw(im)
    cx, cy = W // 2, 200
    d.ellipse((cx - 130, cy - 130, cx + 130, cy + 130), fill=(255, 255, 255))
    icono(d, clave, cx, cy, ccol)
    f1 = fuente(76)
    while d.textlength(titulo, font=f1) > W - 80:
        f1 = fuente(f1.size - 4)
    w = d.textlength(titulo, font=f1)
    d.text((cx - w / 2, 350), titulo, font=f1, fill=BLANCO)
    f2 = fuente(36)
    while d.textlength(sub, font=f2) > W - 80:
        f2 = fuente(f2.size - 2)
    w = d.textlength(sub, font=f2)
    d.text((cx - w / 2, 455), sub, font=f2, fill=(230, 235, 250))
    im.save(os.path.join(IMG_DIR, clave + ".png"), optimize=True)

os.makedirs(IMG_DIR, exist_ok=True)
for k in BANNERS:
    crear_imagen(k)
print("Imágenes creadas:", len(BANNERS))

# ---------------------------------------------------------------- parche del bot
s = open(RUTA_BOT, encoding="utf-8").read()
if "def ejecutar(" in s:
    print("El menú ya estaba instalado en el bot.")
    sys.exit(0)

def cambiar(viejo, nuevo):
    global s
    if s.count(viejo) != 1:
        print("NO ENCONTRADO:", viejo[:70])
        sys.exit(1)
    s = s.replace(viejo, nuevo)

cambiar('''def enviar(chat, texto, markup=None):
    datos = {"chat_id": chat, "text": texto}''', '''def enviar(chat, texto, markup=None):
    if _ctx["img"] and str(chat) == _ctx["cid"]:
        nombre = _ctx["img"]
        _ctx["img"] = None
        st = enviar_con_foto(chat, nombre, texto, markup)
        if st is not None:
            return st
    datos = {"chat_id": chat, "text": texto}''')

bloque = '''IMG_DIR = "/opt/chivato/img"
IMAGENES = {
    "/start": "inicio", "/menu": "menu", "/ayuda": "ayuda", "/help": "ayuda",
    "/propina": "propina", "/premium": "propina", "/contacto": "contacto", "/fin": "contacto",
    "/suscribir": "suscribir", "/parar": "parar", "/umbral": "umbral",
    "/filtro": "filtro", "/quitarfiltro": "filtro", "/ultimas": "ultimas", "/estado": "estado",
}
_ctx = {"img": None, "cid": None}

def teclado_menu():
    def b(texto, cb):
        return {"text": texto, "callback_data": cb}
    return json.dumps({"inline_keyboard": [
        [b("☕ Propina", "m_propina"), b("💬 Contacto", "m_contacto")],
        [b("🔔 Suscribir", "m_suscribir"), b("🔕 Parar", "m_parar")],
        [b("🔥 Últimas", "m_ultimas"), b("📊 Estado", "m_estado")],
        [b("⭐ Umbral", "m_umbral"), b("🔎 Filtro", "m_filtro")],
        [b("❓ Ayuda", "m_ayuda"), b("🔄 Refresh", "m_menu")],
    ]})

def teclado_volver():
    return json.dumps({"inline_keyboard": [[{"text": "📋 Menú", "callback_data": "m_menu"}]]})

def enviar_con_foto(chat, nombre, texto, markup):
    ruta = os.path.join(IMG_DIR, nombre + ".png")
    if not os.path.exists(ruta):
        return None
    mk = markup or teclado_volver()
    try:
        with open(ruta, "rb") as f:
            if len(texto) <= 1000:
                r = requests.post(API + "/sendPhoto", data={"chat_id": chat, "caption": texto, "reply_markup": mk},
                                  files={"photo": f}, timeout=60)
                return r.status_code
            r = requests.post(API + "/sendPhoto", data={"chat_id": chat}, files={"photo": f}, timeout=60)
        requests.post(API + "/sendMessage", data={"chat_id": chat, "text": texto, "reply_markup": mk}, timeout=30)
        return r.status_code
    except Exception as e:
        print("error foto", e)
        return None

def ejecutar(d, cid, texto):
    cmd = texto.strip().split()[0].split("@")[0].lower()
    _ctx["img"] = IMAGENES.get(cmd)
    _ctx["cid"] = str(cid)
    try:
        comando(d, cid, texto)
    finally:
        _ctx["img"] = None

def teclado_propina():'''
cambiar('def teclado_propina():', bloque)

cambiar('''        {"text": "🎁 2500 ⭐", "callback_data": "tip_2500"},
    ]]})''', '''        {"text": "🎁 2500 ⭐", "callback_data": "tip_2500"},
    ], [
        {"text": "📋 Menú", "callback_data": "m_menu"},
    ]]})''')

cambiar('enviar(cid, AYUDA, teclado_propina())', 'enviar(cid, AYUDA, teclado_menu())')

cambiar('    "/propina - ☕ hazte apoyante con una propina\\n"',
        '    "/menu - 📋 abrir el menú de botones\\n"\n    "/propina - ☕ hazte apoyante con una propina\\n"')

cambiar('    elif cmd == "/suscribir":', '''    elif cmd == "/menu":
        enviar(cid, "📋 MENÚ\\nElige una opción 👇", teclado_menu())
    elif cmd == "/suscribir":''')

cambiar('''                enviar_factura(cid, int(cb[4:]))
            continue''', '''                enviar_factura(cid, int(cb[4:]))
            elif cid and cb.startswith("m_"):
                ejecutar(d, cid, "/" + cb[2:])
            continue''')

cambiar('            comando(d, cid, txt)\n', '            ejecutar(d, cid, txt)\n')

open(RUTA_BOT, "w", encoding="utf-8").write(s)
print("Menú instalado en el bot correctamente")
