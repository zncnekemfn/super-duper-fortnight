import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- ALIENLACE1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("# --- ALI1 ---", "def _al_tarjeta(", "def _pl_enviar("):
    if n not in src:
        print("ABORTO: falta", n); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''
# --- ALIENLACE1 ---
# El enlace de afiliado de AliExpress va escondido tras el texto "Ver oferta" (no se ve la URL larga).
_al_tarjeta_orig = _al_tarjeta
def _al_tarjeta(cid, x, link, extra=""):
    try:
        import html as _h
        dat = {"titulo": x["titulo"], "ahora": x["ahora"] or 0.0, "antes": x["antes"] or (x["ahora"] or 0.0), "pct": x["pct"] or 0,
               "foto": _al_foto(x["img"]), "hora": _cn_time.strftime("AVISO %H:%M · %d/%m/%Y"), "rat": "", "nv": "",
               "pie1": "Enlace de afiliado. Los precios pueden cambiar."}
        img = _cn_frame(dat, 0.0, 6.0, True)
        cap = "\U0001f6d2 %s\n" % _h.escape(str(x["titulo"])[:150])
        if x["ahora"]:
            cap += "\U0001f4a5 %s%s€" % ("-%d%% → " % x["pct"] if x["pct"] else "", ("%.2f" % x["ahora"]).replace(".", ","))
            if x["antes"] and x["antes"] > x["ahora"]:
                cap += " (antes %s €)" % ("%.2f" % x["antes"]).replace(".", ",")
            cap += "\n"
        cap += '\U0001f449 <a href="%s">Ver oferta en AliExpress</a>\n(Enlace de afiliado.)' % _h.escape(link, quote=True)
        if extra:
            cap += "\n\n" + _h.escape(extra[:500])
        ruta = _ft_os.path.join(_ft_tmp.gettempdir(), "alienlace_%d.jpg" % int(_cn_time.time() * 1000))
        try:
            img.save(ruta, "JPEG", quality=92)
            with open(ruta, "rb") as fh:
                r = requests.post("https://api.telegram.org/bot%s/sendPhoto" % _vd_token(),
                                  data={"chat_id": cid, "caption": cap, "parse_mode": "HTML"}, files={"photo": fh}, timeout=60)
            if r.status_code != 200:
                print("alienlace: telegram", r.status_code, r.text[:120], flush=True)
                return _al_tarjeta_orig(cid, x, link, extra)
        finally:
            try: _ft_os.remove(ruta)
            except Exception: pass
    except Exception as e:
        print("error alienlace", str(e)[:100], flush=True)
        return _al_tarjeta_orig(cid, x, link, extra)
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_alienlace_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: enlace de AliExpress como 'Ver oferta en AliExpress'.")
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato   y luego /aliauto probar")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
