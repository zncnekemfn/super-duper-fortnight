import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- MEMFOTOS1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("def _fp_img_ok(", "def _cn_foto(", "_cn_fotos = {}"):
    if n not in src:
        print("ABORTO: falta", n); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''
# --- MEMFOTOS1 ---
# Memoria: las fotos de producto llegan enormes (1748x2480) y se guardaban 60 a tamano completo (~13 MB cada una).
# Ahora se reducen a 900 px y la cache guarda como maximo 20.
_mf_img_ok_orig = _fp_img_ok
def _fp_img_ok(u):
    im = _mf_img_ok_orig(u)
    if im is not None:
        try:
            im.thumbnail((900, 900))
        except Exception as e:
            print("error reducir foto", str(e)[:60], flush=True)
    return im

_mf_foto_orig = _cn_foto
def _cn_foto(asin):
    r = _mf_foto_orig(asin)
    try:
        while len(_cn_fotos) > 20:
            _cn_fotos.pop(next(iter(_cn_fotos)))
    except Exception:
        _cn_fotos.clear()
    return r
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_memfotos_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: fotos reducidas a 900 px y cache de 20 (menos memoria).")
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato   y luego /autotest")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
