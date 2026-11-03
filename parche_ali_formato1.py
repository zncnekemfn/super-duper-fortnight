import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- ALIFORMATO1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("# --- ALIENLACE1 ---", "_al_tarjeta_orig", "def _cn_frame(", "def _al_foto("):
    if n not in src:
        print("ABORTO: falta", n); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)
HAY_DIF = "def _aa_difundir(" in src
BLOQUE = r'''
# --- ALIFORMATO1 ---
# Mismo formato de aviso que Amazon (gancho, barra de ahorro, separadores) para las ofertas de AliExpress.
def _al_eur(v):
    return ("%.2f" % float(v)).replace(".", ",") + " €"

def _al_cap(x, link, extra=""):
    import html as _h
    pct = int(x["pct"] or 0)
    gancho = "PRECIAZO" if pct >= 60 else ("CHOLLO DETECTADO" if pct >= 35 else "BAJADA DE PRECIO")
    n = max(1, min(10, int(round(pct / 10.0))))
    barra = "▰" * n + "▱" * (10 - n)
    sep = "━" * 16
    o = ["⚡ %s ⚡" % gancho, sep, "\U0001f6d2 " + _h.escape(str(x["titulo"])[:140]),
         "\U0001f4a5 -%d%%  ➜  %s" % (pct, _al_eur(x["ahora"]))]
    if x["antes"] and x["antes"] > x["ahora"]:
        o.append("%s ahorras %s" % (barra, _al_eur(x["antes"] - x["ahora"])))
    o.append(sep)
    if x["antes"] and x["antes"] > x["ahora"]:
        o.append("\U0001f4ca Precio anterior en AliExpress: %s" % _al_eur(x["antes"]))
    r, v = _al_num(x.get("rat")), _al_num(x.get("ventas"))
    if r is not None or v is not None:
        o.append("⭐ " + " · ".join(([("%s %% de valoraciones positivas" % ("%g" % r).replace(".", ","))] if r is not None else [])
                                    + ([("%d vendidos" % v)] if v is not None else [])))
    o.append('\U0001f449 <a href="%s">Ver oferta en AliExpress</a>' % _h.escape(link, quote=True))
    o.append("(Enlace de afiliado. El precio anterior es el que indica AliExpress.)")
    if extra:
        o.append("")
        o.append(_h.escape(extra[:400]))
    return "\n".join(o)

def _al_jpeg(x):
    dat = {"titulo": x["titulo"], "ahora": x["ahora"] or 0.0, "antes": x["antes"] or (x["ahora"] or 0.0), "pct": x["pct"] or 0,
           "foto": _al_foto(x["img"]), "hora": _cn_time.strftime("AVISO %H:%M · %d/%m/%Y"), "rat": "", "nv": "",
           "pie1": "Enlace de afiliado. Los precios pueden cambiar."}
    buf = _cn_io.BytesIO()
    _cn_frame(dat, 0.0, 6.0, True).save(buf, "JPEG", quality=92)
    return buf.getvalue()

def _al_tarjeta(cid, x, link, extra=""):
    try:
        cap = _al_cap(x, link, extra)
        r = requests.post("https://api.telegram.org/bot%s/sendPhoto" % _vd_token(),
                          data={"chat_id": cid, "caption": cap, "parse_mode": "HTML"}, files={"photo": ("oferta.jpg", _al_jpeg(x))}, timeout=60)
        if r.status_code != 200:
            print("aliformato: telegram", r.status_code, r.text[:120], flush=True)
            return _al_tarjeta_orig(cid, x, link, extra)
    except Exception as e:
        print("error aliformato", str(e)[:100], flush=True)
        return _al_tarjeta_orig(cid, x, link, extra)
'''
DIF = r'''
def _aa_difundir(d, x, link):
    datos = _al_jpeg(x)
    cap = _al_cap(x, link)
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
'''
if HAY_DIF:
    BLOQUE += DIF
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_aliformato_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: ofertas de AliExpress con el formato de las de Amazon" + (" (incluye envío a usuarios)." if HAY_DIF else "."))
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato   y luego /aliauto probar")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
