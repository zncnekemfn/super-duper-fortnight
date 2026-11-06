import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
MARCA = "# --- POSTX1 ---"
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("# --- VIDEOSDIA1 ---", "def _vs_texto(", "def _rf_candidatas(", "def _vd_keepa(", "def _vd_imagen(", "def _vd_render(",
          "def _vd_enviar(", "def hook_anuncios_pago(", "def enviar("):
    if n not in src:
        print("ABORTO: falta", n); sys.exit(1)
BLOQUE = r'''
# --- POSTX1 ---
# /post  (solo ADMIN): crea el post para X de una oferta: video + texto listo para copiar.
#   - respondiendo (reply) a un aviso del bot con /post
#   - o /post <enlace de Amazon o ASIN>
_px_pre_hook = hook_anuncios_pago
_px_ocupado = [False]

def _px_num(s):
    s = str(s).strip().replace("€", "").strip()
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    return float(s)

def _px_asin(txt):
    m = re.search(r"(?:/dp/|/gp/product/|/aw/d/)([A-Z0-9]{10})", txt or "")
    if m: return m.group(1)
    m = re.search(r"\b(B0[A-Z0-9]{8})\b", txt or "")
    return m.group(1) if m else None

def _px_parse(txt, asin):
    """Reconstruye la oferta a partir del texto de un aviso (por si ya no esta en la lista de 24 h)."""
    try:
        ahora = _px_num(re.search(r"➜\s*([\d.,]+)\s*€", txt).group(1))
        pct = int(re.search(r"-(\d+)\s*%", txt).group(1))
        mah = re.search(r"ahorras\s*([\d.,]+)\s*€", txt)
        mant = re.search(r"Precio anterior:\s*([\d.,]+)\s*€", txt)
        if mah: antes = ahora + _px_num(mah.group(1))
        elif mant: antes = _px_num(mant.group(1))
        else: antes = ahora / max(0.01, (1 - pct / 100.0))
        tit = ""
        for l in txt.split("\n"):
            if "\U0001f6cd" in l or "\U0001f3ae" in l:
                tit = re.sub(r"^[^\w]+", "", l).strip(); break
        if not tit: return None
        return {"asin": asin, "t": tit, "a": ahora, "b": antes, "pct": pct}
    except Exception:
        return None

def _px_oferta(d, asin, txt_resp):
    for c in _rf_candidatas(d):
        if c.get("asin") == asin:
            return c
    return _px_parse(txt_resp or "", asin)

def _px_hacer(d, x, destino):
    import tempfile as _tf, os as _os
    if _px_ocupado[0]:
        enviar(destino, "Ya estoy generando otro post. Espera un momento."); return
    _px_ocupado[0] = True
    ruta = None
    try:
        enviar(destino, "\U0001f3ac Preparando el post de X...")
        p = _vd_keepa(d, x["asin"])
        img = _vd_imagen(p) if p else None
        if img is not None:
            ruta = _os.path.join(_tf.gettempdir(), "postx_%s.mp4" % x["asin"])
            _vd_render(img, x["t"], x["a"], x["b"], x["pct"], ruta)
            _vd_enviar(destino, ruta, "\U0001f3ac Video para X")
        else:
            enviar(destino, "No pude bajar la foto; te paso solo el texto.")
        enviar(destino, _vs_texto(x))
    except Exception as e:
        print("error postx", str(e)[:120], flush=True)
        try: enviar(destino, "Error creando el post: %s" % str(e)[:150])
        except Exception: pass
    finally:
        _px_ocupado[0] = False
        try:
            if ruta and _os.path.exists(ruta): _os.remove(ruta)
        except Exception:
            pass

def hook_anuncios_pago(d, u):
    try:
        m = u.get("message")
        t = ((m.get("text") or "") if m else "").strip()
        if m and t and t.lower().split("@")[0].split()[0] == "/post" and str(m["chat"]["id"]) == str(ADMIN):
            cid = m["chat"]["id"]
            resp = m.get("reply_to_message") or {}
            txt_resp = (resp.get("text") or resp.get("caption") or "")
            args = " ".join(t.split()[1:])
            asin = _px_asin(args) or _px_asin(txt_resp)
            if not asin:
                enviar(cid, "Responde con /post a un aviso del bot, o escribe /post <enlace de Amazon o ASIN>.")
                return True
            x = _px_oferta(d, asin, txt_resp)
            if not x:
                enviar(cid, "No encuentro los datos de esa oferta (%s). Responde con /post al propio aviso del bot." % asin)
                return True
            _vd_th.Thread(target=_px_hacer, args=(d, x, cid), daemon=True).start()
            return True
    except Exception as e:
        print("error /post", str(e)[:100], flush=True)
    return _px_pre_hook(d, u)
'''
n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
nuevo = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: BLOQUE + "\n" + m.group(0), src, count=1, flags=re.M)
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: error de sintaxis", e); sys.exit(1)
copia = RUTA + ".bak_postx1_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("OK. Uso: responde con /post a un aviso del bot (o /post <enlace Amazon>) y te llega el video + el texto para X.")
print("Reinicia: sudo systemctl restart chivato")
print("Deshacer: cp %s %s && sudo systemctl restart chivato" % (copia, RUTA))
