import re, shutil, time, py_compile
RUTA = "/opt/chivato/bot.py"
MARCA = "# --- KEEPAPAG2 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado"); raise SystemExit
BUSCA = '"page": 0, "domainId": 9, "priceTypes": [0],'
NUEVO = '"page": _KP_PAG, "domainId": 9, "priceTypes": [0],'
partes = [m.start() for m in re.finditer(r"^def revisar_keepa\(d\):", src, re.M)]
if not partes:
    print("No encuentro revisar_keepa, no toco nada"); raise SystemExit
cambios = 0
for ini in reversed(partes):
    fin = src.find("\ndef ", ini + 5)
    if fin == -1: fin = len(src)
    cuerpo = src[ini:fin]
    if cuerpo.count(BUSCA) == 1:
        src = src[:ini] + cuerpo.replace(BUSCA, NUEVO) + src[fin:]
        cambios += 1
if cambios == 0:
    print("No encuentro la consulta de Keepa que esperaba, no toco nada"); raise SystemExit
BLOQUE = '''
# --- KEEPAPAG2 ---
_KP_PAG = 0
_kp_orig = revisar_keepa

def revisar_keepa(d):
    global _KP_PAG
    total = 0
    for _pg in (0, 1):
        _KP_PAG = _pg
        try:
            total += _kp_orig(d) or 0
        except Exception as e:
            print("error keepa pag", _pg, e, flush=True)
        finally:
            _KP_PAG = 0
    if total:
        print("keepa 2 paginas, nuevos:", total, flush=True)
    return total
'''
fin_ = 'if __name__ == "__main__":'
if src.count(fin_) != 1:
    print("No encuentro el sitio donde insertar, no toco nada"); raise SystemExit
bak = RUTA + ".bak_kp_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, bak)
open(RUTA, "w", encoding="utf-8").write(src.replace(fin_, BLOQUE + "\n" + fin_))
try:
    py_compile.compile(RUTA, doraise=True)
except Exception as e:
    shutil.copy(bak, RUTA); print("Error, restaurado:", e); raise SystemExit
print("Listo (%d funcion/es). Ahora: systemctl restart chivato" % cambios)
