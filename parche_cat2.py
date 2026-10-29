import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()

if "# --- CATEGORIAS ---" not in src:
    print("ABORTO: primero hay que aplicar parche_categorias.py"); sys.exit(1)
if "# cat2" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)

ANCLA = '    ids = sorted(vistas, key=lambda c: -vistas[c])[:14]\n'
if src.count(ANCLA) != 1:
    print("ABORTO: ancla no encontrada"); sys.exit(1)
NUEVO = ('    ids = sorted([c for c in vistas if (d.get("cat_nombres") or {}).get(c, "?") != "?"],'
         ' key=lambda c: -vistas[c])[:20]  # cat2\n')
src = src.replace(ANCLA, NUEVO, 1)

try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
copia = RUTA + ".bak_cat2_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")

