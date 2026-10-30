import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()

if "# --- ESCUDO ---" in src:
    print("Ya estaba aplicado. No hago nada.")
    sys.exit(0)
if "# --- SEGUIR ---" not in src:
    print("ABORTO: falta parche_B.py (/seguir)"); sys.exit(1)

def unico(patron, fn, nombre):
    global src
    n = len(re.findall(patron, src, re.M))
    if n != 1:
        print("ABORTO: ancla '%s' encontrada %d veces" % (nombre, n)); sys.exit(1)
    src = re.sub(patron, fn, src, count=1, flags=re.M)

FUNC = r'''# --- ESCUDO ---
ESC_MAX = 10
ESC_DIAS = 30
ESC_CADA = 1800
ESC_LOTE = 30

def _e_d(d):
    return d.setdefault("escudo", {})

def _e_umbral(pago):
    return max(200, int(pago * 0.05))

def _e_dias_rest(e):
    return ESC_DIAS - int((time.time() - e["ts"]) // 86400)

def escudo_cmd(d, cid, args):
    es = _e_d(d)
    lista = es.setdefault(cid, [])
    if args and args[0].lower() in ("quitar", "borrar", "del"):
        if len(args) > 1 and args[1].lower() in ("todos", "todo"):
            es[cid] = []
            enviar(cid, "\U0001f5d1 Has quitado todas tus compras del Escudo.")
        elif len(args) > 1 and args[1].isdigit() and 1 <= int(args[1]) <= len(lista):
            e = lista.pop(int(args[1]) - 1)
            enviar(cid, "\U0001f5d1 Dejo de vigilar: %s" % (e.get("t") or e["asin"])[:80])
        else:
            enviar(cid, "Uso: /escudo quitar 2  (el número de tu lista) o /escudo quitar todos")
        return
    if not args:
        if not lista:
            enviar(cid, "\U0001f6e1 ESCUDO DE COMPRA\n\nCuéntame lo que acabas de comprar en Amazon y vigilo su precio durante %d días. "
                        "Si baja después de que compres, te aviso para que aún estés a tiempo de reclamar o volver a comprarlo más barato.\n\n"
                        "Ejemplo:\n/compre https://www.amazon.es/dp/B0XXXXXXXX 49.90\n\n"
                        "Si lo compraste hace unos días, añade d3 (hace 3 días):\n/compre enlace 49.90 d3\n\n"
                        "Puedes vigilar hasta %d compras." % (ESC_DIAS, ESC_MAX))
            return
        t = "\U0001f6e1 TU ESCUDO DE COMPRA (%d/%d)\n\n" % (len(lista), ESC_MAX)
        for i, e in enumerate(lista):
            act = (_s_eur(e["cur"]) + " EUR") if e.get("cur") else "sin precio"
            mn = e.get("min")
            baja = (" · mínimo visto: %s EUR" % _s_eur(mn)) if mn and mn < e["pago"] else ""
            t += "%d. %s\n   Pagaste: %s EUR · Ahora: %s%s · Quedan %d días\n" % (
                i + 1, (e.get("t") or e["asin"])[:70], _s_eur(e["pago"]), act, baja, max(_e_dias_rest(e), 0))
        t += "\nAñadir: /compre enlace precio\nQuitar: /escudo quitar 2"
        enviar(cid, t)
        return
    dias = 0
    rest = []
    for a in args:
        m = re.fullmatch(r"[dD](\d{1,2})", a.strip())
        if m:
            dias = min(int(m.group(1)), ESC_DIAS - 1)
        else:
            rest.append(a)
    asin, precio, err = _s_extraer(rest)
    if err:
        enviar(cid, "⚠️ " + err)
        return
    if not precio or precio < 100:
        enviar(cid, "Dime también lo que pagaste. Ejemplo: /compre %s 49.90" % _s_url(asin))
        return
    ya = next((e for e in lista if e["asin"] == asin), None)
    if not ya and len(lista) >= ESC_MAX:
        enviar(cid, "Ya vigilas %d compras (máximo). Quita alguna con /escudo quitar 1" % ESC_MAX)
        return
    info = _s_precios(d, [asin]).get(asin)
    if info is None:
        enviar(cid, "No he podido comprobar ese producto ahora mismo. Inténtalo de nuevo en unos minutos.")
        return
    cur, titulo = info
    e = ya or {"asin": asin}
    e.update({"pago": precio, "t": titulo, "cur": cur, "ts": int(time.time()) - dias * 86400, "ult": None, "min": cur, "cierre": False})
    if not ya:
        lista.append(e)
    t = "\U0001f6e1 Escudo activado\n\n%s\nPagaste: %s EUR · Ahora cuesta: %s\nLo vigilo durante %d días (te quedan %d)." % (
        titulo[:90], _s_eur(precio), (_s_eur(cur) + " EUR") if cur else "sin precio", ESC_DIAS, max(_e_dias_rest(e), 0))
    if cur and precio - cur >= _e_umbral(precio) and _e_dias_rest(e) > 0:
        t += ("\n\n\U0001f4c9 Ya cuesta %s EUR menos que lo que pagaste. Si sigues dentro del plazo de devolución de tu pedido "
              "(Amazon suele dar 30 días), puedes valorar devolverlo y volver a comprarlo más barato:\n%s" % (_s_eur(precio - cur), _s_url(asin)))
        e["ult"] = cur
    elif cur:
        t += "\n\nPor ahora no ha bajado. Si baja, te aviso."
    enviar(cid, t)

def _e_tarea(d):
    es = d.get("escudo") or {}
    if not any(es.values()):
        return
    ahora = time.time()
    if ahora - d.get("esc_ult", 0) < ESC_CADA:
        return
    d["esc_ult"] = ahora
    if d.get("a_tok", 999) < 150:
        return
    chk = d.setdefault("esc_chk", {})
    activos = {}
    for cid, lst in es.items():
        for e in lst:
            if not e.get("cierre"):
                activos[e["asin"]] = 1
    asins = sorted(activos.keys(), key=lambda a: chk.get(a, 0))[:ESC_LOTE]
    if not asins:
        return
    precios = _s_precios(d, asins)
    for a in asins:
        chk[a] = int(ahora)
    en_sil = globals().get("_a_en_silencio")
    for cid in list(es.keys()):
        for e in list(es[cid]):
            if e.get("cierre"):
                continue
            rest = _e_dias_rest(e)
            if e["asin"] in precios:
                cur, titulo = precios[e["asin"]]
                if titulo:
                    e["t"] = titulo
                e["cur"] = cur
                if cur and (not e.get("min") or cur < e["min"]):
                    e["min"] = cur
            cur = e.get("cur")
            sil = bool(en_sil and en_sil(d["users"].get(cid)))
            if rest <= 0:
                if sil:
                    continue
                e["cierre"] = True
                mn = e.get("min")
                if mn and mn < e["pago"] - 50:
                    txt = ("\U0001f6e1 Plazo del Escudo terminado\n\n%s\nPagaste %s EUR y el mínimo que vi fue %s EUR. "
                           "Para la próxima, fíjate en el historial antes de comprar." % ((e.get("t") or e["asin"])[:90], _s_eur(e["pago"]), _s_eur(mn)))
                else:
                    txt = ("\U0001f6e1 Plazo del Escudo terminado\n\n%s\nPagaste %s EUR y no bajó en %d días. ✅ Buena compra." % (
                        (e.get("t") or e["asin"])[:90], _s_eur(e["pago"]), ESC_DIAS))
                if enviar(cid, txt) == 403:
                    es[cid] = []
                    break
                continue
            if not cur or e["pago"] - cur < _e_umbral(e["pago"]):
                continue
            ult = e.get("ult")
            if ult is not None and cur > ult - max(100, int(e["pago"] * 0.02)):
                continue
            if sil:
                continue
            e["ult"] = cur
            msg = ("\U0001f6e1 ¡HA BAJADO TU COMPRA!\n\n%s\nPagaste: %s EUR · Ahora: %s EUR (%s EUR menos)\nTe quedan %d días de plazo.\n\n"
                   "Si sigues dentro del plazo de devolución de tu pedido (Amazon suele dar 30 días), puedes valorar devolverlo y volver a comprarlo más barato. "
                   "Comprueba las condiciones de tu pedido; no es una garantía.\n%s" % (
                       (e.get("t") or e["asin"])[:90], _s_eur(e["pago"]), _s_eur(cur), _s_eur(e["pago"] - cur), rest, _s_url(e["asin"])))
            if enviar(cid, msg) == 403:
                es[cid] = []
                break
    for cid in list(es.keys()):
        es[cid] = [e for e in es[cid] if not (e.get("cierre") and _e_dias_rest(e) < -3)]

'''

TAIL = r'''# --- ESCUDO (tarea) ---
_pu_orig_esc = procesar_updates
def procesar_updates(d, *a, **k):
    try:
        _e_tarea(d)
    except Exception as e:
        print("error tarea escudo", e, flush=True)
    return _pu_orig_esc(d, *a, **k)

AYUDA = AYUDA + "\n\n\U0001f6e1 /compre enlace precio - vigilo tu compra 30 días y te aviso si baja"

'''

unico(r'^def comando\(d, cid, texto\):\n', lambda m: FUNC + m.group(0), "comando")
unico(r'^    elif cmd in \("/propina", "/premium"\):\n',
      lambda m: '    elif cmd in ("/compre", "/escudo", "/compra"):\n        escudo_cmd(d, cid, args)\n' + m.group(0), "propina")
unico(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), "main")

try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)

copia = RUTA + ".bak_escudo_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
