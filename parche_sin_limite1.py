import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
COND = 'if u.get("n", 0) >= MAX_AVISOS_GRATIS:'
if "# SIN LIMITE DE AVISOS" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if src.count(COND) != 1:
    print("ABORTO: no encuentro la condicion del limite exactamente una vez (%d)." % src.count(COND)); sys.exit(1)
nuevo = src.replace(COND, "if False:  # SIN LIMITE DE AVISOS (antes: " + COND[3:-1] + ")")
txt = ", máx. {MAX_AVISOS_GRATIS} al día"
quitado = nuevo.count(txt)
nuevo = nuevo.replace(txt, "")
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: error de sintaxis", e); sys.exit(1)
cp = RUTA + ".bak_sinlimite_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy2(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: ya no hay limite diario de avisos por usuario.")
print("Texto del plan actualizado: %d" % quitado)
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato")
print("Deshacer: cp %s %s && sudo systemctl restart chivato" % (cp, RUTA))
