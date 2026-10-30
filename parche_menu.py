import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()

if "# --- MENU ---" in src:
    print("Ya estaba aplicado. No hago nada.")
    sys.exit(0)

def unico(patron, fn, nombre):
    global src
    n = len(re.findall(patron, src, re.M))
    if n != 1:
        print("ABORTO: ancla '%s' encontrada %d veces" % (nombre, n))
        sys.exit(1)
    src = re.sub(patron, fn, src, count=1, flags=re.M)

def opcional(patron, fn, nombre):
    global src
    n = len(re.findall(patron, src, re.M))
    if n != 1:
        print("AVISO: '%s' encontrado %d veces, no se cambia (no es grave)" % (nombre, n))
        return
    src = re.sub(patron, fn, src, count=1, flags=re.M)

FUNC = r'''# --- MENU ---
def _menu_texto(d, cid):
    t = "\U0001f4cb MENÚ\n\n"
    try:
        u = d["users"].get(cid)
        if u is None:
            return t + "Aún no tienes los avisos activos. Pulsa ✅ Suscribir para empezar.\n\nElige una opción \U0001f447"
        t += "\U0001f3af Descuento mínimo: %s%%\n" % u.get("umbral", UMBRAL_DEF)
        cats = u.get("cats") or []
        t += "\U0001f4c2 Categorías: %s\n" % (("%d elegidas" % len(cats)) if cats else "todas")
        pal = u.get("palabras") or []
        if pal:
            t += "\U0001f50e Palabras clave: %d\n" % len(pal)
        if "seguir_cmd" in globals():
            t += "\U0001f514 Siguiendo: %d productos\n" % len((d.get("seguir") or {}).get(cid, []))
        s = u.get("sil")
        if s and len(s) == 2:
            t += "\U0001f319 No molestar: %02d:00 a %02d:00\n" % (s[0], s[1])
        if u.get("res") is not None:
            t += "\U0001f5de Resumen diario: %02d:00\n" % u["res"]
    except Exception as e:
        print("error menu texto", e, flush=True)
    return t + "\nElige una opción \U0001f447"

def teclado_menu():
    def b(texto, cb):
        return {"text": texto, "callback_data": cb}
    filas = [
        [b("☕ Propina Café", "m_propina")],
        [b("\U0001f525 Últimas", "m_ultimas"), b("\U0001f4cc Tablón", "m_tablon")],
        [b("\U0001f514 Seguir", "m_seguir"), b("\U0001f4c2 Categorías", "m_categorias"), b("\U0001f3af Descuento", "m_umbral")],
        [b("\U0001f319 No molestar", "m_silencio"), b("\U0001f5de Resumen", "m_resumen"), b("\U0001f4ca Mi estado", "m_estado")],
        [b("\U0001f381 Invitar", "m_referido"), b("\U0001f4e2 Anunciar", "m_anunciar")],
        [b("\U0001f50e Filtro", "m_filtro"), b("\U0001f4ac Contacto", "m_contacto")],
        [b("✅ Suscribir", "m_suscribir"), b("\U0001f515 Parar", "m_parar")],
        [b("❓ Ayuda", "m_ayuda"), b("\U0001f504 Actualizar", "mn_ref")],
    ]
    falta = {"m_seguir": "seguir_cmd", "m_categorias": "cat_menu", "m_silencio": "silencio_cmd", "m_resumen": "resumen_cmd"}
    out = []
    for fila in filas:
        fila = [x for x in fila if falta.get(x["callback_data"]) is None or falta[x["callback_data"]] in globals()]
        if fila:
            out.append(fila)
    return json.dumps({"inline_keyboard": out})

def hook_menu(d, u):
    cq = u.get("callback_query")
    if not cq or cq.get("data") != "mn_ref":
        return False
    try:
        m = cq.get("message") or {}
        cid = str((m.get("chat") or {}).get("id", ""))
        try:
            requests.post(API + "/answerCallbackQuery", data={"callback_query_id": cq["id"], "text": "Actualizado"}, timeout=10)
        except Exception:
            pass
        if cid:
            requests.post(API + "/editMessageText", data={
                "chat_id": cid, "message_id": m.get("message_id"),
                "text": _menu_texto(d, cid), "reply_markup": teclado_menu()}, timeout=15)
    except Exception as e:
        print("error menu", e, flush=True)
    return True

'''

unico(r'^def comando\(d, cid, texto\):\n', lambda m: FUNC + m.group(0), "comando")
unico(r'"[^"\n]*MEN[^"\n]*\\nElige una opci[^"\n]*"', lambda m: '_menu_texto(d, cid)', "texto menu")
unico(r'^([ \t]+)if hook_anuncios_pago\(d, u\):\n',
      lambda m: m.group(1) + 'if hook_menu(d, u):\n' + m.group(1) + '    continue\n' + m.group(0), "hook")
opcional(r'/propina - \\u2615 apoya el proyecto con una propina \(opcional\)',
         lambda m: '/propina - \\u2615 Propina Caf\\u00e9 (opcional)', "ayuda propina")

try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)

copia = RUTA + ".bak_menu_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
