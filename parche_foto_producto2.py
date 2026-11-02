import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- FOTOPROD2 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("# --- FOTOPROD1 ---", "def _fp_desde_pagina(", "def _cn_foto(", "def hook_anuncios_pago(", "def _vd_token("):
    if n not in src:
        print("ABORTO: no encuentro", n, "(aplica antes parche_foto_producto1.py)"); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)

BLOQUE = r'''
# --- FOTOPROD2 ---
# 1) Busca la foto del producto por varios caminos y deja en el log por que falla
# 2) Respaldo manual: envia una foto al bot con el pie "/foto ENLACE" (o responde a una foto con /foto ENLACE)
_FP_UA_D = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
_FP_UA_M = "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"

def _fp_bajar(u):
    from PIL import Image
    r = requests.get(u, timeout=20)
    if r.status_code == 200 and len(r.content) > 3000:
        im = Image.open(_cn_io.BytesIO(r.content)).convert("RGB")
        if im.width >= 150:
            return im
    return None

def _fp_desde_pagina(asin):
    try:
        combos = [("https://www.amazon.es/dp/%s" % asin, _FP_UA_D), ("https://www.amazon.es/dp/%s" % asin, _FP_UA_M),
                  ("https://www.amazon.es/gp/aw/d/%s" % asin, _FP_UA_M)]
        for url, ua in combos:
            try:
                h = {"User-Agent": ua, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                     "Accept-Language": "es-ES,es;q=0.9", "Upgrade-Insecure-Requests": "1"}
                r = requests.get(url, headers=h, timeout=20)
                t = r.text or ""
                ids = []
                for mm in _fp_re.finditer(r"https?://m\.media-amazon\.com/images/I/([A-Za-z0-9%+\-]{8,})\.", t):
                    if mm.group(1) not in ids:
                        ids.append(mm.group(1))
                cap = ("captcha" in t.lower()) or ("robot" in t.lower() and "amazon" in t.lower() and len(t) < 20000)
                print("foto pagina: http", r.status_code, "len", len(t), "captcha", cap, "ids", len(ids), url[-22:], flush=True)
                for i in ids[:3]:
                    for suf in ("._AC_SL1200_.jpg", ".jpg"):
                        try:
                            im = _fp_bajar("https://m.media-amazon.com/images/I/%s%s" % (i, suf))
                        except Exception:
                            im = None
                        if im is not None and im.width >= 250:
                            print("foto pagina ok", asin, im.size, flush=True)
                            return im
            except Exception as e:
                print("error foto pagina", str(e)[:80], flush=True)
        for u in ("https://m.media-amazon.com/images/P/%s.01._SCLZZZZZZZ_.jpg" % asin,
                  "https://images-eu.ssl-images-amazon.com/images/P/%s.03.LZZZZZZZ.jpg" % asin,
                  "https://images-eu.ssl-images-amazon.com/images/P/%s.01.LZZZZZZZ.jpg" % asin):
            try:
                im = _fp_bajar(u)
            except Exception:
                im = None
            if im is not None:
                print("foto por ASIN ok", asin, flush=True)
                return im
        print("foto: ninguna via funciona para", asin, "-> usa /foto con una foto adjunta", flush=True)
    except Exception as e:
        print("error foto producto2", e, flush=True)
    return None

_FP_MAN = {"im": None, "t": 0.0}

_cn_foto_pre_fp2 = _cn_foto

def _cn_foto(asin):
    try:
        if _FP_MAN["im"] is not None and _cn_time.time() - _FP_MAN["t"] < 90:
            im = _FP_MAN["im"]; _FP_MAN["im"] = None
            return im
    except Exception:
        pass
    return _cn_foto_pre_fp2(asin)

def _fp_foto_de_mensaje(m):
    from PIL import Image
    ph = m.get("photo") or ((m.get("reply_to_message") or {}).get("photo"))
    if not ph:
        return None
    fid = sorted(ph, key=lambda p: (p.get("file_size") or 0, p.get("width") or 0))[-1]["file_id"]
    r = requests.get("https://api.telegram.org/bot%s/getFile" % _vd_token(), params={"file_id": fid}, timeout=20)
    ruta = r.json()["result"]["file_path"]
    r2 = requests.get("https://api.telegram.org/file/bot%s/%s" % (_vd_token(), ruta), timeout=30)
    return Image.open(_cn_io.BytesIO(r2.content)).convert("RGB")

_fp2_pre_hook = hook_anuncios_pago

def hook_anuncios_pago(d, u):
    try:
        m = u.get("message")
        if m and str(m["chat"]["id"]) == str(ADMIN):
            t = (m.get("text") or m.get("caption") or "").strip()
            if t and t.split()[0].lower().split("@")[0] == "/foto" and (m.get("photo") or (m.get("reply_to_message") or {}).get("photo")):
                im = _fp_foto_de_mensaje(m)
                if im is not None:
                    _FP_MAN["im"] = im; _FP_MAN["t"] = _cn_time.time()
                    m["text"] = t
                    enviar(m["chat"]["id"], "Uso tu foto para la tarjeta.")
    except Exception as e:
        print("error foto manual", e, flush=True)
    return _fp2_pre_hook(d, u)
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_fotoprod2_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado. Copia:", cp)
print("Reinicia: sudo systemctl restart chivato")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
