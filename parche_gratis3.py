import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()

if "# --- TODO GRATIS 3 ---" in src:
    print("Ya estaba aplicado. No hago nada.")
    sys.exit(0)

def unico(patron, fn, nombre):
    global src
    n = len(re.findall(patron, src, re.M))
    if n != 1:
        print("ABORTO: ancla '%s' encontrada %d veces" % (nombre, n))
        sys.exit(1)
    src = re.sub(patron, fn, src, count=1, flags=re.M)

unico(r'"[^"\n]*APOYANTES \(propina desde 500 Stars\):\\n"',
      lambda m: '"\\U0001f193 INCLUIDO PARA TODOS:\\n"', "titulo apoyantes")
unico(r'Más chollos en /ultimas y chat sin l.mite\\n',
      lambda m: 'M\\u00e1s chollos en /ultimas\\n', "chat sin limite")

src = src.rstrip("\n") + "\n\n# --- TODO GRATIS 3 ---\n"
try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)

copia = RUTA + ".bak_gratis3_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
