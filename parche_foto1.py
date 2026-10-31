import re, shutil, time, sys, os

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- FOTO1 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- VIDEO11 ---" not in src:
    print("ABORTO: primero hay que aplicar parche_video11 (y el 12/13)"); sys.exit(1)

TAIL = r'''# --- FOTO1 ---
# Avisos de oferta como foto neon-gaming (sin fotos de Amazon). /foto on|off
import threading as _ft_th, re as _ft_re, os as _ft_os, tempfile as _ft_tmp, json as _ft_json

_ft_loc = _ft_th.local()
_ft_cache = {}
_ft_lock = _ft_th.Lock()
FT_W, FT_H = 1080, 1350

def _ft_activo(d):
    try:
        return bool(d.setdefault("foto_aviso", {"on": True}).get("on", True))
    except Exception:
        return False

def _ft_precios(texto, pct):
    t = str(texto or "")
    nums = [float(x.replace(",", ".")) for x in _ft_re.findall(r"(\d+[.,]\d\d) ?(?:EUR|€)", t)]
    if not nums:
        return None
    ahora = nums[0]
    antes = nums[1] if len(nums) > 1 and nums[1] > nums[0] else None
    if antes is None and pct and 0 < pct < 95:
        antes = round(ahora / (1 - pct / 100.0), 2)
    return (ahora, antes) if antes else None

def _ft_render(titulo, ahora, antes, pct, ruta):
    from PIL import Image, ImageDraw, ImageChops, ImageFilter
    import random
    W, H = FT_W, FT_H
    F = _vd7_f
    CY, MG, VD, RJ, BL = (0, 235, 255), (255, 40, 200), (80, 255, 150), (255, 50, 90), (255, 255, 255)
    GR = (150, 162, 210)
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    for y in range(H):
        k = y / float(H)
        d.line((0, y, W, y), fill=(int(6 + 26 * k * k), int(3 + 4 * k), int(20 + 34 * k)))
    gl = Image.new("RGB", (W, H), (0, 0, 0)); g = ImageDraw.Draw(gl)
    rnd = random.Random(3)
    for _ in range(70):
        x, y, r = rnd.uniform(0, W), rnd.uniform(0, H * 0.6), rnd.uniform(1, 3)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(120, 110, 200))
    hz = 960
    for k in range(1, 15):
        f = (k / 14.0) ** 2; y = hz + (H - hz) * f
        d.line((0, y, W, y), fill=(int(70 * f + 30), 12, int(110 * f + 40)), width=2)
    for i in range(-14, 15):
        d.line((W / 2 + i * 30, hz, W / 2 + i * 230, H), fill=(52, 10, 90), width=2)

    def rr(dd, b, r, **kw):
        x0, y0, x1, y1 = b
        r = max(0, min(r, (int(min(x1 - x0, y1 - y0)) - 3) // 2))
        dd.rounded_rectangle(b, r, **kw)

    def neon(b, r, c, w=4):
        rr(d, b, r, outline=c, width=w); rr(g, b, r, outline=c, width=w + 4)

    def tx(x, y, s, f, fill, gc=None):
        tw = d.textlength(s, font=f)
        d.text((x - tw / 2, y), s, font=f, fill=fill)
        if gc:
            g.text((x - tw / 2, y), s, font=f, fill=gc)

    money = lambda v: ("%.2f" % v).replace(".", ",") + " €"
    gancho = "PRECIAZO" if pct >= 60 else ("CHOLLO" if pct >= 35 else "BAJADA DE PRECIO")
    # cabecera
    f1 = F(38, True); s1 = "OFERTA DETECTADA"
    w1 = d.textlength(s1, font=f1) + 90
    neon((W / 2 - w1 / 2, 60, W / 2 + w1 / 2, 130), 35, RJ, 4)
    tx(W / 2, 72, s1, f1, BL, RJ)
    # titulo en 1-2 lineas
    tit = _ft_re.sub(r"(?i)\bamazon\b", "", str(titulo or "")); tit = _ft_re.sub(r"\s+", " ", tit).strip()
    fs = 54
    while fs >= 34:
        fn = F(fs, True); pal = tit.split(" "); lin = []; cur = ""
        for p in pal:
            pr = (cur + " " + p).strip()
            if d.textlength(pr, font=fn) <= W - 140:
                cur = pr
            else:
                lin.append(cur); cur = p
        lin.append(cur)
        if len(lin) <= 2:
            break
        fs -= 4
    if len(lin) > 2:
        lin = lin[:2]
        while d.textlength(lin[1] + "…", font=fn) > W - 140 and len(lin[1]) > 3:
            lin[1] = lin[1][:-1]
        lin[1] = lin[1].rstrip() + "…"
    for i, l in enumerate(lin):
        tx(W / 2, 175 + i * (fs + 14), l, fn, BL, CY)
    # tarjeta
    neon((90, 350, 990, 1060), 44, CY, 5); rr(d, (94, 354, 986, 1056), 42, fill=(10, 8, 34))
    fp = F(26, True); sp = gancho
    wp = d.textlength(sp, font=fp) + 60
    neon((110, 380, 110 + wp, 440), 30, MG, 3); tx(110 + wp / 2, 396, sp, fp, (255, 170, 240), MG)
    cx, cy = 850, 440
    d.ellipse((cx - 98, cy - 98, cx + 98, cy + 98), fill=(60, 6, 30)); neon((cx - 98, cy - 98, cx + 98, cy + 98), 98, RJ, 5)
    tx(cx, cy - 34, "-%d%%" % pct, F(56, True), BL, RJ)
    tx(W / 2, 500, "AHORA", F(32), GR)
    fpr = 180
    sa = money(ahora)
    while d.textlength(sa, font=F(fpr, True)) > 760 and fpr > 80:
        fpr -= 8
    tx(W / 2, 540, sa, F(fpr, True), VD, VD)
    sb = "antes " + money(antes); fb = F(42)
    wb = d.textlength(sb, font=fb)
    tx(W / 2, 760, sb, fb, GR)
    d.line((W / 2 - wb / 2 - 4, 786, W / 2 + wb / 2 + 4, 786), fill=GR, width=3)
    rr(d, (150, 850, 930, 892), 21, fill=(20, 16, 52))
    anc = max(60, int(780 * max(0, min(100, pct)) / 100.0))
    rr(d, (150, 850, 150 + anc, 892), 21, fill=CY); rr(g, (150, 850, 150 + anc, 892), 21, fill=CY)
    tx(W / 2, 925, "Ahorras " + money(max(0.0, antes - ahora)), F(46, True), VD, VD)
    tx(W / 2, 1000, time.strftime("Aviso de las %H:%M · %d/%m/%Y"), F(28), GR)
    tx(W / 2, 1115, "CHIVATO DE OFERTAS", F(44, True), BL, CY)
    for i, l in enumerate(("Como afiliado de Amazon obtengo ingresos por las compras adscritas.",
                           "Los precios corresponden al momento del aviso y pueden cambiar.")):
        tx(W / 2, 1230 + i * 34, l, F(24), (140, 150, 195))
    im = ImageChops.add(im, gl.filter(ImageFilter.GaussianBlur(10)))
    sc = Image.new("RGB", (W, H), (255, 255, 255)); s = ImageDraw.Draw(sc)
    for yy in range(0, H, 4):
        s.line((0, yy, W, yy), fill=(226, 226, 236))
    im = ImageChops.multiply(im, sc)
    im.save(ruta, "JPEG", quality=90)

def _ft_foto(item):
    pct = int(item.get("d") or 0)
    asin = ""
    mm = _ft_re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", str(item.get("u") or ""))
    if mm:
        asin = mm.group(1)
    pre = _ft_precios(item.get("t"), pct)
    if not asin or not pre or pct <= 0:
        return None
    clave = "%s_%.2f_%d" % (asin, pre[0], pct)
    with _ft_lock:
        ruta = _ft_cache.get(clave)
        if ruta and _ft_os.path.exists(ruta):
            return ruta
        tit = _ft_re.sub(r" - \d+[.,]\d\d.*", "", str(item.get("t") or ""), flags=_ft_re.S).strip() or asin
        ruta = _ft_os.path.join(_ft_tmp.gettempdir(), "aviso_%s.jpg" % clave)
        _ft_render(tit, pre[0], pre[1], pct, ruta)
        if len(_ft_cache) > 40:
            for k in list(_ft_cache)[:20]:
                try:
                    _ft_os.remove(_ft_cache.pop(k))
                except Exception:
                    _ft_cache.pop(k, None)
        _ft_cache[clave] = ruta
        return ruta

_enviar_pre_ft = enviar

def enviar(c, t, m=None, *a, **k):
    item = getattr(_ft_loc, "item", None)
    if item is not None and not a and not k and isinstance(t, str) and len(t) <= 1000:
        try:
            ruta = _ft_foto(item)
            tok = _vd_token()
            if ruta and tok:
                datos = {"chat_id": c, "caption": t}
                if m:
                    datos["reply_markup"] = m if isinstance(m, str) else _ft_json.dumps(m)
                if _ft_re.search(r"</?(b|i|a|code|u)[ >]", t):
                    datos["parse_mode"] = "HTML"
                with open(ruta, "rb") as fh:
                    r = requests.post("https://api.telegram.org/bot%s/sendPhoto" % tok, data=datos, files={"photo": fh}, timeout=60)
                if r.status_code == 200:
                    return r
                print("foto aviso rechazada", r.status_code, flush=True)
        except Exception as e:
            print("error foto aviso", e, flush=True)
    return _enviar_pre_ft(c, t, m, *a, **k)

_enviar_aviso_pre_ft = enviar_aviso

def enviar_aviso(d, cid, item):
    if _ft_activo(d):
        _ft_loc.item = item
    try:
        return _enviar_aviso_pre_ft(d, cid, item)
    finally:
        _ft_loc.item = None

_comando_pre_ft = comando

def comando(d, cid, texto):
    p = str(texto or "").split()
    if p and p[0].split("@")[0].lower() == "/foto" and str(cid) == str(ADMIN):
        f = d.setdefault("foto_aviso", {"on": True})
        if len(p) > 1 and p[1].lower() in ("on", "off"):
            f["on"] = (p[1].lower() == "on")
        enviar(cid, "\U0001f5bc AVISOS EN FOTO NEON: %s\n\n/foto on · /foto off" % ("ACTIVADOS" if f.get("on", True) else "APAGADOS (texto de siempre)"))
        return
    return _comando_pre_ft(d, cid, texto)

'''

n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
src = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), src, count=1, flags=re.M)
try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)
copia = RUTA + ".bak_foto1_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
