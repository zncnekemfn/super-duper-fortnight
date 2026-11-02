import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- FOTOPROD3 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("# --- FOTOPROD2 ---", "def _fp_desde_pagina(", "_FP_MAN", "def _cn_foto(", "def _cn_frame(", "def hook_anuncios_pago(", "def _vd_token(", "KEEPA_KEY"):
    if n not in src:
        print("ABORTO: no encuentro", n, "(aplica antes parche_foto_producto1 y 2)"); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)

BLOQUE = r'''
# --- FOTOPROD3 ---
# 1) Keepa entrega ahora las fotos en el campo "images" (imagesCSV viene vacio): se usa ese primero.
# 2) La pagina de Amazon se pide primero como movil (escritorio da captcha) y se leen las URL completas.
# 3) /autotest: comprueba en vivo que la tarjeta con foto, el video y la busqueda de foto funcionan.
def _fp_img_ok(u):
    from PIL import Image
    r = requests.get(u, timeout=20)
    if r.status_code == 200 and len(r.content) > 3000:
        im = Image.open(_cn_io.BytesIO(r.content)).convert("RGB")
        if im.width >= 150:
            return im
    return None

def _fp_keepa_imagen(asin):
    try:
        if not KEEPA_KEY:
            return None
        r = requests.get("https://api.keepa.com/product", params={"key": KEEPA_KEY, "domain": 9, "asin": asin}, timeout=25)
        if r.status_code != 200:
            print("foto keepa: http", r.status_code, flush=True); return None
        pr = (r.json().get("products") or [None])[0] or {}
        nombres = []
        for im in (pr.get("images") or [])[:1]:
            if isinstance(im, dict):
                for k in ("l", "m"):
                    if im.get(k) and im[k] not in nombres:
                        nombres.append(im[k])
        csv = str(pr.get("imagesCSV") or "").split(",")[0]
        if csv and csv not in nombres:
            nombres.append(csv)
        for n in nombres[:3]:
            try:
                im = _fp_img_ok("https://m.media-amazon.com/images/I/" + n)
            except Exception:
                im = None
            if im is not None:
                return im
        print("foto keepa: sin imagen para", asin, "images:", len(pr.get("images") or []), flush=True)
    except Exception as e:
        print("error foto keepa", str(e)[:100], flush=True)
    return None

def _fp_desde_pagina(asin):
    try:
        dp = "https://www.amazon.es/dp/%s" % asin; aw = "https://www.amazon.es/gp/aw/d/%s" % asin
        for url, ua in ((dp, _FP_UA_M), (aw, _FP_UA_M), (dp, _FP_UA_D)):
            try:
                h = {"User-Agent": ua, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                     "Accept-Language": "es-ES,es;q=0.9", "Upgrade-Insecure-Requests": "1"}
                r = requests.get(url, headers=h, timeout=25)
                t = r.text or ""
                cap = "captcha" in t.lower()
                cand = []
                for pat in (r'"hiRes"\s*:\s*"(https://[^"]+?\.jpg)"', r'"large"\s*:\s*"(https://[^"]+?\.jpg)"',
                            r'data-old-hires="(https://[^"]+?\.jpg)"', r'<meta[^>]+property="og:image"[^>]+content="(https://[^"]+?\.jpg)"',
                            r'"mainUrl"\s*:\s*"(https://[^"]+?\.jpg)"'):
                    for mm in _fp_re.finditer(pat, t):
                        if mm.group(1) not in cand and "/images/I/" in mm.group(1):
                            cand.append(mm.group(1))
                print("foto pagina: http", r.status_code, "captcha", cap, "candidatas", len(cand), url[-20:], flush=True)
                for u in cand[:3]:
                    try:
                        im = _fp_img_ok(u)
                    except Exception:
                        im = None
                    if im is not None and im.width >= 250:
                        print("foto pagina ok", asin, im.size, flush=True)
                        return im
            except Exception as e:
                print("error foto pagina", str(e)[:80], flush=True)
        print("foto: ninguna via funciona para", asin, "-> usa /foto con una foto adjunta", flush=True)
    except Exception as e:
        print("error foto producto3", e, flush=True)
    return None

_cn_foto_pre_fp3 = _cn_foto

def _cn_foto(asin):
    try:
        if _FP_MAN["im"] is not None and _cn_time.time() - _FP_MAN["t"] < 90:
            return _cn_foto_pre_fp3(asin)
        if asin:
            c = _cn_fotos.get(asin)
            if c is not None:
                return c
            im = _fp_keepa_imagen(asin)
            if im is not None:
                if len(_cn_fotos) > 60:
                    _cn_fotos.clear()
                _cn_fotos[asin] = im
                print("foto keepa ok", asin, im.size, flush=True)
                return im
    except Exception as e:
        print("error foto keepa", str(e)[:100], flush=True)
    return _cn_foto_pre_fp3(asin)

def _at_enviar_foto(cid, img, cap):
    ruta = _ft_os.path.join(_ft_tmp.gettempdir(), "autotest_%d.jpg" % int(_cn_time.time() * 1000))
    try:
        img.save(ruta, "JPEG", quality=90)
        with open(ruta, "rb") as fh:
            requests.post("https://api.telegram.org/bot%s/sendPhoto" % _vd_token(), data={"chat_id": cid, "caption": cap[:1000]}, files={"photo": fh}, timeout=60)
    finally:
        try: _ft_os.remove(ruta)
        except Exception: pass

def _at_hacer(d, cid):
    from PIL import Image
    res = []
    def paso(nombre, ok, extra=""):
        res.append(("✅ " if ok else "❌ ") + nombre + ((" · " + extra) if extra else ""))
    tarjeta = None
    try:
        dat = {"titulo": "Prueba de producto", "ahora": 29.99, "antes": 59.99, "pct": 50, "foto": Image.new("RGB", (600, 600), (30, 120, 200)),
               "hora": "AUTOTEST", "rat": "4,5", "nv": "100"}
        tarjeta = _cn_frame(dat, 0.0, 6.0, True)
        r, g, b = tarjeta.getpixel((540, 402))
        paso("Tarjeta de /foto con producto", b > r + 30, "el producto se ve" if b > r + 30 else "NO se ve el producto en la tarjeta")
    except Exception as e:
        paso("Tarjeta de /foto con producto", False, str(e)[:80])
    try:
        f = _cn_frame(dat, 3.0, 6.0, False)
        paso("Fotograma del /video", f.size == (1080, 1080))
    except Exception as e:
        paso("Fotograma del /video", False, str(e)[:80])
    paso("ffmpeg instalado", bool(__import__("shutil").which("ffmpeg")))
    try:
        asin = None
        try:
            mm = _ft_re.search(r"/dp/([A-Z0-9]{10})", str((_mi_d(d)["of"] or [{}])[0].get("url") or ""))
            asin = mm.group(1) if mm else None
        except Exception:
            pass
        asin = asin or "B0GZZM4CXF"
        _cn_fotos.pop(asin, None)
        im = _cn_foto(asin)
        paso("Foto real de un producto (%s)" % asin, im is not None, ("%dx%d" % im.size) if im is not None else "ninguna via da foto")
    except Exception as e:
        paso("Foto real de un producto", False, str(e)[:80])
    for nom, ok in (("Comando /foto", "_fe2_cmd" in globals()), ("Comando /video", "video_cmd" in globals() or "_vd_cmd_amazon" in globals())):
        paso(nom, ok)
    bien = all(x.startswith("✅") for x in res)
    cab = "AUTOTEST: TODO BIEN" if bien else "AUTOTEST: HAY FALLOS"
    texto = cab + "\n\n" + "\n".join(res)
    try:
        if tarjeta is not None:
            _at_enviar_foto(cid, tarjeta, texto)
        else:
            enviar(cid, texto)
    except Exception as e:
        enviar(cid, texto)

_at_pre_hook = hook_anuncios_pago

def hook_anuncios_pago(d, u):
    try:
        m = u.get("message")
        t = ((m.get("text") or "") if m else "").strip()
        if m and t and t.split()[0].lower().split("@")[0] == "/autotest" and str(m["chat"]["id"]) == str(ADMIN):
            enviar(m["chat"]["id"], "Ejecutando el autotest…")
            _vd_th.Thread(target=_at_hacer, args=(d, m["chat"]["id"]), daemon=True).start()
            return True
    except Exception as e:
        print("error /autotest", e, flush=True)
    return _at_pre_hook(d, u)
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
if "import shutil" not in src and "shutil" not in src.split("# --- FOTOPROD3 ---")[0]:
    nuevo = nuevo.replace("# --- FOTOPROD3 ---\n", "# --- FOTOPROD3 ---\nimport shutil\n", 1)
cp = RUTA + ".bak_fotoprod3_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado. Copia:", cp)
print("Reinicia: sudo systemctl restart chivato   y luego escribe /autotest en el bot")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
