import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- ADIVINAFOTO1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("# --- ADIVINAMES1 ---", "def _ad_ranking(", "def _cn_sans(", "def _ad_teclado(", "def _vd_token("):
    if n not in src:
        print("ABORTO: falta", n, "(primero parche_adivina_mes1.py)"); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''
# --- ADIVINAFOTO1 ---
# El ranking de /adivina se envia como foto (estilo caramelo del bot): top 5 del mes, top 3 de la semana,
# premio y posicion de quien lo pide. Si algo falla, envia el texto de siempre.
_adf_txt_orig = _ad_ranking

def _adf_img(d, cid):
    from PIL import Image, ImageDraw
    W, H = 1080, 1350
    G = (236, 170, 98); GL = (243, 197, 138); GR = (176, 160, 146)
    im = Image.new("RGB", (W, H), (6, 5, 4)); dr = ImageDraw.Draw(im)
    dr.rounded_rectangle((36, 36, W - 36, H - 36), 44, fill=(13, 10, 9), outline=(62, 50, 44), width=2)
    dr.rounded_rectangle((72, 72, 470, 116), 22, fill=(14, 10, 8), outline=G, width=2)
    dr.text((271, 94), "ADIVINA EL PRECIO", font=_cn_mono(21), fill=GL, anchor="mm")
    mes = _adm_mes(); s = _ad_semana()
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    nm = meses[int(mes.split("-")[1]) - 1]
    dr.text((72, 150), "Ranking de", font=_cn_serb(64), fill=(255, 255, 255))
    dr.text((72, 224), nm, font=_cn_serb(64), fill=G)
    top, todos = _adm_top(d, mes, 5)
    y = 330
    if not top:
        dr.text((72, y + 20), "Todavía nadie ha puntuado este mes.", font=_cn_sans(30, False), fill=GR)
        dr.text((72, y + 70), "¡Sé el primero con /adivina!", font=_cn_sans(30), fill=G)
        y += 120
    for i, (c, v) in enumerate(top):
        yo = (c == str(cid))
        dr.rounded_rectangle((72, y, W - 72, y + 84), 24, fill=(60, 40, 20) if yo else (20, 15, 13), outline=G if i == 0 or yo else (62, 50, 44), width=3 if i == 0 else 2)
        dr.ellipse((92, y + 16, 144, y + 68), outline=G, width=3)
        dr.text((118, y + 42), str(i + 1), font=_cn_sans(28), fill=G, anchor="mm")
        dr.text((170, y + 42), (v.get("nom") or "Jugador") + ("  (tú)" if yo else ""), font=_cn_sans(32), fill=(255, 255, 255), anchor="lm")
        dr.text((W - 100, y + 42), "%d pts" % v["mp"][mes], font=_cn_sans(32), fill=GL, anchor="rm")
        y += 98
    y = max(y, 330 + 5 * 98) + 20
    dr.text((72, y), "ESTA SEMANA", font=_cn_mono(22), fill=GR)
    sem = [(c, v) for c, v in _ad_d(d)["j"].items() if v["sem"].get(s, 0) > 0]
    sem.sort(key=lambda x: -x[1]["sem"][s])
    y += 40
    if not sem:
        dr.text((72, y), "Todavía nadie.", font=_cn_sans(26, False), fill=GR); y += 44
    for i, (c, v) in enumerate(sem[:3]):
        dr.text((72, y), "%d.  %s" % (i + 1, v.get("nom") or "Jugador"), font=_cn_sans(28), fill=(255, 255, 255))
        dr.text((W - 100, y), "%d pts" % v["sem"][s], font=_cn_sans(28), fill=GL, anchor="ra")
        y += 46
    y = max(y, 330 + 5 * 98 + 20 + 40 + 3 * 46) + 24
    dr.line((72, y, W - 72, y), fill=(62, 50, 44), width=2)
    pos = next((i + 1 for i, (c, v) in enumerate(todos) if c == str(cid)), None)
    mine = _ad_d(d)["j"].get(str(cid), {})
    rondas = mine.get("mr", {}).get(mes, 0)
    dr.text((72, y + 24), ("Tu posición: %d de %d  ·  %d rondas" % (pos, len(todos), rondas)) if pos else "Aún no estás en el ranking del mes: juega con /adivina",
            font=_cn_sans(28), fill=G)
    dr.text((72, y + 76), "\U0001f381 Premio del mes: " if False else "Premio del mes:", font=_cn_sans(26, False), fill=GR)
    pr = _adm_premio(d)
    dr.text((72, y + 112), pr[:48] + ("…" if len(pr) > 48 else ""), font=_cn_sans(30), fill=(255, 255, 255))
    dr.text((W // 2, H - 66), "Mínimo %d rondas · Sin compra necesaria · Se cierra el día 1" % _ADM_MIN_RONDAS, font=_cn_sans(18, False), fill=GR, anchor="mm")
    buf = _cn_io.BytesIO(); im.save(buf, "JPEG", quality=90)
    return buf.getvalue()

def _ad_ranking(d, cid):
    try:
        datos = _adf_img(d, cid)
        r = requests.post("https://api.telegram.org/bot%s/sendPhoto" % _vd_token(),
                          data={"chat_id": cid, "caption": "\U0001f3c6 Ranking · Adivina el precio", "reply_markup": _ad_teclado()},
                          files={"photo": ("ranking.jpg", datos)}, timeout=60)
        if r.status_code == 200:
            return
        print("error ranking foto HTTP", r.status_code, flush=True)
    except Exception as e:
        print("error ranking foto", str(e)[:100], flush=True)
    _adf_txt_orig(d, cid)
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_adivinafoto_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Ranking con foto aplicado. Reinicia: sudo systemctl restart chivato")
print("Prueba: /adivina ranking")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
