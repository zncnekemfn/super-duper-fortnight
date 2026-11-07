import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- CATFIX1 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("def hook_categorias(", "def _cat_teclado(", "def _cat_texto(", "def cat_menu(", "def es_apoyante("):
    if n not in src:
        print("ABORTO: falta", n); sys.exit(1)
BLOQUE = r'''
# --- CATFIX1 ---
# Menu de categorias: si Telegram rechaza editar el mensaje, se manda un menu nuevo y se deja el motivo en el registro.
_cf_pre = hook_categorias

def hook_categorias(d, u):
    cq = u.get("callback_query")
    if not cq or not str(cq.get("data") or "").startswith("cat_"):
        return _cf_pre(d, u)
    try:
        try:
            requests.post(API + "/answerCallbackQuery", data={"callback_query_id": cq["id"]}, timeout=10)
        except Exception as e:
            print("catfix answer fallo", str(e)[:80], flush=True)
        cid = str(cq["from"]["id"])
        if not es_apoyante(d, cid):
            enviar(cid, TEXTO_CAT_APOYANTE)
            return True
        us = d["users"].setdefault(cid, nuevo_usuario())
        dato = cq["data"][4:]
        sel = list(us.get("cats") or [])
        if dato == "all":
            sel = []
        elif dato in sel:
            sel.remove(dato)
        else:
            sel.append(dato)
        us["cats"] = sel
        print("catfix click", cid, dato, "->", len(sel), "marcadas", flush=True)
        tec, _ = _cat_teclado(d, cid)
        r = requests.post(API + "/editMessageText", data={
            "chat_id": cid, "message_id": (cq.get("message") or {}).get("message_id"),
            "text": _cat_texto(d, cid), "reply_markup": tec}, timeout=15)
        if r.status_code != 200:
            print("catfix edit rechazado", r.status_code, str(r.text)[:140], flush=True)
            if "not modified" not in str(r.text):
                cat_menu(d, cid)
    except Exception as e:
        print("catfix error", str(e)[:150], flush=True)
    return True
'''
n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
nuevo = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: BLOQUE + "\n" + m.group(0), src, count=1, flags=re.M)
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: error de sintaxis", e); sys.exit(1)
copia = RUTA + ".bak_catfix1_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("OK. Reinicia: sudo systemctl restart chivato")
print("Luego pulsa un boton del menu y mira:  journalctl -u chivato --since '2 min ago' --no-pager | grep catfix")
print("Deshacer: cp %s %s && sudo systemctl restart chivato" % (copia, RUTA))
