import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()

if "# --- ANUNCIOS DE PAGO ---" in src:
    print("Ya estaba aplicado. No hago nada.")
    sys.exit(0)

def unico(patron, fn, nombre):
    global src
    n = len(re.findall(patron, src, re.M))
    if n != 1:
        print("ABORTO: ancla '%s' encontrada %d veces" % (nombre, n))
        sys.exit(1)
    src = re.sub(patron, fn, src, count=1, flags=re.M)

def opcional(patron, nuevo, nombre):
    global src
    if len(re.findall(patron, src, re.M)) == 1:
        src = re.sub(patron, lambda m: nuevo, src, count=1, flags=re.M)
    else:
        print("(aviso: texto '%s' no encontrado, se deja como estaba)" % nombre)

FUNC = r'''
# --- ANUNCIOS DE PAGO ---
import datetime as _dt

AP_MAX_DIA = 3
AP_SEL_MIN = 60
PAQ_AP = {
    "t7": {"n": "Tabl\u00f3n 7 d\u00edas", "stars": 500, "dias": 7, "horas": [13],
           "d": "7 d\u00edas en /tablon + 1 env\u00edo al d\u00eda a las 13:00"},
    "t30": {"n": "Tabl\u00f3n 30 d\u00edas", "stars": 2000, "dias": 30, "horas": [10, 15, 20],
            "d": "30 d\u00edas en /tablon + 3 env\u00edos al d\u00eda (10:00, 15:00 y 20:00)"},
    "dif": {"n": "Difusi\u00f3n a todos", "stars": 2500, "dias": 0, "horas": [],
            "d": "1 env\u00edo \u00fanico a todos los usuarios"},
}

def _apd(d):
    for k in ("ap_sel", "pub_dia", "ap_rot", "ap_hechos"):
        d.setdefault(k, {})
    d.setdefault("ventas_ads", [])

def _ap_ahora():
    try:
        from zoneinfo import ZoneInfo
        return _dt.datetime.now(ZoneInfo("Europe/Madrid"))
    except Exception:
        return _dt.datetime.utcnow() + _dt.timedelta(hours=1)

def _ap_texto_menu(apoyante):
    t = "\U0001f4e2 AN\u00daNCIATE EN EL BOT\n\nElige un paquete. Se paga en Stars \u2b50 y solo cuando yo apruebe tu anuncio:\n\n"
    for pk in ("t7", "t30", "dif"):
        p = PAQ_AP[pk]
        t += "\u2022 %s \u00b7 %d \u2b50\n  %s\n\n" % (p["n"], p["stars"], p["d"])
    t += "No hace falta ser apoyante. M\u00e1ximo %d anuncios al d\u00eda por usuario." % AP_MAX_DIA
    if apoyante:
        t += "\n\n\u2b50 Como apoyante tambi\u00e9n tienes 1 anuncio gratis al mes (bot\u00f3n de abajo)."
    return t

def _ap_teclado_menu(apoyante):
    f = []
    for pk, ic in (("t7", "\U0001f4cc"), ("t30", "\U0001f4cc"), ("dif", "\U0001f4e3")):
        p = PAQ_AP[pk]
        f.append([{"text": "%s %s \u00b7 %d \u2b50" % (ic, p["n"], p["stars"]), "callback_data": "pk_" + pk}])
    if apoyante:
        f.append([{"text": "\u2b50 Mi anuncio gratis del mes", "callback_data": "pk_free"}])
    f.append([{"text": "\U0001f4cb Men\u00fa", "callback_data": "m_menu"}])
    return json.dumps({"inline_keyboard": f})

def _ap_teclado_admin(aid):
    return json.dumps({"inline_keyboard": [[
        {"text": "\u2705 Aprobar y cobrar", "callback_data": "apg_ok_" + aid},
        {"text": "\u274c Rechazar", "callback_data": "apg_no_" + aid}]]})

def _ap_instrucciones(pk):
    p = PAQ_AP[pk]
    return ("\u2705 Has elegido: %s (%d \u2b50)\n\nAhora escribe tu anuncio as\u00ed:\n"
            "/anunciar texto | https://enlace | texto del bot\u00f3n\n\n"
            "Ejemplo:\n/anunciar Vendo funda para iPhone, 5 \u20ac | https://ejemplo.com/funda | \U0001f449 Ver\n\n"
            "Para a\u00f1adir una foto, escribe el comando en el pie de la foto.\n"
            "Lo reviso y, si lo apruebo, te llega la factura. No pagas nada antes.") % (p["n"], p["stars"])

def anuncio_pago_cmd(d, cid, args, foto):
    """Devuelve True si el comando /anunciar lo gestiona el flujo de pago."""
    if cid == ADMIN:
        return False
    _apd(d)
    ap = es_apoyante(d, cid)
    sel = d["ap_sel"].get(cid)
    if sel and time.time() - sel.get("ts", 0) > AP_SEL_MIN * 60:
        d["ap_sel"].pop(cid, None)
        sel = None
    if not args:
        enviar(cid, _ap_texto_menu(ap), _ap_teclado_menu(ap))
        return True
    if not sel:
        if ap:
            return False  # anuncio gratis mensual de apoyante (flujo de siempre)
        enviar(cid, _ap_texto_menu(ap), _ap_teclado_menu(ap))
        return True
    dat = parsear_anuncio(" ".join(args))
    if not dat:
        enviar(cid, "No entiendo el formato. Usa: /anunciar texto | https://enlace | bot\u00f3n")
        return True
    for a in d["anuncios"].values():
        if a.get("autor") == cid and a.get("tipo") == "pago" and a.get("estado") in ("revision", "esperando_pago"):
            enviar(cid, "Ya tienes un anuncio en revisi\u00f3n o pendiente de pago. Espera a que lo resuelva.")
            return True
    pk = sel["pk"]
    p = PAQ_AP[pk]
    aid = nuevo_id_anuncio(d)
    dat.update({"tipo": "pago", "autor": cid, "estado": "revision", "ts": int(time.time()),
                "foto": foto[0], "env": 0, "clics": 0, "u": {}, "pk": pk})
    d["anuncios"][aid] = dat
    d["ap_sel"].pop(cid, None)
    enviar(cid, "\u2705 Recibido (%s \u00b7 %d \u2b50). Lo reviso y, si lo apruebo, te llega la factura. No pagas nada antes." % (p["n"], p["stars"]))
    enviar_anuncio(d, ADMIN, dat, aid, "\U0001f4e5 Anuncio de PAGO %s \u00b7 %s \u00b7 %d \u2b50 \u00b7 usuario %s" % (aid, p["n"], p["stars"], cid))
    enviar(ADMIN, "\u00bfApruebo el anuncio %s?" % aid, _ap_teclado_admin(aid))
    return True

def _ap_factura(chat, aid, pk):
    p = PAQ_AP[pk]
    try:
        r = requests.post(API + "/sendInvoice", data={
            "chat_id": chat, "title": p["n"], "description": ("Anuncio %s: %s" % (aid, p["d"]))[:250],
            "payload": "ad:" + aid, "provider_token": "", "currency": "XTR",
            "prices": json.dumps([{"label": p["n"], "amount": p["stars"]}])}, timeout=30)
        return r.status_code
    except Exception as e:
        print("error factura anuncio", e, flush=True)
        return 0

def _ap_usados(d, cid, dia):
    pd = d["pub_dia"].get(cid)
    n = pd.get("n", 0) if pd and pd.get("dia") == dia else 0
    if d["ult_pub"].get(cid) == hoy():
        n += 1
    return n

def _ap_enviar(d, ads):
    """Env\u00eda los anuncios de pago a los usuarios respetando el tope diario. Devuelve n\u00ba de env\u00edos."""
    _apd(d)
    dia = _ap_ahora().strftime("%Y-%m-%d")
    vivos = [a for a in ads if a in d["anuncios"]]
    vivos.sort(key=lambda a: d["anuncios"][a].get("pago_ts", 0))
    if not vivos:
        return 0
    total = 0
    for cid in list(d["users"].keys()):
        if cid == ADMIN or not autorizado(d, cid):
            continue
        us = d["users"].get(cid) or {}
        if any(us.get(k) for k in ("parado", "pausa", "pausado", "off", "stop")):
            continue
        if es_apoyante(d, cid) and d["sinpub"].get(cid):
            continue
        if _ap_usados(d, cid, dia) >= AP_MAX_DIA:
            continue
        cand = [a for a in vivos if d["anuncios"][a].get("autor") != cid]
        if not cand:
            continue
        ult = d["ap_rot"].get(cid)
        i = (cand.index(ult) + 1) % len(cand) if ult in cand else 0
        aid = cand[i]
        ad = d["anuncios"][aid]
        st = enviar_anuncio(d, cid, ad, aid, "\U0001f4e2 Publicidad")
        if st == 403:
            d["users"].pop(cid, None)
            continue
        if st == 200:
            pd = d["pub_dia"].get(cid)
            if not pd or pd.get("dia") != dia:
                pd = {"dia": dia, "n": 0}
            pd["n"] = pd.get("n", 0) + 1
            d["pub_dia"][cid] = pd
            d["ap_rot"][cid] = aid
            ad["env"] = ad.get("env", 0) + 1
            total += 1
        time.sleep(0.05)
    return total

def tarea_anuncios(d):
    """Reparto autom\u00e1tico de anuncios de tabl\u00f3n (se llama en cada vuelta del bucle principal)."""
    _apd(d)
    ahora = _ap_ahora()
    dia = ahora.strftime("%Y-%m-%d")
    ts = time.time()
    for pk in ("t7", "t30"):
        for h in PAQ_AP[pk]["horas"]:
            if not (h <= ahora.hour < h + 2):
                continue
            clave = "%s-%d-%s" % (dia, h, pk)
            if d["ap_hechos"].get(clave):
                continue
            d["ap_hechos"][clave] = 1
            ads = [a for a, ad in d["anuncios"].items()
                   if ad.get("tipo") == "pago" and ad.get("pk") == pk
                   and ad.get("estado") == "activo" and ad.get("fin", 0) > ts]
            if ads:
                n = _ap_enviar(d, ads)
                print("anuncios pago %s %02dh: %d envios" % (pk, h, n), flush=True)
    for a, ad in d["anuncios"].items():
        if ad.get("tipo") == "pago" and ad.get("estado") == "activo" and ad.get("fin", 0) <= ts:
            ad["estado"] = "finalizado"
            if ad.get("autor"):
                enviar(ad["autor"], "\u23f0 Tu campa\u00f1a %s ha terminado (%d env\u00edos). Gracias por anunciarte. Puedes renovar con /anunciar." % (a, ad.get("env", 0)))
            enviar(ADMIN, "\u23f0 Campa\u00f1a %s finalizada: %d env\u00edos." % (a, ad.get("env", 0)))
    if len(d["ap_hechos"]) > 60:
        for k in list(d["ap_hechos"].keys())[:-40]:
            d["ap_hechos"].pop(k, None)

def _ap_cb_paquete(d, cid, pk):
    ap = es_apoyante(d, cid)
    if pk == "free":
        if not ap:
            enviar(cid, "\u2b50 El anuncio gratis es solo para apoyantes. Mira /propina.")
            return
        d["ap_sel"].pop(cid, None)
        enviar(cid, "\u2b50 Tu anuncio gratis del mes:\n/anunciar texto | https://enlace | texto del bot\u00f3n\n\n"
                    "Para foto, escribe el comando en el pie de la foto. Lo reviso antes de publicarlo.")
        return
    if pk not in PAQ_AP or not autorizado(d, cid):
        return
    d["ap_sel"][cid] = {"pk": pk, "ts": int(time.time())}
    enviar(cid, _ap_instrucciones(pk))

def _ap_cb_admin(d, cid, data):
    if cid != ADMIN:
        return
    partes = data.split("_")
    if len(partes) != 3:
        return
    acc, aid = partes[1], partes[2]
    ad = d["anuncios"].get(aid)
    if not ad or ad.get("tipo") != "pago":
        enviar(ADMIN, "No encuentro ese anuncio.")
        return
    if ad.get("estado") != "revision":
        enviar(ADMIN, "El anuncio %s ya est\u00e1 en estado: %s" % (aid, ad.get("estado")))
        return
    autor = ad.get("autor")
    p = PAQ_AP.get(ad.get("pk"))
    if not p:
        return
    if acc == "no":
        ad["estado"] = "rechazado"
        if autor:
            enviar(autor, "Tu anuncio no se ha podido publicar y no se te ha cobrado nada. Puedes enviar otro con /anunciar.")
        enviar(ADMIN, "\U0001f5d1\ufe0f Anuncio %s rechazado." % aid)
    elif acc == "ok":
        ad["estado"] = "esperando_pago"
        ad["aprob_ts"] = int(time.time())
        enviar(autor, "\u2705 Tu anuncio ha sido aprobado. Paga la factura de abajo para publicarlo (%s \u00b7 %d \u2b50)." % (p["n"], p["stars"]))
        st = _ap_factura(autor, aid, ad["pk"])
        if st == 200:
            enviar(ADMIN, "\U0001f4b3 Factura de %d \u2b50 enviada al usuario %s (anuncio %s). Se publicar\u00e1 cuando pague." % (p["stars"], autor, aid))
        else:
            ad["estado"] = "revision"
            enviar(ADMIN, "\u26a0\ufe0f No he podido enviar la factura (c\u00f3digo %s). El anuncio %s sigue en revisi\u00f3n." % (st, aid))

def _ap_pre_checkout(d, pq):
    aid = str(pq.get("invoice_payload", ""))[3:]
    ad = d["anuncios"].get(aid)
    p = PAQ_AP.get(ad.get("pk")) if ad else None
    ok = bool(p) and ad.get("estado") == "esperando_pago" and pq.get("total_amount") == p["stars"]
    datos = {"pre_checkout_query_id": pq["id"], "ok": "true" if ok else "false"}
    if not ok:
        datos["error_message"] = "Este anuncio ya no est\u00e1 disponible para pagar."
    requests.post(API + "/answerPreCheckoutQuery", data=datos, timeout=15)

def _ap_pagado(d, m, sp):
    cid = str((m.get("from") or {}).get("id") or (m.get("chat") or {}).get("id"))
    aid = str(sp.get("invoice_payload", ""))[3:]
    n = sp.get("total_amount", 0)
    ad = d["anuncios"].get(aid)
    p = PAQ_AP.get(ad.get("pk")) if ad else None
    if not ad or not p:
        enviar(ADMIN, "\u26a0\ufe0f Pago de %s \u2b50 para un anuncio desconocido (%s) del usuario %s. Rev\u00edsalo." % (n, aid, cid))
        return
    if ad.get("estado") != "esperando_pago":
        enviar(ADMIN, "\u26a0\ufe0f Pago repetido o fuera de tiempo del anuncio %s (estado %s, usuario %s, %s \u2b50)." % (aid, ad.get("estado"), cid, n))
        return
    ts = int(time.time())
    ad["pagado"] = n
    ad["pago_ts"] = ts
    d["ventas_ads"].append({"u": cid, "a": aid, "n": n, "t": ts, "pk": ad["pk"]})
    if ad["pk"] == "dif":
        ad["estado"] = "difundido"
        enviar(cid, "\u2705 Pago recibido. Enviando tu anuncio a todos los usuarios\u2026")
        env = _ap_enviar(d, [aid])
        enviar(cid, "\U0001f4e3 Tu anuncio se ha enviado a %d personas (se omite a quien ya ha visto %d anuncios hoy o ha desactivado la publicidad)." % (env, AP_MAX_DIA))
    else:
        ad["estado"] = "activo"
        ad["ini"] = ts
        ad["fin"] = ts + p["dias"] * 86400
        ad["ts_tab"] = ts
        d["tablon"].append(aid)
        enviar(cid, "\u2705 Pago recibido. Tu anuncio est\u00e1 activo durante %d d\u00edas: se enviar\u00e1 autom\u00e1ticamente a los usuarios y estar\u00e1 visible en /tablon." % p["dias"])
    enviar(ADMIN, "\U0001f4b0 Anuncio %s pagado: %s \u2b50 \u00b7 %s \u00b7 usuario %s" % (aid, n, p["n"], cid))

def hook_anuncios_pago(d, u):
    """Intercepta callbacks pk_/apg_ y los pagos de anuncios. True = ya gestionado."""
    cq = u.get("callback_query")
    pq = u.get("pre_checkout_query")
    sp = (u.get("message") or {}).get("successful_payment")
    es_cb = bool(cq) and str(cq.get("data") or "").startswith(("pk_", "apg_"))
    es_pq = bool(pq) and str(pq.get("invoice_payload", "")).startswith("ad:")
    es_sp = bool(sp) and str(sp.get("invoice_payload", "")).startswith("ad:")
    if not (es_cb or es_pq or es_sp):
        return False
    try:
        _apd(d)
        if es_cb:
            try:
                requests.post(API + "/answerCallbackQuery", data={"callback_query_id": cq["id"]}, timeout=10)
            except Exception:
                pass
            cid = str(cq["from"]["id"])
            data = cq.get("data")
            if data.startswith("pk_"):
                _ap_cb_paquete(d, cid, data[3:])
            else:
                _ap_cb_admin(d, cid, data)
        elif es_pq:
            _ap_pre_checkout(d, pq)
        else:
            _ap_pagado(d, u["message"], sp)
    except Exception as e:
        print("error anuncios pago", e, flush=True)
    return True

def enviar_pendientes(d):
    _enviar_pendientes_orig(d)
    try:
        tarea_anuncios(d)
    except Exception as e:
        print("error tarea anuncios", e, flush=True)

def tablon_activo(d):
    ahora = time.time()
    return [a for a in _tablon_activo_orig(d)
            if not d["anuncios"].get(a, {}).get("fin") or d["anuncios"][a]["fin"] > ahora]


'''

