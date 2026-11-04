import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- UMBRAL2 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("def pasa_filtros(", "UMBRAL_DEF = 30"):
    if n not in src:
        print("ABORTO: falta", n, "(antes: cambia UMBRAL_DEF a 30 con el sed)"); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''
# --- UMBRAL2 ---
# Los usuarios existentes tienen guardado umbral=50 (el de antes). Se pasan una sola vez al nuevo minimo (UMBRAL_DEF).
# Quien elija despues otro valor (tambien 50) lo conserva.
_u2_pasa_orig = pasa_filtros
def pasa_filtros(d, cid, u, dsc, titulo):
    try:
        if isinstance(u, dict) and not u.get("umbral_mig"):
            u["umbral_mig"] = True
            if u.get("umbral") == 50 and UMBRAL_DEF != 50:
                u["umbral"] = UMBRAL_DEF
    except Exception as e:
        print("error umbral2", str(e)[:80], flush=True)
    return _u2_pasa_orig(d, cid, u, dsc, titulo)
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: error de sintaxis", e); sys.exit(1)
cp = RUTA + ".bak_umbral2_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy2(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: los usuarios que tenian 50 pasan a", "el nuevo minimo (una sola vez).")
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato")
print("Deshacer: cp %s %s && sudo systemctl restart chivato" % (cp, RUTA))
