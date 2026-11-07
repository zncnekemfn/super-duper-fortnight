import re, sys, time, shutil
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- VOLUMEN1 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "for _pg in (0, 1):" not in src or "_KQ_RANK_MAX" not in src:
    print("ABORTO: no encuentro la consulta de Keepa esperada"); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: anclaje final (%d)" % len(anc)); sys.exit(1)
nuevo = src.replace("for _pg in (0, 1):", "for _pg in (0, 1, 2, 3):")
BLOQUE = '''# --- VOLUMEN1 ---
# Mas ofertas: 4 paginas de Keepa por ciclo (antes 2), productos hasta el puesto 200.000 en ventas
# y hasta 8 avisos nuevos por consulta (antes 5). Los demas filtros de calidad no cambian.
_KQ_RANK_MAX = 200000
KEEPA_MAX_POR_CICLO = 8
'''
nuevo = nuevo[:anc[0].start()] + BLOQUE + "\n" + nuevo[anc[0].start():] if False else re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: BLOQUE + "\n" + m.group(0), nuevo, count=1, flags=re.M)
try: compile(nuevo, RUTA, "exec")
except SyntaxError as e:
    print("ABORTO: error de sintaxis", e); sys.exit(1)
bak = RUTA + ".bak_volumen1_" + time.strftime("%Y%m%d_%H%M%S")
shutil.copy(RUTA, bak)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Aplicado. Reinicia con: sudo systemctl restart chivato")
print("Despues vigila los tokens: sudo journalctl -u chivato -n 40 --no-pager | grep 'keepa calidad tokens'")
print("Para deshacer: cp %s %s && sudo systemctl restart chivato" % (bak, RUTA))
