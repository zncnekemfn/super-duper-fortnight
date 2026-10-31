import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- VIDEO2 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- VIDEO ---" not in src:
    print("ABORTO: primero hay que aplicar parche_video.py"); sys.exit(1)

TAIL = r'''# --- VIDEO2 ---
_video_cmd_v1 = video_cmd
_VD_CLAVES = ("on", "off", "umbral", "max")
_VD_ASIN_RE = r"/(?:dp|gp/product|d)/([A-Z0-9]{10})(?:[/?#]|$)"

def _vd_de_enlace(url):
    """Devuelve el ASIN de un enlace de Amazon o de un enlace corto (amzlinks.in, amzn.to...)."""
    try:
        r = requests.get(url, timeout=15, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
        vistos = [str(h.headers.get("Location", "")) for h in r.history] + [str(r.url)]
        for u in vistos:
            m = _vd_re.search(_VD_ASIN_RE, u)
            if m:
                return m.group(1)
        m = _vd_re.search(r"(?:amazon\.[a-z.]+)/(?:[^\"'\s<>]*?/)?(?:dp|gp/product)/([A-Z0-9]{10})", r.text or "")
        return m.group(1) if m else ""
    except Exception as e:
        print("error video enlace", e, flush=True)
        return ""

def video_cmd(d, cid, args):
    if args and args[0].lower() not in _VD_CLAVES:
        asin = ""
        for a in args:
            if a.lower().startswith("http"):
                asin = _vd_de_enlace(a)
            elif _vd_re.fullmatch(r"[A-Za-z0-9]{10}", a):
                asin = a.upper()
            if asin:
                break
        if not asin:
            enviar(cid, "No he podido sacar el ASIN. Envia el enlace de Amazon completo (o un enlace corto) o el ASIN de 10 caracteres.\n"
                        "Ejemplo: /video https://www.amazon.es/dp/B0ABCDEFGH")
            return
        args = [asin]
    return _video_cmd_v1(d, cid, args)

'''
n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
src = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), src, count=1, flags=re.M)
try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)
copia = RUTA + ".bak_video2_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
