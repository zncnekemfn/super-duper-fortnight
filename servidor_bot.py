import os, re, json, time, requests
import xml.etree.ElementTree as ET

def cargar_env(path="/opt/chivato/.env"):
    try:
        for linea in open(path):
            linea = linea.strip()
            if "=" in linea and not linea.startswith("#"):
                k, v = linea.split("=", 1)
                os.environ.setdefault(k, v)
    except Exception:
        pass

cargar_env()
TOKEN = os.environ["TG_TOKEN"]
ADMIN = str(os.environ["TG_CHAT"])
TAG = os.environ.get("AFFILIATE_TAG", "")
API = f"https://api.telegram.org/bot{TOKEN}"
RSS = "https://www.chollometro.com/rss"
DATA = "/opt/chivato/data.json"
UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"}

INTERVALO = 120
MIN_GUARDAR = 30
UMBRAL_DEF = 50
RETRASO_GRATIS = 600
MAX_AVISOS_GRATIS = 3
MSG_GRATIS_DIA = 3
MIN_PROPINA = 500
MAX_PROPINA = 2500
DIAS_APOYO = 365
ULTIMAS_GRATIS = 3
ULTIMAS_APOYO = 10
MAX_FILTROS = 10
CHAT_MIN = 15
AVISO = "Como afiliado de Amazon obtengo ingresos por las compras adscritas."

def hoy():
    return time.strftime("%Y-%m-%d")

def nuevo_usuario():
    return {"umbral": UMBRAL_DEF, "palabras": [], "dia": "", "n": 0}

def cargar():
    try:
        d = json.load(open(DATA))
    except Exception:
        d = {}
    d.setdefault("users", {})
    d.setdefault("seen", {})
    d.setdefault("recent", [])
    d.setdefault("offset", 0)
    d.setdefault("tips", [])
    d.setdefault("apoyo", {})
    d.setdefault("hilos", {})
    d.setdefault("chat", {})
    d.setdefault("cuota", {})
    if ADMIN not in d["users"]:
        d["users"][ADMIN] = nuevo_usuario()
    return d

def guardar(d):
    tmp = DATA + ".tmp"
    json.dump(d, open(tmp, "w"))
    os.replace(tmp, DATA)

def es_apoyante(d, cid):
    if cid == ADMIN:
        return True
    v = d["apoyo"].get(cid, 0)
    return v == -1 or v > time.time()

def texto_plan(d, cid):
    if cid == ADMIN:
        return "👑 Creador"
    v = d["apoyo"].get(cid, 0)
    if v == -1:
        return "⭐ Apoyante (para siempre)"
    if v > time.time():
        return "⭐ Apoyante hasta " + time.strftime("%d/%m/%Y", time.localtime(v))
    return "Gratis"

def dar_apoyo(d, cid, dias):
    act = d["apoyo"].get(cid, 0)
    if dias == 0 or act == -1:
        d["apoyo"][cid] = -1
    else:
        d["apoyo"][cid] = max(time.time(), act) + dias * 86400

def enviar(chat, texto, markup=None):
    datos = {"chat_id": chat, "text": texto}
    if markup:
        datos["reply_markup"] = markup
    try:
        r = requests.post(API + "/sendMessage", data=datos, timeout=30)
        return r.status_code
    except Exception as e:
        print("error envio", e)
        return 0

def teclado_propina():
    return json.dumps({"inline_keyboard": [[
        {"text": "☕ 500 ⭐", "callback_data": "tip_500"},
        {"text": "🍺 1000 ⭐", "callback_data": "tip_1000"},
        {"text": "🎁 2500 ⭐", "callback_data": "tip_2500"},
    ]]})

def enviar_factura(chat, n):
    datos = {
        "chat_id": chat,
        "title": "Propina ☕ y apoyo al bot",
        "description": f"Propina de {n} Stars. Te conviertes en apoyante y desbloqueas ventajas.",
        "payload": f"tip_{n}",
        "currency": "XTR",
        "prices": json.dumps([{"label": "Propina", "amount": n}]),
    }
    try:
        r = requests.post(API + "/sendInvoice", data=datos, timeout=30)
        if r.status_code != 200:
            print("error factura", r.text[:200])
    except Exception as e:
        print("error factura", e)

