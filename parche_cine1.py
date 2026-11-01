import re, sys, time, shutil
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- CINE1 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("def _ft_render(", "def _ft_foto(", "def _ft_item_de_texto(", "def _vd_f(", "def _vd_render(", "def _vd_hacer(", "KEEPA_KEY"):
    if n not in src:
        print("ABORTO: no encuentro %s" % n); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: anclaje final (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''# --- CINE1 ---
import io as _cn_io, threading as _cn_th, os as _cn_os, time as _cn_time
_cn_loc = _cn_th.local()
_CN_IMGID = {}
_cn_fotos = {}
_CN_DIRS = ("/usr/share/fonts/truetype/dejavu/", "/usr/share/fonts/dejavu/", "/usr/share/fonts/TTF/")

def _cn_f(nombre, size, bold=False):
    from PIL import ImageFont
    for dd in _CN_DIRS:
        try:
            return ImageFont.truetype(dd + nombre, size)
        except Exception:
            pass
    return _vd_f(size, bold)

def _cn_sans(s, b=True): return _cn_f("DejaVuSans-Bold.ttf" if b else "DejaVuSans.ttf", s, b)
def _cn_mono(s): return _cn_f("DejaVuSansMono.ttf", s)
def _cn_serb(s): return _cn_f("DejaVuSerif-Bold.ttf", s, True)
def _cn_seri(s): return _cn_f("DejaVuSerif-Italic.ttf", s)

def _cn_eur(v): return ("%.2f" % float(v)).replace(".", ",") + " €"

def _cn_ease(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

def _cn_foto(asin):
    """Foto del producto (PIL RGB) o None. Usa el id guardado o pide el producto a Keepa."""
    from PIL import Image
    if not asin:
        return None
    if asin in _cn_fotos:
        return _cn_fotos[asin]
    img = None
    try:
        idimg = _CN_IMGID.get(asin)
        if not idimg and KEEPA_KEY:
            r = requests.get("https://api.keepa.com/product", params={"key": KEEPA_KEY, "domain": 9, "asin": asin}, timeout=20)
            if r.status_code == 200:
                pr = (r.json().get("products") or [None])[0] or {}
                idimg = str(pr.get("imagesCSV") or "").split(",")[0]
        if idimg:
            r2 = requests.get("https://m.media-amazon.com/images/I/" + idimg, timeout=20)
            if r2.status_code == 200:
                img = Image.open(_cn_io.BytesIO(r2.content)).convert("RGB")
    except Exception as e:
        print("error foto producto", e, flush=True)
    if len(_cn_fotos) > 60:
        _cn_fotos.clear()
    _cn_fotos[asin] = img
    return img

def _cn_pill(img, xy, txt, font, fg, line, fill, pad=24, alpha=1.0):
    from PIL import Image, ImageDraw
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    w = d.textlength(txt, font=font); h = font.size + 22; x, y = xy
    d.rounded_rectangle((x, y, x + w + 2 * pad, y + h), radius=int(h // 2), fill=fill, outline=line, width=2)
    d.text((x + pad, y + h / 2), txt, font=font, fill=fg, anchor="lm")
    if alpha < 1:
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * alpha)))
    img.alpha_composite(lay)
    return x + w + 2 * pad

def _cn_fondo(ww, ph_h, foto, zoom=1.0):
    """Zona de foto: plato de estudio con luz y el producto encima (o -NN% gigante si no hay foto)."""
    from PIL import Image, ImageDraw, ImageChops, ImageFilter
    base = Image.radial_gradient("L").resize((ww, ph_h + 80))
    luz = ImageChops.invert(base)
    fondo = Image.merge("RGB", [luz.point(lambda v, a=a, b=b: int(a + b * (v / 255.0) ** 1.3)) for a, b in ((34, 150), (36, 150), (44, 150))])
    sh = Image.new("L", fondo.size, 0); sd = ImageDraw.Draw(sh)
    cx = int(ww * 0.52)
    sd.polygon([(cx - 70, 0), (cx + 70, 0), (cx + 330, ph_h), (cx - 330, ph_h)], fill=70)
    sh = sh.filter(ImageFilter.GaussianBlur(40))
    fondo = ImageChops.add(fondo, Image.merge("RGB", [sh.point(lambda v: int(v * 0.5))] * 3))
    if foto is not None:
        bw, bh = int(ww * 0.9 * zoom), int(ph_h * 0.8 * zoom)
        f = foto.copy(); f.thumbnail((bw, bh), Image.LANCZOS)
        px, py = (ww - f.width) // 2, 110 + (int(ph_h * 0.8) - f.height) // 2
        reg = fondo.crop((px, py, px + f.width, py + f.height))
        fondo.paste(ImageChops.multiply(reg, f), (px, py))
    return fondo

def _cn_frame(dat, t=0.0, total=6.0, still=True):
    from PIL import Image, ImageDraw, ImageChops, ImageFilter
    W = H = 1080
    WIN = (36, 36, W - 36, H - 36); PH = 640
    base = Image.new("RGBA", (W, H), (5, 6, 10, 255))
    ww, wh = WIN[2] - WIN[0], WIN[3] - WIN[1]
    win = Image.new("RGBA", (ww, wh), (9, 11, 17, 255))
    z = 1.0 if still else 1.0 + 0.06 * (t / total)
    ph = _cn_fondo(ww, PH, dat.get("foto"), z).crop((0, 0, ww, PH))
    if dat.get("foto") is None:
        gh = Image.new("RGBA", ph.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(gh)
        gd.text((ww // 2, PH // 2 + 20), "-%d%%" % dat["pct"], font=_cn_serb(300), fill=(255, 255, 255, 40), anchor="mm")
        ph = Image.alpha_composite(ph.convert("RGBA"), gh).convert("RGB")
    u = 1.0 if still else _cn_ease((t - 0.2) / 1.6)
    if u < 1:
        bl = ph.filter(ImageFilter.GaussianBlur(26 * (1 - u)))
        ph = Image.blend(bl, Image.new("RGB", ph.size, (70, 62, 52)), 0.55 * (1 - u))
        ph = ImageChops.multiply(ph, Image.new("RGB", ph.size, (int(120 + 135 * u),) * 3))
    win.paste(ph, (0, 0))
    wd = Image.new("RGBA", win.size, (0, 0, 0, 0)); g = ImageDraw.Draw(wd)
    for y in range(PH - 250, PH + 1):
        g.line((0, y, ww, y), fill=(9, 11, 17, int(255 * ((y - (PH - 250)) / 250.0) ** 1.5)))
    win.alpha_composite(wd)
    A = lambda dt, dur=0.5: 1.0 if still else _cn_ease((t - dt) / dur)
    _cn_pill(win, (26, 24), "OFERTA DETECTADA", _cn_mono(22), (240, 242, 248), (255, 255, 255, 120), (8, 10, 16, 190), alpha=A(0.0))
    d = ImageDraw.Draw(win)
    if still:
        tc = dat.get("hora", "")
    else:
        tc = "REEL 01 · 00:%02d:%02d" % (int(t), int((t * 100) % 100))
    d.text((ww - 30, 38), tc, font=_cn_mono(21), fill=(30, 32, 40) if False else (215, 220, 232), anchor="rm")
    d.line((26, 94, ww - 26, 94), fill=(70, 74, 86), width=1)
    navx = ww - 30
    for l in ("VALORACIONES", "HISTÓRICO", "AHORRO", "PRECIO"):
        d.text((navx, 118), l, font=_cn_mono(17), fill=(205, 210, 224), anchor="rm")
        navx -= d.textlength(l, font=_cn_mono(17)) + 30
    a = A(1.4)
    if a > 0:
        lay = Image.new("RGBA", win.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        ld.ellipse((ww - 190, 160, ww - 40, 310), fill=(8, 10, 16, 200), outline=(120, 255, 214, 230), width=3)
        ld.text((ww - 115, 235), "-%d%%" % dat["pct"], font=_cn_sans(44), fill=(130, 255, 220), anchor="mm")
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a))); win.alpha_composite(lay)
    a = A(1.7); yo = int(18 * (1 - a)); x = 36
    if dat.get("mn"):
        x = _cn_pill(win, (x, PH + 4 + yo), dat["mn"], _cn_sans(26, False), (150, 255, 225), (120, 255, 214, 160), (20, 64, 62, 140), alpha=a) + 12
    if dat.get("rat"):
        txt = "★ " + dat["rat"] + ((" · " + dat["nv"] + " valoraciones") if dat.get("nv") else "")
        _cn_pill(win, (x, PH + 4 + yo), txt, _cn_sans(26, False), (235, 236, 244), (255, 255, 255, 90), (14, 18, 28, 190), alpha=a)
    a2 = A(2.0)
    lay = Image.new("RGBA", win.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    tit = _ft_re.sub(r"(?i)\bamazon\b", "", str(dat.get("titulo") or "")); tit = _ft_re.sub(r"\s+", " ", tit).strip()
    fs = 50
    while fs >= 34:
        fn = _cn_sans(fs); pal = tit.split(" "); lin = []; cur = ""
        for p in pal:
            pr = (cur + " " + p).strip()
            if ld.textlength(pr, font=fn) <= ww - 72: cur = pr
            else: lin.append(cur); cur = p
        lin.append(cur)
        if len(lin) <= 2: break
        fs -= 4
    if len(lin) > 2:
        lin = lin[:2]
        while ld.textlength(lin[1] + "…", font=fn) > ww - 72 and len(lin[1]) > 3: lin[1] = lin[1][:-1]
        lin[1] = lin[1].rstrip() + "…"
    y0 = PH + 70 + (0 if len(lin) == 2 else int((fs + 8) / 2))
    for i, l in enumerate(lin):
        ld.text((36, y0 + i * (fs + 10)), l, font=fn, fill=(255, 255, 255), anchor="lm")
    lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a2))); win.alpha_composite(lay)
    k = 1.0 if still else _cn_ease((t - 2.3) / 1.3)
    val = dat["antes"] + (dat["ahora"] - dat["antes"]) * k
    pa = A(2.2, 0.4)
    lay = Image.new("RGBA", win.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    pf = _cn_serb(104); yp = PH + 262
    ld.text((36, yp), _cn_eur(val), font=pf, fill=(255, 255, 255), anchor="lm")
    ax = 36 + ld.textlength(_cn_eur(dat["ahora"]), font=pf) + 26
    sb = "antes " + _cn_eur(dat["antes"]); fb = _cn_sans(30, False)
    ld.text((ax, yp - 26), sb, font=fb, fill=(160, 168, 185), anchor="lm")
    ld.line((ax, yp - 26, ax + ld.textlength(sb, font=fb), yp - 26), fill=(160, 168, 185), width=3)
    lay.putalpha(lay.getchannel("A").point(lambda v: int(v * pa))); win.alpha_composite(lay)
    ahorro = max(0.0, dat["antes"] - dat["ahora"])
    _cn_pill(win, (ax, yp + 2), "Ahorras " + _cn_eur(ahorro), _cn_sans(28), (130, 255, 220), (120, 255, 214, 170), (20, 70, 60, 140), alpha=A(3.6))
    d = ImageDraw.Draw(win)
    d.text((36, wh - 34), "Como afiliado de Amazon obtengo ingresos por las compras adscritas.", font=_cn_sans(17, False), fill=(150, 158, 176), anchor="lm")
    d.text((36, wh - 14), "CHIVATO DE OFERTAS · Los precios corresponden al momento del aviso y pueden cambiar.", font=_cn_sans(15, False), fill=(110, 118, 136), anchor="lm")
    m = Image.new("L", win.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, ww - 1, wh - 1), 44, fill=255)
    base.paste(win, (WIN[0], WIN[1]), m)
    ImageDraw.Draw(base).rounded_rectangle(WIN, 44, outline=(46, 50, 62), width=2)
    return base.convert("RGB")

