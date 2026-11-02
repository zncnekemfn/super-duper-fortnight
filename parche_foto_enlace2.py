import re, shutil, time, sys
RUTA = "/opt/chivato/bot.py"
MARCA = "# --- FOTOENLACE2 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("def _vd_de_enlace(", "def _vd_keepa(", "def _vd_token(", "def _ft_render(", "def hook_anuncios_pago(", "_cn_loc"):
    if n not in src:
        print("ABORTO: no encuentro", n); sys.exit(1)

BLOQUE = r'''
# --- FOTOENLACE2 ---
# /foto ENLACE [ahora] [antes] -> SOLO foto (sin video), estilo de los avisos. Independiente de /video.
_FE_TAG = "alexexplore0e-21"
_fe2_pre_hook = hook_anuncios_pago

def _fe2_num(a):
    try:
        return float(str(a).replace(",", ".").replace("€", ""))
    except Exception:
        return None

def _fe2_hacer(d, asin, p, ahora, antes, pct, destino):
    ruta = None
    try:
        titulo = (p.get("title") or asin)
        try:
            _ids = str(p.get("imagesCSV") or "").split(",")[0]
            if _ids: _CN_IMGID[asin] = _ids
        except Exception:
            pass
        item = {"u": "https://www.amazon.es/dp/" + asin}
        try:
            mr = _ft_re.search(r"([\d.,]+)\s*·\s*([\d.]+)\s*valoraci", _vn_valoracion(asin) or "")
            if mr:
                item["rat"] = mr.group(1); item["nv"] = mr.group(2)
        except Exception:
            pass
        _cn_loc.item = item
        ruta = _ft_os.path.join(_ft_tmp.gettempdir(), "foto_enlace_%s.jpg" % asin)
        _ft_render(titulo, ahora, antes, pct, ruta)
        if not _ft_os.path.exists(ruta):
            raise RuntimeError("no se genero la imagen")
        link = "https://www.amazon.es/dp/%s?tag=%s" % (asin, _FE_TAG)
        cap = ("⚡ PRECIAZO ⚡\n\n%s\n\U0001f4a5 -%d%% → %.2f € (antes %.2f €)\n\n\U0001f449 %s\n"
               "(Como afiliado de Amazon obtengo ingresos por las compras adscritas.)") % (
               str(titulo)[:160], pct, ahora, antes, link)
        with open(ruta, "rb") as fh:
            r = requests.post("https://api.telegram.org/bot%s/sendPhoto" % _vd_token(),
                              data={"chat_id": destino, "caption": cap[:1000]}, files={"photo": fh}, timeout=60)
        if r.status_code != 200:
            enviar(destino, "La foto se ha generado pero Telegram no la ha aceptado.")
    except Exception as e:
        print("error foto enlace", e, flush=True)
        try: enviar(destino, "Error generando la foto: %s" % str(e)[:150])
        except Exception: pass
    finally:
        try:
            _cn_loc.item = None
            if ruta and _ft_os.path.exists(ruta): _ft_os.remove(ruta)
        except Exception:
            pass

def _fe2_cmd(d, cid, args):
    asin, nums = "", []
    for a in args:
        if a.lower().startswith("http"):
            asin = asin or _vd_de_enlace(a)
        elif _vd_re.fullmatch(r"[A-Za-z0-9]{10}", a) and not asin and _fe2_num(a) is None:
            asin = a.upper()
        elif _fe2_num(a) is not None:
            nums.append(_fe2_num(a))
    if not asin:
        enviar(cid, "Foto de una oferta a partir de un enlace:\n/foto ENLACE\n/foto ENLACE 10.29 18.00 (ahora y antes)\nTambien vale el ASIN.")
        return
    p = _vd_keepa(d, asin)
    if not p:
        enviar(cid, "Keepa no ha devuelto ese producto."); return
    st = p.get("stats") or {}
    cur, av = st.get("current") or [], st.get("avg90") or []
    def g(l, i):
        return l[i] if len(l) > i and isinstance(l[i], (int, float)) and l[i] > 0 else None
    origen = ""
    if len(nums) >= 2 and nums[1] > nums[0] > 0:
        ahora, antes, origen = nums[0], nums[1], "precios indicados por ti"
    else:
        a_c = g(cur, 18) or g(cur, 0) or g(cur, 1) or g(cur, 10)
        if not a_c:
            enviar(cid, "No encuentro el precio actual de ese producto."); return
        ahora = a_c / 100.0
        lista = g(cur, 4)
        media = max([x for x in (g(av, 0), g(av, 1), g(av, 18)) if x] or [0])
        if len(nums) == 1 and nums[0] > ahora:
            antes, origen = nums[0], "precio anterior indicado por ti"
        elif lista and lista > a_c:
            antes, origen = lista / 100.0, "precio tachado de Amazon"
        elif media and media > a_c:
            antes, origen = media / 100.0, "media de los ultimos 90 dias"
        else:
            enviar(cid, "No hay un precio anterior mayor. Escribelo tu:\n/foto ENLACE %.2f PRECIO_ANTES" % ahora)
            return
    pct = int(round(100.0 * (antes - ahora) / antes))
    enviar(cid, "Preparando la FOTO de %s: %.2f € (antes %.2f €, -%d%%). Origen del precio anterior: %s." % (asin, ahora, antes, pct, origen))
    _vd_th.Thread(target=_fe2_hacer, args=(d, asin, p, ahora, antes, pct, cid), daemon=True).start()

def hook_anuncios_pago(d, u):
    try:
        m = u.get("message")
        t = ((m.get("text") or "") if m else "").strip()
        if m and t and t.lower().split("@")[0].split()[0] == "/foto" and str(m["chat"]["id"]) == str(ADMIN):
            _fe2_cmd(d, m["chat"]["id"], t.split()[1:])
            return True
    except Exception as e:
        print("error /foto", e, flush=True)
    return _fe2_pre_hook(d, u)
'''
n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
nuevo = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: BLOQUE + "\n" + m.group(0), src, count=1, flags=re.M)
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
copia = RUTA + ".bak_fotoenlace2_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado. Copia:", copia)
print("Ahora ejecuta: systemctl restart chivato")
