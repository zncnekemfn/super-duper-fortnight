import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- PLANTILLAS1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("def _cn_frame(", "def _cn_fondo(", "def _cn_pill(", "def _cn_mono(", "def _cn_serb(", "def _cn_sans(", "def _cn_eur(",
          "def hook_anuncios_pago(", "def _vd_token(", "_vd_th", "_ft_tmp", "_ft_os", "FOTOENLACE2"):
    if n not in src:
        print("ABORTO: no encuentro", n, "(aplica antes los parches de /foto y el estilo caramelo)"); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)

BLOQUE = r'''
# --- PLANTILLAS1 ---
# /tarjeta ENLACE [ahora] [antes]  -> tarjeta de oferta SIN foto de producto (el -NN% gigante), mismo estilo que /foto
# /tophoy                          -> tarjeta con las 3 mayores ofertas de las ultimas 24 h
# /pregunta Texto | op1 | op2 ...  -> tarjeta de pregunta para pedir interaccion (2 a 4 opciones)
_PL_SIN = {"t": 0.0}

_cn_frame_pre_pl = _cn_frame

def _cn_frame(dat, t=0.0, total=6.0, still=True):
    try:
        if still and _PL_SIN["t"] and _cn_time.time() - _PL_SIN["t"] < 45:
            _PL_SIN["t"] = 0.0
            dat = dict(dat, foto=None)
    except Exception:
        pass
    return _cn_frame_pre_pl(dat, t, total, still)

def _pl_base(pilltxt):
    from PIL import Image, ImageDraw
    W = H = 1080; WIN = (36, 36, W - 36, H - 36); PH = 640
    base = Image.new("RGBA", (W, H), (6, 5, 4, 255))
    ww, wh = WIN[2] - WIN[0], WIN[3] - WIN[1]
    win = Image.new("RGBA", (ww, wh), (13, 10, 9, 255))
    win.paste(_cn_fondo(ww, PH, None).crop((0, 0, ww, PH)), (0, 0))
    wd = Image.new("RGBA", win.size, (0, 0, 0, 0)); g = ImageDraw.Draw(wd)
    for y in range(PH - 250, PH + 1):
        g.line((0, y, ww, y), fill=(13, 10, 9, int(255 * ((y - (PH - 250)) / 250.0) ** 1.5)))
    win.alpha_composite(wd)
    _cn_pill(win, (26, 24), pilltxt, _cn_mono(22), (240, 242, 248), (255, 255, 255, 120), (14, 10, 8, 190))
    d = ImageDraw.Draw(win)
    d.text((ww - 30, 38), _cn_time.strftime("AVISO %H:%M · %d/%m/%Y"), font=_cn_mono(21), fill=(215, 220, 232), anchor="rm")
    d.line((26, 94, ww - 26, 94), fill=(80, 66, 58), width=1)
    return base, win, d, ww, wh, WIN

def _pl_cerrar(base, win, WIN, afiliado):
    from PIL import Image, ImageDraw
    ww, wh = win.size
    d = ImageDraw.Draw(win)
    if afiliado:
        d.text((36, wh - 34), "Como afiliado de Amazon obtengo ingresos por las compras adscritas.", font=_cn_sans(17, False), fill=(150, 158, 176), anchor="lm")
    d.text((36, wh - 14), "CHIVATO DE OFERTAS · Los precios corresponden al momento del aviso y pueden cambiar.", font=_cn_sans(15, False), fill=(110, 118, 136), anchor="lm")
    m = Image.new("L", win.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, ww - 1, wh - 1), 44, fill=255)
    base.paste(win, (WIN[0], WIN[1]), m)
    ImageDraw.Draw(base).rounded_rectangle(WIN, 44, outline=(62, 50, 44), width=2)
    return base.convert("RGB")

def _pl_corta(d, txt, fn, ancho):
    txt = str(txt)
    if d.textlength(txt, font=fn) <= ancho:
        return txt
    while len(txt) > 3 and d.textlength(txt + "…", font=fn) > ancho:
        txt = txt[:-1]
    return txt.rstrip() + "…"

def _pl_top_img(ofs):
    from PIL import ImageDraw
    base, win, d, ww, wh, WIN = _pl_base("TOP CHOLLOS · HOY")
    for i, o in enumerate(ofs[:3]):
        y = 130 + i * 205
        d.rounded_rectangle((30, y, ww - 30, y + 190), radius=30, fill=(20, 15, 12), outline=(80, 66, 58), width=3)
        d.ellipse((56, y + 35, 176, y + 155), fill=(14, 10, 8), outline=(236, 170, 98), width=4)
        d.text((116, y + 95), "-%d%%" % o["pct"], font=_cn_sans(34), fill=(236, 170, 98), anchor="mm")
        d.text((210, y + 58), _pl_corta(d, o["t"], _cn_sans(31), ww - 30 - 210 - 30), font=_cn_sans(31), fill=(255, 255, 255), anchor="lm")
        pf = _cn_serb(66)
        d.text((210, y + 132), _cn_eur(o["ahora"]), font=pf, fill=(255, 255, 255), anchor="lm")
        ax = 210 + d.textlength(_cn_eur(o["ahora"]), font=pf) + 24
        sb = "antes " + _cn_eur(o["antes"]); fb = _cn_sans(27, False)
        d.text((ax, y + 138), sb, font=fb, fill=(160, 168, 185), anchor="lm")
        d.line((ax, y + 138, ax + d.textlength(sb, font=fb), y + 138), fill=(160, 168, 185), width=3)
    d.text((ww // 2, wh - 110), "Elige tu descuento mínimo en @ChivatoOfertas_bot", font=_cn_sans(30), fill=(236, 170, 98), anchor="mm")
    return _pl_cerrar(base, win, WIN, True)

def _pl_preg_img(preg, ops):
    base, win, d, ww, wh, WIN = _pl_base("PREGUNTA DEL DÍA")
    fn = _cn_serb(70); lin = []; cur = ""
    for p in str(preg).split():
        pr = (cur + " " + p).strip()
        if d.textlength(pr, font=fn) <= ww - 110: cur = pr
        else: lin.append(cur); cur = p
    lin.append(cur)
    lin = lin[:4]
    y = 190
    for i, l in enumerate(lin):
        d.text((ww // 2, y + i * 86), l, font=fn, fill=(255, 255, 255), anchor="mm", stroke_width=5, stroke_fill=(13, 10, 9))
    yo = max(y + len(lin) * 86 + 40, 470)
    fo = _cn_sans(38)
    for i, t in enumerate(ops[:4]):
        x = 54 + (i % 2) * 460; yy = yo + (i // 2) * 125
        d.rounded_rectangle((x, yy, x + 440, yy + 100), radius=50, fill=(42, 29, 16), outline=(236, 170, 98), width=3)
        d.text((x + 220, yy + 50), _pl_corta(d, t, fo, 390), font=fo, fill=(243, 197, 138), anchor="mm")
    d.text((ww // 2, wh - 70), "Chollos al momento en @ChivatoOfertas_bot", font=_cn_sans(30), fill=(236, 170, 98), anchor="mm")
    return _pl_cerrar(base, win, WIN, False)

def _pl_enviar(cid, img, cap):
    ruta = _ft_os.path.join(_ft_tmp.gettempdir(), "plantilla_%d.jpg" % int(_cn_time.time() * 1000))
    try:
        img.save(ruta, "JPEG", quality=92)
        with open(ruta, "rb") as fh:
            r = requests.post("https://api.telegram.org/bot%s/sendPhoto" % _vd_token(),
                              data={"chat_id": cid, "caption": cap[:1000]}, files={"photo": fh}, timeout=60)
        if r.status_code != 200:
            enviar(cid, "La imagen se ha generado pero Telegram no la ha aceptado.")
    finally:
        try: _ft_os.remove(ruta)
        except Exception: pass

def _pl_top_hacer(d, cid):
    try:
        lim = _cn_time.time() - 86400
        of = [o for o in _mi_d(d)["of"] if o.get("ts", 0) >= lim and o.get("antes", 0) > o.get("ahora", 0)]
        of = sorted(of, key=lambda o: -o["pct"])[:3]
        if not of:
            enviar(cid, "Todavia no hay ofertas guardadas en las ultimas 24 h."); return
        ofs = [dict(o, t=re.sub(r"\s+-\s*[\d.,]+\s*EUR\s*$", "", str(o["t"])).strip()) for o in of]
        img = _pl_top_img(ofs)
        cap = "\U0001f525 TOP CHOLLOS DE HOY\n\n"
        for i, o in enumerate(ofs):
            cap += "%d. %s\n\U0001f4a5 -%d%% → %.2f € (antes %.2f €)\n\U0001f449 %s\n\n" % (i + 1, o["t"][:60], o["pct"], o["ahora"], o["antes"], o.get("url", ""))
        cap += "(Como afiliado de Amazon obtengo ingresos por las compras adscritas.)"
        _pl_enviar(cid, img, cap)
    except Exception as e:
        print("error /tophoy", e, flush=True)
        try: enviar(cid, "Error generando el top: %s" % str(e)[:150])
        except Exception: pass

def _pl_preg_hacer(cid, texto):
    try:
        partes = [p.strip() for p in texto.split("|") if p.strip()]
        preg, ops = partes[0], partes[1:5]
        img = _pl_preg_img(preg, ops)
        cap = "\U0001f4ac %s\n\nResponde en los comentarios \U0001f447\n\U0001f449 @ChivatoOfertas_bot" % preg
        _pl_enviar(cid, img, cap)
    except Exception as e:
        print("error /pregunta", e, flush=True)
        try: enviar(cid, "Error generando la pregunta: %s" % str(e)[:150])
        except Exception: pass

_pl_pre_hook = hook_anuncios_pago

def hook_anuncios_pago(d, u):
    try:
        m = u.get("message")
        t = ((m.get("text") or "") if m else "").strip()
        if m and t and str(m["chat"]["id"]) == str(ADMIN):
            prim = t.split()[0]; cmd = prim.lower().split("@")[0]; cid = m["chat"]["id"]
            if cmd == "/tarjeta":
                if len(t.split()) == 1:
                    enviar(cid, "Tarjeta de oferta SIN foto de producto (descuento gigante):\n/tarjeta ENLACE\n/tarjeta ENLACE 29.29 55.00 (ahora y antes)")
                    return True
                _PL_SIN["t"] = _cn_time.time()
                m["text"] = "/foto" + t[len(prim):]
                return _pl_pre_hook(d, u)
            if cmd == "/tophoy":
                enviar(cid, "Preparando el TOP de hoy…")
                _vd_th.Thread(target=_pl_top_hacer, args=(d, cid), daemon=True).start()
                return True
            if cmd == "/pregunta":
                texto = t[len(prim):].strip()
                if not texto:
                    enviar(cid, "Tarjeta de pregunta para pedir interaccion:\n/pregunta ¿Desde que descuento compras sin pensar? | 30% | 50% | 70% | Solo -80%")
                    return True
                enviar(cid, "Preparando la pregunta…")
                _vd_th.Thread(target=_pl_preg_hacer, args=(cid, texto), daemon=True).start()
                return True
    except Exception as e:
        print("error plantillas", e, flush=True)
    return _pl_pre_hook(d, u)
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_plantillas_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Plantillas instaladas: /tarjeta  /tophoy  /pregunta. Copia:", cp)
print("Reinicia: sudo systemctl restart chivato")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
