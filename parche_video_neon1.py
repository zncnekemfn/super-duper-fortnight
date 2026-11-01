import re, sys, time, shutil
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- VIDEO_NEON ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("def _vd_enviar(", "def _ft_pie(", "def _a_teclado(", "def _vd_token("):
    if n not in src:
        print("ABORTO: no encuentro %s" % n); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: anclaje final (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''# --- VIDEO_NEON ---
import re as _vn_re
_vd_enviar_pre_neon = _vd_enviar

def _vn_valoracion(asin):
    try:
        if not KEEPA_KEY:
            return ""
        r = requests.get("https://api.keepa.com/product",
                         params={"key": KEEPA_KEY, "domain": 9, "asin": asin, "stats": 90, "history": 0, "rating": 1}, timeout=20)
        if r.status_code != 200:
            return ""
        p = (r.json().get("products") or [None])[0] or {}
        cu = (p.get("stats") or {}).get("current") or []
        rt = cu[16] if len(cu) > 16 else -1
        nv = cu[17] if len(cu) > 17 else -1
        if rt is not None and rt > 0:
            s = "\U00002b50 " + ("%.1f" % (rt / 10.0)).replace(".", ",")
            if nv is not None and nv > 0:
                s += " · " + ("{:,}".format(int(nv))).replace(",", ".") + (" valoración" if int(nv) == 1 else " valoraciones")
            return s
    except Exception as e:
        print("error valoracion video", e, flush=True)
    return ""

def _vn_caption(texto):
    lin0 = texto.split("\n")[0]
    titulo = lin0.lstrip("\U0001f525 ").strip()
    mp = _vn_re.search(r"(\d+[.,]\d\d) ?€ \(antes (\d+[.,]\d\d) ?€\) · -(\d+)%", texto)
    mu = _vn_re.search(r"https?://\S*amazon\.es/dp/([A-Z0-9]{10})\S*", texto)
    if not titulo or not mp or not mu:
        return None, None
    ahora = mp.group(1).replace(".", ",")
    antes = mp.group(2).replace(".", ",")
    pct = mp.group(3)
    url = mu.group(0)
    lineas = ["\U0001f525 -%s%%" % pct,
              "%s - %s EUR" % (titulo, ahora),
              "\U0001f4ca Media 90 días: %s EUR (%s%% menos)" % (antes, pct)]
    val = _vn_valoracion(mu.group(1))
    if val:
        lineas.append(val)
    lineas += [url,
               "(Como afiliado de Amazon obtengo ingresos por las compras adscritas.)"]
    sint = "\n".join(lineas)
    cap = _ft_pie(sint)
    if not cap or cap == sint:
        return None, None
    return cap, url

def _vd_enviar(cid, ruta, texto):
    try:
        cap, url = _vn_caption(texto)
        if not cap:
            return _vd_enviar_pre_neon(cid, ruta, texto)
        tok = _vd_token()
        if not tok:
            return _vd_enviar_pre_neon(cid, ruta, texto)
        datos = {"chat_id": cid, "caption": cap[:1024], "supports_streaming": "true",
                 "width": VD_W, "height": VD_H}
        try:
            datos["reply_markup"] = _a_teclado({"u": url})
        except Exception:
            pass
        with open(ruta, "rb") as fh:
            r = requests.post("https://api.telegram.org/bot%s/sendVideo" % tok,
                              data=datos, files={"video": fh}, timeout=120)
        if r.status_code == 200:
            return True
    except Exception as e:
        print("error video neon", e, flush=True)
    return _vd_enviar_pre_neon(cid, ruta, texto)

'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
nuevo = nuevo.replace("' valoraciones'", "(' valoraci\\u00f3n' if int(_nv) == 1 else ' valoraciones')")
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_vneon_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Video con texto neon anadido. Copia:", cp)
print("Ahora ejecuta: systemctl restart chivato")
print("Deshacer: cp", cp, RUTA, "&& systemctl restart chivato")
