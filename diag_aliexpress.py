# Solo lectura: prueba la conexion con la API de afiliados de AliExpress. No toca el bot. No imprime el secreto.
import hashlib, hmac, json, sys, time
import requests
ENV = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/aliexpress.env"
URL = "https://api-sg.aliexpress.com/sync"

def cargar():
    d = {}
    for l in open(ENV, encoding="utf-8"):
        if "=" in l:
            k, v = l.rstrip("\n").split("=", 1); d[k.strip()] = v.strip()
    return d

def firmar(params, secret, metodo):
    base = "".join(k + str(params[k]) for k in sorted(params))
    if metodo == "sha256":
        return hmac.new(secret.encode(), base.encode(), hashlib.sha256).hexdigest().upper()
    return hashlib.md5((secret + base + secret).encode()).hexdigest().upper()

def llamar(cfg, metodo_api, extra, firma):
    p = {"app_key": cfg["ALI_APP_KEY"], "method": metodo_api, "timestamp": str(int(time.time() * 1000)),
         "sign_method": firma, "format": "json", "v": "2.0"}
    p.update(extra)
    p["sign"] = firmar({k: v for k, v in p.items() if k != "sign"}, cfg["ALI_APP_SECRET"], firma)
    r = requests.post(URL, data=p, timeout=30)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, {"texto": r.text[:300]}

def corto(j, n=500):
    s = json.dumps(j, ensure_ascii=False)
    return s if len(s) <= n else s[:n] + "…"

def main():
    cfg = cargar()
    for k in ("ALI_APP_KEY", "ALI_APP_SECRET", "ALI_TRACKING_ID"):
        if not cfg.get(k):
            print("FALTA", k, "en", ENV); return
    print("AppKey:", cfg["ALI_APP_KEY"], "| TrackingID:", cfg["ALI_TRACKING_ID"], "| secreto: %d caracteres" % len(cfg["ALI_APP_SECRET"]))
    firma_ok = None
    for firma in ("sha256", "md5"):
        st, j = llamar(cfg, "aliexpress.affiliate.link.generate",
                       {"promotion_link_type": "0", "source_values": "https://www.aliexpress.com/item/1005004757833857.html",
                        "tracking_id": cfg["ALI_TRACKING_ID"]}, firma)
        txt = json.dumps(j)
        print("\n[link.generate firma=%s] http %s" % (firma, st)); print(corto(j))
        if "promotion_link" in txt:
            firma_ok = firma; print("=> FUNCIONA con firma", firma); break
        if "ignature" not in txt and "sign" not in txt.lower():
            firma_ok = firma; break
    if not firma_ok:
        print("\nNinguna firma ha sido aceptada. Revisa AppKey y secreto."); return
    st, j = llamar(cfg, "aliexpress.affiliate.product.query",
                   {"keywords": "auriculares bluetooth", "page_size": "3", "page_no": "1", "ship_to_country": "ES",
                    "target_currency": "EUR", "target_language": "ES", "tracking_id": cfg["ALI_TRACKING_ID"]}, firma_ok)
    print("\n[product.query] http %s" % st); print(corto(j, 900))
    st, j = llamar(cfg, "aliexpress.affiliate.hotproduct.query",
                   {"keywords": "auriculares", "page_size": "3", "ship_to_country": "ES", "target_currency": "EUR",
                    "target_language": "ES", "tracking_id": cfg["ALI_TRACKING_ID"]}, firma_ok)
    print("\n[hotproduct.query (Advanced API)] http %s" % st); print(corto(j, 600))
    print("\nFIN. Mandame captura de este resultado.")

main()
