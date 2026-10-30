import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()

if "# --- SEGUIR ---" in src:
    print("Ya estaba aplicado. No hago nada.")
    sys.exit(0)

def unico(patron, fn, nombre):
    global src
    n = len(re.findall(patron, src, re.M))
    if n != 1:
        print("ABORTO: ancla '%s' encontrada %d veces" % (nombre, n))
        sys.exit(1)
    src = re.sub(patron, fn, src, count=1, flags=re.M)

FUNC = r'''# --- SEGUIR ---
import re
import json

MAX_SEGUIR = 10
SEG_CADA = 600
SEG_LOTE = 30
_SEG_UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}
_SEG_RE_ASIN = re.compile(r"(?:/dp/|/gp/product/|/product/|/gp/aw/d/)([A-Za-z0-9]{10})")

def _s_d(d):
    return d.setdefault("seguir", {})

def _s_url(asin):
    return ("https://www.amazon.es/dp/%s?tag=%s" % (asin, TAG)) if TAG else ("https://www.amazon.es/dp/%s" % asin)

def _s_eur(c):
    return "%.2f" % (c / 100.0)

def _s_extraer(args):
    """Devuelve (asin, precio_en_centimos o None, error)."""
    asin, precio = "", None
    for tk in args:
        t = tk.strip()
        if not t:
            continue
        if t.lower().startswith("http") or "amzn." in t.lower() or t.lower().startswith("a.co/"):
            m = _SEG_RE_ASIN.search(t)
            if not m:
                try:
                    u = t if t.lower().startswith("http") else "https://" + t
                    r = requests.get(u, headers=_SEG_UA, timeout=12, allow_redirects=True)
                    m = _SEG_RE_ASIN.search(r.url or "") or _SEG_RE_ASIN.search(r.text[:20000] if r.text else "")
                except Exception:
                    m = None
            if m:
                asin = m.group(1).upper()
            continue
        if re.fullmatch(r"[A-Za-z0-9]{10}", t) and re.search(r"[A-Za-z]", t) and not asin:
            asin = t.upper()
            continue
        p = re.fullmatch(r"(?:€)?(\d+(?:[.,]\d{1,2})?)(?:€|eur|euros)?", t.lower())
        if p:
            try:
                precio = int(round(float(p.group(1).replace(",", ".")) * 100))
            except Exception:
                pass
    if not asin:
        return "", None, "No encuentro el producto. Pega el enlace de Amazon (amazon.es/dp/...) o el código ASIN."
    return asin, precio, ""

def _s_precios(d, asins):
    """Consulta Keepa (1 token por producto). Devuelve {asin: (precio_cents o None, titulo)}."""
    out = {}
    if not asins or not KEEPA_KEY:
        return out
    try:
        r = requests.get("https://api.keepa.com/product",
                         params={"key": KEEPA_KEY, "domain": 9, "asin": ",".join(asins), "stats": 1, "history": 0}, timeout=30)
        if r.status_code != 200:
            print("keepa seguir HTTP", r.status_code, flush=True)
            return out
        j = r.json()
        if j.get("tokensLeft") is not None:
            d["a_tok"] = j.get("tokensLeft")
        for p in (j.get("products") or []):
            a = p.get("asin")
            cur = ((p.get("stats") or {}).get("current")) or []
            c = [cur[t] for t in (0, 1) if len(cur) > t and isinstance(cur[t], int) and cur[t] > 0]
            out[a] = (min(c) if c else None, (p.get("title") or a).strip())
    except Exception as e:
        print("error seguir keepa", e, flush=True)
    return out

def seguir_cmd(d, cid, args):
    seg = _s_d(d)
    lista = seg.setdefault(cid, [])
    if args and args[0].lower() in ("quitar", "borrar", "del"):
        if len(args) > 1 and args[1].lower() in ("todos", "todo"):
            seg[cid] = []
            enviar(cid, "\U0001f5d1 Has dejado de seguir todos los productos.")
        elif len(args) > 1 and args[1].isdigit() and 1 <= int(args[1]) <= len(lista):
            e = lista.pop(int(args[1]) - 1)
            enviar(cid, "\U0001f5d1 Dejas de seguir: %s" % (e.get("t") or e["asin"])[:80])
        else:
            enviar(cid, "Uso: /seguir quitar 2  (el número de tu lista) o /seguir quitar todos")
        return
    if not args:
        if not lista:
            enviar(cid, "\U0001f514 SEGUIR PRODUCTOS\n\nPega un enlace de Amazon y el precio al que lo quieres, y te aviso cuando baje a ese precio.\n\n"
                        "Ejemplo:\n/seguir https://www.amazon.es/dp/B0XXXXXXXX 25\n\nTambién puedes seguir hasta %d productos." % MAX_SEGUIR)
            return
        t = "\U0001f514 PRODUCTOS QUE SIGUES (%d/%d)\n\n" % (len(lista), MAX_SEGUIR)
        for i, e in enumerate(lista):
            act = _s_eur(e["cur"]) + " EUR" if e.get("cur") else "sin precio"
            t += "%d. %s\n   Ahora: %s · Tu precio: %s EUR\n" % (i + 1, (e.get("t") or e["asin"])[:70], act, _s_eur(e["obj"]))
        t += "\nAñadir: /seguir enlace precio\nQuitar: /seguir quitar 2"
        enviar(cid, t)
        return
    asin, precio, err = _s_extraer(args)
    if err:
        enviar(cid, "⚠️ " + err)
        return
    ya = next((e for e in lista if e["asin"] == asin), None)
    if not ya and len(lista) >= MAX_SEGUIR:
        enviar(cid, "Ya sigues %d productos (máximo). Quita alguno con /seguir quitar 1" % MAX_SEGUIR)
        return
    info = _s_precios(d, [asin]).get(asin)
    if info is None:
        enviar(cid, "No he podido comprobar ese producto ahora mismo. Inténtalo de nuevo en unos minutos.")
        return
    cur, titulo = info
    defecto = False
    if precio is None:
        if not cur:
            enviar(cid, "Ese producto no tiene precio ahora mismo. Añade el precio que quieres: /seguir enlace 25")
            return
        precio = int(cur * 0.9)
        defecto = True
    e = ya or {"asin": asin, "ts": int(time.time())}
    e.update({"obj": precio, "t": titulo, "cur": cur, "ult": None})
    if not ya:
        lista.append(e)
    t = "✅ Siguiendo: %s\nPrecio actual: %s\nTe aviso cuando llegue a %s EUR o menos." % (
        titulo[:90], (_s_eur(cur) + " EUR") if cur else "sin stock", _s_eur(precio))
    if defecto:
        t += "\n(He puesto un 10%% menos que el actual. Cámbialo con /seguir enlace precio)"
    if cur and cur <= precio:
        t += "\n\U0001f525 Ya está a tu precio o por debajo:\n" + _s_url(asin)
        e["ult"] = cur
    enviar(cid, t)

def _s_tarea(d):
    seg = d.get("seguir") or {}
    if not seg:
        return
    ahora = time.time()
    if ahora - d.get("seg_ult", 0) < SEG_CADA:
        return
    d["seg_ult"] = ahora
    if d.get("a_tok", 999) < 150:
        return
    chk = d.setdefault("seg_chk", {})
    asins = sorted({e["asin"] for lst in seg.values() for e in lst}, key=lambda a: chk.get(a, 0))[:SEG_LOTE]
    if not asins:
        return
    precios = _s_precios(d, asins)
    for a in asins:
        chk[a] = int(ahora)
    for cid in list(seg.keys()):
        for e in seg[cid]:
            if e["asin"] not in precios:
                continue
            cur, titulo = precios[e["asin"]]
            e["cur"] = cur
            if titulo:
                e["t"] = titulo
            if not cur:
                continue
            if cur > e["obj"]:
                e["ult"] = None
                continue
            if e.get("ult") is not None and cur >= e["ult"]:
                continue
            en_sil = globals().get("_a_en_silencio")
            if en_sil and en_sil(d["users"].get(cid)):
                continue
            e["ult"] = cur
            msg = ("\U0001f514 ¡TU PRODUCTO HA LLEGADO A TU PRECIO!\n\n%s\nAhora: %s EUR (tu precio: %s EUR)\n%s"
                   % ((e.get("t") or e["asin"])[:100], _s_eur(cur), _s_eur(e["obj"]), _s_url(e["asin"])))
            if enviar(cid, msg) == 403:
                seg[cid] = []
                break
            time.sleep(0.05)
    for cid in [c for c, v in seg.items() if not v]:
        seg.pop(cid, None)

def seguir_admin(d, cid):
    seg = d.get("seguir") or {}
    n = sum(len(v) for v in seg.values())
    distintos = len({e["asin"] for v in seg.values() for e in v})
    enviar(cid, "\U0001f514 SEGUIMIENTOS\n\nUsuarios que siguen algo: %d\nProductos seguidos: %d (distintos: %d)" % (len(seg), n, distintos))

'''

TAIL = r'''# --- SEGUIR (arranque) ---
_pu_orig_seg = procesar_updates
def procesar_updates(d, *a, **k):
    try:
        _s_tarea(d)
    except Exception as e:
        print("error tarea seguir", e, flush=True)
    return _pu_orig_seg(d, *a, **k)

AYUDA = AYUDA + "\n\n\U0001f514 /seguir enlace precio - te aviso cuando un producto llegue a tu precio (/seguir para ver tu lista)"

'''

unico(r'^def comando\(d, cid, texto\):\n', lambda m: FUNC + m.group(0), "comando")
unico(r'^    elif cmd in \("/propina", "/premium"\):\n',
      lambda m: ('    elif cmd in ("/seguir", "/seguidos"):\n        seguir_cmd(d, cid, args)\n'
                 '    elif cmd == "/seguimientos" and cid == ADMIN:\n        seguir_admin(d, cid)\n') + m.group(0), "propina")
unico(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), "main")

try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)

copia = RUTA + ".bak_seguir_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
