import sys, time, shutil, re
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- PROPINA300 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
L = src.split("\n")
i5 = [i for i, l in enumerate(L) if '"callback_data": "tip_500"' in l]
i1 = [i for i, l in enumerate(L) if '"callback_data": "tip_1000"' in l]
i2 = [i for i, l in enumerate(L) if '"callback_data": "tip_2500"' in l]
if len(i5) != 1 or len(i1) != 1 or len(i2) != 1:
    print("ABORTO: no encuentro los 3 botones de propina"); sys.exit(1)
ind = re.match(r"\s*", L[i5[0]]).group(0)
L[i5[0]] = ind + '{"text": "\\u2615 300 \\u2b50", "callback_data": "tip_300"},  # --- PROPINA300 ---'
for i in sorted((i1[0], i2[0]), reverse=True):
    del L[i]
nuevo = "\n".join(L)
nuevo = re.sub(r"(?m)^MIN_PROPINA = \d+", "MIN_PROPINA = 300", nuevo)
nuevo = nuevo.replace("500 Stars", "300 Stars")
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_propina_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Propina cambiada a 300 Stars + cripto. Copia:", cp)
print("Ahora ejecuta: systemctl restart chivato")
print("Deshacer: cp", cp, RUTA, "&& systemctl restart chivato")
