import re, shutil, time, sys

RUTA = "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()

if "def ref_entrada(d, cid, payload):" in src:
    print("Ya estaba aplicado. No hago nada.")
    sys.exit(0)

def unico(patron, fn, nombre):
    global src
    n = len(re.findall(patron, src, re.M))
    if n != 1:
        print("ABORTO: ancla '%s' encontrada %d veces" % (nombre, n))
        sys.exit(1)
    src = re.sub(patron, fn, src, count=1, flags=re.M)

FUNC = '''REF_DIAS_INVITADO = int(os.environ.get("REF_DIAS_INVITADO", "3"))
REF_NIVELES = [(3, 7), (10, 30), (25, 90), (50, 180)]
REF_ENTRADA = os.environ.get("REF_ENTRADA", "") == "1"
REF_BOT = os.environ.get("REF_BOT", "ChivatoAmazon_bot").lstrip("@")

def _ref(d):
    return d.setdefault("ref", {"por": {}, "n": {}, "nivel": {}})

def ref_valido(payload):
    return len(payload) > 1 and payload[0] in "rR" and payload[1:].isdigit()

def ref_entrada(d, cid, payload):
    if not ref_valido(payload):
        return False
    quien = payload[1:]
    r = _ref(d)
    if cid in d["users"] or cid in r["por"] or quien == cid:
        return False
    if quien != ADMIN and quien not in d["users"]:
        return False
    r["por"][cid] = quien
    r["n"][quien] = r["n"].get(quien, 0) + 1
    dar_apoyo(d, cid, REF_DIAS_INVITADO)
    enviar(cid, "\\U0001F381 \\u00a1Bienvenido! Te regalo %d d\\u00edas de apoyo completo por llegar con una invitaci\\u00f3n." % REF_DIAS_INVITADO)
    n = r["n"][quien]
    enviar(quien, "\\U0001F517 Alguien ha entrado con tu enlace. Llevas %d invitado(s)." % n)
    for umbral, dias in REF_NIVELES:
        if n >= umbral > r["nivel"].get(quien, 0):
            r["nivel"][quien] = umbral
            dar_apoyo(d, quien, dias)
            enviar(quien, "\\U0001F3C6 \\u00a1Nivel conseguido! Con %d invitados ganas %d d\\u00edas de apoyo completo." % (umbral, dias))
            enviar(ADMIN, "\\U0001F3C6 Usuario %s ha llegado a %d invitados (+%d d\\u00edas)." % (quien, umbral, dias))
    return True

def ref_mostrar(d, cid):
    import urllib.parse as _up
    r = _ref(d)
    n = r["n"].get(cid, 0)
    sig = None
    for u, dd in REF_NIVELES:
        if u > r["nivel"].get(cid, 0):
            sig = (u, dd)
            break
    link = "https://t.me/%s?start=r%s" % (REF_BOT, cid)
    txt = "\\U0001F517 <b>Tu enlace de invitaci\\u00f3n</b> (toca para copiar):\\n<code>%s</code>\\n\\nInvitados que han entrado: <b>%d</b>\\n" % (link, n)
    if sig:
        txt += "Siguiente premio: a los %d invitados, %d d\\u00edas de apoyo completo (te faltan %d).\\n" % (sig[0], sig[1], max(sig[0] - n, 0))
    else:
        txt += "\\u00a1Has conseguido todos los premios! \\U0001F3C6\\n"
    txt += "Quien entre con tu enlace recibe %d d\\u00edas de apoyo de regalo." % REF_DIAS_INVITADO
    compartir = "https://t.me/share/url?url=" + _up.quote(link) + "&text=" + _up.quote("Avisos de chollos de Amazon en Telegram")
    kb = {"inline_keyboard": [[{"text": "\\U0001F4E4 Compartir mi enlace", "url": compartir}],
                              [{"text": "\\U0001F4CB Men\\u00fa", "callback_data": "m_menu"}]]}
    try:
        requests.post(API + "/sendMessage", data={"chat_id": cid, "text": txt, "parse_mode": "HTML",
                      "disable_web_page_preview": "true", "reply_markup": json.dumps(kb)}, timeout=30)
    except Exception as e:
        print("error referido", e, flush=True)

AYUDA = AYUDA + "\\n\\n\\U0001F517 /referido - Tu enlace para invitar y ganar d\\u00edas de apoyo"

'''
unico(r'^def comando\(d, cid, texto\):\n', lambda m: FUNC + m.group(0), "comando")

# /start con enlace de referido (usuario que ya puede entrar)
unico(r'^    if cmd in \("/start", "/ayuda", "/help"\):\n',
      lambda m: '    if cmd == "/start" and args:\n        ref_entrada(d, cid, args[0])\n' + m.group(0), "start")

# comando /referido
unico(r'^    elif cmd in \("/propina", "/premium"\):\n',
      lambda m: '    elif cmd in ("/referido", "/referral"):\n        ref_mostrar(d, cid)\n' + m.group(0), "propina")

# entrada con referido cuando el modo privado esta activo (solo si REF_ENTRADA=1)
unico(r'^    if codigo and canjear\(d, cid, codigo\):\n',
      lambda m: ('    if REF_ENTRADA and codigo and ref_valido(codigo) and ref_entrada(d, cid, codigo):\n'
                 '        d["autorizados"][cid] = {"codigo": "referido", "ts": int(time.time())}\n'
                 '        ejecutar(d, cid, "/start")\n        return\n') + m.group(0), "acceso")

try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)

copia = RUTA + ".bak_ref_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