# 1) los envios pendientes y el tablon se envuelven (los originales siguen funcionando)
unico(r'^def enviar_pendientes\(d\):$', lambda m: 'def _enviar_pendientes_orig(d):', "enviar_pendientes")
unico(r'^def tablon_activo\(d\):$', lambda m: 'def _tablon_activo_orig(d):', "tablon_activo")

# 3) /anunciar: primero el flujo de pago; si no aplica, sigue el de siempre
unico(r'^    elif cmd == "/anunciar":\n',
      lambda m: '    elif cmd == "/anunciar" and anuncio_pago_cmd(d, cid, args, _foto):\n        pass\n' + m.group(0), "anunciar")

# 4) pagos y botones de anuncios, antes del pre_checkout de las propinas
unico(r'^([ \t]+)pq = u\.get\("pre_checkout_query"\)$',
      lambda m: m.group(1) + 'if hook_anuncios_pago(d, u):\n' + m.group(1) + '    continue\n' + m.group(0), "pre_checkout")

# 2) el codigo nuevo va justo antes de procesar_updates (al final, para no confundir los anclas)
unico(r'^def procesar_updates\(d\):\n', lambda m: FUNC + m.group(0), "procesar_updates")

# 5) textos (opcionales)
opcional(r'/anunciar: publica tu anuncio en el bot \(1 al mes\)',
         '/anunciar: an\\u00fanciate en el bot (paquetes de pago; apoyantes: 1 gratis al mes)', "ayuda")
opcional(r'Los apoyantes \S+ pueden publicar el suyo con /anunciar\.',
         'Publica el tuyo con /anunciar.', "tablon vacio")

try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)

copia = RUTA + ".bak_anuncios_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
