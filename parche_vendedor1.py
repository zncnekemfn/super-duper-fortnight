import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- VENDEDOR1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("# --- VERIFICA1 ---", "def _vf_serie(", "def _vf_asin(", "def _vf_mediana(", "def _pl_base(", "def _pl_cerrar(", "def _pl_corta(", "def _pl_enviar(", "def hook_anuncios_pago(", "KEEPA_KEY", "_vd_th"):
    if n not in src:
        print("ABORTO: no encuentro", n, "(aplica antes parche_verifica1)"); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)
MENU = ("def teclado_menu(" in src and "def hook_menu(" in src)

BLOQUE = r'''
# --- VENDEDOR1 ---
# /vendedor ENLACE  y boton "🟠 Vendedor" del menu: ficha del vendedor de un producto de Amazon.es con semaforo de riesgo.
# Es una estimacion con datos de Keepa: senales de riesgo, no una confirmacion de estafa.
_VN_ULT = {}
_VN_ESPERA = {}
_VN_AMAZON_ES = "A1AT7YVPFBWXBL"
_VN_UE = ("ES", "FR", "DE", "IT", "PT", "NL", "BE", "IE", "AT", "LU", "PL", "SE", "DK", "FI", "CZ", "GR", "RO", "HU", "BG", "HR", "SK", "SI", "LT", "LV", "EE", "CY", "MT")

def _vn_id_vendedor(pr):
    st = pr.get("stats") or {}
    sid = st.get("buyBoxSellerId")
    if isinstance(sid, str) and len(sid) > 5:
        return sid
    h = pr.get("buyBoxSellerIdHistory") or []
    if len(h) >= 2:
        v = h[-1]
        if isinstance(v, str) and len(v) > 5:
            return v
    return None

def _vn_datos(asin):
    rr = requests.get("https://api.keepa.com/product", params={"key": KEEPA_KEY, "domain": 9, "asin": asin, "stats": 90, "buybox": 1}, timeout=35)
    if rr.status_code != 200:
        print("vendedor keepa http", rr.status_code, flush=True)
        return None
    pr = (rr.json().get("products") or [None])[0] or {}
    st = pr.get("stats") or {}
    sid = _vn_id_vendedor(pr)
    es_amazon = bool(st.get("buyBoxIsAmazon")) or sid == _VN_AMAZON_ES
    fba = st.get("buyBoxIsFBA")
    vend = {}
    if sid and not es_amazon:
        try:
            r2 = requests.get("https://api.keepa.com/seller", params={"key": KEEPA_KEY, "domain": 9, "seller": sid}, timeout=30)
            if r2.status_code == 200:
                vend = (r2.json().get("sellers") or {}).get(sid) or {}
            else:
                print("vendedor keepa seller http", r2.status_code, flush=True)
        except Exception as e:
            print("error vendedor seller", str(e)[:80], flush=True)
    pct = None; cnt = None
    try:
        pct = vend.get("currentRating")
        cnt = vend.get("currentRatingCount")
        if (pct is None or cnt is None) and vend.get("csv"):
            c = vend["csv"]
            if pct is None and c[0]: pct = c[0][-1]
            if cnt is None and len(c) > 1 and c[1]: cnt = c[1][-1]
        if pct is not None and pct < 0: pct = None
        if cnt is not None and cnt < 0: cnt = None
    except Exception:
        pass
    pais = None
    try:
        ad = vend.get("address") or []
        if ad and isinstance(ad[-1], str) and len(ad[-1]) == 2:
            pais = ad[-1].upper()
    except Exception:
        pass
    serie = None
    csv = pr.get("csv") or []
    for idx in (0, 1):
        if len(csv) > idx and csv[idx] and len(csv[idx]) >= 4:
            s = _vf_serie(csv[idx], _cn_time.time())
            if s[-1] is not None:
                serie = s; break
    return {"titulo": pr.get("title") or asin, "sid": sid, "amazon": es_amazon, "fba": fba, "nombre": vend.get("sellerName") or vend.get("businessName"),
            "pct": pct, "cnt": cnt, "pais": pais, "china": bool(vend.get("shipsFromChina")), "serie": serie, "conocido": bool(sid or es_amazon)}

def _vn_analizar(x):
    filas = []; riesgo = 0
    # quien vende
    if not x["conocido"]:
        filas.append(("VENDE", "No se sabe", None))
    elif x["amazon"]:
        filas.append(("VENDE", "Amazon", 0))
    else:
        filas.append(("VENDE", "Vendedor externo", 1)); riesgo += 1
    # quien envia
    if x["amazon"]:
        filas.append(("ENVÍA", "Amazon", 0))
    elif x["fba"] is True:
        filas.append(("ENVÍA", "Amazon (FBA)", 0))
    elif x["fba"] is False:
        filas.append(("ENVÍA", "El propio vendedor", 2)); riesgo += 1
    else:
        filas.append(("ENVÍA", "No se sabe", None))
    # valoracion
    if x["amazon"]:
        filas.append(("VALORACIÓN", "Amazon", 0))
    elif x["pct"] is None or x["cnt"] is None:
        filas.append(("VALORACIÓN", "Sin datos", 1)); riesgo += 1
    else:
        n = 0
        if x["cnt"] < 50: n = 2
        elif x["cnt"] < 200: n = 1
        if x["pct"] < 90: n = max(n, 2)
        elif x["pct"] < 95: n = max(n, 1)
        riesgo += 2 if (x["cnt"] < 50 or x["pct"] < 90) else (1 if n else 0)
        filas.append(("VALORACIÓN", "%d%% · %s valoraciones" % (round(x["pct"]), format(int(x["cnt"]), ",").replace(",", ".")), n))
    # pais
    if x["amazon"]:
        filas.append(("SEDE", "Amazon", 0))
    elif x["pais"]:
        fuera = x["pais"] not in _VN_UE
        filas.append(("SEDE", x["pais"] + (" (fuera de la UE)" if fuera else ""), 1 if fuera else 0)); riesgo += 1 if fuera else 0
    else:
        filas.append(("SEDE", "Sin datos", None))
    # precio
    base = None; caida = None
    try:
        dias = x["serie"]
        if dias and dias[-1] is not None:
            ant = [v for v in dias[:60] if v is not None] or [v for v in dias if v is not None]
            base = _vf_mediana(ant)
            if base: caida = 1 - dias[-1] / base
    except Exception:
        pass
    if caida is None:
        filas.append(("PRECIO", "Sin histórico", None))
    elif caida >= 0.6:
        filas.append(("PRECIO", "%d%% por debajo de lo habitual" % round(caida * 100), 2)); riesgo += 3
    elif caida >= 0.35:
        filas.append(("PRECIO", "%d%% por debajo de lo habitual" % round(caida * 100), 1)); riesgo += 1
    elif caida >= 0.0:
        filas.append(("PRECIO", "Cerca de lo habitual", 0))
    else:
        filas.append(("PRECIO", "Por encima de lo habitual", 0))
    if x["amazon"]:
        v = ("ok", "PARECE FIABLE", "Lo vende y envía Amazon.")
    elif not x["conocido"]:
        v = ("dudoso", "NO SE PUEDE COMPROBAR", "Keepa no da el vendedor de este producto ahora.")
    elif riesgo >= 5:
        v = ("malo", "POSIBLE ESTAFA", "Varias señales de riesgo a la vez. Mejor no comprar.")
    elif riesgo >= 3:
        v = ("dudoso", "OJO, COMPRUEBA ANTES", "Hay señales de riesgo. Mira al vendedor antes de pagar.")
    else:
        v = ("ok", "PARECE FIABLE", "Sin señales de riesgo importantes.")
    return {"filas": filas, "veredicto": v, "riesgo": riesgo}

def _vn_img(x, r):
    from PIL import ImageDraw
    base, win, d, ww, wh, WIN = _pl_base("FICHA DEL VENDEDOR")
    ft = _cn_sans(32)
    pal = str(x["titulo"]).split(); lin = []; cur = ""
    for p in pal:
        pr = (cur + " " + p).strip()
        if d.textlength(pr, font=ft) <= ww - 80: cur = pr
        else: lin.append(cur); cur = p
    lin.append(cur); lin = lin[:2]
    if len(lin) == 2 and len(pal) > len(" ".join(lin).split()):
        lin[1] = _pl_corta(d, lin[1] + " …", ft, ww - 80)
    for i, l in enumerate(lin):
        d.text((40, 128 + i * 40), l, font=ft, fill=(255, 255, 255), anchor="lm")
    nombre = "Amazon" if x["amazon"] else (x["nombre"] or "Vendedor sin nombre")
    d.text((40, 242), _pl_corta(d, nombre, _cn_serb(52), ww - 80), font=_cn_serb(52), fill=(236, 170, 98), anchor="lm")
    col = {0: (120, 220, 140), 1: (236, 170, 98), 2: (240, 110, 90), None: (110, 118, 136)}
    for i, (lab, val, niv) in enumerate(r["filas"]):
        y = 300 + i * 78
        d.rounded_rectangle((30, y, ww - 30, y + 66), radius=22, fill=(20, 15, 12), outline=(80, 66, 58), width=2)
        d.ellipse((52, y + 20, 78, y + 46), fill=col[niv])
        d.text((100, y + 33), lab, font=_cn_mono(22), fill=(160, 168, 185), anchor="lm")
        d.text((ww - 52, y + 33), _pl_corta(d, val, _cn_sans(28), ww - 440), font=_cn_sans(28), fill=(255, 255, 255), anchor="rm")
    tipo, tit, sub = r["veredicto"]
    vc = {"ok": (120, 220, 140), "dudoso": (236, 170, 98), "malo": (240, 110, 90)}[tipo]
    d.rounded_rectangle((40, 712, ww - 40, 905), radius=34, fill=(26, 18, 12), outline=vc, width=4)
    d.text((ww // 2, 765), tit, font=_cn_sans(44), fill=vc, anchor="mm")
    fs = _cn_sans(25, False); sl = []; cur = ""
    for p in sub.split():
        pr = (cur + " " + p).strip()
        if d.textlength(pr, font=fs) <= ww - 140: cur = pr
        else: sl.append(cur); cur = p
    sl.append(cur)
    for i, l in enumerate(sl[:2]):
        d.text((ww // 2, 822 + i * 32), l, font=fs, fill=(235, 238, 245), anchor="mm")
    d.text((ww // 2, 878), "Estimación con datos de Keepa, no es una garantía", font=_cn_sans(19, False), fill=(150, 158, 176), anchor="mm")
    return _pl_cerrar(base, win, WIN, True)

def _vn_hacer(cid, texto):
    try:
        asin = _vf_asin(texto)
        if not asin:
            enviar(cid, "Pégame el enlace del producto de Amazon.es y te enseño quién lo vende y si es fiable."); return
        x = _vn_datos(asin)
        if x is None:
            enviar(cid, "Ahora mismo no puedo consultar los datos. Prueba en un rato."); return
        r = _vn_analizar(x)
        img = _vn_img(x, r)
        tipo, tit, sub = r["veredicto"]
        em = {"ok": "\U0001f7e2", "dudoso": "\U0001f7e1", "malo": "\U0001f534"}[tipo]
        cap = "%s %s\n%s\n\n\U0001f575 Vendedor: %s\n\U0001f449 https://www.amazon.es/dp/%s?tag=alexexplore0e-21" % (
            em, tit, sub, "Amazon" if x["amazon"] else (x["nombre"] or "sin nombre"), asin)
        _pl_enviar(cid, img, cap)
    except Exception as e:
        print("error /vendedor", e, flush=True)
        try: enviar(cid, "No he podido comprobar ese producto. Prueba con otro enlace.")
        except Exception: pass

def _vn_lanzar(cid, uid, texto):
    if _cn_time.time() - _VN_ULT.get(uid, 0) < 30:
        enviar(cid, "Un momento, espera unos segundos entre consultas."); return
    _VN_ULT[uid] = _cn_time.time()
    if len(_VN_ULT) > 500: _VN_ULT.clear()
    enviar(cid, "Mirando al vendedor…")
    _vd_th.Thread(target=_vn_hacer, args=(cid, texto), daemon=True).start()

_vn_pre_hook = hook_anuncios_pago

def hook_anuncios_pago(d, u):
    try:
        m = u.get("message")
        t = ((m.get("text") or "") if m else "").strip()
        if m and t:
            cid = m["chat"]["id"]; uid = (m.get("from") or {}).get("id", cid)
            prim = t.split()[0]; cmd = prim.lower().split("@")[0]
            if cmd == "/vendedor":
                if len(t.split()) == 1 and not _vf_asin(t):
                    _VN_ESPERA[str(cid)] = _cn_time.time()
                    enviar(cid, "Pégame el enlace del producto de Amazon.es y te enseño quién lo vende y si es fiable."); return True
                _VN_ESPERA.pop(str(cid), None)
                _vn_lanzar(cid, uid, t[len(prim):]); return True
            if str(cid) in _VN_ESPERA and not t.startswith("/"):
                if _cn_time.time() - _VN_ESPERA[str(cid)] < 300 and _vf_asin(t):
                    _VN_ESPERA.pop(str(cid), None)
                    _vn_lanzar(cid, uid, t); return True
    except Exception as e:
        print("error hook vendedor", e, flush=True)
    return _vn_pre_hook(d, u)
'''
MENUB = r'''
_vn_tec_orig = teclado_menu
def teclado_menu():
    try:
        kb = json.loads(_vn_tec_orig())
        filas = kb["inline_keyboard"]
        filas.insert(max(0, len(filas) - 1), [{"text": "\U0001f7e0 Vendedor", "callback_data": "m_vendedor"}])
        return json.dumps(kb)
    except Exception as e:
        print("error menu vendedor", e, flush=True)
        return _vn_tec_orig()

_vn_hook_menu_orig = hook_menu
def hook_menu(d, u):
    try:
        cq = u.get("callback_query")
        if cq and cq.get("data") == "m_vendedor":
            try:
                requests.post(API + "/answerCallbackQuery", data={"callback_query_id": cq["id"]}, timeout=10)
            except Exception:
                pass
            cid = str(cq["from"]["id"])
            _VN_ESPERA[cid] = _cn_time.time()
            requests.post(API + "/sendMessage", data={"chat_id": cid, "text": "\U0001f7e0 Pégame el enlace del producto de Amazon.es y te enseño quién lo vende y si es fiable."}, timeout=15)
            return True
    except Exception as e:
        print("error boton vendedor", e, flush=True)
    return _vn_hook_menu_orig(d, u)
'''
if MENU:
    BLOQUE = BLOQUE + MENUB
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_vendedor_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: /vendedor" + (" y boton '🟠 Vendedor' en el menu." if MENU else ". OJO: no encontre el menu, solo hay comando."))
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato   y luego /autotest")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
