import re, shutil, time, sys

RUTA = "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()

if "def revisar_keepa(d):" in src:
    print("Ya estaba aplicado. No hago nada.")
    sys.exit(0)

def cambiar(viejo, nuevo):
    global src
    if src.count(viejo) != 1:
        print("ABORTO: ancla encontrada", src.count(viejo), "veces:", repr(viejo[:50]))
        sys.exit(1)
    src = src.replace(viejo, nuevo)

BLOQUE = '''KEEPA_KEY = os.environ.get("KEEPA_KEY", "")
KEEPA_SOLO = os.environ.get("KEEPA_SOLO", "") == "1"
KEEPA_MAX_POR_CICLO = 5

def revisar_keepa(d):
    import json as _json
    if not KEEPA_KEY:
        return 0
    sel = {"page": 0, "domainId": 9, "priceTypes": [0, 1],
           "deltaPercentRange": [MIN_GUARDAR, 100], "dateRange": 0,
           "isRangeEnabled": True, "sortType": 4}
    r = requests.get("https://api.keepa.com/deal",
                     params={"key": KEEPA_KEY, "selection": _json.dumps(sel)}, timeout=30)
    if r.status_code != 200:
        print("keepa HTTP", r.status_code, flush=True)
        return 0
    j = r.json()
    if j.get("error"):
        print("keepa error", str(j["error"])[:200], flush=True)
        return 0
    lista = (j.get("deals") or {}).get("dr") or []
    nuevos = 0
    for dl in lista:
        if nuevos >= KEEPA_MAX_POR_CICLO:
            break
        try:
            asin = dl.get("asin") or ""
            mejor = None
            for t in (0, 1):
                try:
                    cur = int(dl["current"][t])
                    pct = abs(int(dl["deltaPercent"][0][t]))
                except Exception:
                    continue
                if cur > 0 and (mejor is None or pct > mejor[0]):
                    mejor = (pct, cur)
            if not asin or not mejor:
                continue
            dsc, cents = mejor
            if dsc < MIN_GUARDAR or dsc > 95:
                continue
            clave = "keepa:%s:%s" % (asin, cents)
            if clave in d["seen"]:
                continue
            title = (dl.get("title") or asin).strip()
            url = ("https://www.amazon.es/dp/%s?tag=%s" % (asin, TAG)) if TAG else ("https://www.amazon.es/dp/%s" % asin)
            d["seen"][clave] = int(time.time())
            item = {"t": "%s - %.2f EUR" % (title[:120], cents / 100.0), "u": url, "d": dsc,
                    "ts": int(time.time()), "libre": False}
            d["recent"].append(item)
            d["recent"] = d["recent"][-30:]
            for cid, u in list(d["users"].items()):
                if es_apoyante(d, cid) and pasa_filtros(d, cid, u, dsc, title):
                    enviar_aviso(d, cid, item)
            nuevos += 1
        except Exception as e:
            print("error keepa item", e, flush=True)
    print("keepa tokens:", j.get("tokensLeft"), flush=True)
    return nuevos

def revisar_feed(d):
    try:
        n = revisar_keepa(d)
        print("keepa ok, nuevos:", n, flush=True)
    except Exception as e:
        print("keepa fallo:", e, flush=True)
    if not (KEEPA_SOLO and KEEPA_KEY):
        revisar_chollometro(d)

def revisar_chollometro(d):
'''

cambiar("def revisar_feed(d):\n", BLOQUE)

try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e)
    sys.exit(1)

copia = RUTA + ".bak_keepa_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
