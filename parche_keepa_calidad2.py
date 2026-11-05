import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- KEEPACALIDAD2 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- KEEPACALIDAD1 ---" not in src:
    print("ABORTO: primero hay que tener aplicado parche_keepa_calidad1.py"); sys.exit(1)
for n in ("def _kq_revisar(", "_kp_orig", "def _cat_aprender(", "def es_apoyante(", "def pasa_filtros(", "def enviar_aviso("):
    if n not in src:
        print("ABORTO: falta", n); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''
# --- KEEPACALIDAD2 ---
# Mejora de la consulta de Keepa: (1) sello de minimo historico y (2) no repetir productos.
# - Minimo historico: una consulta extra con isLowest (cada 10 min como mucho). Si falla, no se pone sello.
# - No repetir: el mismo producto no se vuelve a avisar en 24 h salvo que baje otro 10 %; y las variantes
#   (mismo titulo en las 4 primeras palabras y precio parecido, +-20 %) se avisan una sola vez en 48 h.
_KQ2_VENTANA = 48 * 3600
_KQ2_MIN_CACHE = {"ts": 0, "asins": set()}

def _kq2_clave_titulo(t):
    import re as _kq2_re, unicodedata as _kq2_ud
    s = _kq2_ud.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return " ".join(_kq2_re.findall(r"[a-z0-9]+", s)[:4])

def _kq2_sel(pag):
    return {"page": pag, "domainId": 9, "priceTypes": [0], "isRangeEnabled": True,
            "isFilterEnabled": True, "minRating": 40, "hasReviews": True,
            "salesRankRange": [1, _KQ_RANK_MAX], "dateRange": 3,
            "deltaPercentRange": [MIN_GUARDAR, _KQ_PCT_MAX],
            "currentRange": [_KQ_PRECIO_MIN, 200000],
            "deltaRange": [_KQ_AHORRO_MIN, 200000], "sortType": 2}

def _kq2_minimos():
    ahora = time.time()
    if ahora - _KQ2_MIN_CACHE["ts"] < 600:
        return _KQ2_MIN_CACHE["asins"]
    _KQ2_MIN_CACHE["ts"] = ahora
    asins = set()
    try:
        import json as _kq2_json
        sel = _kq2_sel(0)
        sel["isLowest"] = True
        r = requests.get("https://api.keepa.com/deal",
                         params={"key": KEEPA_KEY, "selection": _kq2_json.dumps(sel)}, timeout=30)
        if r.status_code == 200:
            j = r.json()
            for x in ((j.get("deals") or {}).get("dr") or []):
                if x.get("asin"):
                    asins.add(x["asin"])
        else:
            print("keepa minimos HTTP", r.status_code, flush=True)
    except Exception as e:
        print("keepa minimos error", str(e)[:100], flush=True)
    _KQ2_MIN_CACHE["asins"] = asins
    return asins

def _kq2_revisar(d):
    import json as _kq2_json
    if not KEEPA_KEY:
        return 0
    r = requests.get("https://api.keepa.com/deal",
                     params={"key": KEEPA_KEY, "selection": _kq2_json.dumps(_kq2_sel(_KP_PAG))}, timeout=30)
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
    minimos = _kq2_minimos()
    vis = d.setdefault("kq_vistos", {})
    ahora = int(time.time())
    for k in [k for k, v in vis.items() if ahora - v.get("ts", 0) > 3 * 86400]:
        vis.pop(k, None)
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
            prev = vis.get(asin)
            if prev and ahora - prev.get("ts", 0) < 24 * 3600 and cents > prev.get("p", 0) * 0.9:
                continue
            title = (dl.get("title") or asin).strip()
            tk = _kq2_clave_titulo(title)
            dup = False
            if tk:
                for a2, v in vis.items():
                    if a2 != asin and v.get("k") == tk and ahora - v.get("ts", 0) < _KQ2_VENTANA \
                            and abs(cents - v.get("p", 0)) <= 0.2 * v.get("p", 1):
                        dup = True
                        break
            if dup:
                continue
            url = ("https://www.amazon.es/dp/%s?tag=%s" % (asin, TAG)) if TAG else ("https://www.amazon.es/dp/%s" % asin)
            d["seen"][clave] = ahora
            vis[asin] = {"p": cents, "ts": ahora, "k": tk}
            sello = " · \U0001f3c6 MÍNIMO HISTÓRICO" if asin in minimos else ""
            item = {"t": "%s - %.2f EUR%s" % (title[:120], cents / 100.0, sello), "u": url, "d": dsc,
                    "c": str(dl.get("rootCat") or ""), "ts": ahora, "libre": False}
            d["recent"].append(item)
            d["recent"] = d["recent"][-30:]
            for cid, u in list(d["users"].items()):
                if es_apoyante(d, cid) and pasa_filtros(d, cid, u, dsc, title):
                    enviar_aviso(d, cid, item)
            nuevos += 1
        except Exception as e:
            print("error keepa calidad item", str(e)[:100], flush=True)
    print("keepa calidad tokens:", j.get("tokensLeft"), "nuevos:", nuevos, "minimos:", len(minimos), flush=True)
    return nuevos

_kp_orig = _kq2_revisar
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: error de sintaxis", e); sys.exit(1)
cp = RUTA + ".bak_keepacalidad2_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy2(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: sello de minimo historico y sin ofertas repetidas.")
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato")
print("Deshacer: cp %s %s && sudo systemctl restart chivato" % (cp, RUTA))
