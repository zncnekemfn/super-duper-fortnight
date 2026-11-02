import re, sys, time, shutil
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
pat = re.compile(r'(["\'])\(Como afiliado de Amazon obtengo ingresos por las compras adscritas\.\)\1')
n = len(pat.findall(src))
if n == 0:
    print("Nada que quitar (ya estaba quitada o no hay textos con esa frase)."); sys.exit(0)
nuevo = pat.sub('""', src)
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_quitarfrase_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Frase quitada del texto de los mensajes en %d sitios. La linea pequena de la imagen no se toca." % n)
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato   y luego /autotest")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
