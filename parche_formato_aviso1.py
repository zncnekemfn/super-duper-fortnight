import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- FORMATOAVISO1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)

# 1) Icono del titulo: el mando (U+1F3AE) pasa a ser una bolsa de compras. Solo en los titulos de los avisos.
pat = re.compile(r'"(?:\\U0001f3ae|\U0001f3ae) " \+ (tit\[:140\]|str\(titulo\)\[:140\])')
nuevo, n_icono = pat.subn(lambda m: '"\\U0001f6cd\\ufe0f " + ' + m.group(1), src)
if n_icono == 0:
    print("ABORTO: no encuentro el icono del titulo en el bot; no cambio nada."); sys.exit(1)

# 2) Decimales de la linea de historial: "144.20 EUR" -> "144,20 EUR"
viejo = '"Media 90 días: %.2f EUR (%d%% menos)" % (av90 / 100.0,'
nueva = '"Media 90 días: %s EUR (%d%% menos)" % (("%.2f" % (av90 / 100.0)).replace(".", ","),'
n_dec = nuevo.count(viejo)
if n_dec == 1:
    nuevo = nuevo.replace(viejo, nueva)
else:
    print("Aviso: no cambio los decimales de la media (encontradas %d, esperaba 1). El resto sigue." % n_dec)

anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', nuevo))
nuevo = nuevo[:anc[0].start()] + MARCA + "\n" + nuevo[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: error de sintaxis", e); sys.exit(1)
cp = RUTA + ".bak_formatoaviso1_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy2(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: icono cambiado en %d sitio(s); decimales con coma: %s." % (n_icono, "si" if n_dec == 1 else "no"))
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato")
print("Deshacer: cp %s %s && sudo systemctl restart chivato" % (cp, RUTA))
