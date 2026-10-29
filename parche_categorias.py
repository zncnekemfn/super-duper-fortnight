import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()

if "# --- CATEGORIAS ---" in src:
    print("Ya estaba aplicado. No hago nada.")
    sys.exit(0)
if "# --- ANUNCIOS DE PAGO ---" not in src:
    print("ABORTO: primero hay que aplicar parche_anuncios_pago.py")
    sys.exit(1)

def unico(patron, fn, nombre):
    global src
    n = len(re.findall(patron, src, re.M))
    if n != 1:
        print("ABORTO: ancla '%s' encontrada %d veces" % (nombre, n))
        sys.exit(1)
    src = re.sub(patron, fn, src, count=1, flags=re.M)

FUNC = r'''# --- CATEGORIAS ---
TEXTO_CAT_APOYANTE = ("\U0001f4c2 Elegir categor\u00edas es una ventaja de apoyantes \u2b50\n\n"
                      "Con una propina desde 500 Stars solo recibes las ofertas de las categor\u00edas que quieras. Mira /propina.")

def _cat_aprender(d, j):
    """Guarda los nombres de categor\u00eda que manda Keepa y cu\u00e1ntas ofertas hay de cada una."""
    try:
        d.setdefault("cat_nombres", {})
        d.setdefault("cat_vistas", {})
        deals = j.get("deals") or {}
        for i, n in zip(deals.get("categoryIds") or [], deals.get("categoryNames") or []):
            if n:
                d["cat_nombres"][str(i)] = str(n)
        for dl in (deals.get("dr") or []):
            c = str(dl.get("rootCat") or "")
            if c and c != "0":
                d["cat_vistas"][c] = d["cat_vistas"].get(c, 0) + 1
    except Exception as e:
        print("error aprendiendo categorias", e, flush=True)

def _cat_nombre(d, c):
    return (d.get("cat_nombres") or {}).get(c) or ("Categor\u00eda " + c)

def _cat_texto(d, cid):
    sel = (d["users"].get(cid) or {}).get("cats") or []
    ahora = "todas" if not sel else ", ".join(_cat_nombre(d, c) for c in sel)
    return ("\U0001f4c2 TUS CATEGOR\u00cdAS \u2b50\n\nMarca las categor\u00edas de las que quieres recibir ofertas. "
            "Si no marcas ninguna, recibes todas.\n\nAhora: " + ahora)

def _cat_teclado(d, cid):
    sel = (d["users"].get(cid) or {}).get("cats") or []
    vistas = d.get("cat_vistas") or {}
    ids = sorted(vistas, key=lambda c: -vistas[c])[:14]
    for c in sel:
        if c not in ids:
            ids.append(c)
    filas, fila = [], []
    for c in ids:
        fila.append({"text": ("\u2705 " if c in sel else "\u25ab\ufe0f ") + _cat_nombre(d, c)[:22], "callback_data": "cat_" + c})
        if len(fila) == 2:
            filas.append(fila)
            fila = []
    if fila:
        filas.append(fila)
    filas.append([{"text": "\U0001f504 Todas las categor\u00edas", "callback_data": "cat_all"}])
    filas.append([{"text": "\U0001f4cb Men\u00fa", "callback_data": "m_menu"}])
    return json.dumps({"inline_keyboard": filas}), bool(ids)

def cat_menu(d, cid):
    if not es_apoyante(d, cid):
        enviar(cid, TEXTO_CAT_APOYANTE)
        return
    d["users"].setdefault(cid, nuevo_usuario())
    tec, hay = _cat_teclado(d, cid)
    if not hay:
        enviar(cid, "\U0001f4c2 Todav\u00eda estoy aprendiendo las categor\u00edas de las ofertas. Prueba de nuevo en unos minutos.")
        return
    enviar(cid, _cat_texto(d, cid), tec)

def hook_categorias(d, u):
    cq = u.get("callback_query")
    if not cq or not str(cq.get("data") or "").startswith("cat_"):
        return False
    try:
        try:
            requests.post(API + "/answerCallbackQuery", data={"callback_query_id": cq["id"]}, timeout=10)
        except Exception:
            pass
        cid = str(cq["from"]["id"])
        if not es_apoyante(d, cid):
            enviar(cid, TEXTO_CAT_APOYANTE)
            return True
        us = d["users"].setdefault(cid, nuevo_usuario())
        dato = cq["data"][4:]
        sel = list(us.get("cats") or [])
        if dato == "all":
            sel = []
        elif dato in sel:
            sel.remove(dato)
        else:
            sel.append(dato)
        us["cats"] = sel
        tec, _ = _cat_teclado(d, cid)
        requests.post(API + "/editMessageText", data={
            "chat_id": cid, "message_id": (cq.get("message") or {}).get("message_id"),
            "text": _cat_texto(d, cid), "reply_markup": tec}, timeout=15)
    except Exception as e:
        print("error categorias", e, flush=True)
    return True

def enviar_aviso(d, cid, item):
    c = str(item.get("c") or "")
    sel = (d["users"].get(cid) or {}).get("cats") or []
    if c and sel and es_apoyante(d, cid) and c not in sel:
        return
    return _enviar_aviso_orig(d, cid, item)

AYUDA = AYUDA + "\n\n\U0001f4c2 /categorias - Elige las categor\u00edas de ofertas que quieres recibir (apoyantes)"

'''

# 1) cada oferta de Keepa guarda su categoria
unico(r'(cents / 100\.0\), "u": url, "d": dsc,)', lambda m: m.group(1) + ' "c": str(dl.get("rootCat") or ""),', "item keepa")

# 2) se aprenden los nombres de categoria de la respuesta de Keepa
unico(r'^(    lista = \(j\.get\("deals"\) or \{\}\)\.get\("dr"\) or \[\]\n)',
      lambda m: m.group(1) + '    _cat_aprender(d, j)\n', "lista keepa")

# 3) el envio de avisos se envuelve para filtrar por categoria (solo apoyantes con categorias elegidas)
unico(r'^def enviar_aviso\(d, cid, item\):$', lambda m: 'def _enviar_aviso_orig(d, cid, item):', "enviar_aviso")

# 4) codigo nuevo antes de comando
unico(r'^def comando\(d, cid, texto\):\n', lambda m: FUNC + m.group(0), "comando")

# 5) comando /categorias
unico(r'^    elif cmd in \("/propina", "/premium"\):\n',
      lambda m: '    elif cmd in ("/categorias", "/categoria"):\n        cat_menu(d, cid)\n' + m.group(0), "propina")

# 6) botones de categorias
unico(r'^([ \t]+)if hook_anuncios_pago\(d, u\):\n',
      lambda m: m.group(1) + 'if hook_categorias(d, u):\n' + m.group(1) + '    continue\n' + m.group(0), "hook")

try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)

copia = RUTA + ".bak_cat_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
