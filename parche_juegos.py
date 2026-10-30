import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()

if "# --- JUEGOS ---" in src:
    print("Ya estaba aplicado. No hago nada.")
    sys.exit(0)
if "def _a_ahora():" not in src:
    print("ABORTO: falta parche_A.py"); sys.exit(1)

def unico(patron, fn, nombre):
    global src
    n = len(re.findall(patron, src, re.M))
    if n != 1:
        print("ABORTO: ancla '%s' encontrada %d veces" % (nombre, n)); sys.exit(1)
    src = re.sub(patron, fn, src, count=1, flags=re.M)

FUNC = r'''# --- JUEGOS ---
JG_URL = "https://www.gamerpower.com/api/giveaways"
JG_CADA = 1800
JG_MAX_CICLO = 3

def _jg_d(d):
    c = d.setdefault("juegos", {})
    c.setdefault("canal", True)
    c.setdefault("vistos", {})
    c.setdefault("init", False)
    c.setdefault("ult", 0)
    c.setdefault("n", 0)
    return c

def _jg_consulta():
    try:
        r = requests.get(JG_URL, params={"type": "game", "sort-by": "date"}, timeout=25)
        if r.status_code != 200:
            print("juegos HTTP", r.status_code, flush=True)
            return None
        j = r.json()
        if not isinstance(j, list):
            return []
        return [g for g in j if str(g.get("status", "Active")) == "Active" and g.get("id") is not None]
    except Exception as e:
        print("error juegos", e, flush=True)
        return None

def _jg_fin(g):
    s = str(g.get("end_date") or "")
    if not s or s.upper() == "N/A":
        return ""
    try:
        x = _dta.datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=_dta.timezone.utc).astimezone(_a_tz())
        return x.strftime("%d/%m %H:%M")
    except Exception:
        return ""

def _jg_texto(g):
    t = re.sub(r"\s*Giveaway\s*$", "", str(g.get("title") or "Juego"), flags=re.I).strip()
    l = ["\U0001f3ae JUEGO GRATIS", "", t]
    pl = str(g.get("platforms") or "").strip()
    w = str(g.get("worth") or "").strip()
    if pl:
        l.append("Plataforma: " + pl + ((" · Valor: " + w) if w and w.upper() != "N/A" else ""))
    f = _jg_fin(g)
    if f:
        l.append("Disponible hasta: " + f)
    l += ["", str(g.get("open_giveaway_url") or g.get("gamerpower_url") or ""), "", "Fuente: GamerPower"]
    return "\n".join(l)

def _jg_enviar_foto(cid, g, texto):
    foto = g.get("image") or g.get("thumbnail")
    if foto:
        try:
            r = requests.post(API + "/sendPhoto", data={"chat_id": cid, "photo": foto, "caption": texto[:1000]}, timeout=20)
            if r.status_code == 200:
                return 200
            if r.status_code == 403:
                return 403
        except Exception:
            pass
    return enviar(cid, texto)

def _jg_destinos(d):
    out = []
    en_sil = globals().get("_a_en_silencio")
    for cid, us in list(d["users"].items()):
        if cid == ADMIN or not us or not us.get("juegos") or not autorizado(d, cid):
            continue
        if any(us.get(k) for k in ("parado", "pausa", "pausado", "off", "stop")):
            continue
        if en_sil and en_sil(us):
            continue
        out.append(cid)
    return out

def _jg_tarea(d):
    ahora = time.time()
    c = _jg_d(d)
    if ahora - c["ult"] < JG_CADA:
        return
    c["ult"] = ahora
    lista = _jg_consulta()
    if lista is None:
        return
    if not c["init"]:
        for g in lista:
            c["vistos"][str(g["id"])] = int(ahora)
        c["init"] = True
        print("juegos: inicializado con", len(lista), "sorteos activos", flush=True)
        return
    nuevos = [g for g in lista if str(g["id"]) not in c["vistos"]][:JG_MAX_CICLO]
    for g in nuevos:
        c["vistos"][str(g["id"])] = int(ahora)
        c["n"] += 1
        txt = _jg_texto(g)
        f = globals().get("_cp_enviar")
        if c["canal"] and f:
            try:
                f(d, txt)
            except Exception as ex:
                print("error juegos canal", ex, flush=True)
        ids = _jg_destinos(d)
        if ids:
            import threading
            def _run(ids=ids, g=g, txt=txt):
                for cid in ids:
                    try:
                        _jg_enviar_foto(cid, g, txt)
                    except Exception as ex:
                        print("error juegos envio", ex, flush=True)
                    time.sleep(0.06)
            threading.Thread(target=_run, daemon=True).start()
    if len(c["vistos"]) > 400:
        for k in sorted(c["vistos"], key=lambda x: c["vistos"][x])[:-300]:
            c["vistos"].pop(k, None)

def juegos_cmd(d, cid, args):
    c = _jg_d(d)
    us = d["users"].get(cid)
    a = args[0].lower() if args else ""
    if cid == ADMIN and a == "canal":
        if len(args) > 1 and args[1].lower() in ("on", "off"):
            c["canal"] = (args[1].lower() == "on")
        enviar(cid, "\U0001f3ae Juegos gratis en el canal público: %s\n/juegos canal on · /juegos canal off" % ("ACTIVADO" if c["canal"] else "APAGADO"))
        return
    if cid == ADMIN and a == "probar":
        lista = _jg_consulta() or []
        if not lista:
            enviar(cid, "Ahora mismo no hay juegos gratis activos (o la fuente no responde).")
        else:
            _jg_enviar_foto(cid, lista[0], _jg_texto(lista[0]))
        return
    if a in ("on", "off"):
        if us is None:
            enviar(cid, "Primero activa los avisos con /suscribir.")
            return
        us["juegos"] = (a == "on")
        enviar(cid, "\U0001f3ae Avisos de juegos gratis: %s" % ("ACTIVADOS. Te aviso cuando salga uno nuevo." if us["juegos"] else "DESACTIVADOS."))
        return
    estado = "ACTIVADOS" if (us or {}).get("juegos") else "DESACTIVADOS"
    lista = _jg_consulta()
    t = ["\U0001f3ae JUEGOS GRATIS", "", "Avisos: %s" % estado, "/juegos on · /juegos off", ""]
    if lista:
        t.append("Ahora mismo hay %d disponibles:" % len(lista))
        for g in lista[:6]:
            nom = re.sub(r"\s*Giveaway\s*$", "", str(g.get("title") or ""), flags=re.I).strip()
            f = _jg_fin(g)
            t.append("• %s%s" % (nom[:60], (" (hasta %s)" % f) if f else ""))
        t += ["", "Fuente: GamerPower"]
    elif lista is None:
        t.append("No he podido consultar los juegos ahora mismo. Inténtalo en unos minutos.")
    else:
        t.append("Ahora mismo no hay juegos gratis activos.")
    enviar(cid, "\n".join(t))

'''

TAIL = r'''# --- JUEGOS (tarea) ---
_pu_orig_jg = procesar_updates
def procesar_updates(d, *a, **k):
    try:
        _jg_tarea(d)
    except Exception as e:
        print("error tarea juegos", e, flush=True)
    return _pu_orig_jg(d, *a, **k)

AYUDA = AYUDA + "\n\n\U0001f3ae /juegos on - te aviso cuando haya un juego gratis (Epic, Steam, Prime Gaming y más)"

'''

unico(r'^def comando\(d, cid, texto\):\n', lambda m: FUNC + m.group(0), "comando")
unico(r'^    elif cmd in \("/propina", "/premium"\):\n',
      lambda m: '    elif cmd in ("/juegos", "/juegosgratis"):\n        juegos_cmd(d, cid, args)\n' + m.group(0), "propina")
unico(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), "main")

try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)

copia = RUTA + ".bak_juegos_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
