import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- VIDEO7 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- VIDEO6 ---" not in src:
    print("ABORTO: primero hay que aplicar parche_video6.py"); sys.exit(1)

TAIL = r'''# --- VIDEO7 ---
VD7_W = VD7_H = 720
VD7_FPS = 20
VD7_SEG = 7.0
_vd7_fuentes = {}

def _vd7_f(tam, neg=False):
    k = (tam, neg)
    if k not in _vd7_fuentes:
        _vd7_fuentes[k] = _vd_fuente(tam, neg)
    return _vd7_fuentes[k]

def _vd7_fotos(p):
    """Hasta 3 fotos del producto (la primera con todos los respaldos)."""
    fotos = []
    try:
        fotos.append(_vd_imagen(p))
    except Exception:
        raise
    csv = (p or {}).get("imagesCSV") or ""
    for nombre in [x.strip() for x in csv.split(",") if x.strip()][1:3]:
        try:
            r = requests.get("https://m.media-amazon.com/images/I/%s" % nombre, timeout=15, headers=_VD_UA)
            if r.status_code == 200 and len(r.content) > 2000:
                fotos.append(_vd_abrir(r.content))
        except Exception as e:
            print("error video foto extra", e, flush=True)
    return fotos

def _vd7_hist(p, ahora):
    """Serie de ~16 precios de los ultimos 90 dias (en euros) o None."""
    try:
        csv = (p or {}).get("csv") or []
        serie = None
        for i in (0, 1, 18):
            if len(csv) > i and csv[i] and len(csv[i]) >= 4:
                serie = csv[i]; break
        if not serie:
            return None
        ahora_k = int(time.time() / 60) - 21564000
        pares = [(serie[j], serie[j + 1]) for j in range(0, len(serie) - 1, 2)]
        pts = []
        for n in range(16):
            t = ahora_k - 90 * 1440 + int(90 * 1440 * n / 15.0)
            v = None
            for tt, pp in pares:
                if tt <= t:
                    v = pp
                else:
                    break
            if v is not None and v > 0:
                pts.append(v / 100.0)
        if len(pts) < 5:
            return None
        pts[-1] = float(ahora)
        return pts
    except Exception as e:
        print("error video historial", e, flush=True)
        return None

def _vd7_ease(x):
    return 1 - (1 - max(0.0, min(1.0, x))) ** 3

def _vd7_render(fotos, titulo, ahora, antes, pct, rating, resenas, hist, resumen, ruta):
    from PIL import Image, ImageDraw, ImageFilter
    W, H = VD7_W, VD7_H
    ease = _vd7_ease
    bg = fotos[0].resize((W, W)).filter(ImageFilter.GaussianBlur(40))
    fondo = Image.blend(Image.new("RGB", (W, H), (14, 32, 82)), bg.point(lambda v: int(v * 0.2)), 0.25)
    minimo = bool(hist) and ahora <= min(hist) * 1.005
    ncar = len(fotos)

    def cuadro(t):
        im = fondo.copy(); dr = ImageDraw.Draw(im)
        a = ease(t / 0.6); y = 26
        for l in _vd_envolver(dr, titulo, _vd7_f(28, True), W - 80, 2):
            dr.text((40 + (1 - a) * -40, y), l, font=_vd7_f(28, True), fill=(255, 255, 255)); y += 36
        idx = min(ncar - 1, int(t // 2.2)); z = 1.0 + 0.06 * ((t % 2.2) / 2.2)
        s_ = int(250 * z)
        ph = fotos[idx].copy(); ph.thumbnail((s_, s_))
        x0, y0 = 40, 112
        dr.rounded_rectangle((x0, y0, x0 + 290, y0 + 290), 26, fill=(255, 255, 255))
        im.paste(ph, (x0 + 145 - ph.width // 2, y0 + 145 - ph.height // 2))
        if ncar > 1:
            for i in range(ncar):
                cx = x0 + 145 - 15 * (ncar - 1) + i * 30
                dr.ellipse((cx - 6, y0 + 302, cx + 6, y0 + 314), fill=(255, 143, 31) if i == idx else (120, 140, 180))
        if t > 0.8 and rating:
            dr.text((x0, y0 + 322), "★ %.1f" % rating, font=_vd7_f(26, True), fill=(255, 184, 77))
            if resenas:
                dr.text((x0 + 82, y0 + 326), "%s opiniones" % format(int(resenas), ",").replace(",", "."), font=_vd7_f(21), fill=(190, 205, 235))
        px = 372
        if t > 1.0:
            p_ = ease((t - 1.3) / 1.6); v = antes - (antes - ahora) * p_
            dr.text((px, 160), "ANTES", font=_vd7_f(20), fill=(170, 190, 215))
            tx = "%.2f €" % antes
            dr.text((px, 182), tx, font=_vd7_f(36, True), fill=(200, 210, 225))
            dr.line((px - 4, 203, px + 6 + dr.textlength(tx, font=_vd7_f(36, True)), 203), fill=(255, 90, 90), width=5)
            dr.text((px, 248), "AHORA", font=_vd7_f(20), fill=(170, 190, 215))
            dr.text((px, 270), "%.2f €" % v, font=_vd7_f(74, True), fill=(120, 235, 150) if p_ >= 1 else (255, 255, 255))
        if t > 3.0:
            pa = ease((t - 3.0) / 0.5); r = int(52 * (0.4 + 0.6 * pa)); bx, by = W - 78, 160
            dr.ellipse((bx - r, by - r, bx + r, by + r), fill=(230, 40, 50))
            if pa > .5:
                tx = "-%d%%" % pct
                dr.text((bx - dr.textlength(tx, font=_vd7_f(30, True)) / 2, by - 19), tx, font=_vd7_f(30, True), fill=(255, 255, 255))
        if hist and t > 3.4:
            gx0, gy0, gw, gh = 40, 502, W - 80, 78
            dr.rounded_rectangle((gx0 - 10, gy0 - 36, gx0 + gw + 10, gy0 + gh + 12), 14, fill=(18, 36, 84), outline=(70, 95, 150), width=2)
            dr.text((gx0, gy0 - 30), "Precio en los últimos 90 días", font=_vd7_f(18), fill=(190, 205, 235))
            mx, mn = max(hist), min(hist)
            rng = (mx - mn) or 1.0
            prog = ease((t - 3.4) / 1.6); n = max(2, int(len(hist) * prog))
            pts = [(gx0 + gw * i / (len(hist) - 1), gy0 + gh - (v - mn) / rng * (gh - 10) - 4) for i, v in enumerate(hist)][:n]
            dr.line(pts, fill=(255, 143, 31), width=5, joint="curve")
            ex, ey = pts[-1]
            dr.ellipse((ex - 8, ey - 8, ex + 8, ey + 8), fill=(120, 235, 150))
            if prog >= 1 and minimo:
                dr.text((gx0 + gw - 205, gy0 - 30), "mínimo del período", font=_vd7_f(18, True), fill=(120, 235, 150))
        if resumen and t > 4.6:
            a = ease((t - 4.6) / 0.5); y = 612 if hist else 520
            for l in _vd_envolver(dr, resumen, _vd7_f(21), W - 80, 3 if hist else 5):
                dr.text((40, y + (1 - a) * 16), l, font=_vd7_f(21), fill=(int(220 * a + 14 * (1 - a)), int(230 * a + 28 * (1 - a)), int(250 * a + 82 * (1 - a)))); y += 27
        dr.text((W - 175, H - 24), "Chivato de Ofertas", font=_vd7_f(15), fill=(140, 165, 200))
        return im

    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(VD7_FPS),
           "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "24", "-movflags", "+faststart", ruta]
    pr = _vd_sp.Popen(cmd, stdin=_vd_sp.PIPE, stderr=_vd_sp.PIPE)
    try:
        for i in range(int(VD7_SEG * VD7_FPS)):
            pr.stdin.write(cuadro(i / float(VD7_FPS)).tobytes())
        pr.stdin.close()
        err = pr.stderr.read().decode("utf-8", "ignore")
        pr.wait(timeout=120)
    except Exception:
        pr.kill(); raise
    if pr.returncode != 0:
        raise RuntimeError("ffmpeg: " + err[:200])
    return ruta

def _vd_hacer(d, asin, titulo, ahora, antes, pct, url, destino):
    """Video cuadrado con fotos, valoracion, historial real y texto del producto."""
    ruta = None
    try:
        p = _vd_keepa(d, asin)
        fotos = _vd7_fotos(p)
        st = (p or {}).get("stats") or {}
        cur = st.get("current") or []
        def g(i):
            v = cur[i] if len(cur) > i and isinstance(cur[i], (int, float)) else -1
            return v if v and v > 0 else None
        rating = (g(16) or 0) / 10.0 or None
        resenas = g(17)
        hist = _vd7_hist(p, ahora)
        resumen = _vd_resumen(p)
        ruta = _vd_os.path.join(_vd_tmp.gettempdir(), "oferta_%s.mp4" % asin)
        try:
            _vd7_render(fotos, titulo, ahora, antes, pct, rating, resenas, hist, resumen, ruta)
        except Exception as e:
            print("error video7, uso el modelo anterior", e, flush=True)
            _vd_render(fotos[0], titulo, ahora, antes, pct, ruta)
        cap = "\U0001f525 %s\n\n" % titulo[:110]
        if resumen:
            cap += "%s\n\n" % resumen
        cap += "\U0001f4b6 %.2f € (antes %.2f €) · -%d%%\n\n%s" % (ahora, antes, pct, url or "")
        if not _vd_enviar(destino, ruta, cap):
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

'''
n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
src = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), src, count=1, flags=re.M)
try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)
copia = RUTA + ".bak_video7_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
