import sys
ruta = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
s = open(ruta, encoding="utf-8").read()
if "def difundir(" in s:
    print("La publicidad ya estaba instalada.")
    sys.exit(0)
if "def autorizado(" not in s or "def ejecutar(" not in s:
    print("Faltan antes el menú y el modo privado.")
    sys.exit(1)

def cambiar(viejo, nuevo):
    global s
    if s.count(viejo) != 1:
        print("NO ENCONTRADO:", viejo[:70])
        sys.exit(1)
    s = s.replace(viejo, nuevo)

# --- ajustes
import re
s, n_ = re.subn(r'^(CHAT_MIN = 15.*)$', r'\1\nANUNCIOS_MES = 1\nTABLON_DIAS = 30\nMAX_TABLON = 10', s, count=1, flags=re.M)
if n_ != 1:
    print("NO ENCONTRADO: CHAT_MIN")
    sys.exit(1)

cambiar(r'''    d.setdefault("cuota", {})
''', r'''    d.setdefault("cuota", {})
    d.setdefault("anuncios", {})
    d.setdefault("tablon", [])
    d.setdefault("sinpub", {})
    d.setdefault("ult_pub", {})
    d.setdefault("cuota_anuncio", {})
''')

# --- fotos adjuntas a los comandos (pie de foto)
cambiar(r'''        txt = m.get("text") or ""
''', r'''        txt = m.get("text") or m.get("caption") or ""
        _foto[0] = m["photo"][-1]["file_id"] if m.get("photo") else None
''')

# --- botones de anuncios
cambiar(r'''            elif cid and cb.startswith("m_"):
                ejecutar(d, cid, "/" + cb[2:])
            continue''', r'''            elif cid and cb.startswith("m_"):
                ejecutar(d, cid, "/" + cb[2:])
            elif cid and (cb.startswith("ad_") or cb.startswith("adm_")):
                callback_anuncio(d, cid, cb)
            continue''')

# --- menú y ayuda
cambiar(r'''        [b("❓ Ayuda", "m_ayuda"), b("🔄 Refresh", "m_menu")],''',
        r'''        [b("📌 Tablón", "m_tablon"), b("📢 Anunciar", "m_anunciar")],
        [b("❓ Ayuda", "m_ayuda"), b("🔄 Refresh", "m_menu")],''')
cambiar(r'''    "/ultimas - últimos chollos\n"''', r'''    "/ultimas - últimos chollos\n"
    "/tablon - 📌 tablón de anuncios\n"''')
cambiar(r'''    "• Más chollos en /ultimas y chat sin límite\n\n" + AVISO''',
        r'''    "• Más chollos en /ultimas y chat sin límite\n"
    "• /anunciar: publica tu anuncio en el bot (1 al mes)\n"
    "• /sinpublicidad: quitar la publicidad\n\n" + AVISO''')

