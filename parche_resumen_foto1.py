import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- RESUMENFOTO1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("def _a_tarea(", "def _mi_d(", "def _cn_foto(", "def _vd_token(", "def enviar(", "def _a_ahora("):
    if n not in src:
        print("ABORTO: falta", n); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''
# --- RESUMENFOTO1 ---
# Foto "Lo mejor del dia" antes del texto del resumen diario (top 5 de las ultimas 24 h, con precios y ahorro total).
import io as _rf_io
_rf_d = None
_rf_cache = {"dia": "", "jpeg": None, "fid": None, "intento": 0}
_RF_MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

def _rf_fuente(n, s):
    from PIL import ImageFont
    for D in ("/usr/share/fonts/truetype/dejavu/", "/usr/share/fonts/dejavu/", "/usr/share/fonts/TTF/"):
        try:
            return ImageFont.truetype(D + n, s)
        except Exception:
            pass
    return ImageFont.load_default()

def _rf_eur(x):
    return ("%.2f" % x).replace(".", ",") + " €"

def _rf_items(d):
    ahora = time.time()
    vistos, res = set(), []
    for o in (_mi_d(d).get("of") or []):
        try:
            asin = o.get("asin")
            if not asin or asin in vistos or ahora - float(o.get("ts", 0)) > 24 * 3600:
                continue
            a, b = float(o.get("ahora") or 0), float(o.get("antes") or 0)
            if a < 5 or b <= a:
                continue
            pct = int(o.get("pct") or round(100 * (b - a) / b))
            if pct > 90 or pct < 30:
                continue
            t = re.sub(r"\s+-\s*[\d.,]+\s*EUR\s*$", "", str(o.get("t") or "")).strip()
            lib = globals().get("_fi_es_libro"); idi = globals().get("_fi_otro_idioma")
            if (lib and lib(asin)) or (idi and idi(t)):
                continue
            vistos.add(asin)
            res.append({"asin": asin, "t": t, "a": a, "b": b, "pct": pct})
        except Exception:
            continue
    res.sort(key=lambda x: (-x["pct"], -(x["b"] - x["a"])))
    return res[:5]

def _rf_ajusta(dr, txt, fuente, ancho, lineas=2):
    pal, out, cur = txt.split(), [], ""
    for p in pal:
        prueba = (cur + " " + p).strip()
        if dr.textlength(prueba, font=fuente) <= ancho:
            cur = prueba
        else:
            if cur:
                out.append(cur)
            cur = p
        if len(out) == lineas:
            break
    if len(out) < lineas and cur:
        out.append(cur)
    if len(out) == lineas and (len(" ".join(out)) < len(txt)):
        u = out[-1]
        while u and dr.textlength(u + "…", font=fuente) > ancho:
            u = u[:-1]
        out[-1] = u.rstrip() + "…"
    return out

