import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()

if "# --- ERRORES ---" in src:
    print("Ya estaba aplicado. No hago nada.")
    sys.exit(0)

def unico(patron, fn, nombre):
    global src
    n = len(re.findall(patron, src, re.M))
    if n != 1:
        print("ABORTO: ancla '%s' encontrada %d veces" % (nombre, n))
        sys.exit(1)
    src = re.sub(patron, fn, src, count=1, flags=re.M)

FUNC = r'''# --- ERRORES ---
ERR_CADA = 240
ERR_MAX_CICLO = 5
ERR_RANGO = 2
ERR_TIPOS = (0, 1)

def _err_d(d):
    e = d.setdefault("err", {})
    e.setdefault("on", True)
    e.setdefault("pct", 75)
    e.setdefault("min", 20)
    e.setdefault("todos", False)
    e.setdefault("ult", 0)
    e.setdefault("n", 0)
    e.setdefault("init", {})
    return e

def _err_dest(d):
    e = _err_d(d)
    out = [ADMIN]
    if e["todos"]:
        for cid in list(d["users"].keys()):
            if cid == ADMIN or not autorizado(d, cid):
                continue
            us = d["users"].get(cid) or {}
            if any(us.get(k) for k in ("parado", "pausa", "pausado", "off", "stop")):
                continue
            out.append(cid)
    return out

def _err_consulta(t, pct):
    import json as _jj
    sel = {"page": 0, "domainId": 9, "priceTypes": [t], "deltaPercentRange": [pct, 100],
           "dateRange": ERR_RANGO, "isRangeEnabled": True, "sortType": 4}
    r = requests.get("https://api.keepa.com/deal",
                     params={"key": KEEPA_KEY, "selection": _jj.dumps(sel)}, timeout=30)
    if r.status_code != 200:
        print("keepa errores HTTP", r.status_code, flush=True)
        return None
    j = r.json()
    if j.get("error"):
        print("keepa errores error", str(j["error"])[:120], flush=True)
        return None
    return j

def revisar_errores(d):
    e = _err_d(d)
    if not e["on"] or not KEEPA_KEY:
        return 0
    ahora = time.time()
    if ahora - e["ult"] < ERR_CADA:
        return 0
    e["ult"] = ahora
    envio = globals().get("_enviar_aviso_orig") or enviar_aviso
    enviados = 0
    for t in ERR_TIPOS:
        j = _err_consulta(t, e["pct"])
        if not j:
            continue
        lista = (j.get("deals") or {}).get("dr") or []
        primera = not e["init"].get(str(t))
        for dl in lista:
            try:
                asin = dl.get("asin") or ""
                cur = int(dl["current"][t])
                avg = int(dl["avg"][ERR_RANGO][t])
                pct = abs(int(dl["deltaPercent"][ERR_RANGO][t]))
            except Exception:
                continue
            if not asin or cur <= 0 or avg <= 0:
                continue
            if avg < e["min"] * 100 or pct < e["pct"] or pct > 99:
                continue
            k1 = "err:%s:%s" % (asin, cur)
            k2 = "keepa:%s:%s" % (asin, cur)
            if k1 in d["seen"] or k2 in d["seen"]:
                continue
            if primera:
                d["seen"][k1] = d["seen"][k2] = int(ahora)
                continue
            if enviados >= ERR_MAX_CICLO:
                continue
            d["seen"][k1] = d["seen"][k2] = int(ahora)
            title = (dl.get("title") or asin).strip()
            url = ("https://www.amazon.es/dp/%s?tag=%s" % (asin, TAG)) if TAG else ("https://www.amazon.es/dp/%s" % asin)
            fuente = "precio de Amazon" if t == 0 else "vendedor externo o Amazon"
            item = {"t": "\U0001f6a8 POSIBLE ERROR DE PRECIO (%s)\n%s - %.2f EUR (antes ~%.2f EUR)" % (fuente, title[:100], cur / 100.0, avg / 100.0),
                    "u": url, "d": pct, "c": "", "ts": int(ahora), "libre": True}
            d["recent"].append(item)
            d["recent"] = d["recent"][-30:]
            for cid in _err_dest(d):
                try:
                    envio(d, cid, item)
                except Exception as ex:
                    print("error aviso errores", ex, flush=True)
                time.sleep(0.05)
            e["n"] += 1
            enviados += 1
        e["init"][str(t)] = 1
    print("keepa errores ok, avisos:", enviados, flush=True)
    return enviados

def errores_admin(d, cid, args):
    e = _err_d(d)
    if args:
        a = args[0].lower()
        if a in ("on", "off"):
            e["on"] = (a == "on")
        elif a == "todos":
            e["todos"] = True
        elif a == "solo":
            e["todos"] = False
        elif a in ("pct", "min") and len(args) > 1 and args[1].isdigit():
            v = int(args[1])
            if a == "pct" and 50 <= v <= 99:
                e["pct"] = v
            elif a == "min" and 1 <= v <= 1000:
                e["min"] = v
            else:
                enviar(cid, "Valor fuera de rango (pct: 50 a 99, min: 1 a 1000).")
                return
            e["init"] = {}
        else:
            enviar(cid, "Uso: /errores [on|off|solo|todos|pct 75|min 20]")
            return
    enviar(cid, "\U0001f6a8 CAZA DE ERRORES DE PRECIO\n\nEstado: %s\nAvisos a: %s\nBajada mínima: %d%% (frente a la media del último mes)\n"
                "Precio habitual mínimo: %d EUR\nAvisos enviados: %d\n\n"
                "/errores on · /errores off\n/errores solo (solo tú) · /errores todos (todos los usuarios)\n"
                "/errores pct 70 · /errores min 15"
                % ("ACTIVADA" if e["on"] else "APAGADA", "todos los usuarios" if e["todos"] else "solo tú",
                   e["pct"], e["min"], e["n"]))

def revisar_feed(d):
    try:
        revisar_errores(d)
    except Exception as ex:
        print("error errores", ex, flush=True)
    return _revisar_feed_orig(d)

'''

unico(r'^def revisar_feed\(d\):\n', lambda m: FUNC + 'def _revisar_feed_orig(d):\n', "revisar_feed")
unico(r'^    elif cmd in \("/propina", "/premium"\):\n',
      lambda m: '    elif cmd == "/errores" and cid == ADMIN:\n        errores_admin(d, cid, args)\n' + m.group(0), "propina")

try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)

copia = RUTA + ".bak_errores_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
