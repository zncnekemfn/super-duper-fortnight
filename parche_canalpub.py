import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()

if "# --- CANAL PUBLICO ---" in src:
    print("Ya estaba aplicado. No hago nada.")
    sys.exit(0)
for marca, nombre in (("# --- CANAL ---", "parche_canal.py"), ("# --- MEJORAS A ---", "parche_A.py"), ("# --- ERRORES ---", "parche_errores.py")):
    if marca not in src:
        print("ABORTO: primero hay que aplicar %s" % nombre)
        sys.exit(1)

def unico(patron, fn, nombre):
    global src
    n = len(re.findall(patron, src, re.M))
    if n != 1:
        print("ABORTO: ancla '%s' encontrada %d veces" % (nombre, n))
        sys.exit(1)
    src = re.sub(patron, fn, src, count=1, flags=re.M)

FUNC = r'''# --- CANAL PUBLICO ---
def _cp_d(d):
    c = d.setdefault("canalpub", {})
    c.setdefault("id", None)
    c.setdefault("on", True)
    c.setdefault("hora", 20)
    c.setdefault("errores", True)
    c.setdefault("pie", "")
    c.setdefault("ult", "")
    c.setdefault("n", 0)
    return c

def _cp_enviar(d, texto):
    c = _cp_d(d)
    if not c["id"] or not c["on"]:
        return False
    try:
        r = requests.post(API + "/sendMessage", data={"chat_id": c["id"], "text": texto[:4000]}, timeout=20)
        if r.status_code == 200:
            c["n"] += 1
            return True
        print("error canal publico", r.status_code, flush=True)
    except Exception as e:
        print("error canal publico", e, flush=True)
    return False

def _cp_top(d, n=5):
    ahora = time.time()
    vistos, out = set(), []
    cand = [v for v in (d.get("dia_top") or {}).values() if ahora - v.get("ts", 0) <= 24 * 3600]
    for it in sorted(cand, key=lambda x: -int(x.get("d") or 0)):
        a = _a_asin(it.get("u"))
        if a in vistos:
            continue
        vistos.add(a)
        out.append(it)
        if len(out) >= n:
            break
    return out

def _cp_pie(d):
    p = _cp_d(d)["pie"]
    return ("\n\n" + p) if p else ""

def _cp_publicar_top(d):
    items = _cp_top(d)
    if not items:
        return False
    t = "\U0001f525 LAS %d MEJORES OFERTAS DE HOY\n\n%s\n\n(%s)%s" % (
        len(items), "\n\n".join(_a_linea(i + 1, it) for i, it in enumerate(items)), AVISO, _cp_pie(d))
    return _cp_enviar(d, t)

def _cp_publicar_error(d, item):
    if not _cp_d(d)["errores"]:
        return
    _cp_enviar(d, "%s\n%s\n\n(%s)%s" % (item["t"], item["u"], AVISO, _cp_pie(d)))

def _cp_tarea(d):
    ahora = time.time()
    if ahora - d.get("cp_ult", 0) < 30:
        return
    d["cp_ult"] = ahora
    c = _cp_d(d)
    if not c["id"] or not c["on"]:
        return
    a = _a_ahora()
    hoy_s = a.strftime("%Y-%m-%d")
    if a.hour == c["hora"] and c["ult"] != hoy_s:
        if _cp_publicar_top(d):
            c["ult"] = hoy_s

def canalpub_admin(d, cid, args):
    c = _cp_d(d)
    rv = _canal_d(d)
    if args:
        a = args[0].lower()
        if a in ("on", "off"):
            c["on"] = (a == "on")
        elif a == "hora" and len(args) > 1 and args[1].isdigit() and 0 <= int(args[1]) <= 23:
            c["hora"] = int(args[1])
            c["ult"] = ""
        elif a == "errores" and len(args) > 1 and args[1].lower() in ("on", "off"):
            c["errores"] = (args[1].lower() == "on")
        elif a == "pie":
            texto = " ".join(args[1:]).strip()
            c["pie"] = "" if texto.lower() in ("", "off", "quitar") else texto[:300]
        elif a == "probar":
            if not c["id"]:
                enviar(cid, "Primero activa el canal público (ver /canalpub).")
            elif _cp_publicar_top(d):
                enviar(cid, "✅ Publicado el top de prueba en el canal.")
            else:
                enviar(cid, "Todavía no hay ofertas guardadas de las últimas 24 horas. Prueba más tarde.")
            return
        elif re.match(r"^-?\d{5,}$", args[0]):
            if rv.get("id") == args[0]:
                enviar(cid, "Ese canal ya está como canal de reenvío a usuarios. Usa otro canal distinto.")
                return
            c["id"] = args[0]
            c["on"] = True
        else:
            enviar(cid, "Uso: /canalpub [on|off|hora 20|errores on|errores off|pie texto|pie off|probar]")
            return
    estado = ("%s · %s" % (c["id"], "ACTIVADO" if c["on"] else "APAGADO")) if c["id"] else "sin canal"
    enviar(cid, "\U0001f4e2 CANAL PÚBLICO DE OFERTAS\n\nEstado: %s\nTop diario: a las %02d:00\nErrores de precio: %s\nPie: %s\nPosts publicados: %d\n\n"
                "Para activarlo: añade el bot como administrador del canal y publica algo; te saldrán botones para elegirlo.\n"
                "/canalpub probar · /canalpub hora 20 · /canalpub errores off · /canalpub pie texto"
                % (estado, c["hora"], "SÍ" if c["errores"] else "NO", c["pie"] or "(sin pie)", c["n"]))

def hook_canales(d, u):
    cq = u.get("callback_query")
    if not cq or not str(cq.get("data") or "").startswith("cn_"):
        return False
    try:
        if str(cq["from"]["id"]) != ADMIN:
            return True
        _, acc, cid_canal = (cq["data"].split("_", 2) + ["", ""])[:3]
        c, rv = _cp_d(d), _canal_d(d)
        if acc == "rv":
            if c.get("id") == cid_canal:
                aviso = "Ese canal ya es el público."
            else:
                rv["id"], rv["on"] = cid_canal, True
                aviso = "Listo: lo que publiques ahí llegará a los usuarios."
        elif acc == "pb":
            if rv.get("id") == cid_canal:
                aviso = "Ese canal ya reenvía a usuarios."
            else:
                c["id"], c["on"] = cid_canal, True
                aviso = "Listo: será el canal público de ofertas. Prueba con /canalpub probar"
        else:
            aviso = "Ignorado."
        try:
            requests.post(API + "/answerCallbackQuery", data={"callback_query_id": cq["id"], "text": aviso[:190]}, timeout=10)
            m = cq.get("message") or {}
            requests.post(API + "/editMessageReplyMarkup", data={
                "chat_id": ADMIN, "message_id": m.get("message_id"), "reply_markup": json.dumps({"inline_keyboard": []})}, timeout=10)
        except Exception:
            pass
        enviar(ADMIN, "\U0001f4e1 " + aviso)
    except Exception as e:
        print("error canales", e, flush=True)
    return True

'''

