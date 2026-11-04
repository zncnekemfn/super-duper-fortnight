import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- TIENDAS1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("def enviar_aviso(", "def hook_anuncios_pago(", "def nuevo_usuario(", "# --- ALIBOTONES1 ---"):
    if n not in src:
        print("ABORTO: falta", n, "(instala antes parche_ali_botones1.py)"); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''
# --- TIENDAS1 ---
# /tiendas: cada usuario elige de que tiendas quiere avisos (Amazon, AliExpress).
# Amazon: se filtra en enviar_aviso. AliExpress: marca ali_off (ya la respeta el envio automatico).
def _ti_teclado(us):
    am = not (us or {}).get("amazon_off")
    al = not (us or {}).get("ali_off")
    return json.dumps({"inline_keyboard": [[
        {"text": ("✅ " if am else "⬜ ") + "Amazon", "callback_data": "tnd_am"},
        {"text": ("✅ " if al else "⬜ ") + "AliExpress", "callback_data": "tnd_al"}]]})

def _ti_texto(us):
    am = not (us or {}).get("amazon_off")
    al = not (us or {}).get("ali_off")
    t = "\U0001f3ec TIENDAS\n\nElige de qué tiendas quieres recibir avisos de ofertas y bajadas de precio. Toca para activar o desactivar.\n\nAhora: %s" % (
        " y ".join([n for n, v in (("Amazon", am), ("AliExpress", al)) if v]) or "ninguna")
    if not am and not al:
        t += "\n\n⚠ Con las dos desactivadas no recibirás avisos de ofertas."
    return t

_ti_aviso_orig = enviar_aviso
def enviar_aviso(d, cid, item):
    try:
        us = (d.get("users") or {}).get(cid) or (d.get("users") or {}).get(str(cid)) or {}
        if us.get("amazon_off"):
            return
    except Exception as e:
        print("error tiendas", str(e)[:80], flush=True)
    return _ti_aviso_orig(d, cid, item)

_ti_hook_orig = hook_anuncios_pago
def hook_anuncios_pago(d, u):
    try:
        cq = u.get("callback_query")
        if cq and str(cq.get("data") or "").startswith("tnd_"):
            cid = str(cq["from"]["id"])
            try:
                requests.post(API + "/answerCallbackQuery", data={"callback_query_id": cq["id"]}, timeout=10)
            except Exception:
                pass
            us = d["users"].setdefault(cid, nuevo_usuario())
            k = cq["data"][4:]
            if k == "am":
                us["amazon_off"] = not us.get("amazon_off")
            elif k == "al":
                us["ali_off"] = not us.get("ali_off")
            requests.post(API + "/editMessageText", data={"chat_id": cid,
                "message_id": (cq.get("message") or {}).get("message_id"),
                "text": _ti_texto(us), "reply_markup": _ti_teclado(us)}, timeout=15)
            return True
        m = u.get("message")
        t = ((m.get("text") or "") if m else "").strip()
        if m and t and t.split()[0].lower().split("@")[0] == "/tiendas":
            cid = str(m["chat"]["id"])
            us = d["users"].setdefault(cid, nuevo_usuario())
            enviar(m["chat"]["id"], _ti_texto(us), _ti_teclado(us))
            return True
    except Exception as e:
        print("error hook tiendas", str(e)[:100], flush=True)
    return _ti_hook_orig(d, u)
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_tiendas_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: /tiendas (Amazon / AliExpress).")
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato   y luego /autotest")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
