import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()

if "# --- TODO GRATIS 2 ---" in src:
    print("Ya estaba aplicado. No hago nada.")
    sys.exit(0)

def unico(patron, fn, nombre):
    global src
    n = len(re.findall(patron, src, re.M))
    if n != 1:
        print("ABORTO: ancla '%s' encontrada %d veces" % (nombre, n))
        sys.exit(1)
    src = re.sub(patron, fn, src, count=1, flags=re.M)

unico(r'ap = sum\(1 for k in d\["users"\] if es_apoyante\(d, k\) and k != ADMIN\)',
      lambda m: 'ap = sum(1 for k in d["users"] if _es_apoyante_real(d, k) and k != ADMIN)', "usuarios")
unico(r'if es_apoyante\(d, cid\) else ""',
      lambda m: 'if _es_apoyante_real(d, cid) else ""', "marca")
unico(r'if es_apoyante\(d, uid\):',
      lambda m: 'if _es_apoyante_real(d, uid):', "solo apoyantes")
unico(r'\(publicidad de apoyantes\)',
      lambda m: '(publicidad)', "titulo tablon")

src = src.rstrip("\n") + "\n\n# --- TODO GRATIS 2 ---\n"
try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)

copia = RUTA + ".bak_gratis2_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