TAIL = r'''# --- CANAL PUBLICO (envio) ---
_canal_post_orig_cp = _canal_post

def _canal_post(d, post):
    try:
        chat = post.get("chat") or {}
        cid_canal = str(chat.get("id"))
        titulo = chat.get("title") or cid_canal
        c, p = _canal_d(d), _cp_d(d)
        if p["id"] and cid_canal == str(p["id"]):
            return True
        if c["id"] and cid_canal == c["id"]:
            return _canal_post_orig_cp(d, post)
        if cid_canal not in c["avisados"]:
            c["avisados"].append(cid_canal)
            tec = json.dumps({"inline_keyboard": [
                [{"text": "\U0001f4e8 Reenviar a mis usuarios", "callback_data": "cn_rv_" + cid_canal}],
                [{"text": "\U0001f4e2 Canal público de ofertas", "callback_data": "cn_pb_" + cid_canal}],
                [{"text": "\U0001f6ab Ignorar", "callback_data": "cn_no_" + cid_canal}]]})
            enviar(ADMIN, "\U0001f4e1 El bot ha recibido un mensaje del canal \"%s\".\n¿Para qué quieres usarlo?" % titulo, tec)
    except Exception as e:
        print("error canal post", e, flush=True)
    return True

_pu_orig_cp = procesar_updates
def procesar_updates(d, *a, **k):
    try:
        _cp_tarea(d)
    except Exception as e:
        print("error tarea canal publico", e, flush=True)
    return _pu_orig_cp(d, *a, **k)

'''

unico(r'^def comando\(d, cid, texto\):\n', lambda m: FUNC + m.group(0), "comando")
unico(r'^    elif cmd in \("/propina", "/premium"\):\n',
      lambda m: '    elif cmd == "/canalpub" and cid == ADMIN:\n        canalpub_admin(d, cid, args)\n' + m.group(0), "propina")
unico(r'^([ \t]+)if hook_anuncios_pago\(d, u\):\n',
      lambda m: m.group(1) + 'if hook_canales(d, u):\n' + m.group(1) + '    continue\n' + m.group(0), "hook")
unico(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), "main")
unico(r'^(            e\["n"\] \+= 1\n            enviados \+= 1\n)',
      lambda m: ('            try:\n                _cp_publicar_error(d, item)\n'
                 '            except Exception as ex:\n                print("error canal publico", ex, flush=True)\n') + m.group(1), "errores")

try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)

copia = RUTA + ".bak_canalpub_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
