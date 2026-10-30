import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()

if "# --- CALIDAD ---" in src:
    print("Ya estaba aplicado. No hago nada.")
    sys.exit(0)
if "def _a_historico(" not in src or "_enviar_aviso_prev = enviar_aviso" not in src:
    print("ABORTO: falta parche_A.py"); sys.exit(1)

def unico(patron, fn, nombre):
    global src
    n = len(re.findall(patron, src, re.M))
    if n != 1:
        print("ABORTO: ancla '%s' encontrada %d veces" % (nombre, n)); sys.exit(1)
    src = re.sub(patron, fn, src, count=1, flags=re.M)

FUNC = r'''# --- CALIDAD ---
import re
Q_NIVELES = {1: 35, 2: 50, 3: 65}
Q_COOL_ASIN = 3 * 86400
Q_COOL_TIT = 86400

def _q_d(d):
    q = d.setdefault("q", {})
    q.setdefault("on", True)
    q.setdefault("nivel", 2)
    q.setdefault("ok", 0)
    q.setdefault("no", 0)
    q.setdefault("mot", {})
    q.setdefault("asin", {})
    q.setdefault("tit", {})
    q.setdefault("rech", [])
    q.setdefault("acep", [])
    return q

def _q_clave_tit(item):
    t = re.sub(r" - \d+\.\d\d EUR.*", "", str(item.get("t") or ""), flags=re.S)
    t = re.sub(r"\b(negro|negra|blanco|blanca|azul|rojo|roja|verde|gris|rosa|plata|dorado|oro|morado|amarillo|naranja|beige|marron)\b", "", t.lower())
    t = re.sub(r"[^a-z]", "", t)
    return t[:22] if len(t) >= 12 else ""

def _q_producto(d, asin):
    if not KEEPA_KEY or d.get("a_tok", 999) < 200:
        return None
    try:
        r = requests.get("https://api.keepa.com/product",
                         params={"key": KEEPA_KEY, "domain": 9, "asin": asin, "stats": 90, "history": 0}, timeout=20)
        if r.status_code != 200:
            return None
        j = r.json()
        if j.get("tokensLeft") is not None:
            d["a_tok"] = j.get("tokensLeft")
        return (j.get("products") or [None])[0]
    except Exception as e:
        print("error calidad keepa", e, flush=True)
        return None

def _q_puntuar(p, cur, pct):
    """Devuelve (puntos, [motivos]). Los datos que faltan no penalizan, salvo el ranking ausente."""
    pts, mot = 50, []
    st = (p or {}).get("stats") or {}
    c = st.get("current") or []
    def g(i):
        v = c[i] if len(c) > i and isinstance(c[i], (int, float)) else -1
        return v if v is not None and v >= 0 else None
    rank, rev, rat = g(3), g(17), g(16)
    if rank is None:
        pts -= 8; mot.append("sin ranking")
    elif rank <= 5000:
        pts += 25
    elif rank <= 20000:
        pts += 18
    elif rank <= 100000:
        pts += 10
    elif rank > 500000:
        pts -= 15; mot.append("ranking muy bajo")
    if rev is not None:
        if rev >= 200:
            pts += 15
        elif rev >= 50:
            pts += 8
        elif rev >= 10:
            pts += 2
        elif rev < 5:
            pts -= 20; mot.append("casi sin opiniones")
    if rat is not None:
        r = rat / 10.0
        if r >= 4.2:
            pts += 10
        elif r >= 3.8:
            pts += 3
        elif r < 3.5:
            pts -= 15; mot.append("valoracion baja")
    ms = (p or {}).get("monthlySold")
    if isinstance(ms, (int, float)) and ms > 0:
        pts += 15 if ms >= 100 else (6 if ms >= 20 else 0)
    if st.get("buyBoxIsAmazon"):
        pts += 15
    elif st.get("buyBoxIsFBA"):
        pts += 6
    elif st.get("buyBoxSellerId"):
        pts -= 10; mot.append("vendedor externo")
    if (p or {}).get("brand"):
        pts += 3
    else:
        pts -= 5; mot.append("sin marca")
    if cur and cur < 800:
        pts -= 15; mot.append("precio muy bajo")
    if cur and cur < 1500 and pct >= 70:
        pts -= 10; mot.append("descuento dudoso")
    return pts, mot

def _q_evaluar(d, item):
    """(ok, puntos, motivo). Falla abierto si no hay datos."""
    q = _q_d(d)
    ahora = time.time()
    asin = _a_asin(item.get("u"))
    cur = _a_precio_cents(item.get("t")) or 0
    pct = int(item.get("d") or 0)
    if not asin:
        return True, None, "sin asin"
    for k in [k for k, v in q["asin"].items() if ahora - v[0] > Q_COOL_ASIN]:
        q["asin"].pop(k, None)
    for k in [k for k, v in q["tit"].items() if ahora - v > Q_COOL_TIT]:
        q["tit"].pop(k, None)
    prev = q["asin"].get(asin)
    if prev and not (cur and prev[1] and cur <= prev[1] * 0.9):
        return False, None, "repetido"
    tk = _q_clave_tit(item)
    if tk and tk in q["tit"]:
        return False, None, "variante repetida"
    p = _q_producto(d, asin)
    if p is None:
        return True, None, "sin datos"
    pts, mot = _q_puntuar(p, cur, pct)
    thr = Q_NIVELES.get(q["nivel"], 50)
    if pts < thr:
        return False, pts, ", ".join(mot) or "puntuacion baja"
    return True, pts, ", ".join(mot)

def _q_registrar(d, item, ok, pts, mot):
    q = _q_d(d)
    ahora = time.time()
    asin = _a_asin(item.get("u"))
    if ok:
        q["ok"] += 1
        if asin:
            q["asin"][asin] = (ahora, _a_precio_cents(item.get("t")) or 0)
            tk = _q_clave_tit(item)
            if tk:
                q["tit"][tk] = ahora
        q["acep"].append({"t": str(item.get("t") or "")[:70], "p": pts})
        del q["acep"][:-10]
    else:
        q["no"] += 1
        m = (mot or "otro").split(",")[0].strip()
        q["mot"][m] = q["mot"].get(m, 0) + 1
        q["rech"].append({"t": str(item.get("t") or "")[:70], "u": item.get("u"), "p": pts, "m": mot})
        del q["rech"][:-15]

def calidad_cmd(d, cid, args):
    q = _q_d(d)
    a = args[0].lower() if args else ""
    if a in ("on", "off"):
        q["on"] = (a == "on")
    elif a == "nivel" and len(args) > 1 and args[1] in ("1", "2", "3"):
        q["nivel"] = int(args[1])
    elif a in ("ver", "rechazadas"):
        if not q["rech"]:
            enviar(cid, "Todavía no he rechazado ninguna oferta.")
            return
        t = ["\U0001f6ab ÚLTIMAS RECHAZADAS\n"]
        for r in q["rech"][-10:][::-1]:
            t.append("%s\n   %s%s" % (r["t"], r["m"], (" (%s pts)" % r["p"]) if r["p"] is not None else ""))
        t.append("\nSi alguna era buena, baja el nivel: /calidad nivel 1")
        enviar(cid, "\n".join(t))
        return
    elif a in ("pasadas", "aceptadas"):
        if not q["acep"]:
            enviar(cid, "Todavía no ha pasado ninguna.")
            return
        enviar(cid, "✅ ÚLTIMAS ACEPTADAS\n\n" + "\n".join("%s (%s pts)" % (r["t"], r["p"] if r["p"] is not None else "-") for r in q["acep"][-10:][::-1]))
        return
    tot = q["ok"] + q["no"]
    mot = ", ".join("%s: %d" % (k, v) for k, v in sorted(q["mot"].items(), key=lambda x: -x[1])[:4]) or "-"
    enviar(cid, "\U0001f50e FILTRO DE CALIDAD\n\nEstado: %s\nNivel: %d (%s)\nEnviadas: %d · Rechazadas: %d%s\nMotivos principales: %s\n\n"
                "/calidad on · /calidad off\n/calidad nivel 1 (suave) · 2 (normal) · 3 (estricto)\n/calidad ver (rechazadas) · /calidad pasadas" % (
                "ACTIVADO" if q["on"] else "APAGADO", q["nivel"], {1: "suave", 2: "normal", 3: "estricto"}[q["nivel"]],
                q["ok"], q["no"], (" (%d%% rechazadas)" % round(100.0 * q["no"] / tot)) if tot else "", mot))

'''

TAIL = r'''# --- CALIDAD (filtro) ---
_enviar_aviso_pre_q = enviar_aviso

def enviar_aviso(d, cid, item):
    try:
        q = _q_d(d)
        if q["on"] and not item.get("libre"):
            ev = item.get("_q")
            if ev is None:
                ev = _q_evaluar(d, item)
                item["_q"] = ev
                _q_registrar(d, item, ev[0], ev[1], ev[2])
            if not ev[0]:
                return
    except Exception as e:
        print("error calidad", e, flush=True)
    return _enviar_aviso_pre_q(d, cid, item)

'''

unico(r'^def comando\(d, cid, texto\):\n', lambda m: FUNC + m.group(0), "comando")
unico(r'^    elif cmd in \("/propina", "/premium"\):\n',
      lambda m: '    elif cmd == "/calidad" and cid == ADMIN:\n        calidad_cmd(d, cid, args)\n' + m.group(0), "propina")
unico(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), "main")

try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)

copia = RUTA + ".bak_calidad_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
