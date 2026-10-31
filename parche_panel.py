import os, re, shutil, sys, time, subprocess

# Parche: conecta Chivato con el Centro de mando (panel web) y añade el conversor de enlaces Awin (/awin).
# Uso: python3 parche_panel.py      y luego: systemctl restart chivato
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"

BLOQUE = r'''
# --- PANEL ---
# Conexión con el Centro de mando (panel web). El panel solo LEE data.json;
# sus órdenes llegan como archivos en PN_DIR y se aplican aquí, dentro del bucle del bot.
import glob as _pn_glob, shutil as _pn_shutil, threading as _pn_th
PN_DIR = "/opt/chivato/panel_ordenes"
PN_VID = "/opt/chivato/panel_videos"
PN_ERR_CADUCA = 6 * 3600
PN_MAX_VIDEOS = 15
for _pn_x in (PN_DIR, PN_VID):
    try:
        os.makedirs(_pn_x, exist_ok=True)
    except Exception:
        pass

def _pn_d(d):
    p = d.setdefault("panel", {})
    p.setdefault("err_espera", True)
    p.setdefault("err_cola", [])
    p.setdefault("log", [])
    p.setdefault("v", 1)
    return p

def _pn_log(d, texto, ok=True):
    p = _pn_d(d)
    p["log"].append({"ts": int(time.time()), "t": str(texto)[:300], "ok": bool(ok)})
    p["log"] = p["log"][-50:]
    print("[panel]", texto, flush=True)

def _pn_destinos(d):
    out = []
    for cid in list(d["users"].keys()):
        if cid == ADMIN or not autorizado(d, cid):
            continue
        us = d["users"].get(cid) or {}
        if any(us.get(k) for k in ("parado", "pausa", "pausado", "off", "stop")):
            continue
        out.append(cid)
    return out

# Errores de precio: si "err_espera" está activo, solo te llegan a ti y quedan en cola en el panel.
_pn_err_dest_orig = _err_dest
def _err_dest(d):
    if _pn_d(d)["err_espera"]:
        return [ADMIN]
    return _pn_err_dest_orig(d)

_pn_cp_err_orig = _cp_publicar_error
def _cp_publicar_error(d, item):
    p = _pn_d(d)
    if p["err_espera"]:
        limpio = {k: v for k, v in dict(item).items() if not str(k).startswith("_")}
        p["err_cola"].append({"id": secrets.token_hex(4), "item": limpio, "ts": int(time.time())})
        p["err_cola"] = p["err_cola"][-30:]
        return
    return _pn_cp_err_orig(d, item)

def _pn_err_caducar(d):
    p = _pn_d(d)
    ahora = time.time()
    p["err_cola"] = [x for x in p["err_cola"] if ahora - x.get("ts", 0) < PN_ERR_CADUCA]

def _pn_err_enviar(d, eid):
    p = _pn_d(d)
    x = next((x for x in p["err_cola"] if x.get("id") == eid), None)
    if not x:
        _pn_log(d, "Ese error de precio ya no está en la cola (enviado, descartado o caducado).", False)
        return
    p["err_cola"] = [y for y in p["err_cola"] if y is not x]
    item = dict(x["item"])
    envio = globals().get("_enviar_aviso_orig") or enviar_aviso
    n = 0
    for cid in _pn_destinos(d):
        try:
            envio(d, cid, item)
            n += 1
        except Exception as ex:
            print("panel error aviso", ex, flush=True)
        time.sleep(0.05)
    try:
        _pn_cp_err_orig(d, item)
    except Exception as ex:
        print("panel canal publico", ex, flush=True)
    _pn_log(d, "Error de precio enviado a %d usuarios: %s" % (n, str(item.get("t", ""))[:80].replace("\n", " ")))

def _pn_mensaje(d, texto):
    texto = str(texto or "").strip()[:4000]
    if not texto:
        return
    dest = [ADMIN] + _pn_destinos(d)
    _pn_log(d, "Enviando mensaje a %d usuarios..." % len(dest))
    def _run():
        ok = mal = 0
        for cid in dest:
            try:
                st = enviar(cid, texto)
            except Exception:
                st = 0
            if st == 200:
                ok += 1
            else:
                mal += 1
            time.sleep(0.05)
        _pn_log(d, "Mensaje a todos terminado: %d entregados, %d fallidos." % (ok, mal), mal == 0)
    _pn_th.Thread(target=_run, daemon=True).start()

def _pn_anuncio(d, accion, aid):
    ad = d["anuncios"].get(str(aid))
    if not ad:
        _pn_log(d, "No encuentro el anuncio %s." % aid, False)
        return
    est = ad.get("estado")
    if accion == "ad_pausar":
        if est in ("activo", "tablon"):
            ad["_pn_prev"] = est
            ad["estado"] = "pausado"
            _pn_log(d, "Anuncio %s pausado." % aid)
        else:
            _pn_log(d, "El anuncio %s está en estado '%s' y no se puede pausar." % (aid, est), False)
    elif accion == "ad_reanudar":
        if est == "pausado":
            ad["estado"] = ad.pop("_pn_prev", "activo")
            _pn_log(d, "Anuncio %s reanudado." % aid)
        else:
            _pn_log(d, "El anuncio %s no estaba pausado." % aid, False)
    elif accion == "ad_finalizar":
        ad["estado"] = "finalizado"
        ad.pop("_pn_prev", None)
        if ad.get("tipo") == "pago":
            ad["fin"] = min(ad.get("fin") or time.time(), time.time())
        _pn_log(d, "Anuncio %s finalizado." % aid)

_pn_tablon_orig = tablon_activo
def tablon_activo(d):
    return [a for a in _pn_tablon_orig(d)
            if (d["anuncios"].get(a) or {}).get("estado") not in ("pausado", "finalizado", "rechazado")]

def _pn_orden(d, o):
    t = o.get("tipo")
    p = _pn_d(d)
    if t == "err_enviar":
        _pn_err_enviar(d, str(o.get("id", "")))
    elif t == "err_descartar":
        antes = len(p["err_cola"])
        p["err_cola"] = [x for x in p["err_cola"] if x.get("id") != o.get("id")]
        _pn_log(d, "Error de precio descartado." if len(p["err_cola"]) < antes else "Ese error ya no estaba en la cola.", len(p["err_cola"]) < antes)
    elif t == "err_espera":
        p["err_espera"] = bool(o.get("on"))
        _pn_log(d, "Errores de precio: " + ("los reviso yo antes de enviarlos" if p["err_espera"] else "se envían solos (como antes)"))
    elif t == "mensaje":
        _pn_mensaje(d, o.get("texto"))
    elif t in ("ad_pausar", "ad_reanudar", "ad_finalizar"):
        _pn_anuncio(d, t, o.get("aid"))
    else:
        _pn_log(d, "Orden desconocida: %s" % t, False)

def _pn_ordenes(d):
    _pn_d(d)
    _pn_err_caducar(d)
    try:
        archivos = sorted(_pn_glob.glob(os.path.join(PN_DIR, "*.json")))[:20]
    except Exception:
        return
    hubo = False
    for f in archivos:
        try:
            o = json.load(open(f))
        except Exception:
            o = None
        try:
            os.remove(f)
        except Exception:
            pass
        if not isinstance(o, dict):
            continue
        hubo = True
        try:
            _pn_orden(d, o)
        except Exception as ex:
            _pn_log(d, "Error aplicando orden %s: %s" % (o.get("tipo"), ex), False)
    if hubo:
        guardar(d)

_pu_orig_pn = procesar_updates
def procesar_updates(d, *a, **k):
    try:
        _pn_ordenes(d)
    except Exception as ex:
        print("error panel", ex, flush=True)
    return _pu_orig_pn(d, *a, **k)

# Vídeos para X: además de enviártelos por Telegram, se guarda una copia para el panel.
_pn_vd_enviar_orig = _vd_enviar
def _vd_enviar(cid, ruta, texto):
    ok = _pn_vd_enviar_orig(cid, ruta, texto)
    try:
        base = "v%d_%s" % (int(time.time()), re.sub(r"[^A-Za-z0-9_]", "", os.path.splitext(os.path.basename(ruta))[0])[:40])
        _pn_shutil.copy(ruta, os.path.join(PN_VID, base + ".mp4"))
        with open(os.path.join(PN_VID, base + ".txt"), "w") as fh:
            fh.write(texto or "")
        vids = sorted(_pn_glob.glob(os.path.join(PN_VID, "*.mp4")))
        for v in vids[:-PN_MAX_VIDEOS]:
            for x in (v, v[:-4] + ".txt"):
                try:
                    os.remove(x)
                except Exception:
                    pass
    except Exception as ex:
        print("panel video copia", ex, flush=True)
    return ok

# --- AWIN ---
# Conversor de enlaces de afiliado de Awin. Solo para ti (admin):
#   pega un enlace de una tienda Awin y te devuelve tu enlace de afiliado.
#   /awin                      -> ver tiendas y ayuda
#   /awin add dominio.com 1234 -> añadir tienda (1234 = identificador del anunciante en Awin)
#   /awin quitar dominio.com   -> quitar tienda
from urllib.parse import quote as _aw_quote, urlparse as _aw_urlparse
AWIN_AFF = os.environ.get("AWIN_AFF", "3139759")
AWIN_TIENDAS = {"mibrofit.com": ("131533", "Mibro")}
_AW_URL_RE = re.compile(r"https?://[^\s<>\"']+", re.I)

def _aw_d(d):
    a = d.setdefault("awin", {})
    a.setdefault("m", {})
    a.setdefault("n", 0)
    return a

def _aw_tiendas(d):
    t = {k: list(v) for k, v in AWIN_TIENDAS.items()}
    for dom, v in _aw_d(d)["m"].items():
        t[dom] = list(v)
    return t

def _aw_dominio(url):
    try:
        h = (_aw_urlparse(url).hostname or "").lower()
    except Exception:
        return ""
    return h[4:] if h.startswith("www.") else h

def _aw_buscar(d, url):
    h = _aw_dominio(url)
    for dom, (mid, nombre) in _aw_tiendas(d).items():
        if h == dom or h.endswith("." + dom):
            return dom, mid, nombre
    return None

def awin_enlace(mid, url):
    return "https://www.awin1.com/cread.php?awinmid=%s&awinaffid=%s&ued=%s" % (mid, AWIN_AFF, _aw_quote(url, safe=""))

def _aw_convertir(d, txt):
    out = []
    for url in _AW_URL_RE.findall(txt or ""):
        url = url.rstrip(".,);]")
        if "awin1.com" in url:
            continue
        t = _aw_buscar(d, url)
        if t:
            out.append((t[2], awin_enlace(t[1], url)))
    return out

def awin_cmd(d, cid, args):
    a = _aw_d(d)
    if len(args) >= 3 and args[0].lower() in ("add", "añadir", "anadir") and args[2].isdigit():
        dom = _aw_dominio(args[1] if "://" in args[1] else "https://" + args[1])
        if not dom or "." not in dom:
            enviar(cid, "Dominio no válido. Ejemplo: /awin add tienda.com 12345")
            return
        a["m"][dom] = [args[2], " ".join(args[3:]) or dom]
        enviar(cid, "✅ Tienda añadida: %s (anunciante %s). Pega un enlace suyo y te doy tu enlace de afiliado." % (dom, args[2]))
        return
    if len(args) >= 2 and args[0].lower() in ("quitar", "del", "borrar"):
        dom = _aw_dominio(args[1] if "://" in args[1] else "https://" + args[1])
        if a["m"].pop(dom, None) is not None:
            enviar(cid, "🗑 Tienda %s quitada." % dom)
        elif dom in AWIN_TIENDAS:
            enviar(cid, "%s viene de serie en el bot; no se puede quitar desde aquí." % dom)
        else:
            enviar(cid, "No tenía la tienda %s." % dom)
        return
    if args and args[0].lower().startswith("http"):
        res = _aw_convertir(d, " ".join(args))
        if res:
            a["n"] += len(res)
            enviar(cid, "\n\n".join("🔗 %s:\n%s" % r for r in res))
        else:
            enviar(cid, "Ese enlace no es de ninguna tienda Awin que tenga guardada. Mira /awin")
        return
    lista = "\n".join("• %s · %s (anunciante %s)" % (v[1], k, v[0]) for k, v in sorted(_aw_tiendas(d).items()))
    enviar(cid, "🔗 CONVERSOR AWIN (solo tú)\n\nTu ID de afiliado: %s\nTiendas:\n%s\n\nPega aquí un enlace de esas tiendas y te devuelvo tu enlace de afiliado.\n"
                "/awin add dominio.com 12345 Nombre · añadir tienda\n/awin quitar dominio.com · quitarla\nEnlaces convertidos: %d"
                % (AWIN_AFF, lista or "• ninguna", a["n"]))

_aw_ejecutar_orig = ejecutar
def ejecutar(d, cid, texto):
    partes = texto.strip().split()
    if str(cid) == ADMIN and partes and partes[0].split("@")[0].lower() == "/awin":
        return awin_cmd(d, cid, partes[1:])
    return _aw_ejecutar_orig(d, cid, texto)

_aw_mensaje_orig = mensaje_normal
def mensaje_normal(d, cid, m, txt):
    if str(cid) == ADMIN and not m.get("reply_to_message"):
        res = _aw_convertir(d, txt)
        if res:
            _aw_d(d)["n"] += len(res)
            enviar(cid, "\n\n".join("🔗 %s:\n%s" % r for r in res))
            return
    return _aw_mensaje_orig(d, cid, m, txt)

'''

