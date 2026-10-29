import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()

if "# --- MEJORAS A ---" in src:
    print("Ya estaba aplicado. No hago nada.")
    sys.exit(0)

def unico(patron, fn, nombre):
    global src
    n = len(re.findall(patron, src, re.M))
    if n != 1:
        print("ABORTO: ancla '%s' encontrada %d veces" % (nombre, n))
        sys.exit(1)
    src = re.sub(patron, fn, src, count=1, flags=re.M)

def opcional(patron, fn, nombre):
    global src
    n = len(re.findall(patron, src, re.M))
    if n != 1:
        print("AVISO: '%s' encontrado %d veces, no se cambia (no es grave)" % (nombre, n))
        return
    src = re.sub(patron, fn, src, count=1, flags=re.M)

FUNC = r'''# --- MEJORAS A ---
import re
import json
import datetime as _dta

def _a_tz():
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo("Europe/Madrid")
    except Exception:
        return _dta.timezone(_dta.timedelta(hours=1))

def _a_ahora():
    return _dta.datetime.now(_a_tz())

def _a_asin(url):
    m = re.search(r"/dp/([A-Z0-9]{10})", url or "")
    return m.group(1) if m else ""

def _a_precio_cents(texto):
    t = re.sub(r"\(antes[^)]*\)", "", texto or "")
    p = re.findall(r" - (\d+\.\d\d) EUR", t)
    return int(round(float(p[-1]) * 100)) if p else 0

def _a_clave(item):
    return "%s:%s" % (_a_asin(item.get("u")), _a_precio_cents(item.get("t")))

# ---- historico de precios (1 token de Keepa por oferta) ----
def _a_historico(d, item):
    if item.get("hq"):
        return
    item["hq"] = True
    try:
        if not KEEPA_KEY or d.get("a_tok", 999) < 60:
            return
        asin = _a_asin(item.get("u"))
        cur = _a_precio_cents(item.get("t"))
        if not asin or cur <= 0:
            return
        tp = int(item.get("tp", 0))
        r = requests.get("https://api.keepa.com/product",
                         params={"key": KEEPA_KEY, "domain": 9, "asin": asin, "stats": 90, "history": 0}, timeout=20)
        if r.status_code != 200:
            return
        j = r.json()
        if j.get("tokensLeft") is not None:
            d["a_tok"] = j.get("tokensLeft")
        p = (j.get("products") or [None])[0] or {}
        st = p.get("stats") or {}
        mn = ((st.get("min") or [])[tp:tp + 1] or [None])[0]
        mn90 = ((st.get("minInInterval") or [])[tp:tp + 1] or [None])[0]
        av90 = (st.get("avg90") or [])[tp] if len(st.get("avg90") or []) > tp else -1
        partes = []
        if mn and mn[1] and cur <= mn[1] * 1.005:
            partes.append("\U0001f3c6 Mínimo histórico")
        elif mn90 and mn90[1] and cur <= mn90[1] * 1.005:
            partes.append("\U0001f4c9 Mínimo de los últimos 90 días")
        if av90 and av90 > cur > 0:
            partes.append("Media 90 días: %.2f EUR (%d%% menos)" % (av90 / 100.0, round((1 - cur / float(av90)) * 100)))
        if partes:
            item["h"] = "\U0001f4ca " + " · ".join(partes)
    except Exception as e:
        print("error historico", e, flush=True)

# ---- aviso con historico y botones de valoracion ----
def _a_teclado(item):
    asin = _a_asin(item.get("u")) or "x"
    fila = [{"text": "\U0001f44d", "callback_data": "fb_up_" + asin},
            {"text": "\U0001f44e", "callback_data": "fb_dn_" + asin}]
    c = str(item.get("c") or "")
    if c.isdigit():
        fila.append({"text": "\U0001f515 Menos de esto", "callback_data": "fb_no_" + c})
    return json.dumps({"inline_keyboard": [fila]})

def _enviar_aviso_a(d, cid, item):
    h = ("\n" + item["h"]) if item.get("h") else ""
    msg = "\U0001f525 ~-%s%%\n%s%s\n%s\n\n(%s)" % (item["d"], item["t"], h, item["u"], AVISO)
    if enviar(cid, msg, _a_teclado(item)) == 403:
        d["users"].pop(cid, None)
    time.sleep(0.05)

def hook_feedback(d, u):
    cq = u.get("callback_query")
    if not cq or not str(cq.get("data") or "").startswith("fb_"):
        return False
    try:
        cid = str(cq["from"]["id"])
        _, acc, dato = (cq["data"].split("_", 2) + ["", ""])[:3]
        fb = d.setdefault("fb", {"up": 0, "dn": 0, "mal": {}})
        aviso = "Gracias \U0001f64f"
        if acc == "up":
            fb["up"] += 1
            aviso = "Gracias \U0001f44d"
        elif acc == "dn":
            fb["dn"] += 1
            fb["mal"][dato] = fb["mal"].get(dato, 0) + 1
            aviso = "Gracias, lo tendremos en cuenta"
            if len(fb["mal"]) > 200:
                for k in list(fb["mal"].keys())[:-150]:
                    fb["mal"].pop(k, None)
        elif acc == "no":
            us = d["users"].get(cid)
            ids = sorted(set((d.get("cat_nombres") or {}).keys()) | set(d.get("cat_vistas") or []))
            if us is not None and dato:
                sel = list(us.get("cats") or [])
                nuevo = [x for x in sel if x != dato] if sel else [x for x in ids if x != dato]
                if nuevo and (dato in sel or not sel):
                    us["cats"] = nuevo
                    aviso = "Listo: ya no recibirás esa categoría. Cambia esto en /categorias"
                else:
                    aviso = "Es la única categoría que tienes. Usa /categorias para cambiarla"
        try:
            requests.post(API + "/answerCallbackQuery", data={"callback_query_id": cq["id"], "text": aviso}, timeout=10)
            m = cq.get("message") or {}
            requests.post(API + "/editMessageReplyMarkup", data={
                "chat_id": cid, "message_id": m.get("message_id"), "reply_markup": json.dumps({"inline_keyboard": []})}, timeout=10)
        except Exception:
            pass
    except Exception as e:
        print("error feedback", e, flush=True)
    return True

# ---- no molestar ----
def _a_en_silencio(us):
    s = (us or {}).get("sil")
    if not s or len(s) != 2 or s[0] == s[1]:
        return False
    h = _a_ahora().hour
    a, b = s
    return (a <= h < b) if a < b else (h >= a or h < b)

def silencio_cmd(d, cid, args):
    us = d["users"].get(cid)
    if us is None:
        enviar(cid, "Primero activa los avisos con /suscribir.")
        return
    if args and args[0].lower() == "off":
        us.pop("sil", None)
        enviar(cid, "\U0001f514 Modo no molestar desactivado.")
        return
    if len(args) >= 2 and args[0].isdigit() and args[1].isdigit() and 0 <= int(args[0]) <= 23 and 0 <= int(args[1]) <= 23 and args[0] != args[1]:
        us["sil"] = [int(args[0]), int(args[1])]
        enviar(cid, "\U0001f319 Listo: no te avisaré de %02d:00 a %02d:00 (hora de España). Al terminar te envío un resumen de lo mejor que haya salido.\n/silencio off para quitarlo." % (us["sil"][0], us["sil"][1]))
        return
    s = us.get("sil")
    estado = "activado de %02d:00 a %02d:00" % (s[0], s[1]) if s else "desactivado"
    enviar(cid, "\U0001f319 NO MOLESTAR: %s\n\nEjemplo: /silencio 23 8 (de 23:00 a 8:00)\n/silencio off para quitarlo." % estado)

def _a_linea(i, it):
    return "%d. -%s%% %s\n%s" % (i, it.get("d"), (it.get("t") or "")[:90], it.get("u"))

# ---- resumen diario ----
def resumen_cmd(d, cid, args):
    us = d["users"].get(cid)
    if us is None:
        enviar(cid, "Primero activa los avisos con /suscribir.")
        return
    if args and args[0].lower() == "off":
        us.pop("res", None)
        enviar(cid, "\U0001f5de Resumen diario desactivado.")
        return
    if args and args[0].isdigit() and 0 <= int(args[0]) <= 23:
        us["res"] = int(args[0])
        us.pop("res_ult", None)
        enviar(cid, "\U0001f5de Listo: cada día a las %02d:00 (hora de España) te enviaré las 10 mejores ofertas de las últimas 24 horas.\n/resumen off para quitarlo." % us["res"])
        return
    h = us.get("res")
    enviar(cid, "\U0001f5de RESUMEN DIARIO: %s\n\nEjemplo: /resumen 9 (cada día a las 9:00)\n/resumen off para quitarlo."
           % ("a las %02d:00" % h if h is not None else "desactivado"))

def _a_tarea(d):
    ahora = time.time()
    if ahora - d.get("a_ult", 0) < 60:
        return
    d["a_ult"] = ahora
    h = _a_ahora().hour
    hoy_s = _a_ahora().strftime("%Y-%m-%d")
    cola = d.setdefault("sil_cola", {})
    for cid in list(cola.keys()):
        us = d["users"].get(cid)
        if us is None:
            cola.pop(cid, None)
            continue
        if _a_en_silencio(us):
            continue
        todos = cola.pop(cid)
        items = sorted(todos, key=lambda x: -int(x.get("d") or 0))[:5]
        if items:
            enviar(cid, "\U0001f319 Mientras no te molestaba llegaron %d ofertas nuevas. Las mejores:\n\n%s" %
                   (len(todos), "\n\n".join(_a_linea(i + 1, it) for i, it in enumerate(items))))
            time.sleep(0.05)
    top = d.setdefault("dia_top", {})
    for k in [k for k, v in top.items() if ahora - v.get("ts", 0) > 36 * 3600]:
        top.pop(k, None)
    for cid, us in list(d["users"].items()):
        rh = us.get("res")
        if rh is None or rh != h or us.get("res_ult") == hoy_s:
            continue
        us["res_ult"] = hoy_s
        items = sorted([v for v in top.values() if ahora - v.get("ts", 0) <= 24 * 3600], key=lambda x: -int(x.get("d") or 0))[:10]
        if not items:
            continue
        enviar(cid, "\U0001f5de RESUMEN DEL DÍA: las mejores ofertas de las últimas 24 horas\n\n" + "\n\n".join(_a_linea(i + 1, it) for i, it in enumerate(items)))
        time.sleep(0.05)

def feedback_admin(d, cid):
    fb = d.get("fb") or {"up": 0, "dn": 0, "mal": {}}
    tot = fb["up"] + fb["dn"]
    t = "\U0001f44d\U0001f44e VALORACIONES\n\nVotos: %d\n\U0001f44d %d (%d%%)\n\U0001f44e %d" % (
        tot, fb["up"], round(100.0 * fb["up"] / tot) if tot else 0, fb["dn"])
    mal = sorted(fb.get("mal", {}).items(), key=lambda x: -x[1])[:5]
    if mal:
        t += "\n\nMás votadas como malas:\n" + "\n".join("https://www.amazon.es/dp/%s (%d)" % (a, n) for a, n in mal)
    enviar(cid, t)

'''

