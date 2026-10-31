
import re, shutil, time, sys, os

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- VIDEO11 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- VIDEO9 ---" not in src:
    print("ABORTO: primero hay que aplicar parche_video9.py"); sys.exit(1)

TAIL = r'''# --- VIDEO11 ---
# Video neon-gaming 4:5 (modo seguro, sin fotos de Amazon). /video estilo neon|vertical|cuadrado
VD11_W, VD11_H, VD11_FPS, VD11_SEG = 720, 810, 20, 8.0

def _vd11_render(titulo, ahora, antes, pct, rating, resenas, hist, resumen, ruta, gato=True):
    from PIL import Image, ImageDraw, ImageChops, ImageFilter
    import math, random
    W, H = VD11_W, VD11_H
    ease = _vd7_ease
    F = _vd7_f
    CY, MG, VD, RJ, BL = (0, 235, 255), (255, 40, 200), (80, 255, 150), (255, 50, 90), (255, 255, 255)
    base0 = Image.new("RGB", (W, H)); dg = ImageDraw.Draw(base0)
    for y in range(H):
        k = y / float(H)
        dg.line((0, y, W, y), fill=(int(5 + 26 * k * k), int(3 + 4 * k), int(20 + 34 * k)))
    scan = Image.new("RGB", (W, H), (255, 255, 255)); sd = ImageDraw.Draw(scan)
    for y in range(0, H, 4):
        sd.line((0, y, W, y), fill=(222, 222, 232))
    rnd = random.Random(11)
    estrellas = [(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(1, 2.6), rnd.uniform(25, 70)) for _ in range(40)]
    fecha = time.strftime("%d/%m/%Y %H:%M")
    minimo = bool(hist) and ahora <= min(hist) * 1.005
    money = lambda v: ("%.2f" % v).replace(".", ",") + " €"
    gancho = "¡PRECIAZO!" if pct >= 60 else ("¡CHOLLO!" if pct >= 35 else "¡BAJÓ DE PRECIO!")
    ahorro = max(0.0, antes - ahora)

    def cuadro(t):
        im = base0.copy(); dr = ImageDraw.Draw(im)
        gl = Image.new("RGB", (W, H), (0, 0, 0)); g = ImageDraw.Draw(gl)
        # estrellas
        for (px, py, r, v) in estrellas:
            yy = (py - v * t) % H
            dr.ellipse((px - r, yy - r, px + r, yy + r), fill=(120, 110, 190))
        # suelo con rejilla en movimiento
        hz = 420
        for k in range(14):
            f = ((k + (t * 0.7) % 1.0) / 14.0) ** 2
            y = hz + (H - hz) * f
            dr.line((0, y, W, y), fill=(int(70 * f + 30), 14, int(110 * f + 40)), width=2)
        for i in range(-12, 13):
            x2 = W / 2 + i * 120
            dr.line((W / 2 + i * 18, hz, x2, H), fill=(52, 12, 90), width=2)
        def N(box, r, col, w=3):
            dr.rounded_rectangle(box, r, outline=col, width=w); g.rounded_rectangle(box, r, outline=col, width=w + 3)
        # HUD de progreso segmentado
        seg = 24
        for i in range(seg):
            x0 = 30 + i * (W - 60) / seg
            on = (i + 1) / seg <= t / VD11_SEG + 0.001
            c = CY if on else (30, 36, 70)
            dr.rectangle((x0, 14, x0 + (W - 60) / seg - 4, 22), fill=c)
            if on:
                g.rectangle((x0, 14, x0 + (W - 60) / seg - 4, 22), fill=c)
        # gancho con glitch
        fg = F(78, True)
        while dr.textlength(gancho, font=fg) > W - 50:
            fg = F(fg.size - 4, True)
        gx = W / 2 - dr.textlength(gancho, font=fg) / 2
        a = ease(t / 0.3)
        gy = 28 - int((1 - a) * 40)
        if t < 0.9:
            j = int(math.sin(t * 90) * 9)
            dr.text((gx - 7 + j, gy), gancho, font=fg, fill=MG); dr.text((gx + 7 - j, gy), gancho, font=fg, fill=CY)
        dr.text((gx, gy), gancho, font=fg, fill=BL)
        g.text((gx, gy), gancho, font=fg, fill=CY if int(t * 6) % 2 == 0 or t > 1 else MG)
        # etiqueta
        N((W / 2 - 150, 114, W / 2 + 150, 142), 14, MG, 2)
        tx = "BAJADA DE PRECIO"; ft = F(20, True)
        dr.text((W / 2 - dr.textlength(tx, font=ft) / 2, 117), tx, font=ft, fill=(255, 150, 230))
        # titulo
        if t > 0.9:
            q = ease((t - 0.9) / 0.5); y = 154
            for l in _vd_envolver(dr, titulo, F(32, True), W - 80, 2):
                dr.text((40 + (1 - q) * -60, y), l, font=F(32, True), fill=BL); y += 39
        if t > 1.5 and rating:
            dr.text((40, 234), "★ %.1f" % rating, font=F(26, True), fill=(255, 205, 70))
            if resenas:
                dr.text((130, 238), "%s opiniones" % format(int(resenas), ",").replace(",", "."), font=F(21), fill=(170, 190, 235))
        # panel de precios
        if t > 1.6:
            q = ease((t - 1.6) / 0.5); oy = int((1 - q) * 60)
            dr.rounded_rectangle((30, 270 + oy, W - 30, 528 + oy), 24, fill=(10, 8, 34)); N((30, 270 + oy, W - 30, 528 + oy), 24, CY, 3)
            dr.text((60, 282 + oy), "ANTES", font=F(21), fill=(150, 170, 215))
            tx = money(antes); fb = F(42, True)
            dr.text((60, 304 + oy), tx, font=fb, fill=(190, 200, 225))
            if t > 2.4:
                s = ease((t - 2.4) / 0.35); x2 = 60 + dr.textlength(tx, font=fb)
                dr.line((50, 348 + oy, 50 + (x2 - 30) * s, 324 + oy), fill=RJ, width=7); g.line((50, 348 + oy, 50 + (x2 - 30) * s, 324 + oy), fill=RJ, width=9)
            dr.text((60, 352 + oy), "AHORA", font=F(21), fill=(150, 170, 215))
            p_ = ease((t - 2.6) / 1.4) if t > 2.6 else 0.0
            v = antes - (antes - ahora) * p_
            fcol = VD if p_ >= 1 else BL
            fp = F(96, True)
            while dr.textlength(money(v), font=fp) > W - 130:
                fp = F(fp.size - 6, True)
            dr.text((55, 370 + oy), money(v), font=fp, fill=fcol)
            if p_ >= 1:
                g.text((55, 370 + oy), money(v), font=fp, fill=VD)
            if t > 3.8 and ahorro > 0:
                q2 = ease((t - 3.8) / 0.4); yy = 480 - int((1 - q2) * 16) + oy
                N((60, yy, 60 + 330, yy + 36), 18, VD, 2)
                dr.text((78, yy + 3), "AHORRAS %s" % money(ahorro), font=F(24, True), fill=VD)
        # insignia
        if t > 0.25:
            m = ease((t - 1.7) / 0.7) if t > 1.7 else 0.0
            cx = 360 + (594 - 360) * m; cy = 460 + (338 - 460) * m
            r = (150 + (58 - 150) * m) * (ease((t - 0.25) / 0.35) if t < 0.6 else 1.0)
            r += math.sin(t * 8) * 4 * (1 - m)
            dr.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(60, 4, 30)); N((cx - r, cy - r, cx + r, cy + r), int(r), RJ, 5)
            ft = F(max(22, int(r * 0.6)), True); tx = "-%d%%" % pct
            dr.text((cx - dr.textlength(tx, font=ft) / 2, cy - ft.size * 0.62), tx, font=ft, fill=BL)
            g.text((cx - dr.textlength(tx, font=ft) / 2, cy - ft.size * 0.62), tx, font=ft, fill=RJ)
        # grafica
        gy0 = 546
        if hist and t > 3.6:
            dr.rounded_rectangle((30, gy0, W - 30, gy0 + 124), 22, fill=(10, 8, 34)); N((30, gy0, W - 30, gy0 + 124), 22, MG, 3)
            dr.text((52, gy0 + 8), "Precio en los últimos 90 días", font=F(19), fill=(170, 190, 235))
            mx, mn = max(hist), min(hist); rng = (mx - mn) or 1.0
            prog = ease((t - 3.6) / 1.6); n = max(2, int(len(hist) * prog))
            gx0, gw, gh = 60, W - 120, 62
            pts = [(gx0 + gw * i / (len(hist) - 1), gy0 + 42 + gh - (v_ - mn) / rng * (gh - 8)) for i, v_ in enumerate(hist)][:n]
            dr.line(pts, fill=CY, width=5, joint="curve"); g.line(pts, fill=CY, width=9, joint="curve")
            ex, ey = pts[-1]; dr.ellipse((ex - 9, ey - 9, ex + 9, ey + 9), fill=VD); g.ellipse((ex - 12, ey - 12, ex + 12, ey + 12), fill=VD)
            if prog >= 1 and minimo:
                tx = "mínimo del período"
                dr.text((W - 52 - dr.textlength(tx, font=F(19, True)), gy0 + 8), tx, font=F(19, True), fill=VD)
            if gato:
                pr = min(1.0, (t - 3.6) / 3.4)
                sp = _vd9_gato(t if pr < 1.0 else 0.0, alto=56)
                im.paste(sp, (int(-110 + 760 * pr), gy0 + 124 - sp.height + 8), sp)
        # resumen
        if resumen and t > 5.4:
            a2 = ease((t - 5.4) / 0.5); y = 680
            for l in _vd_envolver(dr, resumen, F(21), W - 90, 2):
                c = (int(215 * a2 + 8 * (1 - a2)), int(225 * a2 + 8 * (1 - a2)), int(250 * a2 + 34 * (1 - a2)))
                dr.text((45, y + (1 - a2) * 12), l, font=F(21), fill=c); y += 27
        # CTA
        if t > 6.6:
            pu = 1 + 0.035 * math.sin((t - 6.6) * 9)
            w2, h2 = 520 * pu, 44 * pu; cy = 767
            box = (W / 2 - w2 / 2, cy - h2 / 2, W / 2 + w2 / 2, cy + h2 / 2)
            dr.rounded_rectangle(box, 23, fill=(40, 6, 36)); N(box, 23, MG, 3)
            tx = "ENLACE EN EL MENSAJE"; fc = F(26, True)
            dr.text((W / 2 - dr.textlength(tx, font=fc) / 2, cy - 17), tx, font=fc, fill=BL)
            g.text((W / 2 - dr.textlength(tx, font=fc) / 2, cy - 17), tx, font=fc, fill=MG)
        dr.text((40, H - 19), "Precios a fecha %s; pueden cambiar." % fecha, font=F(14), fill=(120, 130, 175))
        dr.text((W - 40 - dr.textlength("Chivato de Ofertas", font=F(14)), H - 19), "Chivato de Ofertas", font=F(14), fill=(120, 130, 175))
        im = ImageChops.add(im, gl.filter(ImageFilter.GaussianBlur(7)))
        return ImageChops.multiply(im, scan)

    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(VD11_FPS),
           "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "23", "-movflags", "+faststart", ruta]
    pr = _vd_sp.Popen(cmd, stdin=_vd_sp.PIPE, stderr=_vd_sp.PIPE)
    try:
        for i in range(int(VD11_SEG * VD11_FPS)):
            pr.stdin.write(cuadro(i / float(VD11_FPS)).tobytes())
        pr.stdin.close()
        err = pr.stderr.read().decode("utf-8", "ignore")
        pr.wait(timeout=180)
    except Exception:
        pr.kill(); raise
    if pr.returncode != 0:
        raise RuntimeError("ffmpeg: " + err[:200])
    return ruta

_vd11_estado = {"neon": True}
_vd8_render_pre11 = _vd8_render

def _vd8_render(titulo, ahora, antes, pct, rating, resenas, hist, resumen, ruta):
    if _vd11_estado["neon"]:
        try:
            return _vd11_render(titulo, ahora, antes, pct, rating, resenas, hist, resumen, ruta, gato=bool(_vd9_estado["on"]))
        except Exception as e:
            print("error video neon, uso el anterior", e, flush=True)
            _vd11_estado["neon"] = False
    return _vd8_render_pre11(titulo, ahora, antes, pct, rating, resenas, hist, resumen, ruta)

_vd_hacer_pre11 = _vd_hacer

def _vd_hacer(d, asin, titulo, ahora, antes, pct, url, destino):
    v = _vd_d(d)
    _vd11_estado["neon"] = (v.get("estilo", "neon") == "neon") and not v.get("foto")
    return _vd_hacer_pre11(d, asin, titulo, ahora, antes, pct, url, destino)

_vd_enviar_pre11 = _vd_enviar

def _vd_enviar(cid, ruta, texto):
    global VD_W, VD_H
    if _vd11_estado["neon"]:
        VD_W, VD_H = VD11_W, VD11_H
    elif "_vd10_estado" not in globals():
        VD_W, VD_H = 720, 720
    return _vd_enviar_pre11(cid, ruta, texto)

_video_cmd_pre11 = video_cmd

def video_cmd(d, cid, args):
    v = _vd_d(d)
    if args and args[0].lower() in ("estilo", "formato"):
        if len(args) > 1 and args[1].lower() in ("neon", "neón", "vertical", "cuadrado"):
            e = args[1].lower().replace("ó", "o")
            v["estilo"] = e
            v["vertical"] = (e == "vertical")
        e = v.get("estilo", "neon")
        enviar(cid, "\U0001f3ac Estilo del video: %s\n\n/video estilo neon (4:5, neon-gaming, el nuevo)\n/video estilo vertical (9:16, para Reels/TikTok)\n/video estilo cuadrado (el de antes)\n(Solo en el modo seguro, sin fotos de Amazon; con /video foto sale el cuadrado.)" % e.upper())
        return
    return _video_cmd_pre11(d, cid, args)

'''

n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
src = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), src, count=1, flags=re.M)
try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)
copia = RUTA + ".bak_video11_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
# la mini app (si esta instalada) tiene que mostrar bien videos de cualquier formato
idx = os.path.join(os.path.dirname(os.path.abspath(RUTA)), "miniapp", "index.html")
try:
    h = open(idx, encoding="utf-8").read()
    for viejo in ("height:calc(100dvh - 400px);min-height:260px;aspect-ratio:9/16;width:auto;margin:0 auto;", "aspect-ratio:1/1;width:100%;"):
        h = h.replace(viejo, "width:100%;")
    h = h.replace(".vbox video{width:100%;height:100%;object-fit:cover;", ".vbox video{width:100%;height:auto;max-height:calc(100dvh - 400px);object-fit:contain;margin:0 auto;")
    h = h.replace(".vbox video{width:100%;height:100%;object-fit:contain;", ".vbox video{width:100%;height:auto;max-height:calc(100dvh - 400px);object-fit:contain;margin:0 auto;")
    open(idx, "w", encoding="utf-8").write(h)
    print("Mini app ajustada para videos de cualquier formato.")
except Exception as e:
    print("(mini app no ajustada:", e, ")")
print("Ahora ejecuta: systemctl restart chivato")