def _rf_render(items, fotos, fecha):
    from PIL import Image, ImageDraw, ImageFilter
    W, H = 1080, 1350
    img = Image.new("RGB", (W, H), (13, 10, 9))
    glow = Image.new("RGB", (W, H), (13, 10, 9))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([520, -420, 1380, 440], fill=(120, 64, 24))
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    img = Image.blend(img, glow, 0.8)
    dr = ImageDraw.Draw(img)
    ORO, BLANCO, GRIS = (232, 168, 96), (246, 237, 226), (170, 158, 146)
    dr.text((60, 52), "CHIVATO DE OFERTAS", font=_rf_fuente("DejaVuSans-Bold.ttf", 28), fill=ORO)
    f_p = _rf_fuente("DejaVuSans-Bold.ttf", 25)
    tp = "Resumen · " + fecha
    wp = dr.textlength(tp, font=f_p)
    dr.rounded_rectangle([W - 60 - wp - 44, 38, W - 60, 90], 26, outline=(120, 100, 84), width=2)
    dr.text((W - 60 - wp - 22, 49), tp, font=f_p, fill=BLANCO)
    f_t = _rf_fuente("DejaVuSerif-Bold.ttf", 90)
    dr.text((60, 120), "Lo mejor ", font=f_t, fill=BLANCO)
    dr.text((60 + dr.textlength("Lo mejor ", font=f_t), 120), "del día", font=f_t, fill=ORO)
    dr.text((62, 238), "Las ofertas que más ahorran, con enlace en el mensaje", font=_rf_fuente("DejaVuSans.ttf", 29), fill=GRIS)
    y0, alto, sep = 306, 136, 14
    medallas = [(240, 190, 40), (205, 205, 215), (214, 150, 90), (60, 52, 46), (60, 52, 46)]
    f_n = _rf_fuente("DejaVuSans-Bold.ttf", 31); f_s = _rf_fuente("DejaVuSans.ttf", 24)
    f_pr = _rf_fuente("DejaVuSans-Bold.ttf", 44); f_pi = _rf_fuente("DejaVuSans-Bold.ttf", 24)
    total = 0.0
    for i, it in enumerate(items):
        y = y0 + i * (alto + sep)
        dr.rounded_rectangle([60, y, W - 60, y + alto], 26, fill=(28, 22, 18))
        cx, cy = 112, y + alto // 2
        dr.ellipse([cx - 31, cy - 31, cx + 31, cy + 31], fill=medallas[i])
        fr = _rf_fuente("DejaVuSans-Bold.ttf", 32)
        dr.text((cx, cy), str(i + 1), font=fr, fill=(20, 14, 10) if i < 3 else BLANCO, anchor="mm")
        dr.rounded_rectangle([164, y + 16, 164 + 104, y + 16 + 104], 14, fill=(255, 255, 255))
        ft = fotos.get(it["asin"])
        if ft is not None:
            ft = ft.copy(); ft.thumbnail((96, 96))
            img.paste(ft, (164 + (104 - ft.width) // 2, y + 16 + (104 - ft.height) // 2))
            ft.close()
        for k, linea in enumerate(_rf_ajusta(dr, it["t"], f_n, 470, 2)):
            dr.text((292, y + 20 + k * 38), linea, font=f_n, fill=BLANCO)
        dr.text((292, y + 98), "Amazon · antes " + _rf_eur(it["b"]), font=f_s, fill=GRIS)
        dr.text((W - 76, y + 16), _rf_eur(it["a"]), font=f_pr, fill=ORO, anchor="ra")
        ahorro = it["b"] - it["a"]; total += ahorro
        tx = "-%d € · %d %%" % (round(ahorro), it["pct"])
        wt = dr.textlength(tx, font=f_pi)
        dr.rounded_rectangle([W - 76 - wt - 28, y + 84, W - 76, y + 122], 10, fill=(61, 220, 151))
        dr.text((W - 76 - wt - 14, y + 90), tx, font=f_pi, fill=(8, 40, 26))
    ty = y0 + len(items) * (alto + sep) + 6
    dr.rounded_rectangle([60, ty, W - 60, ty + 96], 26, outline=ORO, width=3, fill=(24, 18, 12))
    dr.text((90, ty + 48), "Si te llevaras los %d, ahorrarías" % len(items), font=_rf_fuente("DejaVuSans-Bold.ttf", 32), fill=BLANCO, anchor="lm")
    dr.text((W - 90, ty + 48), "%d €" % round(total), font=_rf_fuente("DejaVuSans-Bold.ttf", 50), fill=ORO, anchor="rm")
    fy = H - 130
    dr.rectangle([0, fy, W, H], fill=(201, 121, 46))
    dr.text((60, fy + 38), "Más ofertas gratis en @ChivatoOfertas_bot", font=_rf_fuente("DejaVuSans-Bold.ttf", 36), fill=(20, 12, 6), anchor="lm")
    dr.text((60, fy + 92), "Precios del momento del aviso · Pueden cambiar · Enlaces de afiliado", font=_rf_fuente("DejaVuSans.ttf", 22), fill=(40, 24, 10), anchor="lm")
    return img

def _rf_construir(d):
    items = _rf_items(d)
    if len(items) < 3:
        return None
    fotos = {}
    for it in items:
        try:
            fotos[it["asin"]] = _cn_foto(it["asin"])
        except Exception:
            fotos[it["asin"]] = None
    a = _a_ahora()
    img = _rf_render(items, fotos, "%d %s" % (a.day, _RF_MESES[a.month - 1]))
    buf = _rf_io.BytesIO()
    img.save(buf, "JPEG", quality=88)
    img.close()
    return buf.getvalue()

def _rf_foto(cid):
    hoy = _a_ahora().strftime("%Y-%m-%d")
    c = _rf_cache
    if c["dia"] != hoy:
        if time.time() - c["intento"] < 600:
            return
        c["intento"] = time.time()
        c["jpeg"] = _rf_construir(_rf_d)
        c["fid"] = None
        if c["jpeg"]:
            c["dia"] = hoy
    if not c["jpeg"]:
        return
    cap = "\U0001f5de Lo mejor del día · los enlaces van en el mensaje de abajo"
    url = "https://api.telegram.org/bot%s/sendPhoto" % _vd_token()
    if c["fid"]:
        requests.post(url, data={"chat_id": cid, "caption": cap, "photo": c["fid"]}, timeout=30)
        return
    r = requests.post(url, data={"chat_id": cid, "caption": cap}, files={"photo": ("resumen.jpg", c["jpeg"])}, timeout=60)
    try:
        c["fid"] = r.json()["result"]["photo"][-1]["file_id"]
    except Exception:
        pass

_rf_tarea_orig = _a_tarea
def _a_tarea(d):
    global _rf_d
    _rf_d = d
    return _rf_tarea_orig(d)

_rf_enviar_orig = enviar
def enviar(cid, texto, *a, **k):
    try:
        if isinstance(texto, str) and texto.startswith("\U0001f5de RESUMEN DEL D") and _rf_d is not None:
            _rf_foto(cid)
    except Exception as e:
        print("error resumen foto", str(e)[:100], flush=True)
    return _rf_enviar_orig(cid, texto, *a, **k)
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: error de sintaxis", e); sys.exit(1)
cp = RUTA + ".bak_resumenfoto_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy2(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: el resumen diario lleva ahora una foto con las 5 mejores ofertas.")
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato")
print("Deshacer: cp %s %s && sudo systemctl restart chivato" % (cp, RUTA))