TAIL = r'''# --- MEJORAS A (envio) ---
_enviar_aviso_orig = _enviar_aviso_a
_enviar_aviso_prev = enviar_aviso

def enviar_aviso(d, cid, item):
    try:
        k = _a_clave(item)
        if k and not item.get("reg"):
            item["reg"] = True
            d.setdefault("dia_top", {})[k] = {"t": item.get("t"), "u": item.get("u"), "d": item.get("d"), "ts": int(time.time())}
        _a_historico(d, item)
        us = d["users"].get(cid) or {}
        if _a_en_silencio(us):
            cola = d.setdefault("sil_cola", {}).setdefault(cid, [])
            cola.append({"t": item.get("t"), "u": item.get("u"), "d": item.get("d")})
            del cola[:-15]
            return
    except Exception as e:
        print("error mejoras A", e, flush=True)
    return _enviar_aviso_prev(d, cid, item)

_pu_orig_a = procesar_updates
def procesar_updates(d, *a, **k):
    try:
        _a_tarea(d)
    except Exception as e:
        print("error tarea A", e, flush=True)
    return _pu_orig_a(d, *a, **k)

AYUDA = AYUDA + ("\n\n\U0001f319 /silencio 23 8 - no molestar de 23:00 a 8:00 (off para quitarlo)"
                 "\n\U0001f5de /resumen 9 - resumen diario a las 9:00 (off para quitarlo)")

'''

unico(r'^def comando\(d, cid, texto\):\n', lambda m: FUNC + m.group(0), "comando")
unico(r'^    elif cmd in \("/propina", "/premium"\):\n',
      lambda m: ('    elif cmd == "/silencio":\n        silencio_cmd(d, cid, args)\n'
                 '    elif cmd == "/resumen":\n        resumen_cmd(d, cid, args)\n'
                 '    elif cmd == "/valoraciones" and cid == ADMIN:\n        feedback_admin(d, cid)\n') + m.group(0), "propina")
unico(r'^([ \t]+)if hook_anuncios_pago\(d, u\):\n',
      lambda m: m.group(1) + 'if hook_feedback(d, u):\n' + m.group(1) + '    continue\n' + m.group(0), "hook")
unico(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), "main")
opcional(r'"u": url, "d": pct, "c": "", "ts": int\(ahora\), "libre": True\}',
         lambda m: '"u": url, "d": pct, "c": "", "ts": int(ahora), "libre": True, "tp": t}', "tipo precio errores")

try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)

copia = RUTA + ".bak_A_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
