import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- VIDEO4 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- VIDEO3 ---" not in src:
    print("ABORTO: primero hay que aplicar parche_video3.py"); sys.exit(1)

TAIL = r'''# --- VIDEO4 ---
def _vd_keepa(d, asin):
    k = globals().get("KEEPA_KEY") or globals().get("KEEPA")
    if not k:
        return None
    try:
        r = requests.get("https://api.keepa.com/product", params={"key": k, "domain": 9, "asin": asin, "stats": 90}, timeout=30)
        if r.status_code != 200:
            return None
        j = r.json()
        if j.get("tokensLeft") is not None:
            d["a_tok"] = j.get("tokensLeft")
        return (j.get("products") or [None])[0]
    except Exception as e:
        print("error video keepa", e, flush=True)
        return None

def _vd_imagen(p):
    asin = (p or {}).get("asin") or ""
    urls = []
    csv = (p or {}).get("imagesCSV") or ""
    for nombre in [x.strip() for x in csv.split(",") if x.strip()][:2]:
        base = nombre.rsplit(".", 1)[0]
        urls += ["https://m.media-amazon.com/images/I/%s" % nombre,
                 "https://m.media-amazon.com/images/I/%s._AC_SL800_.jpg" % base]
    for o in ((p or {}).get("images") or [])[:2]:
        if isinstance(o, dict):
            for c in ("l", "m"):
                if o.get(c):
                    urls.append("https://m.media-amazon.com/images/I/%s" % o[c])
    if asin in _VD_OG:
        urls.append(_VD_OG[asin])
    if asin:
        urls.append("https://ws-eu.amazon-adsystem.com/widgets/q?_encoding=UTF8&ASIN=%s&Format=_SL600_&ID=AsinImage&MarketPlace=ES&ServiceVersion=20070822&WS=1" % asin)
        urls.append("https://ws-na.amazon-adsystem.com/widgets/q?_encoding=UTF8&ASIN=%s&Format=_SL600_&ID=AsinImage&MarketPlace=ES&ServiceVersion=20070822&WS=1" % asin)
    if not urls:
        raise RuntimeError("no hay ninguna direccion de foto para este producto")
    fallos = []
    for url in urls:
        try:
            r = requests.get(url, timeout=20, headers=_VD_UA)
            if r.status_code == 200 and len(r.content) > 2000:
                return _vd_abrir(r.content)
            fallos.append("%s -> %s" % (url.split("/")[2], r.status_code))
        except Exception as e:
            fallos.append("%s -> %s" % (url.split("/")[2], str(e)[:40]))
    raise RuntimeError("no se pudo descargar la foto (" + "; ".join(fallos[:3]) + ")")

'''
n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
src = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), src, count=1, flags=re.M)
try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)
copia = RUTA + ".bak_video4_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
