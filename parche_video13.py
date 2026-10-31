import shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "def _vd11_rr(" not in src:
    print("ABORTO: falta aplicar antes parche_video12.py"); sys.exit(1)
if "(int(min(x1 - x0, y1 - y0)) - 3) // 2" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
viejo = "r = max(0, min(r, int((min(x1 - x0, y1 - y0)) / 2)))"
if src.count(viejo) != 1:
    print("ABORTO: no encuentro la linea a corregir"); sys.exit(1)
nuevo = src.replace(viejo, "r = max(0, min(r, (int(min(x1 - x0, y1 - y0)) - 3) // 2))")
try:
    compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)
copia = RUTA + ".bak_video13_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
