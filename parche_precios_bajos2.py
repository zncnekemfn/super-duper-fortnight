import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- PRECIOSBAJOS2 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- PRECIOSBAJOS1 ---" not in src:
    print("ABORTO: primero hay que tener aplicado parche_precios_bajos1.py"); sys.exit(1)
for n in ("def _pr_sel(", "_kp_orig", "_KP_PAG"):
    if n not in src:
        print("ABORTO: falta", n); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''
# --- PRECIOSBAJOS2 ---
# La consulta de ofertas baratas devolvia siempre las mismas 150 (ya avisadas), asi que no salian nuevas.
# Ahora cada ciclo mira un "hueco" distinto de Keepa, rotando entre dos ordenes y tres paginas:
#   orden 2 = mayor ahorro en euros, orden 4 = mayor porcentaje; paginas 0, 1 y 2 (150 ofertas cada una).
# Cuesta lo mismo en tokens (una consulta por ciclo). Se puede cambiar _PR2_COMBOS.
_PR2_COMBOS = [(2, 0), (4, 0), (2, 1), (4, 1), (2, 2), (4, 2)]
_PR2_IDX = [0]
_pr2_sel_pre = _kq2_sel

def _pr2_sel(pag):
    s = dict(_pr2_sel_pre(pag))
    if _PR_ACTIVO and pag == 1:
        orden, pagina = _PR2_COMBOS[_PR2_IDX[0] % len(_PR2_COMBOS)]
        s["sortType"] = orden
        s["page"] = pagina
    return s

_kq2_sel = _pr2_sel
_pr2_base = _kp_orig

def _pr2_revisar(d):
    try:
        return _pr2_base(d)
    finally:
        if _KP_PAG == 1:
            _PR2_IDX[0] += 1

_kp_orig = _pr2_revisar
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: error de sintaxis", e); sys.exit(1)
cp = RUTA + ".bak_preciosbajos2_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy2(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: las ofertas baratas ahora rotan entre varios huecos de Keepa.")
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato")
print("Deshacer: cp %s %s && sudo systemctl restart chivato" % (cp, RUTA))
