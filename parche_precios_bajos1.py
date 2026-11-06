import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- PRECIOSBAJOS1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- KEEPACALIDAD2 ---" not in src:
    print("ABORTO: primero hay que tener aplicado parche_keepa_calidad2.py"); sys.exit(1)
for n in ("def _kq2_sel(", "_KQ_AHORRO_MIN"):
    if n not in src:
        print("ABORTO: falta", n); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''
# --- PRECIOSBAJOS1 ---
# Segundo perfil de ofertas: productos baratos de uso diario.
# El bot consulta Keepa en dos paginas por ciclo:
#   pagina 0 -> ofertas "premium" (como hasta ahora, ahorro minimo 10 EUR)
#   pagina 1 -> ofertas baratas: precio entre _PR_MIN y _PR_MAX, ahorro minimo _PR_AHORRO_MIN
# Mismos filtros de calidad (valoracion, resenas, ventas, descuento real frente a 90 dias).
# Para apagarlo: _PR_ACTIVO = False.
_PR_ACTIVO = True
_PR_MIN = 1000          # centimos: precio minimo del perfil barato (10 EUR)
_PR_MAX = 8000          # centimos: precio maximo (80 EUR)
_PR_AHORRO_MIN = 500    # centimos: ahorro minimo (5 EUR)
_PR_AHORRO_PREMIUM = _KQ_AHORRO_MIN
_KQ_AHORRO_MIN = min(_KQ_AHORRO_MIN, _PR_AHORRO_MIN)
_pr_sel_pre = _kq2_sel

def _pr_sel(pag):
    s = dict(_pr_sel_pre(pag))
    if not _PR_ACTIVO:
        return s
    if pag == 1:
        s["page"] = 0
        s["currentRange"] = [_PR_MIN, _PR_MAX]
        s["deltaRange"] = [_PR_AHORRO_MIN, 200000]
        s.pop("isLowest90", None)
    elif pag == 0:
        s["deltaRange"] = [_PR_AHORRO_PREMIUM, 200000]
    return s

_kq2_sel = _pr_sel
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: error de sintaxis", e); sys.exit(1)
cp = RUTA + ".bak_preciosbajos1_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy2(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: ahora tambien llegan ofertas baratas (de 10 a 80 EUR).")
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato")
print("Deshacer: cp %s %s && sudo systemctl restart chivato" % (cp, RUTA))
