import sys
ruta = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
s = open(ruta, encoding="utf-8").read()
if "def autorizado(" in s:
    print("El modo privado ya estaba instalado.")
    sys.exit(0)
if "def ejecutar(" not in s:
    print("Falta instalar antes el menú (actualizar_menu.py).")
    sys.exit(1)

def cambiar(viejo, nuevo):
    global s
    if s.count(viejo) != 1:
        print("NO ENCONTRADO:", viejo[:70])
        sys.exit(1)
    s = s.replace(viejo, nuevo)

cambiar(r'''import os, re, json, time, requests''', r'''import os, re, json, time, secrets, string, requests''')

# --- protección de contenido (no reenviar ni guardar) en todo lo que reciben los usuarios
cambiar(r'''def hoy():
    return time.strftime("%Y-%m-%d")''', r'''def hoy():
    return time.strftime("%Y-%m-%d")

def prot(datos, chat):
    if str(chat) != ADMIN:
        datos["protect_content"] = "true"
    return datos''')

cambiar(r'''    datos = {"chat_id": chat, "text": texto}''', r'''    datos = prot({"chat_id": chat, "text": texto}, chat)''')

cambiar(r'''data={"chat_id": chat, "caption": texto, "reply_markup": mk}''',
        r'''data=prot({"chat_id": chat, "caption": texto, "reply_markup": mk}, chat)''')
cambiar(r'''data={"chat_id": chat}, files''', r'''data=prot({"chat_id": chat}, chat), files''')
cambiar(r'''data={"chat_id": chat, "text": texto, "reply_markup": mk}''',
        r'''data=prot({"chat_id": chat, "text": texto, "reply_markup": mk}, chat)''')

# --- datos del modo privado
cambiar(r'''    if ADMIN not in d["users"]:
        d["users"][ADMIN] = nuevo_usuario()
    return d''', r'''    d.setdefault("codigos", {})
    d.setdefault("autorizados", {})
    if not d.get("migrado_privado"):
        for k in list(d["users"]) + list(d["apoyo"]):
            d["autorizados"].setdefault(k, {"codigo": "previo", "ts": int(time.time())})
        d["migrado_privado"] = True
    if ADMIN not in d["users"]:
        d["users"][ADMIN] = nuevo_usuario()
    return d''')

funciones = r'''TEXTO_PRIVADO = (
    "🔒 Este bot es privado y funciona solo con invitación.\n\n"
    "Si tienes un código, envíalo así:\n/start TUCODIGO\n\n"
    "Si no tienes, pídeselo al creador."
)
_bot_user = [None]

def usuario_bot():
    if not _bot_user[0]:
        try:
            _bot_user[0] = requests.get(API + "/getMe", timeout=15).json()["result"]["username"]
        except Exception:
            return None
    return _bot_user[0]

def autorizado(d, cid):
    return cid == ADMIN or not d.get("privado", True) or cid in d["autorizados"]

def nuevo_codigo(d):
    while True:
        c = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        if c not in d["codigos"]:
            return c

def canjear(d, cid, codigo):
    cod = codigo.strip().upper()
    c = d["codigos"].get(cod)
    if not c:
        return False
    if c.get("exp") and time.time() > c["exp"]:
        d["codigos"].pop(cod, None)
        return False
    if c.get("usos", 0) <= 0:
        d["codigos"].pop(cod, None)
        return False
    c["usos"] -= 1
    d["autorizados"][cid] = {"codigo": cod, "ts": int(time.time())}
    enviar(ADMIN, f"🔑 Nuevo usuario con el código {cod} (ID {cid}). Usos que le quedan al código: {c['usos']}")
    if c["usos"] <= 0:
        d["codigos"].pop(cod, None)
    return True

def acceso(d, cid, cmd, args):
    codigo = args[0] if (cmd == "/start" and args) else None
    if codigo and canjear(d, cid, codigo):
        enviar(cid, "✅ Código aceptado. ¡Bienvenido!")
        ejecutar(d, cid, "/start")
    elif codigo:
        enviar(cid, "❌ Ese código no es válido, ya se ha usado o ha caducado. Pide uno nuevo al creador.")
    else:
        enviar(cid, TEXTO_PRIVADO)

AYUDA = ('''
cambiar('AYUDA = (', funciones)

