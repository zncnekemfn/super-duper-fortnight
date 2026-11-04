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
# Resumen diario con foto "Lo mejor del dia" + mensaje con enlaces (top 5 de las ultimas 24 h y capricho del dia).
import io as _rf_io
import html as _rf_html
_rf_d = None
_rf_cache = {"dia": "", "datos": None, "fid": None, "intento": 0}
_RF_MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
_RF_MESES_L = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
_RF_DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

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

def _rf_candidatas(d):
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
            if pct > 90 or pct < 15:
                continue
            t = re.sub(r"\s+-\s*[\d.,]+\s*EUR\s*$", "", str(o.get("t") or "")).strip()
            lib = globals().get("_fi_es_libro"); idi = globals().get("_fi_otro_idioma")
            if (lib and lib(asin)) or (idi and idi(t)):
                continue
            vistos.add(asin)
            res.append({"asin": asin, "t": t, "a": a, "b": b, "pct": pct})
        except Exception:
            continue
    return res

def _rf_items(d):
    todas = _rf_candidatas(d)
    top = sorted([x for x in todas if x["pct"] >= 30], key=lambda x: (-x["pct"], -(x["b"] - x["a"])))[:5]
    usados = set(x["asin"] for x in top)
    resto = [x for x in todas if x["asin"] not in usados and x["a"] >= 40]
    capricho = max(resto, key=lambda x: x["a"]) if resto else None
    return top, capricho

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

def _rf_vidrio(img, caja, radio, tinte=(255, 255, 255, 24), borde=(255, 255, 255, 80), desenfoque=22):
    """Panel de vidrio esmerilado: difumina lo que hay detras, lo aclara un poco y le pone borde y brillo."""
    from PIL import Image, ImageDraw, ImageFilter
    x0, y0, x1, y1 = caja
    zona = img.crop(caja).filter(ImageFilter.GaussianBlur(desenfoque))
    mask = Image.new("L", (x1 - x0, y1 - y0), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, x1 - x0 - 1, y1 - y0 - 1], radio, fill=255)
    img.paste(zona, (x0, y0), mask)
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.rounded_rectangle(caja, radio, fill=tinte, outline=borde, width=2)
    od.line([x0 + radio, y0 + 3, x1 - radio, y0 + 3], fill=(255, 255, 255, 70), width=2)
    img.alpha_composite(ov)

