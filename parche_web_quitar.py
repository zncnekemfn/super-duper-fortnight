import os, re, shutil, sys, time, py_compile
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
base = os.path.dirname(os.path.abspath(RUTA))
carpeta = os.path.join(base, "miniapp")
src = open(RUTA, encoding="utf-8").read()
if "# --- WEB1 ---" in src:
    nuevo, n = re.subn(r"\n# --- WEB1 ---\n.*?_MiHandler\.do_GET = _web1_get\n", "\n", src, count=1, flags=re.S)
    if n != 1 or "_web1" in nuevo:
        print("ABORTO: no pude quitar el bloque de la web, no toco nada"); sys.exit(1)
    bak = RUTA + ".bak_webquitar_" + time.strftime("%Y%m%d%H%M%S")
    shutil.copy(RUTA, bak)
    tmp = RUTA + ".wq.py"
    open(tmp, "w", encoding="utf-8").write(nuevo)
    try:
        py_compile.compile(tmp, doraise=True)
    except Exception as e:
        os.remove(tmp); print("ABORTO: no compila, no toco nada:", e); sys.exit(1)
    os.replace(tmp, RUTA)
    print("Web quitada de bot.py. Copia:", bak)
    print("Ahora reinicia: sudo systemctl restart chivato")
else:
    print("La web no estaba instalada en bot.py. Nada que quitar.")
for f in ("web.html", "app.html"):
    p = os.path.join(carpeta, f)
    if os.path.exists(p):
        os.remove(p); print("Borrado", p)
print("La mini-app vuelve a abrirse en el dominio, como antes.")