def num(s):
    s = s.strip()
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif re.search(r"\.\d{2}$", s):
        pass
    else:
        s = s.replace(".", "")
    return float(s)

def descuento(txt):
    best = 0
    for m in re.findall(r"(\d{2,3})\s*%", txt):
        best = max(best, int(m))
    precios = []
    for m in re.findall(r"(\d[\d.]*(?:,\d{1,2})?)\s*€", txt):
        try:
            p = num(m)
            if p > 0:
                precios.append(p)
        except Exception:
            pass
    if len(precios) >= 2:
        best = max(best, round((1 - min(precios) / max(precios)) * 100))
    return best

def asin_de(txt):
    m = re.search(r"amazon\.es/(?:[^\s\"'<>]*?/)?(?:dp|gp/product)/([A-Z0-9]{10})", txt)
    return m.group(1) if m else None

def pasa_filtros(d, cid, u, dsc, titulo):
    if not es_apoyante(d, cid):
        return dsc >= UMBRAL_DEF
    if dsc < u.get("umbral", UMBRAL_DEF):
        return False
    pal = u.get("palabras", [])
    if pal and not any(p in titulo.lower() for p in pal):
        return False
    return True

def enviar_aviso(d, cid, item):
    msg = f"🔥 ~-{item['d']}%\n{item['t']}\n{item['u']}\n\n({AVISO})"
    if enviar(cid, msg) == 403:
        d["users"].pop(cid, None)
    time.sleep(0.05)

def revisar_feed(d):
    r = requests.get(RSS, headers=UA, timeout=20)
    if r.status_code != 200:
        print("feed HTTP", r.status_code)
        return
    root = ET.fromstring(r.content)
    nuevos = 0
    for it in root.iter("item"):
        try:
            title = (it.findtext("title") or "").strip()
            link = (it.findtext("link") or "").strip()
            raw = it.findtext("description") or ""
            desc = re.sub(r"<[^>]+>", " ", raw)
            merchant = " ".join(
                " ".join(e.attrib.values()) + " " + (e.text or "")
                for e in it if e.tag.lower().endswith("merchant")
            )
            if "amazon" not in f"{title} {desc} {merchant}".lower():
                continue
            dsc = descuento(title)
            if dsc < MIN_GUARDAR or link in d["seen"]:
                continue
            asin = asin_de(raw + " " + merchant)
            url = f"https://www.amazon.es/dp/{asin}?tag={TAG}" if (asin and TAG) else link
            d["seen"][link] = int(time.time())
            item = {"t": title, "u": url, "d": dsc, "ts": int(time.time()), "libre": False}
            d["recent"].append(item)
            d["recent"] = d["recent"][-30:]
            for cid, u in list(d["users"].items()):
                if es_apoyante(d, cid) and pasa_filtros(d, cid, u, dsc, title):
                    enviar_aviso(d, cid, item)
            nuevos += 1
        except Exception as e:
            print("error item", e)
    claves = list(d["seen"].keys())
    for k in claves[:-3000]:
        d["seen"].pop(k, None)
    print("feed ok, nuevos:", nuevos, "suscriptores:", len(d["users"]), flush=True)

def enviar_pendientes(d):
    ahora = time.time()
    for item in d["recent"]:
        if item.get("libre", True) or ahora < item.get("ts", 0) + RETRASO_GRATIS:
            continue
        item["libre"] = True
        for cid, u in list(d["users"].items()):
            if es_apoyante(d, cid):
                continue
            if not pasa_filtros(d, cid, u, item["d"], item["t"]):
                continue
            if u.get("dia") != hoy():
                u["dia"] = hoy()
                u["n"] = 0
            if u.get("n", 0) >= MAX_AVISOS_GRATIS:
                continue
            u["n"] = u.get("n", 0) + 1
            enviar_aviso(d, cid, item)

