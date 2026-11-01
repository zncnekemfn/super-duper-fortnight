import re, shutil, time, py_compile, sys
RUTA = "/opt/chivato/bot.py"
MARCA = "# --- FOTOENLACE1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "def video_cmd(" not in src or "def _ft_render(" not in src:
    print("ABORTO: faltan los parches de video/foto"); sys.exit(1)

BLOQUE = r'''
# --- FOTOENLACE1 ---
# /foto ENLACE [ahora] [antes]  -> foto de aviso (mismo estilo que los avisos) a partir de un enlace o ASIN
_FE_TAG = "alexexplore0e-21"
_fe_pre_hook = hook_anuncios_pago

def _fe_hacer(d, asin, titulo, ahora, antes, pct, url, destino):
    ruta = None
    try:
        try:
            _cn_loc.item = {"u": url}
            mr = _ft_re.search(r"([\d.,]+)\s*·\s*([\d.]+)\s*valoraci", _vn_valoracion(asin) or "")
            if mr:
                _cn_loc.item["rat"] = mr.group(1); _cn_loc.item["nv"] = mr.group(2)
        except Exception:
            pass
        ruta = _ft_os.path.join(_ft_tmp.gettempdir(), "foto_enlace_%s.jpg" % asin)
        _ft_render(titulo, ahora, antes, pct, ruta)
        link = "https://www.amazon.es/dp/%s?tag=%s" % (asin, _FE_TAG)
        cap = ("⚡ PRECIAZO ⚡\n\n%s\n\U0001f4a5 -%d%% → %.2f € (antes %.2f €)\n\n\U0001f449 %s\n"
               "(Como afiliado de Amazon obtengo ingresos por las compras adscritas.)") % (
               str(titulo)[:160], pct, ahora, antes, link)
        tok = _vd_token()
        with open(ruta, "rb") as fh:
            r = requests.post("https://api.telegram.org/bot%s/sendPhoto" % tok,
                              data={"chat_id": destino, "caption": cap[:1000]}, files={"photo": fh}, timeout=60)
        if r.status_code != 200:
            enviar(destino, "La foto se ha generado pero Telegram no la ha aceptado.")
    except Exception as e:
        print("error foto enlace", e, flush=True)
        try: enviar(destino, "Error generando la foto: %s" % str(e)[:150])
        except Exception: pass
    finally:
        try:
            _cn_loc.item = None
            if ruta and _ft_os.path.exists(ruta): _ft_os.remove(ruta)
        except Exception:
            pass

def _fe_cmd(d, cid, args):
    global _vd_hacer, enviar
    if not args:
        enviar(cid, "Foto de una oferta a partir de un enlace:\n/foto ENLACE\n/foto ENLACE 10.29 18.00 (ahora y antes)\nTambien vale el ASIN.")
        return
    _h, _e = _vd_hacer, enviar
    def _env(c, t, *a, **k):
        return _e(c, str(t).replace("Preparando el video", "Preparando la foto"), *a, **k)
    _vd_hacer, enviar = _fe_hacer, _env
    try:
        video_cmd(d, cid, args)
    finally:
        _vd_hacer, enviar = _h, _e

def hook_anuncios_pago(d, u):
    try:
        m = u.get("message")
        t = ((m.get("text") or "") if m else "").strip()
        if m and t.lower().split("@")[0].split(" ")[0] == "/foto" and str(m["chat"]["id"]) == str(ADMIN):
            _fe_cmd(d, m["chat"]["id"], t.split()[1:])
            return True
    except Exception as e:
        print("error /foto", e, flush=True)
    return _fe_pre_hook(d, u)
'''
n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
nuevo = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: BLOQUE + "\n" + m.group(0), src, count=1, flags=re.M)
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
copia = RUTA + ".bak_fotoenlace_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado. Copia:", copia)
print("Ahora ejecuta: systemctl restart chivato")