cambiar(r'''def ejecutar(d, cid, texto):
    cmd = texto.strip().split()[0].split("@")[0].lower()''', r'''def ejecutar(d, cid, texto):
    cmd = texto.strip().split()[0].split("@")[0].lower()
    if not autorizado(d, cid):
        acceso(d, cid, cmd, texto.strip().split()[1:])
        return''')

cambiar(r'''def mensaje_normal(d, cid, m, txt):
    if cid == ADMIN:''', r'''def mensaje_normal(d, cid, m, txt):
    if not autorizado(d, cid):
        partes = txt.strip().split()
        acceso(d, cid, "/start", partes[:1] if len(partes) == 1 else [])
        return
    if cid == ADMIN:''')

admin = r'''    elif cid == ADMIN and cmd == "/codigo":
        usos = int(args[0]) if args and args[0].isdigit() and int(args[0]) > 0 else 1
        dias = int(args[1]) if len(args) > 1 and args[1].isdigit() else 7
        cod = nuevo_codigo(d)
        d["codigos"][cod] = {"usos": usos, "exp": (time.time() + dias * 86400) if dias else 0, "ts": int(time.time())}
        bot = usuario_bot()
        enlace = f"https://t.me/{bot}?start={cod}" if bot else f"/start {cod}"
        cad = f"en {dias} días" if dias else "nunca"
        enviar(cid, f"🔑 Código: {cod}\nUsos: {usos} · Caduca: {cad}\n\nEnlace para enviar a la persona:\n{enlace}")
    elif cid == ADMIN and cmd == "/codigos":
        if not d["codigos"]:
            enviar(cid, "No hay códigos activos. Crea uno con /codigo")
        else:
            lin = []
            for k, v in d["codigos"].items():
                cad = time.strftime("%d/%m/%Y", time.localtime(v["exp"])) if v.get("exp") else "sin caducidad"
                lin.append(f"{k} · usos: {v['usos']} · caduca: {cad}")
            enviar(cid, "Códigos activos:\n" + "\n".join(lin))
    elif cid == ADMIN and cmd == "/revocar":
        ok = bool(args) and d["codigos"].pop(args[0].upper(), None) is not None
        enviar(cid, "✅ Código revocado" if ok else "No encuentro ese código. Mira /codigos")
    elif cid == ADMIN and cmd == "/expulsar":
        if args and args[0].isdigit():
            for clave in ("autorizados", "users", "chat"):
                d[clave].pop(args[0], None)
            enviar(cid, f"✅ Usuario {args[0]} expulsado. Ya no puede usar el bot.")
        else:
            enviar(cid, "Uso: /expulsar ID")
    elif cid == ADMIN and cmd == "/privado":
        if args and args[0].lower() in ("on", "off"):
            d["privado"] = args[0].lower() == "on"
            if d["privado"]:
                for k in list(d["users"]) + list(d["apoyo"]):
                    d["autorizados"].setdefault(k, {"codigo": "abierto", "ts": int(time.time())})
        enviar(cid, "Modo privado: " + ("ACTIVADO 🔒 (solo con código)" if d.get("privado", True) else "DESACTIVADO 🔓 (abierto a todos)") +
               f"\nUsuarios autorizados: {len(d['autorizados'])}\nUso: /privado on  o  /privado off")
    elif cid == ADMIN and cmd == "/usuarios":'''
cambiar(r'''    elif cid == ADMIN and cmd == "/usuarios":''', admin)

open(ruta, "w", encoding="utf-8").write(s)
print("Modo privado y protección de mensajes instalados correctamente")
