import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- VIDEO ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "_enviar_aviso_prev = enviar_aviso" not in src:
    print("ABORTO: falta parche_A.py"); sys.exit(1)

def unico(patron, fn, nombre):
    global src
    n = len(re.findall(patron, src, re.M))
    if n != 1:
        print("ABORTO: ancla '%s' encontrada %d veces" % (nombre, n)); sys.exit(1)
    src = re.sub(patron, fn, src, count=1, flags=re.M)

TAIL = r'''# --- VIDEO ---
import os as _vd_os, io as _vd_io, subprocess as _vd_sp, threading as _vd_th, tempfile as _vd_tmp
import re as _vd_re

VD_W = VD_H = 720
VD_FPS = 20
VD_SEG = 5.5

def _vd_d(d):
    v = d.setdefault("video", {})
    v.setdefault("on", False)
    v.setdefault("umbral", 60)
    v.setdefault("max", 5)
    v.setdefault("dia", "")
    v.setdefault("hoy", 0)
    v.setdefault("hechos", {})
    return v

def _vd_token():
    return globals().get("TG_TOKEN") or globals().get("TOKEN") or globals().get("BOT_TOKEN")

def _vd_fuente(tam, negrita=False):
    from PIL import ImageFont
    for ruta in ("/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if negrita else ""),
                 "/usr/share/fonts/dejavu/DejaVuSans%s.ttf" % ("-Bold" if negrita else ""),
                 "/usr/share/fonts/truetype/liberation/LiberationSans-%s.ttf" % ("Bold" if negrita else "Regular")):
        if _vd_os.path.exists(ruta):
            return ImageFont.truetype(ruta, tam)
    try:
        return ImageFont.load_default(tam)
    except TypeError:
        return ImageFont.load_default()

def _vd_asin(url):
    m = _vd_re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", str(url or ""))
    return m.group(1) if m else ""

def _vd_precios(texto, pct):
    """(ahora, antes) en euros; None si no se pueden leer."""
    t = str(texto or "")
    nums = [float(x.replace(",", ".")) for x in _vd_re.findall(r"(\d+[.,]\d\d) ?(?:EUR|€)", t)]
    if not nums:
        return None
    ahora = nums[0]
    antes = nums[1] if len(nums) > 1 and nums[1] > nums[0] else None
    if antes is None and pct and 0 < pct < 95:
        antes = round(ahora / (1 - pct / 100.0), 2)
    return (ahora, antes) if antes else None

def _vd_keepa(d, asin):
    k = globals().get("KEEPA_KEY") or globals().get("KEEPA")
    if not k:
        return None
    try:
        r = requests.get("https://api.keepa.com/product", params={"key": k, "domain": 9, "asin": asin, "stats": 90, "history": 0}, timeout=20)
        if r.status_code != 200:
            return None
        j = r.json()
        if j.get("tokensLeft") is not None:
            d["a_tok"] = j.get("tokensLeft")
        return (j.get("products") or [None])[0]
    except Exception as e:
        print("error video keepa", e, flush=True)
        return None

def _vd_imagen(p):
    from PIL import Image
    csv = (p or {}).get("imagesCSV") or ""
    nombre = csv.split(",")[0].strip()
    if not nombre:
        return None
    for url in ("https://m.media-amazon.com/images/I/%s" % nombre, "https://images-na.ssl-images-amazon.com/images/I/%s" % nombre):
        try:
            r = requests.get(url, timeout=20)
            if r.status_code == 200 and len(r.content) > 500:
                im = Image.open(_vd_io.BytesIO(r.content))
                if im.mode in ("RGBA", "LA", "P"):
                    im = im.convert("RGBA")
                    fondo = Image.new("RGB", im.size, "white"); fondo.paste(im, mask=im.split()[-1]); im = fondo
                return im.convert("RGB")
        except Exception as e:
            print("error video imagen", e, flush=True)
    return None

def _vd_envolver(draw, texto, fuente, ancho, lineas=2):
    pal, res, cur = str(texto).split(), [], ""
    for w in pal:
        prueba = (cur + " " + w).strip()
        if draw.textlength(prueba, font=fuente) <= ancho:
            cur = prueba
        else:
            res.append(cur); cur = w
    res.append(cur)
    if len(res) > lineas:
        res = res[:lineas]; res[-1] = res[-1].rstrip(" ,.-") + "..."
    return res

def _vd_facil(x):
    return 1 - (1 - max(0.0, min(1.0, x))) ** 3

def _vd_cuadro(base, prod, titulo, ahora, antes, pct, t):
    from PIL import Image, ImageDraw
    W, H = VD_W, VD_H
    im = base.copy()
    dr = ImageDraw.Draw(im)
    f_tit, f_pre, f_gra, f_peq, f_bad = _vd_fuente(30, True), _vd_fuente(40, True), _vd_fuente(86, True), _vd_fuente(26), _vd_fuente(54, True)
    # titulo
    a = _vd_facil(t / 0.6)
    ly = 34
    for linea in _vd_envolver(dr, titulo, f_tit, W - 80):
        dr.text((40 + int((1 - a) * -30), ly), linea, font=f_tit, fill=(255, 255, 255))
        ly += 38
    # tarjeta con producto
    ta = _vd_facil((t - 0.2) / 0.8)
    lado = 290
    esc = 0.85 + 0.15 * ta
    pr = prod.copy(); pr.thumbnail((int(lado * esc), int(lado * esc)))
    cx, cy = W // 2, 268
    tarj = (cx - lado // 2 - 12, cy - lado // 2 - 12, cx + lado // 2 + 12, cy + lado // 2 + 12)
    dr.rounded_rectangle(tarj, radius=28, fill=(255, 255, 255))
    if ta > 0.02:
        im.paste(pr, (cx - pr.width // 2, cy - pr.height // 2))
    # precios
    y0 = 442
    if t >= 1.0:
        prog = _vd_facil((t - 1.4) / 1.8)
        valor = antes - (antes - ahora) * prog
        txt_antes = "%.2f €" % antes
        dr.text((40, y0), "ANTES", font=f_peq, fill=(170, 190, 215))
        dr.text((40, y0 + 30), txt_antes, font=f_pre, fill=(200, 210, 225))
        ancho = dr.textlength(txt_antes, font=f_pre)
        dr.line((36, y0 + 56, 44 + ancho, y0 + 56), fill=(255, 90, 90), width=5)
        dr.text((40, y0 + 100), "AHORA", font=f_peq, fill=(170, 190, 215))
        col = (255, 255, 255) if prog < 1 else (120, 235, 150)
        dr.text((40, y0 + 125), "%.2f €" % valor, font=f_gra, fill=col)
    # insignia
    if t >= 3.3:
        pa = _vd_facil((t - 3.3) / 0.5)
        r = int(92 * (0.4 + 0.6 * pa) + (6 * (1 - abs(1 - 2 * min(1, (t - 3.3) / 0.5)))))
        bx, by = W - 130, 585
        dr.ellipse((bx - r, by - r, bx + r, by + r), fill=(230, 40, 50))
        if pa > 0.5:
            tx = "-%d%%" % pct
            ww = dr.textlength(tx, font=f_bad)
            dr.text((bx - ww / 2, by - 33), tx, font=f_bad, fill=(255, 255, 255))
    dr.text((40, H - 46), "Chivato de Ofertas", font=f_peq, fill=(140, 165, 200))
    return im

def _vd_render(imagen, titulo, ahora, antes, pct, ruta):
    from PIL import Image
    W, H = VD_W, VD_H
    base = Image.new("RGB", (W, H))
    px = base.load()
    for y in range(H):
        c = (int(18 + 14 * y / H), int(40 + 30 * y / H), int(84 + 40 * y / H))
        for x in range(W):
            px[x, y] = c
    n = int(VD_SEG * VD_FPS)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(VD_FPS),
           "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "24", "-movflags", "+faststart", ruta]
    pr = _vd_sp.Popen(cmd, stdin=_vd_sp.PIPE, stderr=_vd_sp.PIPE)
    try:
        for i in range(n):
            pr.stdin.write(_vd_cuadro(base, imagen, titulo, ahora, antes, pct, i / float(VD_FPS)).tobytes())
        pr.stdin.close()
        err = pr.stderr.read().decode("utf-8", "ignore")
        pr.wait(timeout=120)
    except Exception:
        pr.kill(); raise
    if pr.returncode != 0:
        raise RuntimeError("ffmpeg: " + err[:200])
    return ruta

def _vd_faltan():
    f = []
    try:
        import PIL  # noqa
    except Exception:
        f.append("python3-pil")
    if not _vd_sp.run(["which", "ffmpeg"], capture_output=True).stdout.strip():
        f.append("ffmpeg")
    return f

def _vd_enviar(cid, ruta, texto):
    tok = _vd_token()
    if not tok:
        raise RuntimeError("no encuentro el token del bot")
    with open(ruta, "rb") as fh:
        r = requests.post("https://api.telegram.org/bot%s/sendVideo" % tok,
                          data={"chat_id": cid, "caption": texto[:1000], "supports_streaming": "true", "width": VD_W, "height": VD_H},
                          files={"video": fh}, timeout=120)
    return r.status_code == 200

def _vd_hacer(d, asin, titulo, ahora, antes, pct, url, destino):
    """Genera y envia el video. Ejecutar en hilo."""
    ruta = None
    try:
        p = _vd_keepa(d, asin)
        img = _vd_imagen(p)
        if img is None:
            enviar(destino, "No he podido bajar la foto de %s; sin video." % asin)
            return
        ruta = _vd_os.path.join(_vd_tmp.gettempdir(), "oferta_%s.mp4" % asin)
        _vd_render(img, titulo, ahora, antes, pct, ruta)
        cap = "\U0001f525 %s\n\n\U0001f4b6 %.2f € (antes %.2f €) · -%d%%\n\n%s" % (titulo[:150], ahora, antes, pct, url or "")
        ok = _vd_enviar(destino, ruta, cap)
        if not ok:
            enviar(destino, "El video se ha generado pero Telegram no lo ha aceptado.")
    except Exception as e:
        print("error video", e, flush=True)
        try:
            enviar(destino, "Error generando el video: %s" % str(e)[:150])
        except Exception:
            pass
    finally:
        try:
            if ruta and _vd_os.path.exists(ruta):
                _vd_os.remove(ruta)
        except Exception:
            pass

def video_cmd(d, cid, args):
    v = _vd_d(d)
    a = args[0] if args else ""
    if a.lower() in ("on", "off"):
        v["on"] = (a.lower() == "on")
    elif a.lower() == "umbral" and len(args) > 1 and args[1].isdigit():
        v["umbral"] = max(30, min(95, int(args[1])))
    elif a.lower() == "max" and len(args) > 1 and args[1].isdigit():
        v["max"] = max(1, min(30, int(args[1])))
    elif _vd_re.fullmatch(r"[A-Z0-9]{10}", a.upper() or ""):
        f = _vd_faltan()
        if f:
            enviar(cid, "Falta instalar: " + " ".join(f) + "\nEjecuta: apt install -y " + " ".join(f)); return
        asin = a.upper()
        p = _vd_keepa(d, asin)
        if not p:
            enviar(cid, "Keepa no ha devuelto ese producto."); return
        st = p.get("stats") or {}
        cur, av = st.get("current") or [], st.get("avg90") or []
        def g(l, i):
            return l[i] if len(l) > i and isinstance(l[i], (int, float)) and l[i] > 0 else None
        ahora = g(cur, 0) or g(cur, 1)
        antes = max([x for x in (g(av, 0), g(av, 1)) if x] or [0])
        if not ahora or not antes or antes <= ahora:
            enviar(cid, "No hay un precio anterior mayor para calcular el descuento."); return
        pct = int(round(100.0 * (antes - ahora) / antes))
        enviar(cid, "Preparando el video de %s (-%d%%)..." % (asin, pct))
        _vd_th.Thread(target=_vd_hacer, args=(d, asin, p.get("title") or asin, ahora / 100.0, antes / 100.0, pct, "https://www.amazon.es/dp/" + asin, cid), daemon=True).start()
        return
    f = _vd_faltan()
    enviar(cid, "\U0001f3ac VIDEO DE OFERTAS\n\nAutomatico: %s\nDescuento minimo: %d%%\nMaximo al dia: %d (hoy %d)\nSe envian solo a ti, listos para publicar.\n%s\n\n"
                "/video on · /video off\n/video umbral 70\n/video max 5\n/video ASIN (video de un producto concreto)" % (
                "ACTIVADO" if v["on"] else "APAGADO", v["umbral"], v["max"], v["hoy"],
                ("FALTA INSTALAR: apt install -y " + " ".join(f)) if f else "Requisitos: OK"))

_enviar_aviso_pre_vd = enviar_aviso

def enviar_aviso(d, cid, item):
    try:
        v = _vd_d(d)
        if v["on"] and not item.get("_vd"):
            item["_vd"] = True
            q = item.get("_q")
            if not (q and not q[0]):
                hoy = time.strftime("%Y-%m-%d")
                if v["dia"] != hoy:
                    v["dia"], v["hoy"] = hoy, 0
                asin = _vd_asin(item.get("u"))
                pct = int(item.get("d") or 0)
                pre = _vd_precios(item.get("t"), pct)
                if (asin and pre and pct >= v["umbral"] and v["hoy"] < v["max"] and asin not in v["hechos"] and not _vd_faltan()):
                    v["hoy"] += 1
                    v["hechos"][asin] = time.time()
                    for k in [k for k, t0 in v["hechos"].items() if time.time() - t0 > 7 * 86400]:
                        v["hechos"].pop(k, None)
                    tit = _vd_re.sub(r" - \d+[.,]\d\d.*", "", str(item.get("t") or ""), flags=_vd_re.S).strip() or asin
                    _vd_th.Thread(target=_vd_hacer, args=(d, asin, tit, pre[0], pre[1], pct, item.get("u"), ADMIN), daemon=True).start()
    except Exception as e:
        print("error video aviso", e, flush=True)
    return _enviar_aviso_pre_vd(d, cid, item)

'''

unico(r'^    elif cmd in \("/propina", "/premium"\):\n',
      lambda m: '    elif cmd == "/video" and cid == ADMIN:\n        video_cmd(d, cid, args)\n' + m.group(0), "propina")
unico(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), "main")
try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)
copia = RUTA + ".bak_video_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: apt install -y ffmpeg python3-pil   (si aun no estan)")
print("Y despues: systemctl restart chivato")
