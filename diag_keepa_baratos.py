import json, os, sys
import requests

def clave():
    k = os.environ.get("KEEPA_KEY", "").strip()
    if k:
        return k
    try:
        for l in open("/opt/chivato/.env", encoding="utf-8"):
            l = l.strip()
            if l.startswith("KEEPA_KEY="):
                return l.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return ""

KEY = clave()
if not KEY:
    print("Sin clave de Keepa"); sys.exit(1)

BASE = {"page": 0, "domainId": 9, "priceTypes": [0], "isRangeEnabled": True, "isFilterEnabled": True,
        "minRating": 40, "hasReviews": True, "salesRankRange": [1, 100000], "dateRange": 3,
        "deltaPercentRange": [30, 70], "currentRange": [1000, 8000], "deltaRange": [500, 200000], "sortType": 2}

def variante(nombre, cambios):
    sel = dict(BASE); sel.update(cambios)
    try:
        r = requests.get("https://api.keepa.com/deal", params={"key": KEY, "selection": json.dumps(sel)}, timeout=40)
    except Exception as e:
        print("\n== %s: error de red %s" % (nombre, str(e)[:80])); return
    print("\n== %s" % nombre)
    if r.status_code != 200:
        print("   HTTP", r.status_code); return
    j = r.json()
    dr = (j.get("deals") or {}).get("dr") or []
    filas = []
    for dl in dr:
        try:
            cur = int((dl.get("current") or [0])[0]); av = dl.get("avg") or []
            m90 = int(av[3][0]) if len(av) > 3 and av[3] else 0
            if cur <= 0 or m90 <= 0:
                continue
            filas.append((int(round(100.0 * (m90 - cur) / m90)), cur, m90, (dl.get("title") or "")[:55]))
        except Exception:
            continue
    ok = [f for f in filas if 30 <= f[0] <= 95 and (f[2] - f[1]) >= 500]
    print("   devueltos: %d | con media 90d: %d | pasan filtro del bot (>=30%% y >=5 EUR): %d" % (len(dr), len(filas), len(ok)))
    for pct, cur, m90, t in ok[:8]:
        print("   -%d%%  %.2f EUR (media %.2f)  %s" % (pct, cur / 100.0, m90 / 100.0, t))
    print("   tokens restantes:", j.get("tokensLeft"))

variante("A) perfil actual del bot (10-80 EUR, rating>=4, ventas<=100k)", {})
variante("B) igual, pero ventas hasta 300k", {"salesRankRange": [1, 300000]})
variante("C) igual, pero valoracion >= 3,5", {"minRating": 35})
variante("D) igual, pero ordenado por % de descuento", {"sortType": 4})
