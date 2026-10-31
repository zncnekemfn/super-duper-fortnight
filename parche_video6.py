import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- VIDEO6 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- VIDEO4 ---" not in src:
    print("ABORTO: primero hay que aplicar parche_video4.py"); sys.exit(1)

TAIL = r'''# --- VIDEO6 ---
VD_TXT_MIN, VD_TXT_MAX = 50, 150

def _vd_limpio(t):
    t = _vd_re.sub(r"<[^>]+>", " ", str(t or ""))
    t = _vd_re.sub(r"[•✅✔☑●▪►➤⭐❗‼️]+", " ", t)
    t = _vd_re.sub(r"&[a-z]+;", " ", t)
    t = _vd_re.sub(r"\s+", " ", t).strip(" -:;,.·")
    return t

def _vd_cortar(t, mx):
    if len(t) <= mx:
        return t
    c = t[:mx - 1].rsplit(" ", 1)[0].rstrip(" ,;:.-·")
    return c + "…"

def _vd_resumen(p):
    """Texto de 50-150 caracteres sobre el producto, sacado de las caracteristicas de Amazon."""
    p = p or {}
    trozos = []
    for f in (p.get("features") or [])[:6]:
        f = _vd_limpio(f)
        if len(f) >= 15:
            f = _vd_re.sub(r"^[A-ZÁÉÍÓÚÑ /&-]{3,30}:\s*", "", f)
            trozos.append(f)
    if not trozos:
        d = _vd_limpio(p.get("description"))
        if d:
            trozos.append(d)
    texto = ""
    for t in trozos:
        t = t[0].upper() + t[1:] if t else t
        if not texto:
            texto = t
        elif len(texto) < VD_TXT_MIN and len(texto) + 3 + len(t) <= VD_TXT_MAX:
            texto = texto + " · " + t
        if len(texto) >= VD_TXT_MIN:
            break
    if len(texto) < VD_TXT_MIN:
        extra = " ".join(x for x in (p.get("brand"), p.get("productGroup")) if x)
        if extra and extra.lower() not in texto.lower():
            texto = (texto + " · " + extra).strip(" ·")
    return _vd_cortar(texto, VD_TXT_MAX) if texto else ""

def _vd_hacer(d, asin, titulo, ahora, antes, pct, url, destino):
    """Genera y envia el video con un texto sobre el producto. Ejecutar en hilo."""
    ruta = None
    try:
        p = _vd_keepa(d, asin)
        img = _vd_imagen(p)
        ruta = _vd_os.path.join(_vd_tmp.gettempdir(), "oferta_%s.mp4" % asin)
        _vd_render(img, titulo, ahora, antes, pct, ruta)
        resumen = _vd_resumen(p)
        cap = "\U0001f525 %s\n\n" % titulo[:110]
        if resumen:
            cap += "%s\n\n" % resumen
        cap += "\U0001f4b6 %.2f € (antes %.2f €) · -%d%%\n\n%s" % (ahora, antes, pct, url or "")
        if not _vd_enviar(destino, ruta, cap):
            enviar(destino, "El video se ha generado pero Telegram no lo ha aceptado.")
    except Exception as e:
        print("error video", e, flush=True)
        try:
            enviar(destino, "Error generando el video: %s" % str(e)[:150])
        except Exception:
            pass
    finally:
        try:
            if ruta and _vd_os.path.exists(ruta):
                _vd_os.remove(ruta)
        except Exception:
            pass

'''
n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
src = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), src, count=1, flags=re.M)
try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)
copia = RUTA + ".bak_video6_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