_ft_item_de_texto_pre_cn = _ft_item_de_texto

def _ft_item_de_texto(t):
    it = _ft_item_de_texto_pre_cn(t)
    if it:
        try:
            m = _ft_re.search(r"⭐\s*([\d.,]+)\s*·\s*([\d.]+)\s*valoraci", t)
            if m:
                it["rat"] = m.group(1); it["nv"] = m.group(2)
            if "Mínimo histórico" in t:
                it["mn"] = "Mínimo histórico"
            elif "Mínimo de los últimos 90" in t:
                it["mn"] = "Mínimo 90 días"
        except Exception:
            pass
    return it

_ft_foto_pre_cn = _ft_foto

def _ft_foto(item):
    _cn_loc.item = item
    try:
        return _ft_foto_pre_cn(item)
    finally:
        _cn_loc.item = None

_ft_render_pre_cn = _ft_render

def _ft_render(titulo, ahora, antes, pct, ruta):
    try:
        it = getattr(_cn_loc, "item", None) or {}
        mm = _ft_re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", str(it.get("u") or ""))
        dat = {"titulo": titulo, "ahora": float(ahora), "antes": float(antes), "pct": int(pct),
               "foto": _cn_foto(mm.group(1) if mm else None),
               "mn": it.get("mn"), "rat": it.get("rat"), "nv": it.get("nv"),
               "hora": _cn_time.strftime("AVISO %H:%M · %d/%m/%Y")}
        _cn_frame(dat, 0.0, 6.0, True).save(ruta, "JPEG", quality=92)
        return
    except Exception as e:
        print("error cine", e, flush=True)
    return _ft_render_pre_cn(titulo, ahora, antes, pct, ruta)