AYUDA = (
    "🔥 Chivato de Ofertas\n\n"
    "Te aviso de chollos y errores de precio de Amazon con grandes descuentos.\n\n"
    f"🆓 GRATIS: hasta {MAX_AVISOS_GRATIS} avisos al día, con {RETRASO_GRATIS // 60} min de retraso.\n\n"
    "/propina - ☕ hazte apoyante con una propina\n"
    "/contacto - 💬 escribir al creador\n"
    "/suscribir - activar los avisos\n"
    "/parar - dejar de recibirlos\n"
    "/ultimas - últimos chollos\n"
    "/estado - tu plan y configuración\n\n"
    "⭐ APOYANTES (propina desde 500 Stars):\n"
    "• Avisos ilimitados e instantáneos\n"
    "• /umbral para elegir tu descuento mínimo\n"
    "• /filtro móvil: solo chollos de lo que te interesa\n"
    "• Más chollos en /ultimas y chat sin límite\n\n" + AVISO
)

TEXTO_PROPINA = (
    "☕ ¿Te está sirviendo el bot? Con una propina de 500 Stars o más (Telegram Stars) "
    "apoyas el proyecto y te conviertes en ⭐ apoyante, con avisos al instante, "
    "/umbral, /filtro y chat sin límite. ¡Gracias! 💛"
)

