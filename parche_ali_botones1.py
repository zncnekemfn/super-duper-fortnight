import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- ALIBOTONES1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("# --- ALIFORMATO1 ---", "# --- ALIAUTO2 ---", "def _al_cap(", "def _al_jpeg(", "def hook_menu(", "def hook_anuncios_pago("):
    if n not in src:
        print("ABORTO: falta", n, "(instala antes parche_ali_formato1.py y parche_ali_auto2.py)"); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''
# --- ALIBOTONES1 ---
# Botones 👍 TOP · 👎 FLOJA · 🔕 MENOS en las ofertas automaticas de AliExpress (usuarios y pruebas).
# Votos aparte de los de Amazon (d["fb_ali"]). MENOS = dejar de recibir ofertas de AliExpress (/aliofertas on para volver).
def _al_teclado(x):
    pid = str(x.get("id") or "x")[:40]
    return json.dumps({"inline_keyboard": [[
        {"text": "\U0001f44d TOP", "callback_data": "aly_up_" + pid},
        {"text": "\U0001f44e FLOJA", "callback_data": "aly_dn_" + pid},
        {"text": "\U0001f515 MENOS", "callback_data": "aly_no_" + pid}]]})

def _al_enviar_foto(cid, datos, cap, teclado=None):
    data = {"chat_id": cid, "caption": cap, "parse_mode": "HTML"}
    if teclado:
        data["reply_markup"] = teclado
    return requests.post("https://api.telegram.org/bot%s/sendPhoto" % _vd_token(), data=data, files={"photo": ("oferta.jpg", datos)}, timeout=60)

_al_tarjeta_sinbtn = _al_tarjeta
def _al_tarjeta(cid, x, link, extra="", botones=False):
    if not botones:
        return _al_tarjeta_sinbtn(cid, x, link, extra)
    try:
        r = _al_enviar_foto(cid, _al_jpeg(x), _al_cap(x, link, extra), _al_teclado(x))
        if r.status_code != 200:
            print("alibotones: telegram", r.status_code, r.text[:120], flush=True)
            return _al_tarjeta_sinbtn(cid, x, link, extra)
    except Exception as e:
        print("error alibotones", str(e)[:100], flush=True)
        return _al_tarjeta_sinbtn(cid, x, link, extra)

def _aa_difundir(d, x, link):
    datos = _al_jpeg(x)
    cap = _al_cap(x, link)
    tec = _al_teclado(x)
    n = 0
    for cid in list(d["users"].keys()):
        try:
            us = d["users"].get(cid) or {}
            if not autorizado(d, cid):
                continue
            if any(us.get(k) for k in ("parado", "pausa", "pausado", "off", "stop", "ali_off")):
                continue
            if _a_en_silencio(us):
                continue
            r = _al_enviar_foto(cid, datos, cap, tec)
            if r.status_code == 200:
                n += 1
            _cn_time.sleep(0.06)
        except Exception as e:
            print("error aliauto usuario", str(e)[:80], flush=True)
    return n

def _aa_publicar(d_canal, c, modo_real, destino):
    p, ln, kw = _aa_elegir(c)
    if not p:
        return False, kw
    c["vistos"].append(p["id"])
    if destino == "USUARIOS":
        n = _aa_difundir(d_canal, p, ln)
        c["n"] += 1
        c["hoy"] += 1
        return True, "%s (enviada a %d usuarios)" % (p["titulo"], n)
    extra = ""
    if not modo_real:
        extra = "🧪 PRUEBA (no publicado)\nBúsqueda: %s\nVentas: %s · Valoración: %s · Descuento AliExpress: %s%%" % (kw, p["ventas"], p["rat"], p["pct"])
    _al_tarjeta(destino, p, ln, extra, botones=not modo_real)
    if modo_real:
        c["n"] += 1
        c["hoy"] += 1
    return True, p["titulo"]

_aly_hook_menu_orig = hook_menu
def hook_menu(d, u):
    cq = u.get("callback_query")
    if cq and str(cq.get("data") or "").startswith("aly_"):
        try:
            cid = str(cq["from"]["id"])
            partes = cq["data"].split("_", 2) + ["", ""]
            acc, pid = partes[1], partes[2]
            fb = d.setdefault("fb_ali", {"up": 0, "dn": 0, "mal": {}})
            aviso = "Gracias \U0001f64f"
            if acc == "up":
                fb["up"] += 1
                aviso = "Gracias \U0001f44d"
            elif acc == "dn":
                fb["dn"] += 1
                fb["mal"][pid] = fb["mal"].get(pid, 0) + 1
                aviso = "Gracias, lo tendremos en cuenta"
                if len(fb["mal"]) > 300:
                    for k in list(fb["mal"].keys())[:-200]:
                        fb["mal"].pop(k, None)
            elif acc == "no":
                us = d["users"].get(cid)
                if us is not None:
                    us["ali_off"] = True
                aviso = "Listo: ya no recibirás ofertas de AliExpress. Para volver: /aliofertas on"
            try:
                requests.post(API + "/answerCallbackQuery", data={"callback_query_id": cq["id"], "text": aviso}, timeout=10)
                m = cq.get("message") or {}
                requests.post(API + "/editMessageReplyMarkup", data={"chat_id": cid, "message_id": m.get("message_id"),
                              "reply_markup": json.dumps({"inline_keyboard": []})}, timeout=10)
            except Exception:
                pass
        except Exception as e:
            print("error voto ali", str(e)[:100], flush=True)
        return True
    return _aly_hook_menu_orig(d, u)

_aly_hook_orig = hook_anuncios_pago
def hook_anuncios_pago(d, u):
    try:
        m = u.get("message")
        t = ((m.get("text") or "") if m else "").strip()
        if m and t:
            prim = t.split()[0]
            if prim.lower().split("@")[0] == "/aliofertas":
                cid = str(m["chat"]["id"])
                arg = (t.split() + [""])[1].lower()
                us = d["users"].get(cid)
                if us is not None and arg in ("on", "off"):
                    us["ali_off"] = (arg == "off")
                    enviar(m["chat"]["id"], "✅ Ofertas automáticas de AliExpress: %s" % ("ACTIVADAS" if arg == "on" else "DESACTIVADAS"))
                else:
                    est = "DESACTIVADAS" if (us or {}).get("ali_off") else "ACTIVADAS"
                    enviar(m["chat"]["id"], "\U0001f6d2 Ofertas automáticas de AliExpress: %s\n/aliofertas on · /aliofertas off" % est)
                return True
    except Exception as e:
        print("error hook aliofertas", str(e)[:100], flush=True)
    return _aly_hook_orig(d, u)
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_alibotones_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: botones TOP / FLOJA / MENOS en las ofertas de AliExpress.")
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato   y luego /aliauto probar")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
