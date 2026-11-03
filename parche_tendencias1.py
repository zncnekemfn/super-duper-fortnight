import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- TENDENCIAS1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("KEEPA_KEY", "def hook_anuncios_pago(", "def teclado_menu(", "def hook_menu(", "def enviar(", "_vd_th"):
    if n not in src:
        print("ABORTO: falta", n); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''
# --- TENDENCIAS1 ---
# Boton "Tendencias": los productos mas vendidos ahora en Amazon.es por categoria (lista oficial de mas vendidos, via Keepa).
# Coste Keepa: 50 tokens por categoria + 1 por producto; se guarda 3 horas para gastar poco.
import unicodedata as _td_ud
_TD_CATS = [("Electrónica", "electr"), ("Informática", "inform"), ("Videojuegos", "videojuegos"),
            ("Hogar y cocina", "hogar"), ("Juguetes", "juguetes"), ("Deportes", "deportes")]
_TD_RAIZ = {"ts": 0, "cats": []}
_TD_CACHE = {}
_TD_ULT = {}

def _td_norm(s):
    return "".join(c for c in _td_ud.normalize("NFD", str(s).lower()) if _td_ud.category(c) != "Mn")

def _td_categorias():
    if _TD_RAIZ["cats"] and time.time() - _TD_RAIZ["ts"] < 86400:
        return _TD_RAIZ["cats"]
    r = requests.get("https://api.keepa.com/category", params={"key": KEEPA_KEY, "domain": 9, "category": 0}, timeout=20)
    cs = (r.json() or {}).get("categories") or {}
    out = []
    for etiqueta, kw in _TD_CATS:
        for cid, c in cs.items():
            if kw in _td_norm(c.get("name", "")):
                out.append((etiqueta, str(c.get("catId") or cid)))
                break
    if out:
        _TD_RAIZ.update({"ts": time.time(), "cats": out})
    return out

def _td_precio(p):
    cur = (p.get("stats") or {}).get("current") or []
    for i in (18, 0, 1):
        if len(cur) > i and cur[i] and cur[i] > 0:
            return cur[i] / 100.0
    return None

def _td_lista(cid_cat, nombre):
    c = _TD_CACHE.get(cid_cat)
    if c and time.time() - c[0] < 10800:
        return c[1]
    r = requests.get("https://api.keepa.com/bestsellers", params={"key": KEEPA_KEY, "domain": 9, "category": cid_cat, "range": 0}, timeout=30)
    asins = (((r.json() or {}).get("bestSellersList") or {}).get("asinList")) or []
    asins = asins[:8]
    if not asins:
        return None
    r2 = requests.get("https://api.keepa.com/product", params={"key": KEEPA_KEY, "domain": 9, "asin": ",".join(asins), "stats": 90, "history": 0}, timeout=40)
    prods = {p.get("asin"): p for p in ((r2.json() or {}).get("products") or []) if p}
    lin = []
    for i, a in enumerate(asins):
        p = prods.get(a) or {}
        tit = str(p.get("title") or "Producto")[:70]
        pr = _td_precio(p)
        lin.append("%d. %s%s\n\U0001f449 https://www.amazon.es/dp/%s?tag=%s" % (
            i + 1, tit, (" · %s €" % ("%.2f" % pr).replace(".", ",")) if pr else "", a, TAG))
    txt = "\U0001f4c8 MÁS VENDIDOS AHORA · %s\n\n%s\n\n(Lista de más vendidos de Amazon. Los precios pueden cambiar. Como afiliado de Amazon obtengo ingresos por las compras adscritas.)" % (
        nombre.upper(), "\n\n".join(lin))
    _TD_CACHE[cid_cat] = (time.time(), txt)
    return txt

def _td_menu(cid):
    try:
        cats = _td_categorias()
        if not cats:
            enviar(cid, "Ahora mismo no puedo consultar las tendencias. Prueba en un rato."); return
        filas = [[{"text": n, "callback_data": "tdn_" + i} for n, i in cats[k:k + 2]] for k in range(0, len(cats), 2)]
        enviar(cid, "\U0001f4c8 TENDENCIAS\n\nLo más vendido ahora en Amazon. Elige una categoría:", json.dumps({"inline_keyboard": filas}))
    except Exception as e:
        print("error tendencias menu", str(e)[:100], flush=True)
        enviar(cid, "Ahora mismo no puedo consultar las tendencias. Prueba en un rato.")

def _td_mostrar(cid, cat_id):
    try:
        nombre = next((n for n, i in _td_categorias() if i == cat_id), "")
        if not nombre:
            enviar(cid, "Esa categoría ya no está disponible. Abre Tendencias otra vez."); return
        txt = _td_lista(cat_id, nombre)
        enviar(cid, txt or "No he encontrado la lista de más vendidos para esa categoría ahora mismo.")
    except Exception as e:
        print("error tendencias lista", str(e)[:100], flush=True)
        enviar(cid, "Ahora mismo no puedo consultar las tendencias. Prueba en un rato.")

def _td_lanzar(cid, fn, *a):
    if time.time() - _TD_ULT.get(cid, 0) < 4:
        return
    _TD_ULT[cid] = time.time()
    if len(_TD_ULT) > 500: _TD_ULT.clear()
    _vd_th.Thread(target=fn, args=(cid,) + a, daemon=True).start()

_td_tec_orig = teclado_menu
def teclado_menu():
    try:
        kb = json.loads(_td_tec_orig())
        filas = kb["inline_keyboard"]
        filas.insert(max(0, len(filas) - 1), [{"text": "\U0001f4c8 Tendencias", "callback_data": "m_tend"}])
        return json.dumps(kb)
    except Exception as e:
        print("error menu tendencias", str(e)[:80], flush=True)
        return _td_tec_orig()

_td_hook_menu_orig = hook_menu
def hook_menu(d, u):
    try:
        cq = u.get("callback_query")
        dato = str((cq or {}).get("data") or "")
        if cq and (dato == "m_tend" or dato.startswith("tdn_")):
            try:
                requests.post(API + "/answerCallbackQuery", data={"callback_query_id": cq["id"]}, timeout=10)
            except Exception:
                pass
            cid = cq["from"]["id"]
            if dato == "m_tend":
                _td_lanzar(cid, _td_menu)
            else:
                _td_lanzar(cid, _td_mostrar, dato[4:])
            return True
    except Exception as e:
        print("error boton tendencias", str(e)[:100], flush=True)
    return _td_hook_menu_orig(d, u)

_td_hook_orig = hook_anuncios_pago
def hook_anuncios_pago(d, u):
    try:
        m = u.get("message")
        t = ((m.get("text") or "") if m else "").strip()
        if m and t and t.split()[0].lower().split("@")[0] == "/tendencias":
            _td_lanzar(m["chat"]["id"], _td_menu)
            return True
    except Exception as e:
        print("error hook tendencias", str(e)[:100], flush=True)
    return _td_hook_orig(d, u)
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_tendencias_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: boton '📈 Tendencias' y /tendencias (más vendidos de Amazon).")
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato   y luego /autotest")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
