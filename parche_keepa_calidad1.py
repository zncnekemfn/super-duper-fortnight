import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- KEEPACALIDAD1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("def revisar_keepa(", "_kp_orig", "def _cat_aprender(", "def es_apoyante(", "def pasa_filtros(", "def enviar_aviso("):
    if n not in src:
        print("ABORTO: falta", n); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''
# --- KEEPACALIDAD1 ---
# Nueva consulta a Keepa: descuento frente a la media de 90 dias, ordenado por euros ahorrados,
# con valoracion minima, reseñas, ventas altas y precio minimo. Sustituye a _kp_orig (la consulta
# antigua, que miraba la bajada de las ultimas 24 horas ordenada por porcentaje).
# Se puede afinar cambiando estas cuatro constantes.
_KQ_PRECIO_MIN = 1500    # centimos: precio actual minimo (15 EUR)
_KQ_AHORRO_MIN = 1000    # centimos: ahorro minimo frente a la media de 90 dias (10 EUR)
_KQ_PCT_MAX = 70         # descuento maximo (mas alto suele ser un dato raro de Keepa)
_KQ_RANK_MAX = 100000    # posicion maxima en ventas

def _kq_revisar(d):
    import json as _kq_json
    if not KEEPA_KEY:
        return 0
    sel = {"page": _KP_PAG, "domainId": 9, "priceTypes": [0], "isRangeEnabled": True,
           "isFilterEnabled": True, "minRating": 40, "hasReviews": True,
           "salesRankRange": [1, _KQ_RANK_MAX], "dateRange": 3,
           "deltaPercentRange": [MIN_GUARDAR, _KQ_PCT_MAX],
           "currentRange": [_KQ_PRECIO_MIN, 200000],
           "deltaRange": [_KQ_AHORRO_MIN, 200000], "sortType": 2}
    r = requests.get("https://api.keepa.com/deal",
                     params={"key": KEEPA_KEY, "selection": _kq_json.dumps(sel)}, timeout=30)
    if r.status_code != 200:
        print("keepa calidad HTTP", r.status_code, flush=True)
        return 0
    j = r.json()
    if j.get("error"):
        print("keepa calidad error", str(j["error"])[:200], flush=True)
        return 0
    lista = (j.get("deals") or {}).get("dr") or []
    try:
        _cat_aprender(d, j)
    except Exception as e:
        print("error cat_aprender", str(e)[:80], flush=True)
    nuevos = 0
    for dl in lista:
        if nuevos >= KEEPA_MAX_POR_CICLO:
            break
        try:
            asin = dl.get("asin") or ""
            cents = int((dl.get("current") or [0])[0])
            av = dl.get("avg") or []
            if len(av) < 4 or not av[3]:
                continue
            m90 = int(av[3][0])
            if not asin or cents <= 0 or m90 <= 0:
                continue
            dsc = int(round(100.0 * (m90 - cents) / m90))
            if dsc < MIN_GUARDAR or dsc > 95 or (m90 - cents) < _KQ_AHORRO_MIN:
                continue
            clave = "keepa:%s:%s" % (asin, cents)
            if clave in d["seen"]:
                continue
            title = (dl.get("title") or asin).strip()
            url = ("https://www.amazon.es/dp/%s?tag=%s" % (asin, TAG)) if TAG else ("https://www.amazon.es/dp/%s" % asin)
            d["seen"][clave] = int(time.time())
            item = {"t": "%s - %.2f EUR" % (title[:120], cents / 100.0), "u": url, "d": dsc,
                    "c": str(dl.get("rootCat") or ""), "ts": int(time.time()), "libre": False}
            d["recent"].append(item)
            d["recent"] = d["recent"][-30:]
            for cid, u in list(d["users"].items()):
                if es_apoyante(d, cid) and pasa_filtros(d, cid, u, dsc, title):
                    enviar_aviso(d, cid, item)
            nuevos += 1
        except Exception as e:
            print("error keepa calidad item", str(e)[:100], flush=True)
    print("keepa calidad tokens:", j.get("tokensLeft"), "nuevos:", nuevos, flush=True)
    return nuevos

_kp_orig = _kq_revisar
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: error de sintaxis", e); sys.exit(1)
cp = RUTA + ".bak_keepacalidad1_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy2(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: Keepa ahora busca descuentos reales frente a la media de 90 dias.")
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato")
print("Deshacer: cp %s %s && sudo systemctl restart chivato" % (cp, RUTA))
