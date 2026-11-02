import sys, time, shutil
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
a = 'bool(shutil.which("ffmpeg"))'
if "# --- FOTOPROD3 ---" not in src:
    print("ABORTO: falta FOTOPROD3"); sys.exit(1)
if src.count(a) != 1:
    print("Nada que corregir (ya estaba)."); sys.exit(0)
nuevo = src.replace(a, 'bool(__import__("shutil").which("ffmpeg"))')
compile(nuevo, "bot.py", "exec")
cp = RUTA + ".bak_fotoprod3b_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Corregido. Copia:", cp)
print("Reinicia: sudo systemctl restart chivato   y escribe /autotest")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
