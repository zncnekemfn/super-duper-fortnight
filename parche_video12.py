import shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- VIDEO11 ---" not in src:
    print("ABORTO: falta aplicar antes parche_video11.py"); sys.exit(1)
if "def _vd11_rr(" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)

HELPER = '''def _vd11_rr(d, box, r=0, **kw):
    x0, y0, x1, y1 = box
    r = max(0, min(r, int((min(x1 - x0, y1 - y0)) / 2)))
    d.rounded_rectangle(box, r, **kw)

'''
i = src.index("# --- VIDEO11 ---")
j = src.index("_vd11_estado = {", i)
bloque = src[i:j]
if "def _vd11_render(" not in bloque:
    print("ABORTO: no encuentro la funcion del video neon"); sys.exit(1)
bloque = bloque.replace("dr.rounded_rectangle(", "_vd11_rr(dr, ").replace("g.rounded_rectangle(", "_vd11_rr(g, ")
bloque = bloque.replace("def _vd11_render(", HELPER + "def _vd11_render(", 1)
nuevo = src[:i] + bloque + src[j:]
try:
    compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)
copia = RUTA + ".bak_video12_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
