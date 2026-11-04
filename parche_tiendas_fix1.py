import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- TIENDASFIX1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- TIENDAS1 ---" not in src:
    print("ABORTO: TIENDAS1 no esta instalado."); sys.exit(1)
def bloque(s, marca):
    i = s.find(marca)
    if i < 0:
        return None
    m = re.search(r'(?m)^(# --- [A-Z0-9_]+ ---|if __name__ == ["\']__main__["\']:)', s[i + len(marca):])
    j = i + len(marca) + (m.start() if m else len(s) - i - len(marca))
    return i, j
nuevo = src
cuenta = 0
for marca in ("# --- TIENDAS1 ---", "# --- TIENDASBOTON1 ---"):
    r = bloque(nuevo, marca)
    if not r:
        continue
    i, j = r
    b = nuevo[i:j]
    b2 = b.replace("_td_", "_ti_")
    cuenta += b.count("_td_")
    nuevo = nuevo[:i] + b2 + nuevo[j:]
nuevo = nuevo.replace("# --- TIENDAS1 ---", "# --- TIENDAS1 ---\n" + MARCA, 1)
if cuenta == 0:
    print("ABORTO: no encontre nada que cambiar."); sys.exit(1)
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: error de sintaxis", e); sys.exit(1)
cp = RUTA + ".bak_tiendasfix_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy2(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: arreglada la colision de nombres entre Tiendas y Tendencias (%d cambios)." % cuenta)
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato   y luego /menu")
print("Deshacer: cp %s %s && sudo systemctl restart chivato" % (cp, RUTA))
