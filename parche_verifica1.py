import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- VERIFICA1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("# --- PLANTILLAS1 ---", "def _pl_base(", "def _pl_cerrar(", "def _pl_corta(", "def _pl_enviar(", "def hook_anuncios_pago(", "KEEPA_KEY", "_vd_th", "def _cn_eur("):
    if n not in src:
        print("ABORTO: no encuentro", n, "(aplica antes parche_plantillas1)"); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)

BLOQUE = r'''
# --- VERIFICA1 ---
# /verifica ENLACE  (para todos los usuarios): historial de 90 dias de un producto de Amazon.es y veredicto:
# oferta real / minimo de 90 dias / precio normal / mas caro de lo habitual / posible falso descuento.
_VF_ULT = {}

def _vf_asin(texto):
    m = re.search(r"(?:/dp/|/gp/product/|/gp/aw/d/|/product/)([A-Z0-9]{10})", texto)
    if m:
        return m.group(1)
    m = re.search(r"https?://(?:amzn\.to|amzn\.eu|a\.co)/\S+", texto)
    if m:
        try:
            r = requests.get(m.group(0).rstrip(").,"), timeout=15, allow_redirects=True,
                             headers={"User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"})
            m2 = re.search(r"(?:/dp/|/gp/product/|/gp/aw/d/)([A-Z0-9]{10})", r.url)
            if m2:
                return m2.group(1)
        except Exception as e:
            print("error /verifica enlace corto", str(e)[:80], flush=True)
    m = re.search(r"\b(B0[A-Z0-9]{8})\b", texto)
    return m.group(1) if m else None

def _vf_serie(csv, ahora):
    # csv de Keepa: [t, precio, t, precio...] t en minutos Keepa, precio en centimos (-1 = sin dato/stock)
    pts = []
    for i in range(0, len(csv) - 1, 2):
        t = (csv[i] + 21564000) * 60
        p = csv[i + 1]
        pts.append((t, p / 100.0 if p is not None and p >= 0 else None))
    dias = []
    for k in range(90):
        ts = ahora - (89 - k) * 86400
        v = None; vis = False
        for t, p in pts:
            if t <= ts:
                v = p; vis = True
            else:
                break
        dias.append(v if vis else None)
    return dias

def _vf_mediana(v):
    v = sorted(v)
    return v[len(v) // 2] if v else None

def _vf_analizar(dias):
    vals = [x for x in dias if x is not None]
    if len(vals) < 14 or dias[-1] is None:
        return None
    ahora = dias[-1]
    antiguos = [x for x in dias[:60] if x is not None]
    base = _vf_mediana(antiguos) if len(antiguos) >= 20 else _vf_mediana(vals)
    mn, mx = min(vals), max(vals)
    media = sum(vals) / len(vals)
    pico = max([x for x in dias[-21:] if x is not None] or [ahora])
    if pico >= base * 1.15 and base * 0.92 <= ahora <= base * 1.05:
        v = ("falso", "POSIBLE FALSO DESCUENTO", "Subió un %d%% en las últimas 3 semanas y ahora vuelve a su precio de siempre." % round((pico / base - 1) * 100))
    elif ahora <= base * 0.92:
        v = ("real", "OFERTA REAL", "Está un %d%% por debajo de su precio habitual%s." % (round((1 - ahora / base) * 100), " y es su mínimo de 90 días" if ahora <= mn * 1.02 else ""))
    elif len(vals) >= 30 and ahora <= mn * 1.02 and mx >= mn * 1.08:
        v = ("minimo", "MÍNIMO DE 90 DÍAS", "No ha estado más barato en los últimos 90 días.")
    elif ahora >= base * 1.05:
        v = ("caro", "MÁS CARO DE LO HABITUAL", "Ahora cuesta un %d%% más que su precio habitual." % round((ahora / base - 1) * 100))
    else:
        v = ("normal", "PRECIO NORMAL", "Cuesta lo mismo que casi siempre. No es un chollo.")
    return {"ahora": ahora, "min": mn, "max": mx, "media": media, "base": base, "veredicto": v, "dias": dias}

def _vf_img(titulo, r):
    from PIL import Image, ImageDraw
    base, win, d, ww, wh, WIN = _pl_base("VERIFICADOR DE OFERTAS")
    ft = _cn_sans(34)
    palabras = str(titulo).split(); lin = []; cur = ""
    for p in palabras:
        pr = (cur + " " + p).strip()
        if d.textlength(pr, font=ft) <= ww - 80: cur = pr
        else: lin.append(cur); cur = p
    lin.append(cur)
    lin = lin[:2]
    if len(lin) == 2 and len(palabras) > len(" ".join(lin).split()):
        lin[1] = _pl_corta(d, lin[1] + " …", ft, ww - 80)
    for i, l in enumerate(lin):
        d.text((40, 128 + i * 42), l, font=ft, fill=(255, 255, 255), anchor="lm")
    # grafico
    x0, x1, y0, y1 = 120, ww - 50, 245, 560
    dias = r["dias"]
    vals = [x for x in dias if x is not None]
    lo, hi = min(vals), max(vals)
    if hi - lo < 0.01: hi = lo + 1
    pad = (hi - lo) * 0.12
    lo -= pad; hi += pad
    def Y(v): return y1 - (v - lo) / (hi - lo) * (y1 - y0)
    def X(i): return x0 + i * (x1 - x0) / 89.0
    for k in range(3):
        vv = lo + (hi - lo) * k / 2.0
        yy = Y(vv)
        d.line((x0, yy, x1, yy), fill=(62, 50, 44), width=1)
        d.text((x0 - 12, yy), _cn_eur(vv), font=_cn_sans(20, False), fill=(160, 168, 185), anchor="rm")
    yb = Y(r["base"])
    for xx in range(x0, x1, 22):
        d.line((xx, yb, xx + 11, yb), fill=(150, 158, 176), width=2)
    d.text((x1, yb - 14), "habitual", font=_cn_sans(18, False), fill=(150, 158, 176), anchor="rs")
    pts = []; ult = None
    for i, v in enumerate(dias):
        if v is None: continue
        if ult is not None:
            pts.append((X(i), Y(ult)))
        pts.append((X(i), Y(v))); ult = v
    ov = Image.new("RGBA", win.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    od.polygon(pts + [(pts[-1][0], y1), (pts[0][0], y1)], fill=(236, 170, 98, 55))
    win.alpha_composite(ov)
    d = ImageDraw.Draw(win)
    d.line(pts, fill=(236, 170, 98), width=5, joint="curve")
    px, py = pts[-1]
    d.ellipse((px - 11, py - 11, px + 11, py + 11), fill=(255, 255, 255), outline=(236, 170, 98), width=4)
    d.text((x0, y1 + 24), "hace 90 días", font=_cn_sans(20, False), fill=(160, 168, 185), anchor="lm")
    d.text((x1, y1 + 24), "hoy", font=_cn_sans(20, False), fill=(160, 168, 185), anchor="rm")
    # cifras
    tiles = (("AHORA", r["ahora"]), ("MÍNIMO", r["min"]), ("MEDIA", r["media"]), ("MÁXIMO", r["max"]))
    tw = (ww - 80 - 3 * 14) // 4
    for i, (n, v) in enumerate(tiles):
        x = 40 + i * (tw + 14)
        d.rounded_rectangle((x, 640, x + tw, 745), radius=22, fill=(20, 15, 12), outline=(236, 170, 98) if i == 0 else (80, 66, 58), width=3 if i == 0 else 2)
        d.text((x + tw // 2, 668), n, font=_cn_mono(20), fill=(160, 168, 185), anchor="mm")
        d.text((x + tw // 2, 714), _cn_eur(v), font=_cn_sans(31), fill=(255, 255, 255), anchor="mm")
    # veredicto
    tipo, tit, sub = r["veredicto"]
    col = {"real": (120, 220, 140), "minimo": (120, 220, 140), "normal": (236, 170, 98), "caro": (240, 120, 100), "falso": (240, 110, 90)}[tipo]
    d.rounded_rectangle((40, 775, ww - 40, 915), radius=34, fill=(26, 18, 12), outline=col, width=4)
    d.text((ww // 2, 810), tit, font=_cn_sans(44), fill=col, anchor="mm")
    fs = _cn_sans(25, False); sl = []; cur = ""
    for p in sub.split():
        pr = (cur + " " + p).strip()
        if d.textlength(pr, font=fs) <= ww - 140: cur = pr
        else: sl.append(cur); cur = p
    sl.append(cur)
    for i, l in enumerate(sl[:2]):
        d.text((ww // 2, (862 if len(sl) > 1 else 872) + i * 32), l, font=fs, fill=(235, 238, 245), anchor="mm")
    return _pl_cerrar(base, win, WIN, True)

def _vf_hacer(cid, texto):
    try:
        asin = _vf_asin(texto)
        if not asin:
            enviar(cid, "Pégame un enlace de Amazon.es y te digo si el precio es real.\nEjemplo: /verifica https://www.amazon.es/dp/B0XXXXXXXX"); return
        rr = requests.get("https://api.keepa.com/product", params={"key": KEEPA_KEY, "domain": 9, "asin": asin}, timeout=30)
        if rr.status_code != 200:
            print("verifica keepa http", rr.status_code, flush=True)
            enviar(cid, "Ahora mismo no puedo consultar el histórico. Prueba en un rato."); return
        pr = (rr.json().get("products") or [None])[0] or {}
        csv = pr.get("csv") or []
        serie = None
        for idx in (0, 1):
            if len(csv) > idx and csv[idx] and len(csv[idx]) >= 4:
                s = _vf_serie(csv[idx], _cn_time.time())
                if s[-1] is not None:
                    serie = s; break
        res = _vf_analizar(serie) if serie else None
        if res is None:
            enviar(cid, "No tengo histórico suficiente de este producto (o ahora no está disponible). Prueba con otro."); return
        titulo = pr.get("title") or asin
        img = _vf_img(titulo, res)
        tipo, tit, sub = res["veredicto"]
        cap = "\U0001f50e %s\n%s\n\n\U0001f4b6 Ahora %s · mínimo %s · media %s · máximo %s (90 días)\n\U0001f449 https://www.amazon.es/dp/%s?tag=alexexplore0e-21" % (
            tit, sub, _cn_eur(res["ahora"]), _cn_eur(res["min"]), _cn_eur(res["media"]), _cn_eur(res["max"]), asin)
        _pl_enviar(cid, img, cap)
    except Exception as e:
        print("error /verifica", e, flush=True)
        try: enviar(cid, "No he podido verificar ese producto. Prueba con otro enlace.")
        except Exception: pass

_vf_pre_hook = hook_anuncios_pago

def hook_anuncios_pago(d, u):
    try:
        m = u.get("message")
        t = ((m.get("text") or "") if m else "").strip()
        if m and t:
            prim = t.split()[0]; cmd = prim.lower().split("@")[0]
            if cmd in ("/verifica", "/verificar"):
                cid = m["chat"]["id"]; uid = (m.get("from") or {}).get("id", cid)
                if _cn_time.time() - _VF_ULT.get(uid, 0) < 15:
                    enviar(cid, "Un momento, espera unos segundos entre consultas."); return True
                _VF_ULT[uid] = _cn_time.time()
                if len(_VF_ULT) > 500: _VF_ULT.clear()
                enviar(cid, "Mirando el histórico de 90 días…")
                _vd_th.Thread(target=_vf_hacer, args=(cid, t[len(prim):]), daemon=True).start()
                return True
    except Exception as e:
        print("error hook verifica", e, flush=True)
    return _vf_pre_hook(d, u)
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_verifica_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: /verifica ENLACE. Copia:", cp)
print("Reinicia: sudo systemctl restart chivato   y luego /autotest y /verifica ENLACE")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
