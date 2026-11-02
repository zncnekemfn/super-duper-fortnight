import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- FOTOPROD1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("def _cn_foto(", "_cn_fotos", "_cn_io"):
    if n not in src:
        print("ABORTO: no encuentro", n); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)

BLOQUE = r'''
# --- FOTOPROD1 ---
# Si no hay foto del producto (Keepa / imagen clasica), la saca de la propia pagina del producto
import re as _fp_re

def _fp_desde_pagina(asin):
    from PIL import Image
    try:
        h = {"User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36",
             "Accept-Language": "es-ES,es;q=0.9"}
        r = requests.get("https://www.amazon.es/dp/%s" % asin, headers=h, timeout=20)
        if r.status_code != 200:
            print("foto pagina: http", r.status_code, asin, flush=True); return None
        t = r.text
        cand = []
        for pat in (r'"hiRes"\s*:\s*"(https://[^"]+?\.jpg)"', r'"large"\s*:\s*"(https://[^"]+?\.jpg)"',
                    r'data-old-hires="(https://[^"]+?\.jpg)"', r'id="landingImage"[^>]*?src="(https://[^"]+?\.jpg)"',
                    r'<meta[^>]+property="og:image"[^>]+content="(https://[^"]+?\.jpg)"',
                    r'"mainUrl"\s*:\s*"(https://[^"]+?\.jpg)"'):
            for m in _fp_re.finditer(pat, t):
                u = m.group(1)
                if u not in cand:
                    cand.append(u)
            if len(cand) >= 4:
                break
        for u in cand[:4]:
            r2 = requests.get(u, timeout=20)
            if r2.status_code == 200 and len(r2.content) > 3000:
                im = Image.open(_cn_io.BytesIO(r2.content)).convert("RGB")
                if im.width >= 150:
                    print("foto pagina ok", asin, im.size, flush=True)
                    return im
        print("foto pagina: sin imagen valida", asin, "candidatas:", len(cand), flush=True)
    except Exception as e:
        print("error foto pagina", e, flush=True)
    return None

try:
    _cn_foto_pre_fp = _cn_foto
    def _cn_foto(asin):
        img = _cn_foto_pre_fp(asin)
        if img is not None or not asin:
            return img
        img = _fp_desde_pagina(asin)
        if img is not None:
            _cn_fotos[asin] = img
        return img
except NameError:
    pass
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_fotoprod_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado. Copia:", cp)
print("Reinicia: sudo systemctl restart chivato")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
