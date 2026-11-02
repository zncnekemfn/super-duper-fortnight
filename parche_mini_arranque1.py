import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- MINIARRANQUE1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("def _mi_arrancar(", "def revisar_keepa(", "_mi = "):
    if n not in src:
        print("ABORTO: no encuentro", n); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)

BLOQUE = r'''
# --- MINIARRANQUE1 ---
# La mini-app se levanta al iniciar el bot (antes esperaba al primer mensaje o aviso)
try:
    _mi_arrancar()
except Exception as _e_ma:
    print("miniarranque:", _e_ma, flush=True)

_rk_pre_ma = revisar_keepa

def revisar_keepa(d, *a, **k):
    try:
        if _mi.get("d") is None:
            _mi["d"] = d
        _mi_arrancar()
    except Exception:
        pass
    return _rk_pre_ma(d, *a, **k)
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_miniarranque_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado. Copia:", cp)
print("Reinicia: sudo systemctl restart chivato")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
