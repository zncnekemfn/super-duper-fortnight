# Diagnostico de la foto de producto (solo lectura, no toca nada). Uso: python3 diag_foto.py ASIN_o_enlace
import os, re, sys
try:
    import requests
except Exception:
    print("Falta 'requests'"); sys.exit(1)
arg = sys.argv[1] if len(sys.argv) > 1 else ""
m = re.search(r"([A-Z0-9]{10})", arg.upper()) if arg else None
if not m:
    print("Uso: python3 diag_foto.py B0GZZM4CXF"); sys.exit(1)
asin = m.group(1)
BASE = "/opt/chivato"
key = os.environ.get("KEEPA_KEY", ""); donde = "entorno" if key else ""
if not key:
    for f in (os.path.join(BASE, ".env"), os.path.join(BASE, "env"), os.path.join(BASE, "chivato.env")):
        try:
            for l in open(f, encoding="utf-8"):
                if l.strip().startswith("KEEPA_KEY"):
                    key = l.split("=", 1)[1].strip().strip('"').strip("'"); donde = f
        except Exception:
            pass
if not key:
    try:
        t = open(os.path.join(BASE, "bot.py"), encoding="utf-8").read()
        mm = re.search(r'KEEPA_KEY\s*=\s*(?:os\.environ\.get\([^,]+,\s*)?["\']([A-Za-z0-9]{20,})["\']', t)
        if mm: key = mm.group(1); donde = "bot.py"
    except Exception:
        pass
print("ASIN:", asin, "| clave de Keepa:", ("encontrada en " + donde) if key else "NO encontrada")
UA_D = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
UA_M = "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
cands = []

print("\n[1] KEEPA")
if key:
    try:
        r = requests.get("https://api.keepa.com/product", params={"key": key, "domain": 9, "asin": asin}, timeout=25)
        j = r.json() if r.status_code == 200 else {}
        pr = (j.get("products") or [None])[0] or {}
        print(" http", r.status_code, "| tokens restantes:", j.get("tokensLeft"), "| productos:", len(j.get("products") or []))
        print(" titulo:", str(pr.get("title"))[:60])
        csv = str(pr.get("imagesCSV") or "")
        print(" imagesCSV:", csv[:80] or "(vacio)")
        print(" images:", str(pr.get("images"))[:100] if pr.get("images") else "(vacio)")
        if csv.split(",")[0]:
            cands.append(("keepa csv", "https://m.media-amazon.com/images/I/" + csv.split(",")[0]))
        for im in (pr.get("images") or [])[:2]:
            if isinstance(im, dict) and (im.get("l") or im.get("m")):
                cands.append(("keepa images", "https://m.media-amazon.com/images/I/" + (im.get("l") or im.get("m"))))
    except Exception as e:
        print(" error:", str(e)[:120])
else:
    print(" (sin clave, salto)")

print("\n[2] PAGINA DE AMAZON")
for url, ua, nom in (("https://www.amazon.es/dp/" + asin, UA_D, "escritorio"), ("https://www.amazon.es/dp/" + asin, UA_M, "movil"), ("https://www.amazon.es/gp/aw/d/" + asin, UA_M, "aw/d movil")):
    try:
        r = requests.get(url, headers={"User-Agent": ua, "Accept-Language": "es-ES,es;q=0.9", "Accept": "text/html,application/xhtml+xml"}, timeout=25)
        t = r.text or ""
        ids = []
        for mm in re.finditer(r"https?://m\.media-amazon\.com/images/I/([A-Za-z0-9%+\-]{8,})\.", t):
            if mm.group(1) not in ids: ids.append(mm.group(1))
        tit = re.search(r"<title[^>]*>(.*?)</title>", t, re.S | re.I)
        print(" %-11s http %s | %d bytes | captcha: %s | imagenes: %d | titulo: %s" % (nom, r.status_code, len(t), "SI" if "captcha" in t.lower() else "no", len(ids), (tit.group(1).strip()[:50] if tit else "-")))
        if ids: cands.append(("pagina " + nom, "https://m.media-amazon.com/images/I/%s._AC_SL1200_.jpg" % ids[0]))
    except Exception as e:
        print(" %-11s error: %s" % (nom, str(e)[:100]))

print("\n[3] IMAGEN POR ASIN")
for u in ("https://m.media-amazon.com/images/P/%s.01._SCLZZZZZZZ_.jpg" % asin, "https://images-eu.ssl-images-amazon.com/images/P/%s.03.LZZZZZZZ.jpg" % asin, "https://images-eu.ssl-images-amazon.com/images/P/%s.01.LZZZZZZZ.jpg" % asin):
    cands.append(("por ASIN", u))

print("\n[4] DESCARGA DE CADA CANDIDATA")
bien = []
for nom, u in cands:
    try:
        r = requests.get(u, timeout=20)
        ok = r.status_code == 200 and len(r.content) > 3000
        print(" %-14s http %s | %d bytes | %s" % (nom, r.status_code, len(r.content), "VALIDA" if ok else "no sirve"))
        if ok: bien.append(nom)
    except Exception as e:
        print(" %-14s error: %s" % (nom, str(e)[:80]))
print("\nRESUMEN:", ("vias que sirven: " + ", ".join(bien)) if bien else "NINGUNA via da foto desde este servidor")
