import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- VIDEO3 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- VIDEO2 ---" not in src:
    print("ABORTO: primero hay que aplicar parche_video2.py"); sys.exit(1)

TAIL = r'''# --- VIDEO3 ---
_VD_OG = {}
_VD_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}

def _vd_de_enlace(url):
    """ASIN de un enlace de Amazon o corto; guarda ademas la foto del enlace (og:image) como respaldo."""
    try:
        r = requests.get(url, timeout=15, allow_redirects=True, headers=_VD_UA)
        vistos = [str(h.headers.get("Location", "")) for h in r.history] + [str(r.url)]
        asin = ""
        for u in vistos:
            m = _vd_re.search(_VD_ASIN_RE, u)
            if m:
                asin = m.group(1); break
        txt = r.text or ""
        if not asin:
            m = _vd_re.search(r"(?:amazon\.[a-z.]+)/(?:[^\"'\s<>]*?/)?(?:dp|gp/product)/([A-Z0-9]{10})", txt)
            asin = m.group(1) if m else ""
        if asin:
            m = (_vd_re.search(r'property=["\']og:image["\'][^>]*content=["\']([^"\']+)', txt)
                 or _vd_re.search(r'content=["\']([^"\']+)["\'][^>]*property=["\']og:image', txt))
            if m and m.group(1).startswith("http"):
                _VD_OG[asin] = m.group(1)
        return asin
    except Exception as e:
        print("error video enlace", e, flush=True)
        return ""

def _vd_abrir(contenido):
    from PIL import Image
    im = Image.open(_vd_io.BytesIO(contenido))
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        fondo = Image.new("RGB", im.size, "white"); fondo.paste(im, mask=im.split()[-1]); im = fondo
    return im.convert("RGB")

def _vd_imagen(p):
    asin = (p or {}).get("asin") or ""
    urls = []
    csv = (p or {}).get("imagesCSV") or ""
    for nombre in [x.strip() for x in csv.split(",") if x.strip()][:2]:
        base = nombre.rsplit(".", 1)[0]
        urls += ["https://m.media-amazon.com/images/I/%s" % nombre,
                 "https://m.media-amazon.com/images/I/%s._AC_SL800_.jpg" % base,
                 "https://images-na.ssl-images-amazon.com/images/I/%s" % nombre]
    if asin in _VD_OG:
        urls.append(_VD_OG[asin])
    if not urls:
        raise RuntimeError("Keepa no ha dado ninguna foto de este producto (imagesCSV vacio)")
    fallos = []
    for url in urls:
        try:
            r = requests.get(url, timeout=20, headers=_VD_UA)
            if r.status_code == 200 and len(r.content) > 500:
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
copia = RUTA + ".bak_video3_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