def _rf_render(items, fotos, fecha, capricho=None):
    from PIL import Image, ImageDraw, ImageFilter
    W = 1080
    y0, alto, sep = 306, 136, 14
    n = len(items)
    ty = y0 + n * (alto + sep) + 6
    cy2 = ty + 96 + 16
    H = (cy2 + 100 + 40 + 130) if capricho else 1350
    img = Image.new("RGBA", (W, H), (13, 10, 9, 255))
    luz = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(luz)
    for cx, cy, r, col in ((880, 260, 330, (190, 100, 34, 200)), (120, 600, 260, (232, 168, 96, 120)),
                           (900, 900, 300, (201, 121, 46, 150)), (200, H - 230, 280, (150, 80, 30, 170)),
                           (560, 120, 200, (232, 168, 96, 80))):
        ld.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    luz = luz.filter(ImageFilter.GaussianBlur(120))
    img.alpha_composite(luz)
    ORO, BLANCO, GRIS = (232, 168, 96), (246, 237, 226), (190, 178, 166)
    som = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(som)
    for i in range(n):
        y = y0 + i * (alto + sep)
        sd.rounded_rectangle([64, y + 12, W - 64, y + alto + 12], 26, fill=(0, 0, 0, 120))
    sd.rounded_rectangle([64, ty + 12, W - 64, ty + 108], 26, fill=(0, 0, 0, 120))
    if capricho:
        sd.rounded_rectangle([64, cy2 + 12, W - 64, cy2 + 112], 26, fill=(0, 0, 0, 120))
    img.alpha_composite(som.filter(ImageFilter.GaussianBlur(14)))
    _rf_vidrio(img, (W - 60 - 300, 38, W - 60, 90), 26, tinte=(255, 255, 255, 20))
    for i in range(n):
        y = y0 + i * (alto + sep)
        _rf_vidrio(img, (60, y, W - 60, y + alto), 26)
    _rf_vidrio(img, (60, ty, W - 60, ty + 96), 26, tinte=(232, 168, 96, 46), borde=(240, 190, 120, 190))
    if capricho:
        _rf_vidrio(img, (60, cy2, W - 60, cy2 + 100), 26, tinte=(61, 220, 151, 22), borde=(120, 230, 180, 120))
    img = img.convert("RGB")
    dr = ImageDraw.Draw(img)
    dr.text((60, 52), "CHIVATO DE OFERTAS", font=_rf_fuente("DejaVuSans-Bold.ttf", 28), fill=ORO)
    dr.text((W - 60 - 150, 64), "Resumen · " + fecha, font=_rf_fuente("DejaVuSans-Bold.ttf", 25), fill=BLANCO, anchor="mm")
    f_t = _rf_fuente("DejaVuSerif-Bold.ttf", 90)
    dr.text((60, 120), "Lo mejor ", font=f_t, fill=BLANCO)
    dr.text((60 + dr.textlength("Lo mejor ", font=f_t), 120), "del día", font=f_t, fill=ORO)
    dr.text((62, 238), "Las ofertas que más ahorran, con enlace en el mensaje", font=_rf_fuente("DejaVuSans.ttf", 29), fill=GRIS)
    medallas = [(240, 190, 40), (205, 205, 215), (214, 150, 90), (70, 60, 52), (70, 60, 52)]
    f_n = _rf_fuente("DejaVuSans-Bold.ttf", 31); f_s = _rf_fuente("DejaVuSans.ttf", 24)
    f_pr = _rf_fuente("DejaVuSans-Bold.ttf", 44); f_pi = _rf_fuente("DejaVuSans-Bold.ttf", 24)
    total = 0.0
    for i, it in enumerate(items):
        y = y0 + i * (alto + sep)
        cx, cy = 112, y + alto // 2
        dr.ellipse([cx - 31, cy - 31, cx + 31, cy + 31], fill=medallas[i], outline=(255, 255, 255), width=1)
        dr.text((cx, cy), str(i + 1), font=_rf_fuente("DejaVuSans-Bold.ttf", 32), fill=(20, 14, 10) if i < 3 else BLANCO, anchor="mm")
        dr.rounded_rectangle([164, y + 16, 164 + 104, y + 16 + 104], 16, fill=(255, 255, 255))
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
        dr.rounded_rectangle([W - 76 - wt - 28, y + 84, W - 76, y + 122], 12, fill=(61, 220, 151))
        dr.text((W - 76 - wt - 14, y + 90), tx, font=f_pi, fill=(8, 40, 26))
    dr.text((90, ty + 48), "Si te llevaras los %d, ahorrarías" % n, font=_rf_fuente("DejaVuSans-Bold.ttf", 32), fill=BLANCO, anchor="lm")
    dr.text((W - 90, ty + 48), "%d €" % round(total), font=_rf_fuente("DejaVuSans-Bold.ttf", 50), fill=ORO, anchor="rm")
    if capricho:
        dr.text((90, cy2 + 28), "EL CAPRICHO DEL DÍA", font=_rf_fuente("DejaVuSans-Bold.ttf", 22), fill=(61, 220, 151), anchor="lm")
        nom = _rf_ajusta(dr, capricho["t"], _rf_fuente("DejaVuSans-Bold.ttf", 31), 560, 1)
        dr.text((90, cy2 + 68), nom[0] if nom else "", font=_rf_fuente("DejaVuSans-Bold.ttf", 31), fill=BLANCO, anchor="lm")
        dr.text((W - 90, cy2 + 38), _rf_eur(capricho["a"]), font=_rf_fuente("DejaVuSans-Bold.ttf", 42), fill=ORO, anchor="rm")
        dr.text((W - 90, cy2 + 76), "antes %s · -%d %%" % (_rf_eur(capricho["b"]), capricho["pct"]), font=_rf_fuente("DejaVuSans.ttf", 23), fill=GRIS, anchor="rm")
    fy = H - 130
    banda = Image.new("RGB", (W, 130))
    bd = ImageDraw.Draw(banda)
    for x in range(W):
        t = x / float(W)
        bd.line([x, 0, x, 130], fill=(int(214 - 40 * t), int(134 - 38 * t), int(56 - 20 * t)))
    img.paste(banda, (0, fy))
    dr = ImageDraw.Draw(img)
    dr.line([0, fy, W, fy], fill=(255, 220, 170), width=2)
    dr.text((60, fy + 38), "Más ofertas gratis en @ChivatoOfertas_bot", font=_rf_fuente("DejaVuSans-Bold.ttf", 36), fill=(20, 12, 6), anchor="lm")
    dr.text((60, fy + 92), "Precios del momento del aviso · Pueden cambiar · Enlaces de afiliado", font=_rf_fuente("DejaVuSans.ttf", 22), fill=(40, 24, 10), anchor="lm")
    return img