funciones = r'''_foto = [None]

def parsear_anuncio(texto):
    partes = [p.strip() for p in texto.split("|")]
    t = partes[0] if partes else ""
    enlace = partes[1] if len(partes) > 1 else ""
    boton = partes[2] if len(partes) > 2 and partes[2] else "👉 Ver oferta"
    if not t or not enlace.lower().startswith(("http://", "https://")):
        return None
    return {"texto": t[:700], "enlace": enlace, "boton": boton[:30]}

def nuevo_id_anuncio(d):
    d["anuncio_n"] = d.get("anuncio_n", 0) + 1
    return "a" + str(d["anuncio_n"])

def teclado_anuncio(aid, boton):
    return json.dumps({"inline_keyboard": [[{"text": boton, "callback_data": "ad_" + aid}]]})

def teclado_difusion(aid):
    return json.dumps({"inline_keyboard": [
        [{"text": "📤 Enviar a todos", "callback_data": "adm_all_" + aid}],
        [{"text": "⭐ Solo apoyantes", "callback_data": "adm_ap_" + aid}],
        [{"text": "🗑 Borrar", "callback_data": "adm_no_" + aid}],
    ]})

def teclado_aprobar(aid):
    return json.dumps({"inline_keyboard": [
        [{"text": "📢 Difundir + tablón", "callback_data": "adm_dif_" + aid}],
        [{"text": "📌 Solo tablón", "callback_data": "adm_tab_" + aid}],
        [{"text": "❌ Rechazar", "callback_data": "adm_no_" + aid}],
    ]})

def enviar_anuncio(d, cid, ad, aid, etiqueta):
    cab = etiqueta + "\n\n" + ad["texto"]
    mk = teclado_anuncio(aid, ad["boton"])
    try:
        if ad.get("foto"):
            r = requests.post(API + "/sendPhoto", data=prot({"chat_id": cid, "photo": ad["foto"],
                              "caption": cab[:1000], "reply_markup": mk}, cid), timeout=30)
        else:
            r = requests.post(API + "/sendMessage", data=prot({"chat_id": cid, "text": cab,
                              "reply_markup": mk}, cid), timeout=30)
        return r.status_code
    except Exception as e:
        print("error anuncio", e)
        return 0

def difundir(d, aid, solo_apoyantes=False):
    ad = d["anuncios"][aid]
    et = "📢 Publicidad" if ad.get("tipo") != "apoyante" else "📢 Publicidad · anuncio de un apoyante ⭐"
    enviados = 0
    for cid in list(d["users"].keys()):
        if cid == ADMIN or cid == ad.get("autor") or not autorizado(d, cid):
            continue
        ap = es_apoyante(d, cid)
        if (solo_apoyantes and not ap) or (ap and d["sinpub"].get(cid)):
            continue
        if d["ult_pub"].get(cid) == hoy():
            continue
        st = enviar_anuncio(d, cid, ad, aid, et)
        if st == 403:
            d["users"].pop(cid, None)
            continue
        if st == 200:
            d["ult_pub"][cid] = hoy()
            enviados += 1
        time.sleep(0.05)
    ad["env"] = ad.get("env", 0) + enviados
    ad["estado"] = "difundido"
    return enviados

def tablon_activo(d):
    lim = time.time() - TABLON_DIAS * 86400
    ids = [a for a in d["tablon"] if a in d["anuncios"] and d["anuncios"][a].get("ts_tab", 0) > lim]
    return ids[-MAX_TABLON:][::-1]

def callback_anuncio(d, cid, cb):
    if cb.startswith("ad_"):
        ad = d["anuncios"].get(cb[3:])
        if not ad or not autorizado(d, cid):
            return
        if cid != ADMIN:
            ad["clics"] = ad.get("clics", 0) + 1
            ad.setdefault("u", {})[cid] = 1
        enviar(cid, "🔗 " + ad["enlace"])
        return
    if cid != ADMIN:
        return
    partes = cb.split("_")
    if len(partes) != 3:
        return
    accion, aid = partes[1], partes[2]
    ad = d["anuncios"].get(aid)
    if not ad:
        enviar(ADMIN, "No encuentro ese anuncio.")
        return
    autor = ad.get("autor")
    if accion == "no":
        ad["estado"] = "rechazado"
        if autor:
            d["cuota_anuncio"].get(autor, {}).update({"n": 0})
            enviar(autor, "Tu anuncio no se ha podido publicar. Puedes enviar otro con /anunciar.")
        enviar(ADMIN, f"🗑 Anuncio {aid} descartado.")
    elif accion in ("all", "ap"):
        n = difundir(d, aid, accion == "ap")
        enviar(ADMIN, f"📤 Anuncio {aid} enviado a {n} personas.")
    elif accion in ("tab", "dif"):
        ad["ts_tab"] = int(time.time())
        d["tablon"].append(aid)
        ad["estado"] = "tablon"
        n = difundir(d, aid) if accion == "dif" else 0
        enviar(ADMIN, f"📌 Anuncio {aid} publicado en el tablón" + (f" y enviado a {n} personas." if accion == "dif" else "."))
        if autor:
            enviar(autor, "✅ Tu anuncio ya está publicado. Mira /tablon")

AYUDA = ('''
cambiar('AYUDA = (', funciones)

