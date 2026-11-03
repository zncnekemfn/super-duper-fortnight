import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- ALIRESUELVE1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("# --- ALI1 ---", "def _al_enlaces(", "def _al_id("):
    if n not in src:
        print("ABORTO: falta", n); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''
# --- ALIRESUELVE1 ---
# Enlaces cortos de AliExpress (s.click..., a.aliexpress...): se resuelve el producto y se genera TU enlace de afiliado.
_AL_UA = "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"

def _al_id(url):
    m = re.search(r"/item/(?:[^/?]*/)?(\d{8,})", url) or re.search(r"[?&](?:productIds?|itemId)=(\d{8,})", url)
    if m:
        return m.group(1)
    try:
        r = requests.get(url, timeout=20, allow_redirects=True, headers={"User-Agent": _AL_UA})
        cand = [h.url for h in r.history] + [r.url]
        cand += [h.headers.get("Location", "") for h in r.history]
        for u in cand:
            m = re.search(r"/item/(?:[^/?]*/)?(\d{8,})", u or "") or re.search(r"(?:productIds?|itemId)=(\d{8,})", u or "")
            if m:
                return m.group(1)
        t = r.text or ""
        m = (re.search(r"/item/(\d{8,})\.html", t) or re.search(r'"(?:productId|itemId)"\s*:\s*"?(\d{8,})', t)
             or re.search(r"(?:productIds?|itemId)=(\d{8,})", t))
        return m.group(1) if m else None
    except Exception as e:
        print("error ali id", str(e)[:80], flush=True)
        return None

_al_enlaces_orig = _al_enlaces
def _al_enlaces(urls):
    out = _al_enlaces_orig(urls)
    for u in urls:
        if u in out:
            continue
        try:
            pid = _al_id(u)
            if not pid:
                continue
            can = "https://es.aliexpress.com/item/%s.html" % pid
            o2 = _al_enlaces_orig([can])
            if can in o2:
                out[u] = o2[can]
        except Exception as e:
            print("error ali resuelve", str(e)[:80], flush=True)
    return out
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_aliresuelve_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: /ali acepta enlaces cortos de AliExpress (s.click...).")
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato   y luego prueba /ali con ese enlace")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
