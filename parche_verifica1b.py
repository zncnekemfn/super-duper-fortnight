import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- VERIFICA1 ---" not in src:
    print("ABORTO: falta VERIFICA1"); sys.exit(1)
if "# --- VERIFICA1B ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
NUEVA = r'''# --- VERIFICA1B ---
_VF_HOSTS = ("link.amazon", "amzlinks.in", "amzn.to", "amzn.eu", "a.co", "amzn.com")

def _vf_asin(texto):
    pat = r"(?:/dp/|/gp/product/|/gp/aw/d/|/product/|/d/)([A-Z0-9]{10})(?![A-Za-z0-9])"
    m = re.search(pat, texto)
    if m:
        return m.group(1)
    for u in re.findall(r"https?://[^\s<>\"']+", texto)[:2]:
        u = u.rstrip(").,")
        host = (re.match(r"https?://([^/:?#]+)", u).group(1) or "").lower()
        if not (host in _VF_HOSTS or host.endswith(".amazon.es") or host == "amazon.es" or host.endswith(".amazon.com") or host.endswith(".amazon")):
            continue
        try:
            r = requests.get(u, timeout=20, allow_redirects=True,
                             headers={"User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36",
                                      "Accept-Language": "es-ES,es;q=0.9"})
            for x in [h.headers.get("Location", "") for h in r.history] + [r.url]:
                m2 = re.search(pat, x or "")
                if m2:
                    return m2.group(1)
            m2 = re.search(r"(?:/dp/|/gp/product/)([A-Z0-9]{10})(?![A-Za-z0-9])", r.text or "") or re.search(r'"asin"\s*:\s*"([A-Z0-9]{10})"', r.text or "", re.I)
            if m2:
                return m2.group(1).upper()
        except Exception as e:
            print("error /verifica enlace corto", str(e)[:80], flush=True)
    m = re.search(r"\b(B0[A-Z0-9]{8})\b", texto)
    return m.group(1) if m else None

'''
a = src.index("def _vf_asin(texto):")
b = src.index("def _vf_serie(")
nuevo = src[:a] + NUEVA + src[b:]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_verifica1b_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Corregido: /verifica ahora entiende link.amazon y otros acortadores. Copia:", cp)
print("Reinicia: sudo systemctl restart chivato")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
