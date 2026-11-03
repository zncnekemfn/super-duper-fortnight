import shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
v = '"caption": cap[:1000], "parse_mode": "HTML"'
n = '"caption": cap, "parse_mode": "HTML"'
if "# --- ALIENLACE1 ---" not in src:
    print("ABORTO: primero instala parche_ali_enlace1.py"); sys.exit(1)
if v not in src:
    print("Ya estaba corregido (o no hace falta). No hago nada."); sys.exit(0)
nuevo = src.replace(v, n)
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_alienlace1b_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Corregido: el texto ya no se corta a la mitad del enlace.")
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato   y luego /aliauto probar")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
