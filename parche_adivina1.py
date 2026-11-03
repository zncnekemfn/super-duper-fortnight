import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- ADIVINA1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("def _mi_d(", "def _cn_foto(", "def _a_ahora(", "def teclado_menu(", "def hook_menu(", "def hook_anuncios_pago(", "_cn_io", "_vd_th", "def _vd_token("):
    if n not in src:
        print("ABORTO: falta", n); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''
# --- ADIVINA1 ---
# Juego "Adivina el precio": foto de una oferta real reciente, el usuario escribe el precio y gana puntos.
# Ranking semanal y racha diaria. Usa las ofertas ya guardadas (no gasta tokens de Keepa salvo la foto).
import random as _ad_rnd
_AD_MAX_DIA = 10
_AD_VIDA = 900

def _ad_d(d):
    g = d.setdefault("adivina", {})
    g.setdefault("j", {})
    return g

def _ad_jug(d, cid, nombre=""):
    j = _ad_d(d)["j"].setdefault(str(cid), {"pts": 0, "sem": {}, "rondas": 0, "dia": "", "hoy": 0, "racha": 0, "ult": "", "vistas": [], "nom": "", "ronda": None})
    if nombre:
        j["nom"] = str(nombre)[:14]
    return j

def _ad_hoy():
    return _a_ahora().strftime("%Y-%m-%d")

def _ad_semana():
    y, w, _ = _a_ahora().isocalendar()
    return "%d-W%02d" % (y, w)

def _ad_eur(v):
    return ("%.2f" % float(v)).replace(".", ",") + " €"

def _ad_candidatas(d, j):
    lim = time.time() - 14 * 86400
    of = [o for o in (_mi_d(d).get("of") or []) if o.get("ts", 0) >= lim and (o.get("ahora") or 0) >= 5 and o.get("asin") and o["asin"] not in j["vistas"][-8:]]
    _ad_rnd.shuffle(of)
    return of[:8]

def _ad_foto_bytes(asin):
    img = _cn_foto(asin)
    if img is None:
        return None
    img = img.convert("RGB")
    img.thumbnail((1000, 1000))
    buf = _cn_io.BytesIO()
    img.save(buf, "JPEG", quality=90)
    return buf.getvalue()

def _ad_ronda(d, cid, nombre):
    try:
        j = _ad_jug(d, cid, nombre)
        hoy = _ad_hoy()
        if j["dia"] != hoy:
            j["dia"], j["hoy"] = hoy, 0
        if j["hoy"] >= _AD_MAX_DIA:
            enviar(cid, "\U0001f3af Hoy ya has jugado %d rondas. Vuelve mañana y sigue tu racha. Mira el /adivina ranking." % _AD_MAX_DIA); return
        for o in _ad_candidatas(d, j):
            datos = _ad_foto_bytes(o["asin"])
            if not datos:
                continue
            j["ronda"] = {"asin": o["asin"], "ahora": float(o["ahora"]), "antes": float(o.get("antes") or 0), "pct": o.get("pct"), "t": str(o.get("t"))[:110], "ts": time.time()}
            j["vistas"] = (j["vistas"] + [o["asin"]])[-30:]
            cap = ("\U0001f3af ADIVINA EL PRECIO\n\n%s\n\n¿Cuánto costaba cuando lo avisó el bot? Escribe el precio en euros (ejemplo: 24,99).\nTienes 15 minutos."
                   % j["ronda"]["t"])[:1000]
            requests.post("https://api.telegram.org/bot%s/sendPhoto" % _vd_token(), data={"chat_id": cid, "caption": cap},
                          files={"photo": ("producto.jpg", datos)}, timeout=60)
            return
        enviar(cid, "\U0001f3af Ahora mismo no tengo ofertas nuevas con foto para jugar. Prueba en un rato.")
    except Exception as e:
        print("error adivina ronda", str(e)[:100], flush=True)
        try: enviar(cid, "No he podido preparar la ronda. Prueba en un rato.")
        except Exception: pass

def _ad_teclado():
    return json.dumps({"inline_keyboard": [[{"text": "\U0001f501 Otra ronda", "callback_data": "adv_otra"},
                                            {"text": "\U0001f3c6 Ranking", "callback_data": "adv_rank"}]]})

