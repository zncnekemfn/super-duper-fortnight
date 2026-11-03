import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- ALI1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("def _cn_frame(", "def _pl_enviar(", "def hook_anuncios_pago(", '(dat.get("pie1")', "_vd_th", "_cn_io", "_cn_time"):
    if n not in src:
        print("ABORTO: no encuentro", n, "(aplica antes los parches de tarjetas y plantillas)"); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)
MENU = ("def teclado_menu(" in src and "def hook_menu(" in src)

BLOQUE = r'''
# --- ALI1 ---
# /ali ENLACE_DE_ALIEXPRESS -> tu enlace de afiliado + tarjeta del producto
# /ali PALABRA              -> mejores resultados de AliExpress con tarjeta del mejor
# Las claves se leen de /opt/chivato/aliexpress.env (no estan en el codigo).
import hashlib as _al_hl, hmac as _al_hm
_AL_ENV = "/opt/chivato/aliexpress.env"
_AL_URL = "https://api-sg.aliexpress.com/sync"
_AL_ULT = {}
_AL_ESPERA = {}

def _al_cfg():
    d = {}
    with open(_AL_ENV, encoding="utf-8") as fh:
        for l in fh:
            if "=" in l:
                k, v = l.rstrip("\n").split("=", 1); d[k.strip()] = v.strip()
    return d

def _al_api(metodo, extra):
    c = _al_cfg()
    p = {"app_key": c["ALI_APP_KEY"], "method": metodo, "timestamp": str(int(_cn_time.time() * 1000)),
         "sign_method": "sha256", "format": "json", "v": "2.0"}
    p.update(extra)
    base = "".join(k + str(p[k]) for k in sorted(p))
    p["sign"] = _al_hm.new(c["ALI_APP_SECRET"].encode(), base.encode(), _al_hl.sha256).hexdigest().upper()
    r = requests.post(_AL_URL, data=p, timeout=30)
    return r.json()

def _al_resultado(j):
    for k, v in (j or {}).items():
        if k.endswith("_response") and isinstance(v, dict):
            return ((v.get("resp_result") or {}).get("result")) or {}
    if "error_response" in (j or {}):
        print("ali error", str(j["error_response"])[:200], flush=True)
    return {}

def _al_trk():
    return _al_cfg()["ALI_TRACKING_ID"]

def _al_enlaces(urls):
    out = {}
    try:
        j = _al_api("aliexpress.affiliate.link.generate", {"promotion_link_type": "0", "source_values": ",".join(urls), "tracking_id": _al_trk()})
        res = _al_resultado(j)
        pl = ((res.get("promotion_links") or {}).get("promotion_link")) or []
        for x in pl:
            if x.get("source_value") and x.get("promotion_link"):
                out[x["source_value"]] = x["promotion_link"]
    except Exception as e:
        print("error ali enlaces", str(e)[:100], flush=True)
    return out

def _al_num(v):
    try:
        return float(str(v).replace(",", ".").strip().replace("%", ""))
    except Exception:
        return None

def _al_prod(p):
    ahora = _al_num(p.get("target_app_sale_price") or p.get("app_sale_price") or p.get("target_sale_price") or p.get("sale_price"))
    antes = _al_num(p.get("target_original_price") or p.get("original_price"))
    pct = None
    if ahora and antes and antes > ahora:
        pct = int(round((1 - ahora / antes) * 100))
    elif _al_num(p.get("discount")) is not None:
        pct = int(_al_num(p.get("discount")))
    img = p.get("product_main_image_url")
    if not img:
        pi = (p.get("product_small_image_urls") or {}).get("string") or []
        img = pi[0] if pi else None
    return {"id": str(p.get("product_id") or ""), "titulo": p.get("product_title") or "Producto de AliExpress", "ahora": ahora, "antes": antes, "pct": pct,
            "img": img, "url": p.get("product_detail_url") or "", "link": p.get("promotion_link"), "rat": p.get("evaluate_rate"),
            "ventas": p.get("lastest_volume")}

def _al_foto(u):
    try:
        from PIL import Image
        if u:
            r = requests.get(u, timeout=20)
            if r.status_code == 200 and len(r.content) > 2000:
                return Image.open(_cn_io.BytesIO(r.content)).convert("RGB")
    except Exception as e:
        print("error foto ali", str(e)[:80], flush=True)
    return None

def _al_tarjeta(cid, x, link, extra=""):
    dat = {"titulo": x["titulo"], "ahora": x["ahora"] or 0.0, "antes": x["antes"] or (x["ahora"] or 0.0), "pct": x["pct"] or 0,
           "foto": _al_foto(x["img"]), "hora": _cn_time.strftime("AVISO %H:%M · %d/%m/%Y"), "rat": "", "nv": "",
           "pie1": "Enlace de afiliado. Los precios pueden cambiar."}
    img = _cn_frame(dat, 0.0, 6.0, True)
    cap = "\U0001f6d2 %s\n" % str(x["titulo"])[:150]
    if x["ahora"]:
        cap += "\U0001f4a5 %s%s€" % ("-%d%% → " % x["pct"] if x["pct"] else "", ("%.2f" % x["ahora"]).replace(".", ","))
        if x["antes"] and x["antes"] > x["ahora"]:
            cap += " (antes %s €)" % ("%.2f" % x["antes"]).replace(".", ",")
        cap += "\n"
    cap += "\U0001f449 %s\n(Enlace de afiliado.)" % link
    if extra:
        cap += "\n\n" + extra
    _pl_enviar(cid, img, cap)

def _al_id(url):
    m = re.search(r"/item/(\d{8,})", url) or re.search(r"[?&]productIds?=(\d{8,})", url)
    if m:
        return m.group(1)
    try:
        r = requests.get(url, timeout=20, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"})
        m = re.search(r"/item/(\d{8,})", r.url) or re.search(r"productIds?=(\d{8,})", r.url)
        return m.group(1) if m else None
    except Exception:
        return None

def _al_hacer(cid, texto):
    try:
        texto = (texto or "").strip()
        mu = re.search(r"https?://[^\s<>\"']*aliexpress\.[^\s<>\"']+", texto)
        if mu:
            url = mu.group(0).rstrip(").,")
            ln = _al_enlaces([url]).get(url)
            if not ln:
                enviar(cid, "No he podido generar el enlace de ese producto. Comprueba que es un enlace de AliExpress."); return
            pid = _al_id(url)
            x = None
            if pid:
                try:
                    j = _al_api("aliexpress.affiliate.productdetail.get", {"product_ids": pid, "target_currency": "EUR", "target_language": "ES",
                                                                              "country": "ES", "tracking_id": _al_trk()})
                    ps = ((_al_resultado(j).get("products") or {}).get("product")) or []
                    if ps: x = _al_prod(ps[0])
                except Exception as e:
                    print("error ali detalle", str(e)[:100], flush=True)
            if x and x["ahora"]:
                _al_tarjeta(cid, x, ln)
            else:
                enviar(cid, "\U0001f6d2 Tu enlace de afiliado:\n%s\n(Enlace de afiliado.)" % ln)
            return
        if not texto:
            enviar(cid, "Pega un enlace de AliExpress o escribe qué buscas. Ejemplo: /ali auriculares bluetooth"); return
        j = _al_api("aliexpress.affiliate.product.query", {"keywords": texto[:80], "page_size": "20", "page_no": "1", "sort": "LAST_VOLUME_DESC",
                    "ship_to_country": "ES", "target_currency": "EUR", "target_language": "ES", "tracking_id": _al_trk()})
        ps = [_al_prod(p) for p in (((_al_resultado(j).get("products") or {}).get("product")) or [])]
        ps = [p for p in ps if p["ahora"]]
        if not ps:
            enviar(cid, "No he encontrado nada para eso en AliExpress. Prueba con otra palabra."); return
        ps.sort(key=lambda p: -(p["pct"] or 0))
        top = ps[:3]
        falt = [p["url"] for p in top if not p["link"] and p["url"]]
        if falt:
            m = _al_enlaces(falt)
            for p in top:
                if not p["link"]: p["link"] = m.get(p["url"])
        top = [p for p in top if p["link"]]
        if not top:
            enviar(cid, "No he podido preparar los enlaces. Prueba en un rato."); return
        lista = "Otros resultados:\n" + "\n".join("• %s%s: %s" % (str(p["titulo"])[:50], " (%s€)" % ("%.2f" % p["ahora"]).replace(".", ","), p["link"]) for p in top[1:]) if len(top) > 1 else ""
        _al_tarjeta(cid, top[0], top[0]["link"], lista)
    except Exception as e:
        print("error /ali", e, flush=True)
        try: enviar(cid, "No he podido consultar AliExpress ahora mismo. Prueba en un rato.")
        except Exception: pass

def _al_lanzar(cid, uid, texto):
    if _cn_time.time() - _AL_ULT.get(uid, 0) < 10:
        enviar(cid, "Un momento, espera unos segundos entre consultas."); return
    _AL_ULT[uid] = _cn_time.time()
    if len(_AL_ULT) > 500: _AL_ULT.clear()
    enviar(cid, "Buscando en AliExpress…")
    _vd_th.Thread(target=_al_hacer, args=(cid, texto), daemon=True).start()

_al_pre_hook = hook_anuncios_pago

def hook_anuncios_pago(d, u):
    try:
        m = u.get("message")
        t = ((m.get("text") or "") if m else "").strip()
        if m and t:
            cid = m["chat"]["id"]; uid = (m.get("from") or {}).get("id", cid)
            prim = t.split()[0]; cmd = prim.lower().split("@")[0]
            if cmd == "/ali":
                arg = t[len(prim):].strip()
                if not arg:
                    _AL_ESPERA[str(cid)] = _cn_time.time()
                    enviar(cid, "\U0001f6d2 Pega un enlace de AliExpress y te doy tu enlace de afiliado, o escribe qué buscas (ejemplo: auriculares bluetooth)."); return True
                _AL_ESPERA.pop(str(cid), None)
                _al_lanzar(cid, uid, arg); return True
            if str(cid) in _AL_ESPERA and not t.startswith("/"):
                if _cn_time.time() - _AL_ESPERA[str(cid)] < 300:
                    _AL_ESPERA.pop(str(cid), None)
                    _al_lanzar(cid, uid, t); return True
                _AL_ESPERA.pop(str(cid), None)
    except Exception as e:
        print("error hook ali", e, flush=True)
    return _al_pre_hook(d, u)
'''
MENUB = r'''
_al_tec_orig = teclado_menu
def teclado_menu():
    try:
        kb = json.loads(_al_tec_orig())
        filas = kb["inline_keyboard"]
        filas.insert(max(0, len(filas) - 1), [{"text": "\U0001f6d2 AliExpress", "callback_data": "m_ali"}])
        return json.dumps(kb)
    except Exception as e:
        print("error menu ali", e, flush=True)
        return _al_tec_orig()

_al_hook_menu_orig = hook_menu
def hook_menu(d, u):
    try:
        cq = u.get("callback_query")
        if cq and cq.get("data") == "m_ali":
            try:
                requests.post(API + "/answerCallbackQuery", data={"callback_query_id": cq["id"]}, timeout=10)
            except Exception:
                pass
            cid = str(cq["from"]["id"])
            _AL_ESPERA[cid] = _cn_time.time()
            requests.post(API + "/sendMessage", data={"chat_id": cid, "text": "\U0001f6d2 Pega un enlace de AliExpress y te doy tu enlace de afiliado, o escribe qué buscas (ejemplo: auriculares bluetooth)."}, timeout=15)
            return True
    except Exception as e:
        print("error boton ali", e, flush=True)
    return _al_hook_menu_orig(d, u)
'''
if MENU:
    BLOQUE = BLOQUE + MENUB
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_ali_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: /ali" + (" y boton '🛒 AliExpress' en el menu." if MENU else ". OJO: no encontre el menu, solo hay comando."))
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato   y luego /autotest")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
