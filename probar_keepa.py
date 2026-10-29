import os, json, requests

def cargar_env(path="/opt/chivato/.env"):
    for l in open(path):
        l = l.strip()
        if "=" in l and not l.startswith("#"):
            k, v = l.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

cargar_env()
KEY = os.environ.get("KEEPA_KEY", "")
print("clave cargada:", "si" if KEY else "NO", "longitud:", len(KEY))
sel = {"page": 0, "domainId": 9, "priceTypes": [0, 1],
       "deltaPercentRange": [30, 100], "dateRange": 0,
       "isRangeEnabled": True, "sortType": 4}
try:
    r = requests.get("https://api.keepa.com/deal",
                     params={"key": KEY, "selection": json.dumps(sel)}, timeout=30)
    print("HTTP", r.status_code)
    j = r.json()
    print("error:", str(j.get("error"))[:200])
    print("tokensLeft:", j.get("tokensLeft"), "refillIn:", j.get("refillIn"))
    lista = (j.get("deals") or {}).get("dr") or []
    print("ofertas recibidas:", len(lista))
    for dl in lista[:5]:
        dp = dl.get("deltaPercent")
        print("-", dl.get("asin"), str(dl.get("title"))[:50],
              "| actual:", (dl.get("current") or [])[:2],
              "| dp:", (dp[0][:2] if dp else None),
              "| cat:", dl.get("rootCat"))
except Exception as e:
    print("fallo:", type(e).__name__, str(e)[:200].replace(KEY, "***") if KEY else str(e)[:200])
