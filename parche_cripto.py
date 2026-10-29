import re, shutil, time, sys

RUTA = "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()

if "def cripto_callback(d, cq):" in src:
    print("Ya estaba aplicado. No hago nada.")
    sys.exit(0)

# 1) Boton "Pagar con cripto" debajo de los de Stars
pat = re.compile(r'("callback_data": "tip_2500"\},\n)([ \t]*)(\], \[\n)')
ms = pat.findall(src)
if len(ms) != 1:
    print("ABORTO: ancla del teclado de propina encontrada", len(ms), "veces")
    sys.exit(1)
def _sub(m):
    ws = m.group(2)
    return (m.group(1) + ws + m.group(3) + ws + "    " +
            '{"text": "\u20bf Pagar con cripto (SOL)", "callback_data": "cripto"},\n' +
            ws + m.group(3))
src = pat.sub(_sub, src, count=1)

# 2) Funcion que gestiona los botones de cripto
FUNC = '''CRYPTO_WALLET = os.environ.get("CRYPTO_WALLET", "").strip()
CRYPTO_PRECIO = os.environ.get("CRYPTO_PRECIO", "0.13").strip()

def _cripto_api(metodo, **datos):
    try:
        return requests.post(API + "/" + metodo, data=datos, timeout=15)
    except Exception as e:
        print("cripto api error", metodo, e, flush=True)

def _cripto_msg(chat, texto, botones=None):
    datos = {"chat_id": chat, "text": texto, "parse_mode": "HTML",
             "disable_web_page_preview": "true"}
    if botones:
        datos["reply_markup"] = json.dumps({"inline_keyboard": botones})
    return _cripto_api("sendMessage", **datos)

def cripto_callback(d, cq):
    import html as _h
    data = cq.get("data") or ""
    if not (data in ("cripto", "crip_ok") or data.startswith("crip_ap_") or data.startswith("crip_no_")):
        return False
    uid = str(cq["from"]["id"])
    _cripto_api("answerCallbackQuery", callback_query_id=cq["id"])
    if data == "cripto":
        if not CRYPTO_WALLET:
            _cripto_msg(uid, "El pago con cripto no est\\u00e1 disponible ahora mismo. Puedes apoyar con Stars.")
            return True
        texto = ("\\u20bf <b>Pagar con cripto</b>\\n\\n"
                 "Env\\u00eda <b>%s SOL</b> a esta direcci\\u00f3n (toca para copiar):\\n\\n"
                 "<code>%s</code>\\n\\n"
                 "\\u26a0\\ufe0f Solo <b>SOL</b> por la red <b>Solana</b>. "
                 "Otros tokens (USDC, SPL\\u2026) u otras redes se pierden y no se pueden recuperar.\\n\\n"
                 "Cuando hayas enviado el pago, pulsa \\u00abYa he pagado\\u00bb. "
                 "Lo reviso a mano y se activa tu apoyo completo (%s d\\u00edas)."
                 % (_h.escape(CRYPTO_PRECIO), _h.escape(CRYPTO_WALLET), DIAS_APOYO))
        _cripto_msg(uid, texto, [[{"text": "\\u2705 Ya he pagado", "callback_data": "crip_ok"}],
                                 [{"text": "\\U0001F4CB Men\\u00fa", "callback_data": "m_menu"}]])
        return True
    if data == "crip_ok":
        if es_apoyante(d, uid):
            _cripto_msg(uid, "Ya tienes el apoyo activo. \\u00a1Gracias!")
            return True
        c = d.setdefault("cripto", {})
        ahora = int(time.time())
        if ahora - c.get(uid, 0) < 600:
            _cripto_msg(uid, "Ya he recibido tu aviso. Lo reviso en cuanto pueda.")
            return True
        c[uid] = ahora
        f = cq["from"]
        nombre = _h.escape((f.get("first_name") or "") + (" @" + f["username"] if f.get("username") else ""))
        _cripto_msg(ADMIN, "\\u20bf <b>Pago cripto pendiente</b>\\nUsuario: %s (ID %s)\\nImporte esperado: %s SOL\\n"
                    "Comprueba en tu wallet que ha entrado antes de aprobar."
                    % (nombre, uid, _h.escape(CRYPTO_PRECIO)),
                    [[{"text": "\\u2705 Aprobar", "callback_data": "crip_ap_" + uid},
                      {"text": "\\u274c Rechazar", "callback_data": "crip_no_" + uid}]])
        _cripto_msg(uid, "Recibido. Reviso el pago y te aviso aqu\\u00ed cuando est\\u00e9 activo.")
        return True
    # aprobar / rechazar: solo el admin
    if uid != ADMIN:
        return True
    destino = data.split("_", 2)[2]
    if data.startswith("crip_ap_"):
        dar_apoyo(d, destino, DIAS_APOYO)
        _cripto_msg(destino, "\\u2705 Pago recibido. Tu apoyo completo est\\u00e1 activo. \\u00a1Gracias!")
        _cripto_msg(ADMIN, "Aprobado: usuario %s." % destino)
    else:
        _cripto_msg(destino, "No he podido confirmar tu pago. Si crees que es un error, escr\\u00edbeme por el chat.")
        _cripto_msg(ADMIN, "Rechazado: usuario %s." % destino)
    return True

'''
a = "def procesar_updates(d):\n"
if src.count(a) != 1:
    print("ABORTO: ancla procesar_updates", src.count(a)); sys.exit(1)
src = src.replace(a, FUNC + a)

# 3) Enganche: nuestros botones se atienden primero
pat2 = re.compile(r'^([ \t]*)cq = u\.get\("callback_query"\)\n', re.M)
ms2 = pat2.findall(src)
if len(ms2) != 1:
    print("ABORTO: ancla del callback encontrada", len(ms2), "veces"); sys.exit(1)
src = pat2.sub(lambda m: m.group(0) + m.group(1) + "if cq and cripto_callback(d, cq):\n" +
               m.group(1) + "    cq = None\n", src, count=1)

try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)

copia = RUTA + ".bak_cripto_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora guarda tu wallet y reinicia (ver instrucciones).")
