import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "Plan: todo incluido" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
pat = re.compile(r'f?"Plan: Gratis\\n[^"\n]*"')
n = len(pat.findall(src))
if n != 1:
    print("ABORTO: encontre el texto del plan %d veces (esperaba 1)." % n); sys.exit(1)
nuevo = pat.sub(lambda m: '"Plan: todo incluido\\nTodas las ofertas, al instante y sin l\\u00edmites.\\nDescuento m\\u00ednimo: ~-%d%%" % UMBRAL_DEF', src, count=1)
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: error de sintaxis", e); sys.exit(1)
cp = RUTA + ".bak_plantexto_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy2(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: el mensaje de plan ya no habla de gratis, retraso ni limites.")
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato")
print("Deshacer: cp %s %s && sudo systemctl restart chivato" % (cp, RUTA))