usuario = r'''    elif cmd == "/tablon":
        ids = tablon_activo(d)
        if not ids:
            enviar(cid, "📌 TABLÓN DE ANUNCIOS\n\nAún no hay anuncios. Los apoyantes ⭐ pueden publicar el suyo con /anunciar.")
        else:
            lin = [f"{i + 1}. {d['anuncios'][a]['texto'][:200]}" for i, a in enumerate(ids)]
            filas = []
            fila = []
            for i, a in enumerate(ids):
                fila.append({"text": f"👉 {i + 1}", "callback_data": "ad_" + a})
                if len(fila) == 5:
                    filas.append(fila)
                    fila = []
            if fila:
                filas.append(fila)
            enviar(cid, "📌 TABLÓN DE ANUNCIOS (publicidad de apoyantes)\n\n" + "\n\n".join(lin) +
                   "\n\nPulsa el número para abrir el enlace.", json.dumps({"inline_keyboard": filas}))
    elif cmd == "/anunciar":
        mes = time.strftime("%Y-%m")
        usado = d["cuota_anuncio"].get(cid, {})
        if not apoyante:
            enviar(cid, "⭐ /anunciar es una ventaja de apoyantes (propina desde 500 Stars). Mira /propina.")
        elif cid != ADMIN and usado.get("mes") == mes and usado.get("n", 0) >= ANUNCIOS_MES:
            enviar(cid, f"Ya has usado tu anuncio de este mes ({ANUNCIOS_MES}). Se renueva el mes que viene.")
        elif not args:
            enviar(cid, "📢 PUBLICA TU ANUNCIO\n\nEscribe:\n/anunciar texto | enlace | texto del botón\n\n"
                        "Ejemplo:\n/anunciar Vendo funda para iPhone, 5 € | https://ejemplo.com/funda | 👉 Ver\n\n"
                        "Para añadir una foto, escribe el comando en el pie de la foto. Lo reviso antes de publicarlo.")
        else:
            dat = parsear_anuncio(" ".join(args))
            if not dat:
                enviar(cid, "No entiendo el formato. Usa: /anunciar texto | https://enlace | botón")
            else:
                aid = nuevo_id_anuncio(d)
                dat.update({"tipo": "apoyante", "autor": cid, "estado": "pendiente", "ts": int(time.time()),
                            "foto": _foto[0], "env": 0, "clics": 0, "u": {}})
                d["anuncios"][aid] = dat
                n = usado.get("n", 0) + 1 if usado.get("mes") == mes else 1
                d["cuota_anuncio"][cid] = {"mes": mes, "n": n}
                enviar(cid, "✅ Recibido. Lo reviso y te aviso cuando esté publicado.")
                enviar_anuncio(d, ADMIN, dat, aid, f"📥 Anuncio pendiente {aid} de {cid}")
                enviar(ADMIN, f"¿Qué hago con el anuncio {aid}?", teclado_aprobar(aid))
    elif cmd == "/sinpublicidad":
        if not apoyante:
            enviar(cid, "⭐ Quitar la publicidad es una ventaja de apoyantes. Mira /propina.")
        else:
            nuevo = not d["sinpub"].get(cid)
            d["sinpub"][cid] = nuevo
            enviar(cid, "🔕 Publicidad desactivada. Con /sinpublicidad la vuelves a activar." if nuevo
                   else "📢 Publicidad activada otra vez.")
    elif cmd == "/suscribir":'''
cambiar(r'''    elif cmd == "/suscribir":''', usuario)

admin = r'''    elif cid == ADMIN and cmd == "/anuncio":
        dat = parsear_anuncio(" ".join(args)) if args else None
        if not dat:
            enviar(cid, "Uso:\n/anuncio texto | https://enlace | texto del botón\n\nCon foto: escribe el comando en el pie de la foto.")
        else:
            aid = nuevo_id_anuncio(d)
            dat.update({"tipo": "patrocinador", "estado": "borrador", "ts": int(time.time()),
                        "foto": _foto[0], "env": 0, "clics": 0, "u": {}})
            d["anuncios"][aid] = dat
            enviar_anuncio(d, ADMIN, dat, aid, "📢 Publicidad")
            enviar(cid, f"Vista previa del anuncio {aid}. ¿Qué hago?", teclado_difusion(aid))
    elif cid == ADMIN and cmd == "/anuncios":
        if not d["anuncios"]:
            enviar(cid, "No hay anuncios. Crea uno con /anuncio")
        else:
            lin = []
            for aid, a in list(d["anuncios"].items())[-10:][::-1]:
                env, cl = a.get("env", 0), a.get("clics", 0)
                ctr = f"{cl * 100 / env:.1f}%" if env else "-"
                lin.append(f"{aid} · {a.get('tipo')} · {a.get('estado')}\n   enviados {env} · clics {cl} ({len(a.get('u', {}))} únicos) · CTR {ctr}\n   {a['texto'][:50]}")
            enviar(cid, "\n\n".join(lin))
    elif cid == ADMIN and cmd == "/informe":
        a = d["anuncios"].get(args[0]) if args else None
        if not a:
            enviar(cid, "Uso: /informe a3  (mira los IDs con /anuncios)")
        else:
            env, cl = a.get("env", 0), a.get("clics", 0)
            ctr = f"{cl * 100 / env:.1f}%" if env else "-"
            tab = "sí" if args[0] in tablon_activo(d) else "no"
            enviar(cid, f"📊 INFORME DE TU ANUNCIO\n\n\"{a['texto'][:80]}\"\n\n• Personas que lo recibieron: {env}\n"
                        f"• Clics en el botón: {cl}\n• Personas distintas que hicieron clic: {len(a.get('u', {}))}\n"
                        f"• Porcentaje de clics: {ctr}\n• Visible ahora en el tablón: {tab}")
    elif cid == ADMIN and cmd == "/quitaranuncio":
        if args and args[0] in d["tablon"]:
            d["tablon"].remove(args[0])
            enviar(cid, "✅ Quitado del tablón.")
        else:
            enviar(cid, "Uso: /quitaranuncio a3")
    elif cid == ADMIN and cmd == "/usuarios":'''
cambiar(r'''    elif cid == ADMIN and cmd == "/usuarios":''', admin)

open(ruta, "w", encoding="utf-8").write(s)
print("Publicidad instalada correctamente")
