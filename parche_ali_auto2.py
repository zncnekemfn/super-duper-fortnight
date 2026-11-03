import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- ALIAUTO2 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("# --- ALIAUTO1 ---", "# --- ALIENLACE1 ---", "def _aa_tarea(", "def _aa_estado(", "def _a_en_silencio(", "def autorizado("):
    if n not in src:
        print("ABORTO: falta", n, "(instala antes parche_ali_auto1, parche_ali_enlace1 y 1b)"); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''
# --- ALIAUTO2 ---
# Modo "usuarios": las ofertas de AliExpress se envian solo a los usuarios del bot (no al canal).
# /aliauto modo usuarios
def _aa_difundir(d, x, link):
    import html as _h
    dat = {"titulo": x["titulo"], "ahora": x["ahora"] or 0.0, "antes": x["antes"] or (x["ahora"] or 0.0), "pct": x["pct"] or 0,
           "foto": _al_foto(x["img"]), "hora": _cn_time.strftime("AVISO %H:%M · %d/%m/%Y"), "rat": "", "nv": "",
           "pie1": "Enlace de afiliado. Los precios pueden cambiar."}
    img = _cn_frame(dat, 0.0, 6.0, True)
    buf = _cn_io.BytesIO()
    img.save(buf, "JPEG", quality=92)
    datos = buf.getvalue()
    cap = "\U0001f6d2 %s\n" % _h.escape(str(x["titulo"])[:150])
    if x["ahora"]:
        cap += "\U0001f4a5 %s%s€" % ("-%d%% → " % x["pct"] if x["pct"] else "", ("%.2f" % x["ahora"]).replace(".", ","))
        if x["antes"] and x["antes"] > x["ahora"]:
            cap += " (antes %s €)" % ("%.2f" % x["antes"]).replace(".", ",")
        cap += "\n"
    cap += '\U0001f449 <a href="%s">Ver oferta en AliExpress</a>\n(Enlace de afiliado.)' % _h.escape(link, quote=True)
    n = 0
    for cid in list(d["users"].keys()):
        try:
            us = d["users"].get(cid) or {}
            if not autorizado(d, cid):
                continue
            if any(us.get(k) for k in ("parado", "pausa", "pausado", "off", "stop")):
                continue
            if _a_en_silencio(us):
                continue
            r = requests.post("https://api.telegram.org/bot%s/sendPhoto" % _vd_token(),
                              data={"chat_id": cid, "caption": cap, "parse_mode": "HTML"}, files={"photo": ("oferta.jpg", datos)}, timeout=60)
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
    _al_tarjeta(destino, p, ln, extra)
    if modo_real:
        c["n"] += 1
        c["hoy"] += 1
    return True, p["titulo"]

def _aa_hilo(destino, real, d=None):
    try:
        with _aa_lock:
            c = _aa_cargar()
            ok, info = _aa_publicar(d, c, real, destino)
            _aa_guardar(c)
            print("aliauto", ok, str(info)[:80], flush=True)
    except Exception as e:
        print("error hilo aliauto", str(e)[:100], flush=True)

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
        if c["modo"] == "usuarios":
            destino, real = "USUARIOS", True
        elif c["modo"] == "canal":
            destino = (_cp_d(d) or {}).get("id")
            if not destino:
                return
            real = True
        else:
            destino, real = ADMIN, False
        c["ult"] = ahora
        _aa_guardar(c)
        _vd_th.Thread(target=_aa_hilo, args=(destino, real, d), daemon=True).start()
    except Exception as e:
        print("error tarea aliauto", str(e)[:100], flush=True)
    finally:
        _aa_lock.release()

_aa_estado_orig2 = _aa_estado
def _aa_estado(c):
    t = _aa_estado_orig2(c)
    if c.get("modo") == "usuarios":
        t = t.replace("PRUEBA (solo te llega a ti)", "ENVÍA A LOS USUARIOS DEL BOT")
    return t.replace("/aliauto modo prueba|canal", "/aliauto modo prueba|usuarios|canal")

_aa_admin_orig2 = _aa_admin
def _aa_admin(d, cid, args):
    if len(args) > 1 and args[0].lower() == "modo" and args[1].lower() == "usuarios":
        c = _aa_cargar()
        c["modo"] = "usuarios"
        _aa_guardar(c)
        enviar(cid, _aa_estado(c))
        return
    return _aa_admin_orig2(d, cid, args)
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_aliauto2_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: /aliauto modo usuarios")
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
