import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- ALIAUTO1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("# --- ALI1 ---", "def _al_tarjeta(", "def _al_prod(", "def _cp_d(", "def _a_ahora(", "def procesar_updates(", "def hook_anuncios_pago("):
    if n not in src:
        print("ABORTO: falta", n, "(aplica antes parche_ali1.py y los parches de canal)"); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)

BLOQUE = r'''
# --- ALIAUTO1 ---
# Ofertas automaticas de AliExpress en el canal. Arranca APAGADO y en modo PRUEBA
# (las tarjetas solo te llegan a ti). /aliauto para ver y cambiar los ajustes.
_AA_F = "/opt/chivato/ali_auto.json"
_AA_BUSQ = ["auriculares bluetooth", "smartwatch", "powerbank", "cargador rapido usb c", "altavoz bluetooth", "camara de seguridad wifi",
            "aspirador robot", "luces led", "teclado mecanico", "raton gaming", "ssd externo", "gafas de sol", "mochila", "zapatillas running",
            "herramientas bricolaje", "organizador cocina", "freidora de aire accesorios", "cable usb c", "soporte movil coche", "drone"]
_AA_BASE = {"on": False, "modo": "prueba", "pct": 50, "ventas": 300, "rat": 90, "max": 6, "cada": 90, "desde": 9, "hasta": 22,
            "precio_min": 3.0, "pct_max": 90, "i": 0, "dia": "", "hoy": 0, "ult": 0, "vistos": [], "n": 0}
_aa_lock = _vd_th.Lock()

def _aa_cargar():
    c = dict(_AA_BASE)
    try:
        with open(_AA_F, encoding="utf-8") as fh:
            c.update(json.load(fh))
    except Exception:
        pass
    return c

def _aa_guardar(c):
    c["vistos"] = c["vistos"][-3000:]
    try:
        with open(_AA_F + ".tmp", "w", encoding="utf-8") as fh:
            json.dump(c, fh)
        _cn_os_replace(_AA_F + ".tmp", _AA_F)
    except Exception as e:
        print("error guardar aliauto", str(e)[:80], flush=True)

def _cn_os_replace(a, b):
    __import__("os").replace(a, b)

def _aa_ok(x, c):
    """Filtros anti-productos dudosos."""
    if not x["id"] or not x["ahora"] or not x["img"]:
        return False
    if x["ahora"] < c["precio_min"]:
        return False
    if x["pct"] is None or x["pct"] < c["pct"] or x["pct"] > c["pct_max"]:
        return False
    v = _al_num(x["ventas"])
    if v is None or v < c["ventas"]:
        return False
    r = _al_num(x["rat"])
    if r is None or r < c["rat"]:
        return False
    return True

def _aa_buscar(c, kw, pagina="1"):
    j = _al_api("aliexpress.affiliate.product.query", {"keywords": kw, "page_size": "50", "page_no": pagina, "sort": "LAST_VOLUME_DESC",
                "ship_to_country": "ES", "target_currency": "EUR", "target_language": "ES", "tracking_id": _al_trk()})
    ps = [_al_prod(p) for p in (((_al_resultado(j).get("products") or {}).get("product")) or [])]
    vistos = set(c["vistos"])
    return [p for p in ps if p["id"] not in vistos and _aa_ok(p, c)]

def _aa_elegir(c, intentos=4):
    """Devuelve (producto, enlace) o (None, motivo)."""
    tot = 0
    for _ in range(intentos):
        kw = _AA_BUSQ[c["i"] % len(_AA_BUSQ)]
        c["i"] += 1
        try:
            cand = _aa_buscar(c, kw)
        except Exception as e:
            print("error aliauto buscar", str(e)[:80], flush=True)
            continue
        tot += len(cand)
        if not cand:
            continue
        cand.sort(key=lambda p: -((p["pct"] or 0) * (1 + min(_al_num(p["ventas"]) or 0, 20000) / 2000.0)))
        for p in cand[:5]:
            ln = p["link"] or _al_enlaces([p["url"]]).get(p["url"])
            if ln:
                return p, ln, kw
    return None, None, ("sin candidatos que pasen los filtros (%d)" % tot)

def _aa_publicar(d_canal, c, modo_real, destino):
    p, ln, kw = _aa_elegir(c)
    if not p:
        return False, kw
    c["vistos"].append(p["id"])
    extra = ""
    if not modo_real:
        extra = "🧪 PRUEBA (no publicado)\nBúsqueda: %s\nVentas: %s · Valoración: %s · Descuento AliExpress: %s%%" % (kw, p["ventas"], p["rat"], p["pct"])
    _al_tarjeta(destino, p, ln, extra)
    if modo_real:
        c["n"] += 1
        c["hoy"] += 1
    return True, p["titulo"]

def _aa_tarea(d):
    ahora = _cn_time.time()
    if ahora - d.get("aa_ult", 0) < 30:
        return
    d["aa_ult"] = ahora
    if not _aa_lock.acquire(False):
        return
    try:
        c = _aa_cargar()
        if not c["on"]:
            return
        a = _a_ahora()
        hoy = a.strftime("%Y-%m-%d")
        if c["dia"] != hoy:
            c["dia"] = hoy; c["hoy"] = 0
        if not (c["desde"] <= a.hour < c["hasta"]) or c["hoy"] >= c["max"]:
            _aa_guardar(c); return
        if ahora - c["ult"] < c["cada"] * 60:
            return
        canal = (_cp_d(d) or {}).get("id")
        if c["modo"] == "canal" and not canal:
            return
        destino = canal if c["modo"] == "canal" else ADMIN
        c["ult"] = ahora
        _aa_guardar(c)
        _vd_th.Thread(target=_aa_hilo, args=(destino, c["modo"] == "canal"), daemon=True).start()
    except Exception as e:
        print("error tarea aliauto", str(e)[:100], flush=True)
    finally:
        _aa_lock.release()

def _aa_hilo(destino, real):
    try:
        with _aa_lock:
            c = _aa_cargar()
            ok, info = _aa_publicar(None, c, real, destino)
            _aa_guardar(c)
            print("aliauto", ok, str(info)[:60], flush=True)
    except Exception as e:
        print("error hilo aliauto", str(e)[:100], flush=True)

def _aa_estado(c):
    return ("\U0001f6d2 OFERTAS AUTOMÁTICAS ALIEXPRESS\n\nEstado: %s\nModo: %s\nDescuento mínimo: %d%% (máx. %d%%)\nVentas mínimas: %d\nValoración mínima: %d%%\n"
            "Máximo al día: %d (hoy %d)\nSeparación: %d min\nHorario: %02d:00–%02d:00\nPublicadas en total: %d\n\n"
            "/aliauto on · off\n/aliauto probar (te envía 1 candidata a ti)\n/aliauto modo prueba|canal\n/aliauto descuento 50 · ventas 300 · valoracion 90\n/aliauto max 6 · cada 90 · horario 9 22"
            % ("ACTIVADO" if c["on"] else "APAGADO", "PUBLICA EN EL CANAL" if c["modo"] == "canal" else "PRUEBA (solo te llega a ti)",
               c["pct"], c["pct_max"], c["ventas"], c["rat"], c["max"], c["hoy"], c["cada"], c["desde"], c["hasta"], c["n"]))

def _aa_admin(d, cid, args):
    c = _aa_cargar()
    a = args[0].lower() if args else ""
    n = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    if a in ("on", "off"):
        c["on"] = (a == "on")
    elif a == "modo" and len(args) > 1 and args[1].lower() in ("prueba", "canal"):
        if args[1].lower() == "canal" and not (_cp_d(d) or {}).get("id"):
            enviar(cid, "Primero configura el canal público con /canalpub."); return
        c["modo"] = args[1].lower()
    elif a == "descuento" and n is not None and 10 <= n <= 90:
        c["pct"] = n
    elif a == "ventas" and n is not None:
        c["ventas"] = n
    elif a in ("valoracion", "valoración") and n is not None and 50 <= n <= 100:
        c["rat"] = n
    elif a == "max" and n is not None and 1 <= n <= 30:
        c["max"] = n
    elif a == "cada" and n is not None and 10 <= n <= 720:
        c["cada"] = n
    elif a == "horario" and len(args) > 2 and args[1].isdigit() and args[2].isdigit() and 0 <= int(args[1]) < int(args[2]) <= 24:
        c["desde"], c["hasta"] = int(args[1]), int(args[2])
    elif a == "probar":
        enviar(cid, "Buscando una candidata…")
        def _t():
            try:
                with _aa_lock:
                    cc = _aa_cargar()
                    ok, info = _aa_publicar(None, cc, False, cid)
                    _aa_guardar(cc)
                if not ok:
                    enviar(cid, "No hay candidatas con estos filtros ahora (%s). Prueba bajar descuento/ventas con /aliauto." % info)
            except Exception as e:
                print("error probar aliauto", str(e)[:100], flush=True)
                enviar(cid, "No he podido consultar AliExpress ahora mismo.")
        _vd_th.Thread(target=_t, daemon=True).start()
        return
    elif a:
        enviar(cid, "No entiendo ese ajuste. Escribe /aliauto para ver las opciones."); return
    _aa_guardar(c)
    enviar(cid, _aa_estado(c))

_aa_pu_orig = procesar_updates
def procesar_updates(d, *a, **k):
    try:
        _aa_tarea(d)
    except Exception as e:
        print("error aliauto", str(e)[:100], flush=True)
    return _aa_pu_orig(d, *a, **k)

_aa_hook_orig = hook_anuncios_pago
def hook_anuncios_pago(d, u):
    try:
        m = u.get("message")
        t = ((m.get("text") or "") if m else "").strip()
        if m and t:
            cid = m["chat"]["id"]
            prim = t.split()[0]
            if prim.lower().split("@")[0] == "/aliauto" and str(cid) == str(ADMIN):
                _aa_admin(d, cid, t.split()[1:]); return True
    except Exception as e:
        print("error hook aliauto", str(e)[:100], flush=True)
    return _aa_hook_orig(d, u)
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_aliauto_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: /aliauto (apagado y en modo prueba).")
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato   y luego /autotest")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