# ---- video de los enlaces (mismo estilo) ----
import subprocess as _cn_sp

try:
    _vn_valoracion_pre_cn = _vn_valoracion
    _cn_ratc = {}
    def _vn_valoracion(asin):
        if asin in _cn_ratc:
            return _cn_ratc[asin]
        v = _vn_valoracion_pre_cn(asin)
        if len(_cn_ratc) > 80:
            _cn_ratc.clear()
        _cn_ratc[asin] = v
        return v
except NameError:
    pass

_vd_hacer_pre_cn = _vd_hacer

def _vd_hacer(d, asin, titulo, ahora, antes, pct, url, destino):
    _cn_loc.asin = asin
    try:
        return _vd_hacer_pre_cn(d, asin, titulo, ahora, antes, pct, url, destino)
    finally:
        _cn_loc.asin = None

_vd_render_pre_cn = _vd_render

def _vd_render(imagen, titulo, ahora, antes, pct, ruta):
    try:
        foto = None
        if imagen is not None:
            try:
                foto = imagen.convert("RGB")
            except Exception:
                from PIL import Image
                foto = Image.open(_cn_io.BytesIO(imagen)).convert("RGB")
        dat = {"titulo": titulo, "ahora": float(ahora), "antes": float(antes), "pct": int(pct), "foto": foto}
        try:
            mr = _ft_re.search(r"([\d.,]+)\s*·\s*([\d.]+)\s*valoraci", _vn_valoracion(getattr(_cn_loc, "asin", None)) or "")
            if mr:
                dat["rat"] = mr.group(1); dat["nv"] = mr.group(2)
        except Exception:
            pass
        total, fps = 6.0, 30
        tmp = ruta + ".tmp.mp4"
        p = _cn_sp.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1080",
                          "-r", str(fps), "-i", "-", "-vf", "scale=%d:%d" % (VD_W, VD_H), "-c:v", "libx264",
                          "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-f", "mp4", tmp],
                         stdin=_cn_sp.PIPE)
        for i in range(int(total * fps)):
            p.stdin.write(_cn_frame(dat, i / float(fps), total, False).tobytes())
        p.stdin.close()
        if p.wait() != 0:
            raise RuntimeError("ffmpeg fallo")
        _cn_os.replace(tmp, ruta)
        return
    except Exception as e:
        print("error video cine", e, flush=True)
    return _vd_render_pre_cn(imagen, titulo, ahora, antes, pct, ruta)

'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
# guardar el id de la foto cuando el bot ya consulta el producto (ahorra un token de Keepa)
marca = "        # --- VALORACIONES ---"
if nuevo.count(marca) == 1:
    inj = ("        try:\n"
           "            _ids = str(p.get('imagesCSV') or '').split(',')[0]\n"
           "            if _ids: _CN_IMGID[asin] = _ids\n"
           "        except Exception:\n"
           "            pass\n")
    nuevo = nuevo.replace(marca, inj + marca)
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_cine_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Estilo cine en las fotos de los avisos. Copia:", cp)
print("Ahora ejecuta: systemctl restart chivato")
print("Deshacer: cp", cp, RUTA, "&& systemctl restart chivato")
