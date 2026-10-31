import re, shutil, time, sys, os

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- FOTO3 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- FOTO2 ---" not in src:
    print("ABORTO: primero hay que aplicar parche_foto2.py"); sys.exit(1)

TAIL = r'''# --- FOTO3 ---
# Foto cuadrada (1080x1080): Telegram no la recorta en el chat.
FT_W, FT_H = 1080, 1080
_ft_cache.clear()

def _ft_render(titulo, ahora, antes, pct, ruta):
    from PIL import Image, ImageDraw, ImageChops, ImageFilter
    import random
    W, H = 1080, 1080
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
    hz = 800
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
    neon((W / 2 - w1 / 2, 36, W / 2 + w1 / 2, 102), 33, RJ, 4)
    tx(W / 2, 46, s1, f1, BL, RJ)
    # titulo en 1-2 lineas
    tit = _ft_re.sub(r"(?i)\bamazon\b", "", str(titulo or "")); tit = _ft_re.sub(r"\s+", " ", tit).strip()
    fs = 48
    while fs >= 32:
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
        tx(W / 2, 128 + i * (fs + 12), l, fn, BL, CY)
    # tarjeta
    neon((90, 270, 990, 900), 44, CY, 5); rr(d, (94, 274, 986, 896), 42, fill=(10, 8, 34))
    fp = F(26, True); sp = gancho
    wp = d.textlength(sp, font=fp) + 60
    neon((110, 296, 110 + wp, 354), 29, MG, 3); tx(110 + wp / 2, 311, sp, fp, (255, 170, 240), MG)
    cx, cy = 850, 360
    d.ellipse((cx - 88, cy - 88, cx + 88, cy + 88), fill=(60, 6, 30)); neon((cx - 88, cy - 88, cx + 88, cy + 88), 88, RJ, 5)
    tx(cx, cy - 31, "-%d%%" % pct, F(52, True), BL, RJ)
    tx(W / 2, 405, "AHORA", F(30), GR)
    fpr = 160
    sa = money(ahora)
    while d.textlength(sa, font=F(fpr, True)) > 760 and fpr > 80:
        fpr -= 8
    tx(W / 2, 430, sa, F(fpr, True), VD, VD)
    sb = "antes " + money(antes); fb = F(42)
    wb = d.textlength(sb, font=fb)
    tx(W / 2, 630, sb, fb, GR)
    d.line((W / 2 - wb / 2 - 4, 656, W / 2 + wb / 2 + 4, 656), fill=GR, width=3)
    rr(d, (150, 715, 930, 755), 20, fill=(20, 16, 52))
    anc = max(60, int(780 * max(0, min(100, pct)) / 100.0))
    rr(d, (150, 715, 150 + anc, 755), 20, fill=CY); rr(g, (150, 715, 150 + anc, 755), 20, fill=CY)
    tx(W / 2, 772, "Ahorras " + money(max(0.0, antes - ahora)), F(46, True), VD, VD)
    tx(W / 2, 840, time.strftime("Aviso de las %H:%M · %d/%m/%Y"), F(28), GR)
    tx(W / 2, 930, "CHIVATO DE OFERTAS", F(42, True), BL, CY)
    for i, l in enumerate(("Como afiliado de Amazon obtengo ingresos por las compras adscritas.",
                           "Los precios corresponden al momento del aviso y pueden cambiar.")):
        tx(W / 2, 1000 + i * 30, l, F(22), (140, 150, 195))
    im = ImageChops.add(im, gl.filter(ImageFilter.GaussianBlur(10)))
    sc = Image.new("RGB", (W, H), (255, 255, 255)); s = ImageDraw.Draw(sc)
    for yy in range(0, H, 4):
        s.line((0, yy, W, yy), fill=(226, 226, 236))
    im = ImageChops.multiply(im, sc)
    im.save(ruta, "JPEG", quality=90)

'''

n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
src = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), src, count=1, flags=re.M)
try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)
copia = RUTA + ".bak_foto3_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
