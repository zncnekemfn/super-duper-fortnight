import re, shutil, time, sys, os

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- FOTO2 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- FOTO1 ---" not in src:
    print("ABORTO: primero hay que aplicar parche_foto1.py"); sys.exit(1)

# quitar los dos envoltorios viejos del parche foto1 (enviar y enviar_aviso)
a = src.find("_enviar_pre_ft = enviar\n")
b = src.find("_comando_pre_ft = comando\n")
if a < 0 or b < a:
    print("ABORTO: no encuentro el bloque de foto1"); sys.exit(1)
src = src[:a] + src[b:]

TAIL = r'''# --- FOTO2 ---
# Los avisos se convierten en foto en el punto donde el bot habla con Telegram (valen todos los hilos y colas).
_ft_est = {"on": True}

class _FtReq:
    def __init__(self, real):
        object.__setattr__(self, "_real", real)
    def __getattr__(self, n):
        return getattr(self._real, n)
    def post(self, url, *a, **k):
        try:
            if _ft_est.get("on", True) and str(url).endswith("/sendMessage") and not a and not k.get("files"):
                dat = k.get("data")
                if isinstance(dat, dict) and isinstance(dat.get("text"), str):
                    item = _ft_item_de_texto(dat["text"])
                    if item:
                        ruta = _ft_foto(item)
                        if ruta:
                            nd = {x: y for x, y in dat.items() if x not in ("text", "disable_web_page_preview", "link_preview_options")}
                            nd["caption"] = dat["text"]
                            kk = {x: y for x, y in k.items() if x not in ("data", "files", "timeout")}
                            with open(ruta, "rb") as fh:
                                r = self._real.post(str(url)[:-len("sendMessage")] + "sendPhoto", data=nd, files={"photo": fh}, timeout=60, **kk)
                            if r.status_code == 200:
                                return r
                            print("foto aviso rechazada", r.status_code, flush=True)
        except Exception as e:
            print("error foto aviso", e, flush=True)
        return self._real.post(url, *a, **k)

def _ft_item_de_texto(t):
    if len(t) > 1000 or not t.startswith("\U0001f525"):
        return None
    lin = t.split("\n")
    m0 = _ft_re.search(r"(\d{1,2})\s?%", lin[0])
    urls = _ft_re.findall(r"https?://\S*amazon\.es/dp/[A-Z0-9]{10}\S*", t)
    if not m0 or len(urls) != 1:
        return None
    tl = ""
    for l in lin[1:]:
        if _ft_re.search(r"\d+[.,]\d\d ?(?:EUR|€)", l) and "Media" not in l:
            tl = l; break
    if not tl:
        return None
    media = _ft_re.search(r"Media[^:\n]{0,25}:\s*(\d+[.,]\d\d) ?(?:EUR|€)", t)
    if media:
        tl = tl + " (antes %s EUR)" % media.group(1)
    return {"t": tl, "d": int(m0.group(1)), "u": urls[0]}

requests = _FtReq(requests)

_enviar_aviso_pre_ft2 = enviar_aviso

def enviar_aviso(d, cid, item):
    try:
        _ft_est["on"] = _ft_activo(d)
    except Exception:
        pass
    return _enviar_aviso_pre_ft2(d, cid, item)

_comando_pre_ft2 = comando

def comando(d, cid, texto):
    r = _comando_pre_ft2(d, cid, texto)
    try:
        _ft_est["on"] = _ft_activo(d)
    except Exception:
        pass
    return r

'''

n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
src = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), src, count=1, flags=re.M)
try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)
copia = RUTA + ".bak_foto2_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
