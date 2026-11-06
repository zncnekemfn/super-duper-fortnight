import re, shutil, time, sys
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- VIDEOSDIA1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("# --- RESUMENFOTO1 ---", "def _rf_candidatas(", "def _rf_enlace(", "def _vd_hacer(", "def _vd_render(", "def _vd_imagen(",
          "def _vd_keepa(", "def _vd_enviar(", "def _vd_faltan(", "def _a_tarea(", "def _a_ahora(", "def hook_anuncios_pago("):
    if n not in src:
        print("ABORTO: falta", n, "(aplica antes los parches de video y de resumen)"); sys.exit(1)

BLOQUE = r'''
# --- VIDEOSDIA1 ---
# Una vez al dia (20:30) genera el video de las mejores ofertas del dia y te los manda a ti (ADMIN) con el texto listo para X.
# /videos         -> los genera ahora
# /videos on|off  -> activa o desactiva el envio diario
_VS_HORA, _VS_MIN, _VS_N = 20, 30, 3
_vs_pre_hook = hook_anuncios_pago
_vs_tarea_pre = _a_tarea
_vs_ocupado = [False]

def _vs_est(d):
    v = d.setdefault("vs", {})
    v.setdefault("on", True); v.setdefault("dia", "")
    return v

def _vs_elegir(d):
    """Las mejores N ofertas de las ultimas 24 h: sin variantes parecidas, precio >= 10 EUR y ahorro >= 8 EUR."""
    cand = []
    for x in _rf_candidatas(d):
        if x["a"] < 10 or (x["b"] - x["a"]) < 8 or x["pct"] > 85:
            continue
        cand.append(x)
    cand.sort(key=lambda x: -(x["pct"] * min(x["b"] - x["a"], 60)))
    out, claves = [], set()
    for x in cand:
        k = None
        f = globals().get("_kq2_clave_titulo")
        if f:
            try: k = f(x["t"])
            except Exception: k = None
        if k and k in claves:
            continue
        if k: claves.add(k)
        out.append(x)
        if len(out) >= _VS_N:
            break
    return out

def _vs_texto(x):
    t = re.sub(r"\s+", " ", x["t"]).strip()
    if len(t) > 70: t = t[:67].rstrip() + "..."
    def e(n): return ("%.2f" % n).replace(".", ",")
    return ("\U0001f525 %s\n\U0001f4b6 %s € (antes %s €) · -%d%%\n\U0001f6d2 %s\n\n"
            "Más chollos gratis: t.me/ChivatoOfertas_bot\nComo afiliado de Amazon obtengo ingresos por las compras adscritas."
            % (t, e(x["a"]), e(x["b"]), x["pct"], _rf_enlace(x["asin"])))

def _vs_hacer(d, destino):
    import tempfile as _tf, os as _os
    if _vs_ocupado[0]:
        enviar(destino, "Ya estoy generando los videos del dia. Espera a que termine."); return
    _vs_ocupado[0] = True
    try:
        f = _vd_faltan()
        if f:
            enviar(destino, "Falta instalar: " + " ".join(f)); return
        items = _vs_elegir(d)
        if not items:
            enviar(destino, "Hoy no hay ofertas que cumplan (precio >= 10 EUR, ahorro >= 8 EUR). No genero videos."); return
        enviar(destino, "\U0001f3ac Preparando %d videos con las mejores ofertas del dia..." % len(items))
        hechos = 0
        for x in items:
            ruta = None
            try:
                p = _vd_keepa(d, x["asin"])
                img = _vd_imagen(p) if p else None
                if img is None:
                    print("videosdia sin foto", x["asin"], flush=True); continue
                ruta = _os.path.join(_tf.gettempdir(), "dia_%s.mp4" % x["asin"])
                _vd_render(img, x["t"], x["a"], x["b"], x["pct"], ruta)
                if _vd_enviar(destino, ruta, _vs_texto(x)):
                    hechos += 1
            except Exception as ex:
                print("error videosdia", x.get("asin"), str(ex)[:120], flush=True)
            finally:
                try:
                    if ruta and _os.path.exists(ruta): _os.remove(ruta)
                except Exception:
                    pass
        if hechos == 0:
            enviar(destino, "No he podido generar ningun video (fallaron las fotos o Keepa). Mira el registro.")
    finally:
        _vs_ocupado[0] = False

def _a_tarea(d):
    try:
        v = _vs_est(d)
        a = _a_ahora()
        hoy = a.strftime("%Y-%m-%d")
        if v["on"] and v["dia"] != hoy and (a.hour, a.minute) >= (_VS_HORA, _VS_MIN) and a.hour < 23:
            v["dia"] = hoy
            _vd_th.Thread(target=_vs_hacer, args=(d, ADMIN), daemon=True).start()
    except Exception as e:
        print("error videosdia tarea", str(e)[:100], flush=True)
    return _vs_tarea_pre(d)

def hook_anuncios_pago(d, u):
    try:
        m = u.get("message")
        t = ((m.get("text") or "") if m else "").strip()
        if m and t and t.lower().split("@")[0].split()[0] == "/videos" and str(m["chat"]["id"]) == str(ADMIN):
            a = t.split()[1:]
            v = _vs_est(d)
            if a and a[0].lower() in ("on", "off"):
                v["on"] = (a[0].lower() == "on")
                enviar(m["chat"]["id"], "Videos diarios: " + ("ACTIVADOS (cada dia a las %02d:%02d)" % (_VS_HORA, _VS_MIN) if v["on"] else "DESACTIVADOS"))
            else:
                _vd_th.Thread(target=_vs_hacer, args=(d, m["chat"]["id"]), daemon=True).start()
            return True
    except Exception as e:
        print("error /videos", str(e)[:100], flush=True)
    return _vs_pre_hook(d, u)
'''
n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
nuevo = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: BLOQUE + "\n" + m.group(0), src, count=1, flags=re.M)
try:
    compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: error de sintaxis", e); sys.exit(1)
copia = RUTA + ".bak_videosdia1_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: cada dia a las 20:30 recibiras los videos de las 3 mejores ofertas. Prueba ahora con /videos")
print("Copia:", copia)
print("Reinicia: sudo systemctl restart chivato")
print("Deshacer: cp %s %s && sudo systemctl restart chivato" % (copia, RUTA))
