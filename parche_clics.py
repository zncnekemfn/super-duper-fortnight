import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()

if "# --- CLICS ---" in src:
    print("Ya estaba aplicado. No hago nada.")
    sys.exit(0)

def unico(patron, fn, nombre):
    global src
    n = len(re.findall(patron, src, re.M))
    if n != 1:
        print("ABORTO: ancla '%s' encontrada %d veces" % (nombre, n))
        sys.exit(1)
    src = re.sub(patron, fn, src, count=1, flags=re.M)

FUNC = r'''# --- CLICS ---
import datetime as _dtc

def _cl_tz():
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo("Europe/Madrid")
    except Exception:
        return _dtc.timezone(_dtc.timedelta(hours=1))

def _cl_fecha(delta=0):
    return (_dtc.datetime.now(_cl_tz()) - _dtc.timedelta(days=delta)).strftime("%Y-%m-%d")

_CL_ESTADOS = {"activo": "activo", "difundido": "enviado", "finalizado": "terminado", "revision": "en revisión",
               "esperando_pago": "pendiente de pago", "rechazado": "rechazado", "tablon": "en el tablón",
               "pendiente": "pendiente"}

def _cl_resumen(ad, aid):
    env = int(ad.get("env", 0) or 0)
    clics = int(ad.get("clics", 0) or 0)
    unicos = len(ad.get("u") or {})
    t = "%s · %s\n   Enviado a %d usuarios · %d clics (%d personas distintas)" % (
        aid, _CL_ESTADOS.get(ad.get("estado"), ad.get("estado") or "-"), env, clics, unicos)
    if env > 0 and clics > 0:
        t += " · %.1f%% de clics" % (100.0 * clics / env)
    return t

def misanuncios_cmd(d, cid):
    mios = [(a, ad) for a, ad in d["anuncios"].items() if ad.get("autor") == cid]
    if not mios:
        enviar(cid, "Aún no has publicado anuncios. Mira /anunciar para ver los paquetes.")
        return
    mios.sort(key=lambda x: x[1].get("ts", 0), reverse=True)
    t = "\U0001f4ca TUS ANUNCIOS\n\n"
    cd = d.get("clic_dia") or {}
    for aid, ad in mios[:5]:
        t += _cl_resumen(ad, aid) + "\n"
        dias = cd.get(aid) or {}
        if dias:
            serie = []
            for i in range(6, -1, -1):
                f = _cl_fecha(i)
                serie.append("%s: %d" % (f[8:10] + "/" + f[5:7], dias.get(f, 0)))
            t += "   Últimos 7 días → " + " · ".join(serie) + "\n"
        if ad.get("fin"):
            t += "   Activo hasta el %s\n" % _dtc.datetime.fromtimestamp(ad["fin"], _cl_tz()).strftime("%d/%m/%Y")
        t += "\n"
    t += "Los clics se cuentan cuando alguien pulsa el botón de tu anuncio."
    enviar(cid, t)

def clics_admin(d, cid):
    todos = sorted(d["anuncios"].items(), key=lambda x: x[1].get("ts", 0), reverse=True)[:10]
    if not todos:
        enviar(cid, "No hay anuncios todavía.")
        return
    t = "\U0001f4ca CLICS DE LOS ÚLTIMOS ANUNCIOS\n\n"
    for aid, ad in todos:
        t += _cl_resumen(ad, aid) + "\n   Autor: %s · tipo: %s\n\n" % (ad.get("autor") or "tú", ad.get("tipo") or "-")
    enviar(cid, t)

'''

TAIL = r'''# --- CLICS (registro diario) ---
_callback_anuncio_orig = callback_anuncio

def callback_anuncio(d, cid, cb):
    try:
        if cb.startswith("ad_") and cid != ADMIN:
            aid = cb[3:]
            ad = d["anuncios"].get(aid)
            if ad and autorizado(d, cid):
                dias = d.setdefault("clic_dia", {}).setdefault(aid, {})
                f = _cl_fecha()
                dias[f] = dias.get(f, 0) + 1
                for k in sorted(dias.keys())[:-45]:
                    dias.pop(k, None)
    except Exception as e:
        print("error clics", e, flush=True)
    return _callback_anuncio_orig(d, cid, cb)

AYUDA = AYUDA + "\n\n\U0001f4ca /misanuncios - estadísticas y clics de tus anuncios"

'''

unico(r'^def comando\(d, cid, texto\):\n', lambda m: FUNC + m.group(0), "comando")
unico(r'^    elif cmd in \("/propina", "/premium"\):\n',
      lambda m: ('    elif cmd in ("/misanuncios", "/misclics"):\n        misanuncios_cmd(d, cid)\n'
                 '    elif cmd == "/clics" and cid == ADMIN:\n        clics_admin(d, cid)\n') + m.group(0), "propina")
unico(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), "main")

try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)

copia = RUTA + ".bak_clics_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
