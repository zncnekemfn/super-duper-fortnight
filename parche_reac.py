import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()

if "# --- REAC ---" in src:
    print("Ya estaba aplicado. No hago nada.")
    sys.exit(0)
if "def _a_ahora():" not in src:
    print("ABORTO: falta parche_A.py"); sys.exit(1)

def unico(patron, fn, nombre):
    global src
    n = len(re.findall(patron, src, re.M))
    if n != 1:
        print("ABORTO: ancla '%s' encontrada %d veces" % (nombre, n)); sys.exit(1)
    src = re.sub(patron, fn, src, count=1, flags=re.M)

FUNC = r'''# --- REAC ---
REAC_CADA = 900
REAC_RANGO = 2
REAC_MAX_CICLO = 4
REAC_TIPOS = ((9, "AMAZON WAREHOUSE (segunda mano revisada)"), (6, "REACONDICIONADO"))
REAC_COOL = 5 * 86400

def _rc_d(d):
    c = d.setdefault("reac", {})
    c.setdefault("on", True)
    c.setdefault("pct", 35)
    c.setdefault("min", 30)
    c.setdefault("canal", False)
    c.setdefault("vistos", {})
    c.setdefault("tits", {})
    c.setdefault("init", {})
    c.setdefault("ult", 0)
    c.setdefault("n", 0)
    return c

def _rc_clave(t):
    t = re.sub(r"[^a-z]", "", (t or "").lower())
    return t[:22] if len(t) >= 12 else ""

def _rc_consulta(t, pct):
    import json as _jj
    sel = {"page": 0, "domainId": 9, "priceTypes": [t], "deltaPercentRange": [pct, 100],
           "dateRange": REAC_RANGO, "isRangeEnabled": True, "sortType": 4}
    r = requests.get("https://api.keepa.com/deal", params={"key": KEEPA_KEY, "selection": _jj.dumps(sel)}, timeout=30)
    if r.status_code != 200:
        print("keepa reac HTTP", r.status_code, flush=True)
        return None
    j = r.json()
    if j.get("error"):
        print("keepa reac error", str(j["error"])[:120], flush=True)
        return None
    return j

def _rc_destinos(d):
    out = []
    en_sil = globals().get("_a_en_silencio")
    for cid, us in list(d["users"].items()):
        if cid == ADMIN or not us or not us.get("reac") or not autorizado(d, cid):
            continue
        if any(us.get(k) for k in ("parado", "pausa", "pausado", "off", "stop")):
            continue
        if en_sil and en_sil(us):
            continue
        out.append(cid)
    return out

def _rc_tarea(d):
    c = _rc_d(d)
    if not c["on"] or not KEEPA_KEY:
        return
    ahora = time.time()
    if ahora - c["ult"] < REAC_CADA:
        return
    c["ult"] = ahora
    if d.get("a_tok", 999) < 150:
        return
    for k in [k for k, v in c["vistos"].items() if ahora - v > REAC_COOL]:
        c["vistos"].pop(k, None)
    for k in [k for k, v in c["tits"].items() if ahora - v > 86400]:
        c["tits"].pop(k, None)
    envio = globals().get("_enviar_aviso_orig") or enviar_aviso
    enviados = 0
    for t, etiqueta in REAC_TIPOS:
        j = _rc_consulta(t, c["pct"])
        if not j:
            continue
        primera = not c["init"].get(str(t))
        for dl in ((j.get("deals") or {}).get("dr") or []):
            try:
                asin = dl.get("asin") or ""
                cur = int(dl["current"][t])
                avg = int(dl["avg"][REAC_RANGO][t])
                pct = abs(int(dl["deltaPercent"][REAC_RANGO][t]))
            except Exception:
                continue
            if not asin or cur < 500 or avg <= 0:
                continue
            if avg < c["min"] * 100 or avg > 150000 or pct < c["pct"] or pct > 90:
                continue
            k = "%s:%d" % (asin, t)
            tk = _rc_clave(dl.get("title"))
            if k in c["vistos"] or (tk and tk in c["tits"]):
                continue
            if primera:
                c["vistos"][k] = int(ahora)
                continue
            if enviados >= REAC_MAX_CICLO:
                continue
            c["vistos"][k] = int(ahora)
            if tk:
                c["tits"][tk] = int(ahora)
            title = (dl.get("title") or asin).strip()
            url = ("https://www.amazon.es/dp/%s?tag=%s" % (asin, TAG)) if TAG else ("https://www.amazon.es/dp/%s" % asin)
            item = {"t": "♻️ %s\n%s - %.2f EUR (antes ~%.2f EUR)\n⚠️ Revisa la condición y la garantía antes de comprar." % (
                        etiqueta, title[:100], cur / 100.0, avg / 100.0),
                    "u": url, "d": pct, "c": "", "ts": int(ahora), "libre": True}
            c["n"] += 1
            enviados += 1
            f = globals().get("_cp_enviar")
            if c["canal"] and f:
                try:
                    f(d, "%s\n%s\n\n(%s)" % (item["t"], item["u"], AVISO))
                except Exception as ex:
                    print("error reac canal", ex, flush=True)
            for cid in _rc_destinos(d):
                try:
                    envio(d, cid, item)
                except Exception as ex:
                    print("error reac envio", ex, flush=True)
                time.sleep(0.05)
        c["init"][str(t)] = 1
    print("keepa reacondicionados ok, avisos:", enviados, flush=True)

def reac_cmd(d, cid, args):
    c = _rc_d(d)
    us = d["users"].get(cid)
    a = args[0].lower() if args else ""
    if cid == ADMIN and a in ("pct", "min") and len(args) > 1 and args[1].isdigit():
        v = int(args[1])
        if a == "pct" and 20 <= v <= 80:
            c["pct"] = v
        elif a == "min" and 5 <= v <= 1000:
            c["min"] = v
        else:
            enviar(cid, "Valor fuera de rango (pct 20-80, min 5-1000).")
            return
        c["init"] = {}
        a = "estado"
    if cid == ADMIN and a == "canal":
        if len(args) > 1 and args[1].lower() in ("on", "off"):
            c["canal"] = (args[1].lower() == "on")
        enviar(cid, "♻️ Reacondicionados en el canal público: %s\n/reacond canal on · /reacond canal off" % ("ACTIVADO" if c["canal"] else "APAGADO"))
        return
    if cid == ADMIN and a in ("estado", "admin"):
        enviar(cid, "♻️ REACONDICIONADOS (admin)\nBúsqueda: %s\nBajada mínima: %d%% · Precio habitual mínimo: %d EUR\nCanal: %s\nAvisos enviados: %d\n"
                    "Usuarios activados: %d\n/reacond pct 35 · /reacond min 30 · /reacond canal on|off" % (
                    "ON" if c["on"] else "OFF", c["pct"], c["min"], "ON" if c["canal"] else "OFF", c["n"],
                    len([1 for u in d["users"].values() if u and u.get("reac")])))
        return
    if a in ("on", "off"):
        if us is None:
            enviar(cid, "Primero activa los avisos con /suscribir.")
            return
        us["reac"] = (a == "on")
        enviar(cid, "♻️ Avisos de reacondicionados y Amazon Warehouse: %s" % (
            "ACTIVADOS. Te aviso de ofertas de segunda mano revisada con buena rebaja." if us["reac"] else "DESACTIVADOS."))
        return
    enviar(cid, "♻️ REACONDICIONADOS Y AMAZON WAREHOUSE\n\nAvisos: %s\n/reacond on · /reacond off\n\n"
                "Productos reacondicionados o de segunda mano revisados por Amazon con una rebaja fuerte frente a su precio habitual. "
                "Fíjate siempre en la condición y en la garantía antes de comprar." % ("ACTIVADOS" if (us or {}).get("reac") else "DESACTIVADOS"))

'''

TAIL = r'''# --- REAC (tarea) ---
_pu_orig_rc = procesar_updates
def procesar_updates(d, *a, **k):
    try:
        _rc_tarea(d)
    except Exception as e:
        print("error tarea reacondicionados", e, flush=True)
    return _pu_orig_rc(d, *a, **k)

AYUDA = AYUDA + "\n\n♻️ /reacond on - ofertas de reacondicionados y Amazon Warehouse"

'''

unico(r'^def comando\(d, cid, texto\):\n', lambda m: FUNC + m.group(0), "comando")
unico(r'^    elif cmd in \("/propina", "/premium"\):\n',
      lambda m: '    elif cmd in ("/reacond", "/reacondicionados"):\n        reac_cmd(d, cid, args)\n' + m.group(0), "propina")
unico(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), "main")

try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)

copia = RUTA + ".bak_reac_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
