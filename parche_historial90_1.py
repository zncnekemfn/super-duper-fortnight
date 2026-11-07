import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- HIST90A ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("def _cn_frame(", "def _cn_ease(", "_cn_loc"):
    if n not in src:
        print("ABORTO: falta", n, "(hace falta el estilo cine)"); sys.exit(1)
BLOQUE = r'''
# --- HIST90A ---
# Grafico de precio de los ultimos 90 dias dentro de la foto/video del aviso (datos de Keepa).
import time as _h9_t
_h9_pre = _cn_frame
_h9_series = {}
_h9_capas = {}

def _h9_serie(asin):
    ahora = _h9_t.time()
    c = _h9_series.get(asin)
    if c and ahora - c[0] < 6 * 3600:
        return c[1]
    serie = None
    try:
        k = globals().get("KEEPA_KEY") or globals().get("KEEPA")
        if k:
            r = requests.get("https://api.keepa.com/product", params={"key": k, "domain": 9, "asin": asin, "history": 1}, timeout=20)
            if r.status_code == 200:
                p = (r.json().get("products") or [None])[0] or {}
                csv = p.get("csv") or []
                arr = (csv[0] if csv and csv[0] else (csv[1] if len(csv) > 1 else None)) or []
                pares = []
                for i in range(0, len(arr) - 1, 2):
                    ts = (arr[i] + 21564000) * 60
                    pr = arr[i + 1]
                    pares.append((ts, pr / 100.0 if pr and pr > 0 else None))
                if pares:
                    serie = []
                    ult = None; j = 0
                    for i in range(91):
                        tt = ahora - (90 - i) * 86400
                        while j < len(pares) and pares[j][0] <= tt:
                            if pares[j][1] is not None: ult = pares[j][1]
                            j += 1
                        serie.append(ult)
                    # relleno hacia atras si el producto es mas nuevo que 90 dias
                    primero = next((v for v in serie if v is not None), None)
                    serie = [v if v is not None else None for v in serie]
                    if sum(1 for v in serie if v is not None) < 10:
                        serie = None
    except Exception as e:
        print("error hist90", str(e)[:100], flush=True)
        serie = None
    if len(_h9_series) > 200:
        _h9_series.clear()
    _h9_series[asin] = (ahora, serie)
    return serie

def _h9_capa(serie, actual):
    from PIL import Image, ImageDraw
    w, h = 936, 150
    vals = [v for v in serie if v is not None]
    vals.append(actual)
    mn, mx = min(vals), max(vals)
    if mx - mn < 0.01:
        mx = mn + 1.0
    L = Image.new("RGBA", (w, h), (0, 0, 0, 0)); g = ImageDraw.Draw(L)
    g.rounded_rectangle((0, 0, w - 1, h - 1), 26, fill=(9, 11, 17, 185), outline=(255, 255, 255, 45), width=2)
    g.text((22, 20), "ÚLTIMOS 90 DÍAS", font=_cn_mono(17), fill=(205, 210, 224), anchor="lm")
    x0, x1, y0, y1 = 24, w - 215, 44, h - 20
    def px(i): return x0 + (x1 - x0) * i / 90.0
    def py(v): return y1 - (y1 - y0) * (v - mn) / (mx - mn)
    pts = []
    for i, v in enumerate(serie):
        if v is not None: pts.append((px(i), py(v)))
    pts.append((x1, py(actual)))
    area = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ad = ImageDraw.Draw(area)
    ad.polygon(pts + [(pts[-1][0], y1), (pts[0][0], y1)], fill=(120, 255, 214, 38))
    L.alpha_composite(area); g = ImageDraw.Draw(L)
    g.line(pts, fill=(130, 255, 220, 255), width=4, joint="curve")
    g.ellipse((x1 - 9, py(actual) - 9, x1 + 9, py(actual) + 9), fill=(9, 11, 17, 255), outline=(130, 255, 220, 255), width=4)
    e = lambda v: ("%.2f" % v).replace(".", ",") + " €"
    g.text((w - 24, 44), "máx " + e(max(vals)), font=_cn_sans(22, False), fill=(160, 168, 185), anchor="rm")
    g.text((w - 24, 82), "ahora " + e(actual), font=_cn_sans(26), fill=(130, 255, 220), anchor="rm")
    g.text((w - 24, 120), "mín " + e(min(vals)), font=_cn_sans(22, False), fill=(160, 168, 185), anchor="rm")
    return L

def _cn_frame(dat, t=0.0, total=6.0, still=True):
    img = _h9_pre(dat, t, total, still)
    try:
        it = getattr(_cn_loc, "item", None) or {}
        mm = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", str(it.get("u") or ""))
        asin = (mm.group(1) if mm else None) or getattr(_cn_loc, "asin", None)
        if not asin:
            return img
        serie = _h9_serie(asin)
        if not serie:
            return img
        clave = (asin, round(float(dat["ahora"]), 2))
        capa = _h9_capas.get(clave)
        if capa is None:
            capa = _h9_capa(serie, float(dat["ahora"]))
            if len(_h9_capas) > 60: _h9_capas.clear()
            _h9_capas[clave] = capa
        a = 1.0 if still else _cn_ease((t - 1.9) / 0.7)
        if a <= 0:
            return img
        c = capa if a >= 1 else capa.copy()
        if a < 1:
            c.putalpha(c.getchannel("A").point(lambda v: int(v * a)))
        base = img.convert("RGBA")
        base.alpha_composite(c, (72, 500))
        return base.convert("RGB")
    except Exception as ex:
        print("error hist90 frame", str(ex)[:100], flush=True)
        return img
'''
n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
nuevo = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: BLOQUE + "\n" + m.group(0), src, count=1, flags=re.M)
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: error de sintaxis", e); sys.exit(1)
copia = RUTA + ".bak_hist90a_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("OK. Reinicia: sudo systemctl restart chivato   y prueba con /foto <enlace de Amazon>")
print("Deshacer: cp %s %s && sudo systemctl restart chivato" % (copia, RUTA))
