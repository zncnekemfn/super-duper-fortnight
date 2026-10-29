import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()

if "# --- ESTADISTICAS ---" in src:
    print("Ya estaba aplicado. No hago nada.")
    sys.exit(0)

def unico(patron, fn, nombre):
    global src
    n = len(re.findall(patron, src, re.M))
    if n != 1:
        print("ABORTO: ancla '%s' encontrada %d veces" % (nombre, n))
        sys.exit(1)
    src = re.sub(patron, fn, src, count=1, flags=re.M)

FUNC = r'''# --- ESTADISTICAS ---
import datetime as _dts

def _st_tz():
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo("Europe/Madrid")
    except Exception:
        return _dts.timezone(_dts.timedelta(hours=1))

def _st_fecha(ts, fmt="%d/%m %H:%M"):
    return _dts.datetime.fromtimestamp(ts, _st_tz()).strftime(fmt)

def _st_altas(d):
    """Altas por d\u00eda seg\u00fan la fecha de acceso. Los accesos anteriores al modo privado van aparte."""
    previo, dias = 0, {}
    for cid, a in (d.get("autorizados") or {}).items():
        ts = (a or {}).get("ts")
        if not ts or (a or {}).get("codigo") == "previo":
            previo += 1
            continue
        k = _st_fecha(ts, "%Y-%m-%d")
        dias[k] = dias.get(k, 0) + 1
    return previo, dias

def _st_apoyantes(d):
    pagan = set(str(t.get("u")) for t in (d.get("tips") or []))
    activos, de_pago = 0, 0
    for c in (d.get("apoyo") or {}):
        if es_apoyante(d, c):
            activos += 1
            if c in pagan:
                de_pago += 1
    return activos, de_pago

def _st_grafico_png(filas, acumulado):
    import io
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=130)
    etiquetas = [f[0][5:].replace("-", "/") for f in filas]
    valores = [f[1] for f in filas]
    ax.bar(etiquetas, valores, color="#FF8C1A")
    ax.set_ylabel("Altas por d\u00eda")
    ax.tick_params(axis="x", rotation=60, labelsize=8)
    ax2 = ax.twinx()
    ax2.plot(etiquetas, acumulado, color="#172B5C", linewidth=2.2, marker="o", markersize=3)
    ax2.set_ylabel("Total acumulado")
    ax.set_title("Altas de usuarios (\u00faltimos 14 d\u00edas)")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf

def estadisticas_admin(d, cid):
    previo, dias = _st_altas(d)
    hoy = _dts.datetime.now(_st_tz()).date()
    lista = [(hoy - _dts.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(13, -1, -1)]
    antes = previo + sum(v for k, v in dias.items() if k < lista[0])
    filas, acum, tot = [], [], antes
    for k in lista:
        tot += dias.get(k, 0)
        filas.append((k, dias.get(k, 0)))
        acum.append(tot)
    nuevos_hoy = dias.get(lista[-1], 0)
    nuevos_7 = sum(v for k, v in filas[-7:])
    act, pago = _st_apoyantes(d)
    resumen = ("\U0001f4ca ESTAD\u00cdSTICAS\n\nUsuarios: %d\nAccesos autorizados: %d\nNuevos hoy: %d\n\u00daltimos 7 d\u00edas: %d\n"
               "Apoyantes activos: %d (de pago: %d)\nAnteriores al modo privado: %d") % (
                   len(d["users"]), len(d.get("autorizados") or {}), nuevos_hoy, nuevos_7, act, pago, previo)
    try:
        buf = _st_grafico_png(filas, acum)
        requests.post(API + "/sendPhoto", data={"chat_id": cid, "caption": resumen},
                      files={"photo": ("altas.png", buf, "image/png")}, timeout=60)
        return
    except Exception as e:
        print("grafico png no disponible:", e, flush=True)
    mx = max([v for k, v in filas] + [1])
    esc = 1 if mx <= 20 else mx / 20.0
    barras = "\n".join("%s %s %d" % (k[5:].replace("-", "/"), "\u2588" * int(round(v / esc)) if v else "\u00b7", v) for k, v in filas)
    texto = resumen.replace("&", "&amp;").replace("<", "&lt;") + "\n\nAltas por d\u00eda:\n<pre>" + barras + "</pre>"
    try:
        requests.post(API + "/sendMessage", data={"chat_id": cid, "text": texto, "parse_mode": "HTML"}, timeout=30)
    except Exception as e:
        print("error estadisticas", e, flush=True)

def pagos_admin(d, cid):
    tips = d.get("tips") or []
    ventas = d.get("ventas_ads") or []
    tot_t = sum(t.get("n", 0) for t in tips)
    tot_a = sum(v.get("n", 0) for v in ventas)
    t = "\U0001f4b0 PAGOS\n\nPropinas: %d (%d Stars)\nAnuncios pagados: %d (%d Stars)\nTotal: %d Stars\n" % (
        len(tips), tot_t, len(ventas), tot_a, tot_t + tot_a)
    movs = [(x.get("t", 0), "Propina", x.get("n", 0), x.get("u")) for x in tips] + \
           [(x.get("t", 0), "Anuncio", x.get("n", 0), x.get("u")) for x in ventas]
    movs.sort(reverse=True)
    if movs:
        t += "\n\u00daltimos pagos:\n"
        for ts, tipo, n, u in movs[:10]:
            t += "\u2022 %s \u00b7 %s \u00b7 %s Stars \u00b7 usuario %s\n" % (_st_fecha(ts), tipo, n, u)
    else:
        t += "\nTodav\u00eda no hay pagos con Stars.\n"
    pagan = set(str(x.get("u")) for x in tips)
    t += "\nApoyantes:\n"
    ap = d.get("apoyo") or {}
    if not ap:
        t += "\u2022 ninguno\n"
    for c, v in ap.items():
        hasta = "para siempre" if v == -1 else ("hasta " + _st_fecha(v, "%d/%m/%Y") if v > time.time() else "caducado " + _st_fecha(v, "%d/%m/%Y"))
        origen = "pago" if c in pagan else ("t\u00fa" if c == ADMIN else "regalo o manual")
        t += "\u2022 %s \u00b7 %s \u00b7 %s\n" % (c, hasta, origen)
    enviar(cid, t)

'''

unico(r'^def comando\(d, cid, texto\):\n', lambda m: FUNC + m.group(0), "comando")
unico(r'^    elif cmd in \("/propina", "/premium"\):\n',
      lambda m: ('    elif cmd in ("/estadisticas", "/grafico") and cid == ADMIN:\n        estadisticas_admin(d, cid)\n'
                 '    elif cmd == "/pagos" and cid == ADMIN:\n        pagos_admin(d, cid)\n') + m.group(0), "propina")

try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)

copia = RUTA + ".bak_stats_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
