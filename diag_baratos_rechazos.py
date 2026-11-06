import json, os, re, sys, time, unicodedata
import requests

DATA = "/opt/chivato/data.json"

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
try:
    d = json.load(open(DATA, encoding="utf-8"))
except Exception as e:
    print("No puedo leer", DATA, str(e)[:80]); sys.exit(1)

seen = d.get("seen") or {}
vis = dict(d.get("kq_vistos") or {})
print("Memoria del bot: ofertas vistas =", len(seen), "| productos recientes (kq_vistos) =", len(vis))

SEL = {"page": 0, "domainId": 9, "priceTypes": [0], "isRangeEnabled": True, "isFilterEnabled": True,
       "minRating": 40, "hasReviews": True, "salesRankRange": [1, 100000], "dateRange": 3,
       "deltaPercentRange": [30, 70], "currentRange": [1000, 8000], "deltaRange": [500, 200000], "sortType": 2}
r = requests.get("https://api.keepa.com/deal", params={"key": KEY, "selection": json.dumps(SEL)}, timeout=40)
if r.status_code != 200:
    print("Keepa HTTP", r.status_code); sys.exit(1)
lista = (r.json().get("deals") or {}).get("dr") or []
print("Keepa devuelve", len(lista), "ofertas baratas (10-80 EUR)\n")

def ctit(t):
    s = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return " ".join(re.findall(r"[a-z0-9]+", s)[:4])

ahora = int(time.time())
cuenta = {}
ejemplos = {}
def anota(motivo, titulo):
    cuenta[motivo] = cuenta.get(motivo, 0) + 1
    ejemplos.setdefault(motivo, [])
    if len(ejemplos[motivo]) < 3:
        ejemplos[motivo].append((titulo or "")[:60])

for dl in lista:
    try:
        asin = dl.get("asin") or ""
        cents = int((dl.get("current") or [0])[0])
        av = dl.get("avg") or []
        title = (dl.get("title") or asin).strip()
        if len(av) < 4 or not av[3] or not asin or cents <= 0 or int(av[3][0]) <= 0:
            anota("sin media de 90 dias", title); continue
        m90 = int(av[3][0])
        dsc = int(round(100.0 * (m90 - cents) / m90))
        if dsc < 30 or dsc > 95 or (m90 - cents) < 500:
            anota("fuera del filtro de descuento/ahorro", title); continue
        if "keepa:%s:%s" % (asin, cents) in seen:
            anota("YA VISTA con ese mismo precio", title); continue
        prev = vis.get(asin)
        if prev and ahora - prev.get("ts", 0) < 24 * 3600 and cents > prev.get("p", 0) * 0.9:
            anota("mismo producto avisado hace menos de 24 h", title); continue
        tk = ctit(title)
        dup = False
        if tk:
            for a2, v in vis.items():
                if a2 != asin and v.get("k") == tk and ahora - v.get("ts", 0) < 48 * 3600 and abs(cents - v.get("p", 0)) <= 0.2 * max(v.get("p", 1), 1):
                    dup = True; break
        if dup:
            anota("variante parecida ya avisada (48 h)", title); continue
        anota("PASARIA (aviso nuevo)", title)
        vis[asin] = {"p": cents, "ts": ahora, "k": tk}
    except Exception as e:
        anota("error", str(e)[:40])

print("Resultado, oferta por oferta:")
for m, n in sorted(cuenta.items(), key=lambda x: -x[1]):
    print("  %3d  %s" % (n, m))
    for t in ejemplos[m]:
        print("         ej: " + t)