def comando(d, cid, texto):
    partes = texto.strip().split()
    cmd = partes[0].split("@")[0].lower()
    args = partes[1:]
    apoyante = es_apoyante(d, cid)
    if cmd in ("/start", "/ayuda", "/help"):
        if cmd == "/start":
            d["users"].setdefault(cid, nuevo_usuario())
        enviar(cid, AYUDA, teclado_propina())
    elif cmd in ("/propina", "/premium"):
        if args and args[0].isdigit():
            n = int(args[0])
            if n < MIN_PROPINA:
                enviar(cid, f"La propina mínima es de {MIN_PROPINA} Stars.", teclado_propina())
            elif n > MAX_PROPINA:
                enviar(cid, f"La propina máxima es de {MAX_PROPINA} Stars.", teclado_propina())
            else:
                enviar_factura(cid, n)
        else:
            enviar(cid, TEXTO_PROPINA, teclado_propina())
    elif cmd == "/suscribir":
        d["users"].setdefault(cid, nuevo_usuario())
        enviar(cid, "✅ Suscrito. Recibirás los chollos con grandes descuentos.")
    elif cmd == "/parar":
        d["users"].pop(cid, None)
        enviar(cid, "🔕 Avisos desactivados. Con /suscribir los reactivas.")
    elif cmd == "/umbral":
        if not apoyante:
            enviar(cid, "⭐ /umbral es para apoyantes (propina desde 500 Stars). Mira /propina.")
        else:
            n = int(args[0]) if args and args[0].isdigit() else None
            if n is None or n < 10 or n > 95:
                enviar(cid, "Uso: /umbral 70 (un número entre 10 y 95).")
            else:
                d["users"].setdefault(cid, nuevo_usuario())["umbral"] = n
                enviar(cid, f"✅ Recibirás chollos de ~-{n}% o más.")
    elif cmd == "/filtro":
        if not apoyante:
            enviar(cid, "⭐ /filtro es para apoyantes (propina desde 500 Stars). Mira /propina.")
        elif not args:
            pal = d["users"].get(cid, {}).get("palabras", [])
            enviar(cid, "Tus filtros: " + (", ".join(pal) if pal else "ninguno") +
                   "\nUso: /filtro móvil  (añade una palabra)\n/quitarfiltro (borra todos)")
        else:
            u = d["users"].setdefault(cid, nuevo_usuario())
            p = " ".join(args).lower()[:30]
            if len(u["palabras"]) >= MAX_FILTROS:
                enviar(cid, f"Máximo {MAX_FILTROS} filtros. Usa /quitarfiltro.")
            else:
                if p not in u["palabras"]:
                    u["palabras"].append(p)
                enviar(cid, "✅ Filtros: " + ", ".join(u["palabras"]))
    elif cmd == "/quitarfiltro":
        if cid in d["users"]:
            d["users"][cid]["palabras"] = []
        enviar(cid, "✅ Filtros borrados.")
    elif cmd == "/ultimas":
        n = ULTIMAS_APOYO if apoyante else ULTIMAS_GRATIS
        rec = [x for x in d["recent"] if apoyante or x.get("libre", True)][-n:][::-1]
        if not rec:
            enviar(cid, "Aún no tengo chollos guardados. Vuelve en un rato.")
        else:
            cuerpo = "\n\n".join(f"🔥 ~-{x['d']}%\n{x['t']}\n{x['u']}" for x in rec)
            enviar(cid, cuerpo + f"\n\n({AVISO})")
    elif cmd == "/estado":
        u = d["users"].get(cid)
        if not u:
            enviar(cid, f"Plan: {texto_plan(d, cid)}\nSuscrito: no. Usa /suscribir.")
        elif apoyante:
            pal = ", ".join(u.get("palabras", [])) or "ninguno"
            enviar(cid, f"Plan: {texto_plan(d, cid)}\nDescuento mínimo: ~-{u['umbral']}%\nFiltros: {pal}")
        else:
            enviar(cid, f"Plan: Gratis\nDescuento mínimo: ~-{UMBRAL_DEF}%\nAvisos con {RETRASO_GRATIS // 60} min de retraso, máx. {MAX_AVISOS_GRATIS} al día.\nMejora con /propina.")
    elif cmd == "/contacto":
        if cid == ADMIN:
            enviar(cid, "Eres el creador 😄. Responde a los mensajes que te lleguen con 'Responder'.")
        else:
            d["chat"][cid] = time.time() + CHAT_MIN * 60
            enviar(cid, "💬 Escribe tu mensaje y se lo envío directamente al creador. /fin para cerrar el chat.")
    elif cmd == "/fin":
        d["chat"].pop(cid, None)
        enviar(cid, "Chat cerrado. Con /contacto lo abres otra vez.")
    elif cid == ADMIN and cmd == "/usuarios":
        ap = sum(1 for k in d["users"] if es_apoyante(d, k) and k != ADMIN)
        enviar(cid, f"Suscriptores: {len(d['users'])}\nApoyantes activos: {ap}")
    elif cid == ADMIN and cmd == "/propinas":
        total = sum(t["n"] for t in d["tips"])
        enviar(cid, f"Propinas: {len(d['tips'])}\nTotal: {total} Stars")
    elif cid == ADMIN and cmd == "/responder":
        if len(args) >= 2 and args[0].isdigit():
            enviar(args[0], "💬 Respuesta del creador:\n" + " ".join(args[1:]))
            enviar(cid, "✅ Enviado")
        else:
            enviar(cid, "Uso: /responder ID texto")
    elif cid == ADMIN and cmd == "/dar":
        if len(args) >= 2 and args[0].isdigit() and args[1].isdigit():
            dar_apoyo(d, args[0], int(args[1]))
            enviar(args[0], "⭐ ¡Ahora eres apoyante! Mira /estado.")
            enviar(cid, "✅ Hecho")
        else:
            enviar(cid, "Uso: /dar ID días (0 = para siempre)")

def reenviar_a_admin(d, cid, m, texto):
    de = m.get("from") or {}
    user = f" @{de['username']}" if de.get("username") else ""
    marca = "⭐ " if es_apoyante(d, cid) else ""
    cab = f"💬 {marca}{de.get('first_name', '')}{user} (ID {cid}):\n{texto}"
    try:
        r = requests.post(API + "/sendMessage", data={"chat_id": ADMIN, "text": cab}, timeout=30).json()
        mid = (r.get("result") or {}).get("message_id")
        if mid:
            d["hilos"][str(mid)] = cid
            if len(d["hilos"]) > 500:
                for k in list(d["hilos"].keys())[:100]:
                    d["hilos"].pop(k, None)
        return bool(mid)
    except Exception as e:
        print("error reenvio", e)
        return False