s = open(RUTA, encoding="utf-8").read()
if "# --- PANEL ---" in s:
    print("El parche del panel ya estaba aplicado. No cambio nada.")
    sys.exit(0)

marca = 'if __name__ == "__main__":'
pos = s.rfind(marca)
if pos < 0:
    sys.exit("ERROR: no encuentro el arranque del bot. No he tocado nada.")
for nombre in ("def _err_dest", "def _cp_publicar_error", "def tablon_activo", "def _vd_enviar", "def procesar_updates", "def autorizado"):
    if nombre not in s:
        sys.exit("ERROR: no encuentro '%s' en bot.py. No he tocado nada." % nombre)

bak = RUTA + ".bak_panel_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy2(RUTA, bak)
nuevo = s[:pos] + BLOQUE + "\n" + s[pos:]
open(RUTA, "w", encoding="utf-8").write(nuevo)

r = subprocess.run([sys.executable, "-m", "py_compile", RUTA], capture_output=True, text=True)
if r.returncode != 0:
    shutil.copy2(bak, RUTA)
    sys.exit("ERROR: el bot no compila con el parche, he dejado el original.\n" + r.stderr[-800:])

print("Parche aplicado. Copia de seguridad: " + bak)
print("Ahora ejecuta: systemctl restart chivato")
print("Conversor Awin: pega en el bot un enlace de mibrofit.com o escribe /awin")
