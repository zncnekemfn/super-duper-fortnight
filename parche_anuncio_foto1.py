import os, re, shutil, time, py_compile
RUTA = "/opt/chivato/bot.py"
MARCA = "# --- ANUNCIOFOTO1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado"); raise SystemExit
BLOQUE = '''
# --- ANUNCIOFOTO1 ---
import re as _af_re
_af_hook_orig = hook_anuncios_pago

def _af_parsear(cap):
    cap = _af_re.sub(r"^/anuncio(@\\w+)?\\s*", "", cap.strip())
    ad = parsear_anuncio(cap)
    if ad:
        return ad
    m = _af_re.search(r"https?://\\S+", cap)
    if not m:
        return None
    enlace = m.group(0).strip("|").strip()
    t = cap[:m.start()].strip().rstrip("|").strip()
    resto = cap[m.end():].strip().lstrip("|").strip()
    if not t:
        return None
    return {"texto": t[:700], "enlace": enlace, "boton": (resto or "\\U0001F449 Ver oferta")[:30]}

def hook_anuncios_pago(d, u):
    try:
        m = u.get("message")
        cap = (m.get("caption") or "") if m else ""
        if m and m.get("photo") and cap.strip().lower().startswith("/anuncio"):
            cid = m["chat"]["id"]
            if str(cid) == str(ADMIN):
                ad = _af_parsear(cap)
                if not ad:
                    requests.post(API + "/sendMessage", data=prot({"chat_id": cid,
                        "text": "No entiendo el pie de foto. Formato: /anuncio texto | https://enlace | texto del boton"}, cid), timeout=30)
                    return True
                aid = nuevo_id_anuncio(d)
                ad.update({"foto": m["photo"][-1]["file_id"], "autor": ADMIN,
                           "tipo": "admin", "estado": "borrador", "env": 0, "ts": time.time()})
                d["anuncios"][aid] = ad
                _enviar_anuncio_orig(d, cid, ad, aid, "\\U0001F441 Vista previa")
                requests.post(API + "/sendMessage", data=prot({"chat_id": cid,
                    "text": "Asi se vera con foto. Que hago?", "reply_markup": teclado_difusion(aid)}, cid), timeout=30)
                print("anuncio con foto creado", aid)
                return True
    except Exception as e:
        print("error anuncio foto", e)
    return _af_hook_orig(d, u)
'''
fin = 'if __name__ == "__main__":'
if src.count(fin) != 1:
    print("No encuentro el sitio donde insertar (", src.count(fin), ")"); raise SystemExit
bak = RUTA + ".bak_af_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, bak)
nuevo = src.replace(fin, BLOQUE + "\n" + fin)
open(RUTA, "w", encoding="utf-8").write(nuevo)
try:
    py_compile.compile(RUTA, doraise=True)
except Exception as e:
    shutil.copy(bak, RUTA); print("Error, restaurado:", e); raise SystemExit
print("Listo. Ahora: systemctl restart chivato")
