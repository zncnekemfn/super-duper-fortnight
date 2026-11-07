import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- CATFIX2 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- CATFIX1 ---" not in src:
    print("ABORTO: aplica antes parche_cat_fix1.py"); sys.exit(1)
viejo = '''        if r.status_code != 200:
            print("catfix edit rechazado", r.status_code, str(r.text)[:140], flush=True)
            if "not modified" not in str(r.text):
                cat_menu(d, cid)
'''
nuevo = '''        if r.status_code != 200:  # --- CATFIX2 ---
            print("catfix edit rechazado", r.status_code, str(r.text)[:140], flush=True)
            if "no text in the message" in str(r.text):
                # el menu es un mensaje con foto: se edita el pie (caption), no el texto
                r2 = requests.post(API + "/editMessageCaption", data={
                    "chat_id": cid, "message_id": (cq.get("message") or {}).get("message_id"),
                    "caption": _cat_texto(d, cid)[:1024], "reply_markup": tec}, timeout=15)
                if r2.status_code != 200:
                    print("catfix caption rechazado", r2.status_code, str(r2.text)[:140], flush=True)
                    r3 = requests.post(API + "/editMessageReplyMarkup", data={
                        "chat_id": cid, "message_id": (cq.get("message") or {}).get("message_id"),
                        "reply_markup": tec}, timeout=15)
                    if r3.status_code != 200 and "not modified" not in str(r3.text):
                        print("catfix markup rechazado", r3.status_code, str(r3.text)[:140], flush=True)
                        cat_menu(d, cid)
            elif "not modified" not in str(r.text):
                cat_menu(d, cid)
'''
if src.count(viejo) != 1:
    print("ABORTO: no encuentro el punto exacto (%d)" % src.count(viejo)); sys.exit(1)
out = src.replace(viejo, nuevo)
try: compile(out, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: error de sintaxis", e); sys.exit(1)
copia = RUTA + ".bak_catfix2_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(out)
print("OK. Reinicia: sudo systemctl restart chivato")
print("Deshacer: cp %s %s && sudo systemctl restart chivato" % (copia, RUTA))
