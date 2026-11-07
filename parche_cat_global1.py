import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- CATGLOBAL1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("# --- CATEGORIAS ---", "def enviar_aviso(", "def _cat_nombre(", "def hook_anuncios_pago(", "ADMIN"):
    if n not in src:
        print("ABORTO: falta", n); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''
# --- CATGLOBAL1 ---
# Filtro GLOBAL de categorias: el bot solo envia a los usuarios las ofertas de las categorias elegidas por el ADMIN.
# Por defecto: electronica, informatica, moda, hogar y deporte. Se cambia con /catglobal (solo ADMIN).
# Las ofertas sin categoria (p. ej. AliExpress) no se filtran. La mini app sigue guardando todas.
_CG_CLAVES = ("electr", "inform", "moda", "hogar", "deporte", "ropa", "calzado", "zapat")

def _cg_est(d):
    return d.setdefault("cg", {"modo": "def", "sel": []})

def _cg_efectivas(d):
    """Ids de categoria permitidos, o None si no se filtra."""
    e = _cg_est(d)
    if e.get("modo") == "all":
        return None
    if e.get("modo") == "sel":
        return list(e.get("sel") or [])
    nombres = d.get("cat_nombres") or {}
    ids = [c for c, n in nombres.items() if any(k in str(n).lower() for k in _CG_CLAVES)]
    return ids if ids else None

_cg_pre_aviso = enviar_aviso
def enviar_aviso(d, cid, item):
    try:
        ok = _cg_efectivas(d)
        c = str(item.get("c") or "")
        if ok is not None and c and c not in ok:
            return
    except Exception as e:
        print("error catglobal", str(e)[:80], flush=True)
    return _cg_pre_aviso(d, cid, item)

def _cg_texto(d):
    ok = _cg_efectivas(d)
    modo = _cg_est(d).get("modo")
    ahora = "todas" if ok is None else ", ".join(_cat_nombre(d, c) for c in ok)
    return ("\U0001f4c2 CATEGORÍAS DEL BOT (para todos)\n\nSolo se envían ofertas de las categorías marcadas ✅.\n"
            "Modo: %s\n\nAhora: %s" % ({"def": "por defecto", "sel": "elegidas por ti", "all": "todas"}.get(modo, modo), ahora))

def _cg_teclado(d):
    ok = _cg_efectivas(d)
    vistas = d.get("cat_vistas") or {}
    ids = sorted(vistas, key=lambda c: -vistas[c])[:16]
    filas, fila = [], []
    for c in ids:
        marca = "✅ " if (ok is None or c in ok) else "▫️ "
        fila.append({"text": marca + _cat_nombre(d, c)[:22], "callback_data": "cg_" + c})
        if len(fila) == 2:
            filas.append(fila); fila = []
    if fila: filas.append(fila)
    filas.append([{"text": "Por defecto", "callback_data": "cg_def"}, {"text": "Todas", "callback_data": "cg_all"}])
    return json.dumps({"inline_keyboard": filas})

_cg_hook_orig = hook_anuncios_pago
def hook_anuncios_pago(d, u):
    try:
        cq = u.get("callback_query")
        if cq and str(cq.get("data") or "").startswith("cg_"):
            cid = str(cq["from"]["id"])
            try: requests.post(API + "/answerCallbackQuery", data={"callback_query_id": cq["id"]}, timeout=10)
            except Exception: pass
            if cid != str(ADMIN):
                return True
            dato = cq["data"][3:]
            e = _cg_est(d)
            if dato == "def":
                e["modo"], e["sel"] = "def", []
            elif dato == "all":
                e["modo"], e["sel"] = "all", []
            else:
                sel = _cg_efectivas(d)
                sel = list(sel) if sel is not None else list(d.get("cat_vistas") or {})
                if dato in sel: sel.remove(dato)
                else: sel.append(dato)
                e["modo"], e["sel"] = "sel", sel
            msg = cq.get("message") or {}
            r = requests.post(API + "/editMessageText", data={"chat_id": cid, "message_id": msg.get("message_id"),
                              "text": _cg_texto(d), "reply_markup": _cg_teclado(d)}, timeout=15)
            if r.status_code != 200 and "not modified" not in r.text:
                enviar(cid, _cg_texto(d), _cg_teclado(d))
            return True
        m = u.get("message")
        t = ((m.get("text") or "") if m else "").strip()
        if m and t and t.split()[0].lower().split("@")[0] == "/catglobal":
            cid = str(m["chat"]["id"])
            if cid == str(ADMIN):
                if not d.get("cat_vistas"):
                    enviar(cid, "Todavía estoy aprendiendo las categorías. Prueba en unos minutos.")
                else:
                    enviar(cid, _cg_texto(d), _cg_teclado(d))
            return True
    except Exception as e:
        print("error hook catglobal", str(e)[:100], flush=True)
    return _cg_hook_orig(d, u)
'''
nuevo = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: BLOQUE + "\n" + m.group(0), src, count=1, flags=re.M)
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_catglobal_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Aplicado. Reinicia: sudo systemctl restart chivato")
print("Luego en el bot: /catglobal  (elige las categorias; solo tu)")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
