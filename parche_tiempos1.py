import shutil, time, py_compile
RUTA = "/opt/chivato/bot.py"
MARCA = "# --- TIEMPOS1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado"); raise SystemExit
BLOQUE = '''
# --- TIEMPOS1 ---
def _t1_medir(nombre):
    f = globals()[nombre]
    def w(*a, **k):
        t0 = time.time()
        try:
            return f(*a, **k)
        finally:
            dt = time.time() - t0
            if dt > 3:
                print("TIEMPO %s %.0fs" % (nombre, dt), flush=True)
    globals()[nombre] = w

for _n in ("revisar_feed", "enviar_pendientes", "procesar_updates", "guardar"):
    try:
        _t1_medir(_n)
    except Exception as _e:
        print("tiempos: no pude medir", _n, _e, flush=True)
'''
fin = 'if __name__ == "__main__":'
if src.count(fin) != 1:
    print("No encuentro el sitio (", src.count(fin), ")"); raise SystemExit
bak = RUTA + ".bak_t1_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, bak)
open(RUTA, "w", encoding="utf-8").write(src.replace(fin, BLOQUE + "\n" + fin))
try:
    py_compile.compile(RUTA, doraise=True)
except Exception as e:
    shutil.copy(bak, RUTA); print("Error, restaurado:", e); raise SystemExit
print("Listo. Ahora: systemctl restart chivato")
