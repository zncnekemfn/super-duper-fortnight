import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- ADIVINA1B ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("# --- ADIVINA1 ---", "def _ad_candidatas(", "# --- FILTROIDIOMA1 ---", "def _fi_es_libro(", "def _fi_otro_idioma("):
    if n not in src:
        print("ABORTO: falta", n); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''
# --- ADIVINA1B ---
# El juego no usa libros ni titulos en otro idioma.
def _ad_candidatas(d, j):
    lim = time.time() - 14 * 86400
    of = []
    for o in (_mi_d(d).get("of") or []):
        if o.get("ts", 0) < lim or (o.get("ahora") or 0) < 5 or not o.get("asin") or o["asin"] in j["vistas"][-8:]:
            continue
        t = re.sub(r"\s+-\s*[\d.,]+\s*EUR\s*$", "", str(o.get("t") or ""))
        if _fi_es_libro(o["asin"]) or _fi_otro_idioma(t):
            continue
        of.append(o)
    _ad_rnd.shuffle(of)
    return of[:8]
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: error de sintaxis", e); sys.exit(1)
cp = RUTA + ".bak_adivina1b_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy2(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: el juego ya no usa libros ni titulos en otro idioma.")
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato   y luego /adivina")
print("Deshacer: cp %s %s && sudo systemctl restart chivato" % (cp, RUTA))
