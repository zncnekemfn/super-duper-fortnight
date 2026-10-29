import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()

if "# --- CANAL ---" in src:
    print("Ya estaba aplicado. No hago nada.")
    sys.exit(0)

def unico(patron, fn, nombre):
    global src
    n = len(re.findall(patron, src, re.M))
    if n != 1:
        print("ABORTO: ancla '%s' encontrada %d veces" % (nombre, n))
        sys.exit(1)
    src = re.sub(patron, fn, src, count=1, flags=re.M)

FUNC = r'''# --- CANAL ---
def _canal_d(d):
    c = d.setdefault("canal", {})
    c.setdefault("id", None)
    c.setdefault("on", True)
    c.setdefault("avisados", [])
    c.setdefault("n", 0)
    return c

def _canal_dest(d):
    out = []
    for cid in list(d["users"].keys()):
        if cid == ADMIN or not autorizado(d, cid):
            continue
        us = d["users"].get(cid) or {}
        if any(us.get(k) for k in ("parado", "pausa", "pausado", "off", "stop")):
            continue
        out.append(cid)
    return out

def _canal_post(d, post):
    """Mensaje nuevo en un canal. Solo se reenvia si es el canal activado por el admin."""
    try:
        c = _canal_d(d)
        chat = post.get("chat") or {}
        cid_canal = str(chat.get("id"))
        titulo = chat.get("title") or cid_canal
        if not c["id"] or c["id"] != cid_canal:
            if cid_canal not in c["avisados"]:
                c["avisados"].append(cid_canal)
                enviar(ADMIN, "\U0001f4e1 El bot ha recibido un mensaje del canal \"%s\" (%s), que no está activado.\n"
                              "Si es el tuyo, actívalo tocando aquí:\n/canal %s" % (titulo, cid_canal, cid_canal))
            return True
        if not c["on"]:
            return True
        mid = post.get("message_id")
        enviados = 0
        for cid in _canal_dest(d):
            for _intento in range(2):
                try:
                    r = requests.post(API + "/copyMessage", data={
                        "chat_id": cid, "from_chat_id": cid_canal, "message_id": mid}, timeout=20)
                    st = r.status_code
                except Exception:
                    st = 0
                if st == 429:
                    try:
                        time.sleep(min(int(r.json().get("parameters", {}).get("retry_after", 3)), 30))
                    except Exception:
                        time.sleep(3)
                    continue
                break
            if st == 403:
                d["users"].pop(cid, None)
            elif st == 200:
                enviados += 1
            time.sleep(0.05)
        c["n"] = c.get("n", 0) + 1
        enviar(ADMIN, "\U0001f4e1 Mensaje del canal reenviado a %d usuarios." % enviados)
    except Exception as e:
        print("error canal", e)
    return True

def canal_admin(d, cid, args):
    c = _canal_d(d)
    if args and args[0].lower() in ("off", "on"):
        c["on"] = args[0].lower() == "on"
        enviar(cid, "\U0001f4e1 Reenvío del canal: %s" % ("ACTIVADO" if c["on"] else "APAGADO"))
        return
    if args and re.match(r"^-?\d{5,}$", args[0]):
        c["id"] = args[0]
        c["on"] = True
        enviar(cid, "✅ Canal activado (%s). Todo lo que publiques ahí llegará a los usuarios.\n/canal off para apagarlo." % args[0])
        return
    estado = "sin canal activado"
    if c["id"]:
        estado = "canal %s · %s · %d mensajes reenviados" % (c["id"], "ACTIVADO" if c["on"] else "APAGADO", c.get("n", 0))
    enviar(cid, "\U0001f4e1 CANAL\n%s\n\nPara activar uno: añade el bot como administrador del canal y publica algo; "
                "te enviaré el comando exacto.\n/canal off · /canal on" % estado)

'''

unico(r'^def comando\(d, cid, texto\):\n', lambda m: FUNC + m.group(0), "comando")
unico(r'^    elif cmd in \("/propina", "/premium"\):\n',
      lambda m: '    elif cmd == "/canal" and cid == ADMIN:\n        canal_admin(d, cid, args)\n' + m.group(0), "propina")
unico(r'\["message", "callback_query", "pre_checkout_query"\]',
      lambda m: '["message", "callback_query", "pre_checkout_query", "channel_post"]', "allowed_updates")
unico(r'"""Intercepta callbacks pk_/apg_ y los pagos de anuncios\. True = ya gestionado\."""\n',
      lambda m: m.group(0) + '    if u.get("channel_post"):\n        return _canal_post(d, u["channel_post"])\n', "hook")

try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)

copia = RUTA + ".bak_canal_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
