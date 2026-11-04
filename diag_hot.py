# Solo lectura: cuantos productos devuelve hotproduct.query y que descuentos traen. No toca el bot.
import hashlib, hmac, json, sys, time
import requests
ENV = "/opt/chivato/aliexpress.env"
URL = "https://api-sg.aliexpress.com/sync"
c = {}
for l in open(ENV, encoding="utf-8"):
    if "=" in l:
        k, v = l.rstrip("\n").split("=", 1); c[k.strip()] = v.strip()
def api(m, extra):
    p = {"app_key": c["ALI_APP_KEY"], "method": m, "timestamp": str(int(time.time() * 1000)), "sign_method": "sha256", "format": "json", "v": "2.0"}
    p.update(extra)
    base = "".join(k + str(p[k]) for k in sorted(p))
    p["sign"] = hmac.new(c["ALI_APP_SECRET"].encode(), base.encode(), hashlib.sha256).hexdigest().upper()
    return requests.post(URL, data=p, timeout=30).json()
def num(v):
    try: return float(str(v).replace("%", "").replace(",", "."))
    except Exception: return None
for kw in ("teclado mecanico", "auriculares bluetooth", "smartwatch"):
    for met in ("aliexpress.affiliate.hotproduct.query", "aliexpress.affiliate.product.query"):
        j = api(met, {"keywords": kw, "page_size": "50", "page_no": "1", "ship_to_country": "ES", "target_currency": "EUR",
                      "target_language": "ES", "tracking_id": c["ALI_TRACKING_ID"]})
        r = list(j.values())[0].get("resp_result", {}).get("result", {}) if j else {}
        ps = (r.get("products") or {}).get("product") or []
        pcts = []
        for p in ps:
            a = num(p.get("target_app_sale_price") or p.get("app_sale_price")); b = num(p.get("target_original_price") or p.get("original_price"))
            pcts.append(int(round((1 - a / b) * 100)) if a and b and b > a else 0)
        print("%-24s %-9s productos=%d con_descuento=%d >=50%%=%d max=%d" % (kw, "HOT" if "hot" in met else "QUERY", len(ps), sum(1 for x in pcts if x > 0), sum(1 for x in pcts if x >= 50), max(pcts) if pcts else 0))
