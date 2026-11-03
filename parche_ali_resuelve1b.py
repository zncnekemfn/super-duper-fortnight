import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- ALIRESUELVE1B ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- ALIRESUELVE1 ---" not in src:
    print("ABORTO: primero instala parche_ali_resuelve1.py"); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''
# --- ALIRESUELVE1B ---
# Si es un enlace corto de AliExpress que ya es tuyo (s.click...) y no se ha podido regenerar, se usa tal cual.
_al_enlaces_orig1b = _al_enlaces
def _al_enlaces(urls):
    out = _al_enlaces_orig1b(urls)
    for u in urls:
        if u not in out and re.match(r"https?://s\.click\.aliexpress\.com/", u):
            out[u] = u
    return out
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_aliresuelve1b_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: los enlaces s.click tuyos se aceptan tal cual si no se pueden regenerar.")
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