def _rf_enlace(asin):
    return "https://www.amazon.es/dp/%s?tag=%s" % (asin, globals().get("TAG") or "alexexplore0e-21")

def _rf_texto(items, capricho, fecha_larga):
    e = _rf_html.escape
    def corto(t, n=64):
        t = str(t)
        return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "…"
    medallas = ["\U0001f947", "\U0001f948", "\U0001f949", "4️⃣", "5️⃣"]
    L = ["\U0001f3c6 <b>LO MEJOR DEL DÍA</b>", "<i>%s</i>" % e(fecha_larga), "",
         "Los %d chollos de hoy que más ahorro te dan:" % len(items), ""]
    total = 0.0
    for i, it in enumerate(items):
        total += it["b"] - it["a"]
        L.append("%s <a href=\"%s\">%s</a>" % (medallas[i], _rf_enlace(it["asin"]), e(corto(it["t"]))))
        L.append("\U0001f4b6 <b>%s</b> <s>%s</s> · ahorras <b>%d €</b> (−%d %%)" % (_rf_eur(it["a"]), _rf_eur(it["b"]), round(it["b"] - it["a"]), it["pct"]))
        L.append("")
    if capricho:
        L += ["\U0001f48e <b>EL CAPRICHO DEL DÍA</b>",
              "<a href=\"%s\">%s</a> por <b>%s</b> (−%d %%)" % (_rf_enlace(capricho["asin"]), e(corto(capricho["t"])), _rf_eur(capricho["a"]), capricho["pct"]), ""]
    L += ["\U0001f4b0 Si te llevaras los %d, ahorrarías <b>%d €</b>" % (len(items), round(total)), "",
          "#ResumenChivato", "\U0001f4e3 Más ofertas gratis en @ChivatoOfertas_bot",
          "<i>Precios del momento del aviso. Pueden cambiar. Enlaces de afiliado.</i>"]
    return "\n".join(L)

def _rf_preparar(d):
    items, capricho = _rf_items(d)
    if len(items) < 3:
        return None
    fotos = {}
    for it in items:
        try:
            fotos[it["asin"]] = _cn_foto(it["asin"])
        except Exception:
            fotos[it["asin"]] = None
    a = _a_ahora()
    img = _rf_render(items, fotos, "%d %s" % (a.day, _RF_MESES[a.month - 1]), capricho)
    buf = _rf_io.BytesIO()
    img.save(buf, "JPEG", quality=88)
    img.close()
    fecha_larga = "%s, %d de %s" % (_RF_DIAS[a.weekday()], a.day, _RF_MESES_L[a.month - 1])
    return {"jpeg": buf.getvalue(), "texto": _rf_texto(items, capricho, fecha_larga)}

def _rf_resumen(cid):
    """Envia foto + mensaje con enlaces. Devuelve True si el mensaje salio; False si hay que usar el texto de siempre."""
    hoy = _a_ahora().strftime("%Y-%m-%d")
    c = _rf_cache
    if c["dia"] != hoy:
        if time.time() - c["intento"] < 600:
            return False
        c["intento"] = time.time()
        c["datos"] = _rf_preparar(_rf_d)
        c["fid"] = None
        if c["datos"]:
            c["dia"] = hoy
    dat = c["datos"]
    if not dat:
        return False
    base = "https://api.telegram.org/bot%s/" % _vd_token()
    cap = "\U0001f3c6 Lo mejor del día"
    try:
        if c["fid"]:
            requests.post(base + "sendPhoto", data={"chat_id": cid, "caption": cap, "photo": c["fid"]}, timeout=30)
        else:
            r = requests.post(base + "sendPhoto", data={"chat_id": cid, "caption": cap}, files={"photo": ("resumen.jpg", dat["jpeg"])}, timeout=60)
            try:
                c["fid"] = r.json()["result"]["photo"][-1]["file_id"]
            except Exception:
                pass
    except Exception as e:
        print("error resumen foto", str(e)[:100], flush=True)
    r2 = requests.post(base + "sendMessage", data={"chat_id": cid, "text": dat["texto"], "parse_mode": "HTML",
                       "disable_web_page_preview": "true"}, timeout=30)
    return r2.status_code == 200

_rf_tarea_orig = _a_tarea
def _a_tarea(d):
    global _rf_d
    _rf_d = d
    return _rf_tarea_orig(d)

_rf_enviar_orig = enviar
def enviar(cid, texto, *a, **k):
    try:
        if isinstance(texto, str) and texto.startswith("\U0001f5de RESUMEN DEL D") and _rf_d is not None:
            if _rf_resumen(cid):
                return
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