def _ad_responder(d, cid, valor, nombre):
    j = _ad_jug(d, cid, nombre)
    r = j["ronda"]
    j["ronda"] = None
    real = r["ahora"]
    err = abs(valor - real) / real
    pts = max(0, 100 - int(round(err * 200)))
    hoy = _ad_hoy()
    ayer = (_a_ahora() - __import__("datetime").timedelta(days=1)).strftime("%Y-%m-%d")
    if j["ult"] != hoy:
        j["racha"] = j["racha"] + 1 if j["ult"] == ayer else 1
        j["ult"] = hoy
    bonus = min(50, 10 * (j["racha"] - 1)) if pts >= 50 else 0
    total = pts + bonus
    j["pts"] += total
    j["rondas"] += 1
    j["hoy"] += 1
    s = _ad_semana()
    j["sem"] = {s: j["sem"].get(s, 0) + total}
    if pts >= 95: veredicto = "\U0001f3af ¡Clavado!"
    elif pts >= 75: veredicto = "\U0001f525 ¡Muy cerca!"
    elif pts >= 40: veredicto = "\U0001f44d Nada mal."
    else: veredicto = "\U0001f605 Lejos esta vez."
    txt = "%s\n\nPrecio en el aviso: %s%s\nTu respuesta: %s\n\n+%d puntos%s\nTotal esta semana: %d · Racha: %d día%s" % (
        veredicto, _ad_eur(real), (" (antes %s, -%s%%)" % (_ad_eur(r["antes"]), r["pct"])) if r["antes"] > real and r["pct"] else "",
        _ad_eur(valor), pts, (" + %d de racha" % bonus) if bonus else "", j["sem"][s], j["racha"], "" if j["racha"] == 1 else "s")
    txt += "\n\n(Precio del momento del aviso; puede haber cambiado.)"
    enviar(cid, txt, _ad_teclado())

def _ad_ranking(d, cid):
    s = _ad_semana()
    js = [(c, v) for c, v in _ad_d(d)["j"].items() if v["sem"].get(s, 0) > 0]
    js.sort(key=lambda x: -x[1]["sem"][s])
    if not js:
        enviar(cid, "\U0001f3c6 RANKING SEMANAL\n\nTodavía nadie ha puntuado esta semana. ¡Sé el primero con /adivina!"); return
    medallas = ["\U0001f947", "\U0001f948", "\U0001f949"]
    lin = ["%s %s · %d pts" % (medallas[i] if i < 3 else "%d." % (i + 1), v["nom"] or "Jugador", v["sem"][s]) for i, (c, v) in enumerate(js[:10])]
    pos = next((i + 1 for i, (c, v) in enumerate(js) if c == str(cid)), None)
    pie = ("\n\nTu posición: %d de %d" % (pos, len(js))) if pos else "\n\nAún no estás en el ranking: juega con /adivina."
    enviar(cid, "\U0001f3c6 RANKING SEMANAL · Adivina el precio\n\n" + "\n".join(lin) + pie + "\n\nSe reinicia cada lunes.")

def _ad_lanzar(d, cid, nombre):
    j = _ad_jug(d, cid, nombre)
    if j.get("ronda") and time.time() - j["ronda"]["ts"] < 60:
        enviar(cid, "Ya tienes una ronda en marcha: escribe tu precio."); return
    _vd_th.Thread(target=_ad_ronda, args=(d, cid, nombre), daemon=True).start()

_ad_tec_orig = teclado_menu
def teclado_menu():
    try:
        kb = json.loads(_ad_tec_orig())
        filas = kb["inline_keyboard"]
        filas.insert(max(0, len(filas) - 1), [{"text": "\U0001f3af Adivina el precio", "callback_data": "m_adivina"}])
        return json.dumps(kb)
    except Exception as e:
        print("error menu adivina", str(e)[:80], flush=True)
        return _ad_tec_orig()

_ad_hook_menu_orig = hook_menu
def hook_menu(d, u):
    try:
        cq = u.get("callback_query")
        dato = str((cq or {}).get("data") or "")
        if cq and dato in ("m_adivina", "adv_otra", "adv_rank"):
            try:
                requests.post(API + "/answerCallbackQuery", data={"callback_query_id": cq["id"]}, timeout=10)
            except Exception:
                pass
            cid = cq["from"]["id"]
            if dato == "adv_rank":
                _ad_ranking(d, cid)
            else:
                _ad_lanzar(d, cid, cq["from"].get("first_name", ""))
            return True
    except Exception as e:
        print("error boton adivina", str(e)[:100], flush=True)
    return _ad_hook_menu_orig(d, u)

_ad_hook_orig = hook_anuncios_pago
def hook_anuncios_pago(d, u):
    try:
        m = u.get("message")
        t = ((m.get("text") or "") if m else "").strip()
        if m and t:
            cid = m["chat"]["id"]
            nombre = (m.get("from") or {}).get("first_name", "")
            prim = t.split()[0].lower().split("@")[0]
            if prim == "/adivina":
                arg = (t.split() + [""])[1].lower()
                if arg == "ranking":
                    _ad_ranking(d, cid)
                else:
                    _ad_lanzar(d, cid, nombre)
                return True
            j = _ad_d(d)["j"].get(str(cid))
            if j and j.get("ronda") and re.match(r"^\d{1,6}([.,]\d{1,2})?\s*(€|eur|euros)?$", t.lower()):
                if time.time() - j["ronda"]["ts"] <= _AD_VIDA:
                    _ad_responder(d, cid, float(re.match(r"^\d{1,6}([.,]\d{1,2})?", t).group(0).replace(",", ".")), nombre)
                    return True
                j["ronda"] = None
    except Exception as e:
        print("error hook adivina", str(e)[:100], flush=True)
    return _ad_hook_orig(d, u)
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_adivina_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: juego /adivina (Adivina el precio) con boton en el menu, ranking semanal y racha.")
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato   y luego /autotest")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
