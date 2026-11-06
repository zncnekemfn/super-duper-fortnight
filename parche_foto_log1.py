import re, shutil, time, sys
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- FOTOLOG1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
viejo = 'print("foto aviso rechazada", r.status_code, flush=True)'
n = src.count(viejo)
if n < 1:
    print("ABORTO: no encuentro el mensaje 'foto aviso rechazada'"); sys.exit(1)
nuevo_txt = 'print("foto aviso rechazada", r.status_code, str(r.text)[:110].replace("\\n", " "), "chat", str(dat.get("chat_id") if "dat" in dir() else ""), flush=True)'
# version segura: usar solo r.status_code y r.text (siempre existen en ese punto)
nuevo_txt = 'print("foto aviso rechazada", r.status_code, str(r.text)[:110].replace("\\n", " "), flush=True)  ' + MARCA
nuevo = src.replace(viejo, nuevo_txt)
try:
    compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: error de sintaxis", e); sys.exit(1)
copia = RUTA + ".bak_fotolog1_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado en %d sitio(s): el registro ahora dice POR QUE Telegram rechaza la foto." % n)
print("Copia:", copia)
print("Reinicia: sudo systemctl restart chivato")
print("Deshacer: cp %s %s && sudo systemctl restart chivato" % (copia, RUTA))