def mensaje_normal(d, cid, m, txt):
    if cid == ADMIN:
        rep = (m.get("reply_to_message") or {}).get("message_id")
        destino = d["hilos"].get(str(rep)) if rep else None
        if destino:
            enviar(destino, "💬 Respuesta del creador:\n" + txt)
            enviar(ADMIN, "✅ Enviado")
        return
    if d["chat"].get(cid, 0) <= time.time():
        enviar(cid, "Usa /contacto para escribirme o /ayuda para ver los comandos.")
        return
    if not es_apoyante(d, cid):
        c = d["cuota"].setdefault(cid, {"dia": hoy(), "n": 0})
        if c["dia"] != hoy():
            c["dia"] = hoy()
            c["n"] = 0
        if c["n"] >= MSG_GRATIS_DIA:
            enviar(cid, f"Has llegado al límite de {MSG_GRATIS_DIA} mensajes gratis de hoy. Los apoyantes (propina desde {MIN_PROPINA} Stars) tienen chat sin límite: /propina")
            return
        c["n"] += 1
    if reenviar_a_admin(d, cid, m, txt):
        d["chat"][cid] = time.time() + CHAT_MIN * 60
        enviar(cid, "✅ Enviado. Te respondo por aquí en cuanto pueda.")
    else:
        enviar(cid, "No he podido enviarlo ahora mismo. Inténtalo en un rato.")

def procesar_updates(d):
    try:
        r = requests.get(API + "/getUpdates", params={
            "offset": d["offset"], "timeout": 25,
            "allowed_updates": json.dumps(["message", "callback_query", "pre_checkout_query"]),
        }, timeout=40)
        j = r.json()
    except Exception as e:
        print("error updates", e)
        time.sleep(5)
        return
    if not j.get("ok"):
        print("telegram:", j.get("description"))
        time.sleep(30)
        return
    for u in j.get("result", []):
        d["offset"] = u["update_id"] + 1
        pq = u.get("pre_checkout_query")
        if pq:
            ok = pq.get("total_amount", 0) >= MIN_PROPINA
            datos = {"pre_checkout_query_id": pq["id"], "ok": "true" if ok else "false"}
            if not ok:
                datos["error_message"] = f"La propina mínima es de {MIN_PROPINA} Stars."
            requests.post(API + "/answerPreCheckoutQuery", data=datos, timeout=15)
            continue
        cq = u.get("callback_query")
        if cq:
            requests.post(API + "/answerCallbackQuery", data={"callback_query_id": cq["id"]}, timeout=15)
            cb = cq.get("data", "")
            cid = str(((cq.get("message") or {}).get("chat") or {}).get("id", ""))
            if cid and cb.startswith("tip_") and cb[4:].isdigit():
                enviar_factura(cid, int(cb[4:]))
            continue
        m = u.get("message") or {}
        chat = m.get("chat") or {}
        cid = str(chat.get("id"))
        sp = m.get("successful_payment")
        if sp:
            n = sp.get("total_amount", 0)
            d["tips"].append({"u": cid, "n": n, "t": int(time.time())})
            if n >= MIN_PROPINA:
                dar_apoyo(d, cid, DIAS_APOYO)
                d["users"].setdefault(cid, nuevo_usuario())
            enviar(cid, f"💛 ¡Muchas gracias por tu propina de {n} Stars!\nAhora eres: {texto_plan(d, cid)}\nMira /ayuda y /estado para ver tus ventajas.")
            enviar(ADMIN, f"☕ Nueva propina: {n} Stars (usuario {cid})")
            continue
        if chat.get("type") != "private":
            continue
        txt = m.get("text") or ""
        if txt.startswith("/"):
            comando(d, cid, txt)
        elif txt:
            mensaje_normal(d, cid, m, txt)
    guardar(d)

def main():
    d = cargar()
    ultimo = 0
    print("Bot iniciado", flush=True)
    while True:
        try:
            if time.time() - ultimo >= INTERVALO:
                try:
                    revisar_feed(d)
                except Exception as e:
                    print("error feed", e, flush=True)
                ultimo = time.time()
            enviar_pendientes(d)
            guardar(d)
            procesar_updates(d)
        except Exception as e:
            print("error general", e, flush=True)
            time.sleep(10)

if __name__ == "__main__":
    main()
