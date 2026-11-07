import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- STATS1 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("def hook_anuncios_pago(", "def enviar(", "ADMIN"):
    if n not in src:
        print("ABORTO: falta", n); sys.exit(1)
BLOQUE = r'''
# --- STATS1 ---
# /stats (solo ADMIN): ofertas nuevas por dia (ultimos 7 dias) contando el registro del servicio, y usuarios.
_st_pre_hook = hook_anuncios_pago

def _st_contar(desde, hasta):
    import subprocess as _sp
    r = _sp.run(["journalctl", "-u", "chivato", "--since", desde, "--until", hasta, "--no-pager", "-o", "cat"],
                capture_output=True, text=True, timeout=90)
    return sum(1 for l in r.stdout.splitlines() if "foto keepa ok" in l)

def _st_informe(d, cid):
    import datetime as _dt
    try:
        hoy = _dt.date.today()
        filas = []
        for i in range(7):
            dia = hoy - _dt.timedelta(days=i)
            sig = dia + _dt.timedelta(days=1)
            n = _st_contar(dia.strftime("%Y-%m-%d 00:00:00"), sig.strftime("%Y-%m-%d 00:00:00"))
            etiqueta = "Hoy (hasta ahora)" if i == 0 else ("Ayer" if i == 1 else dia.strftime("%d/%m"))
            filas.append("%s: %d" % (etiqueta, n))
        usuarios = len(d.get("users") or {})
        apartados = len(d.get("inalcanzables") or {})
        bajas = len(d.get("bajas") or {})
        txt = ("\U0001f4ca Ofertas nuevas por dia\n" + "\n".join(filas) +
               "\n\n(Cuenta las fotos de oferta generadas; incluye tus /foto y pruebas manuales.)"
               "\n\n\U0001f465 Usuarios activos: %d\n\U0001f6ab Apartados (no alcanzables): %d\n\U0001f4c9 Bajas registradas: %d" % (usuarios, apartados, bajas))
        enviar(cid, txt)
    except Exception as e:
        print("error stats", str(e)[:120], flush=True)
        try: enviar(cid, "No pude calcular las estadisticas: %s" % str(e)[:120])
        except Exception: pass

def hook_anuncios_pago(d, u):
    try:
        m = u.get("message")
        t = ((m.get("text") or "") if m else "").strip()
        if m and t and t.lower().split("@")[0].split()[0] == "/stats" and str(m["chat"]["id"]) == str(ADMIN):
            import threading as _th
            _th.Thread(target=_st_informe, args=(d, m["chat"]["id"]), daemon=True).start()
            return True
    except Exception as e:
        print("error /stats", str(e)[:100], flush=True)
    return _st_pre_hook(d, u)
'''
n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
nuevo = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: BLOQUE + "\n" + m.group(0), src, count=1, flags=re.M)
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: error de sintaxis", e); sys.exit(1)
copia = RUTA + ".bak_stats1_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("OK. Reinicia: sudo systemctl restart chivato   y prueba /stats")
print("Deshacer: cp %s %s && sudo systemctl restart chivato" % (copia, RUTA))
