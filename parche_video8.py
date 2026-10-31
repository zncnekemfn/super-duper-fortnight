import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- VIDEO8 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- VIDEO7 ---" not in src:
    print("ABORTO: primero hay que aplicar parche_video7.py"); sys.exit(1)

TAIL = r'''# --- VIDEO8 ---
# Modo seguro: video sin foto de Amazon (por defecto). /video foto on lo cambia.
_VD8_MARCAS = ("amazon", "kindle", "echo", "fire tv", "fire hd", "alexa", "ring ", "blink", "eero", "prime video")
_vd_hacer_v7 = _vd_hacer
_video_cmd_v5 = video_cmd

def _vd8_limpiar(titulo):
    t = _vd_re.sub(r"(?i)\bamazon\b", "", str(titulo or ""))
    return _vd_re.sub(r"\s+", " ", t).strip(" -,")

def _vd8_render(titulo, ahora, antes, pct, rating, resenas, hist, resumen, ruta):
    from PIL import Image, ImageDraw
    W, H = VD7_W, VD7_H
    ease = _vd7_ease
    fondo = Image.new("RGB", (W, H))
    dg = ImageDraw.Draw(fondo)
    for y in range(H):
        dg.line((0, y, W, y), fill=(int(14 + 10 * y / H), int(32 + 20 * y / H), int(82 + 30 * y / H)))
    minimo = bool(hist) and ahora <= min(hist) * 1.005
    fecha = time.strftime("%d/%m/%Y %H:%M")

    def cuadro(t):
        im = fondo.copy(); dr = ImageDraw.Draw(im)
        a = ease(t / 0.6); y = 28
        for l in _vd_envolver(dr, titulo, _vd7_f(30, True), W - 80, 2):
            dr.text((40 + (1 - a) * -40, y), l, font=_vd7_f(30, True), fill=(255, 255, 255)); y += 38
        if t > 0.6 and rating:
            dr.text((40, 120), "★ %.1f" % rating, font=_vd7_f(28, True), fill=(255, 184, 77))
            if resenas:
                dr.text((140, 124), "%s opiniones" % format(int(resenas), ",").replace(",", "."), font=_vd7_f(22), fill=(190, 205, 235))
        if t > 0.9:
            p_ = ease((t - 1.1) / 1.6); v = antes - (antes - ahora) * p_
            dr.text((40, 175), "ANTES", font=_vd7_f(22), fill=(170, 190, 215))
            tx = "%.2f €" % antes
            dr.text((40, 200), tx, font=_vd7_f(40, True), fill=(200, 210, 225))
            dr.line((36, 224, 48 + dr.textlength(tx, font=_vd7_f(40, True)), 224), fill=(255, 90, 90), width=5)
            dr.text((40, 262), "AHORA", font=_vd7_f(22), fill=(170, 190, 215))
            dr.text((40, 286), "%.2f €" % v, font=_vd7_f(86, True), fill=(120, 235, 150) if p_ >= 1 else (255, 255, 255))
        if t > 2.8:
            pa = ease((t - 2.8) / 0.5); r = int(100 * (0.4 + 0.6 * pa)); bx, by = W - 130, 250
            dr.ellipse((bx - r, by - r, bx + r, by + r), fill=(230, 40, 50))
            if pa > .5:
                tx = "-%d%%" % pct
                dr.text((bx - dr.textlength(tx, font=_vd7_f(60, True)) / 2, by - 40), tx, font=_vd7_f(60, True), fill=(255, 255, 255))
                tx2 = "DESCUENTO"
                dr.text((bx - dr.textlength(tx2, font=_vd7_f(20, True)) / 2, by + 30), tx2, font=_vd7_f(20, True), fill=(255, 220, 220))
        if hist and t > 3.4:
            gx0, gy0, gw, gh = 40, 440, W - 80, 100
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
            a = ease((t - 4.6) / 0.5); y = 575 if hist else 450
            for l in _vd_envolver(dr, resumen, _vd7_f(21), W - 80, 3 if hist else 5):
                dr.text((40, y + (1 - a) * 16), l, font=_vd7_f(21), fill=(int(220 * a + 14 * (1 - a)), int(230 * a + 28 * (1 - a)), int(250 * a + 82 * (1 - a)))); y += 27
        dr.text((40, H - 30), "Precios a fecha %s; pueden cambiar." % fecha, font=_vd7_f(15), fill=(140, 165, 200))
        dr.text((W - 175, H - 30), "Chivato de Ofertas", font=_vd7_f(15), fill=(140, 165, 200))
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
    """Con fotos activadas usa el video completo; si no, el modo seguro sin fotos de Amazon."""
    if _vd_d(d).get("foto"):
        return _vd_hacer_v7(d, asin, titulo, ahora, antes, pct, url, destino)
    ruta = None
    try:
        p = _vd_keepa(d, asin)
        st = (p or {}).get("stats") or {}
        cur = st.get("current") or []
        def g(i):
            v = cur[i] if len(cur) > i and isinstance(cur[i], (int, float)) else -1
            return v if v and v > 0 else None
        rating = (g(16) or 0) / 10.0 or None
        resenas = g(17)
        marca = (str((p or {}).get("brand") or "") + " " + str(titulo)).lower()
        aviso = any(m in marca for m in _VD8_MARCAS)
        tit = _vd8_limpiar(titulo) or asin
        resumen = _vd8_limpiar(_vd_resumen(p))
        ruta = _vd_os.path.join(_vd_tmp.gettempdir(), "oferta_%s.mp4" % asin)
        _vd8_render(tit, ahora, antes, pct, rating, resenas, _vd7_hist(p, ahora), resumen, ruta)
        cap = "\U0001f525 %s\n\n" % tit[:110]
        if resumen:
            cap += "%s\n\n" % resumen
        cap += "\U0001f4b6 %.2f € (antes %.2f €) · -%d%%\n\n%s" % (ahora, antes, pct, url or "")
        if aviso:
            cap += "\n\n⚠️ Producto de marca Amazon: revisa antes de publicar."
        if not _vd_enviar(destino, ruta, cap):
            enviar(destino, "El video se ha generado pero Telegram no lo ha aceptado.")
    except Exception as e:
        print("error video8", e, flush=True)
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
    if args and args[0].lower() == "foto":
        if len(args) > 1 and args[1].lower() in ("on", "off"):
            v["foto"] = (args[1].lower() == "on")
        enviar(cid, "\U0001f5bc️ Fotos de Amazon en los videos: %s\n\n"
                    "OFF = modo seguro, sin fotos (recomendado para publicar en X)\nON = con fotos del producto (solo para uso privado)\n\n"
                    "/video foto on · /video foto off" % ("ACTIVADAS" if v.get("foto") else "DESACTIVADAS (modo seguro)"))
        return
    _video_cmd_v5(d, cid, args)
    if not args or args[0].lower() in ("on", "off"):
        enviar(cid, "Fotos en los videos: %s (/video foto on|off)" % ("ACTIVADAS" if v.get("foto") else "desactivadas, modo seguro"))

'''
n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
src = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), src, count=1, flags=re.M)
try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)
copia = RUTA + ".bak_video8_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
