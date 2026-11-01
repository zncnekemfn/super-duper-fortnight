import shutil, time, py_compile
RUTA = "/opt/chivato/bot.py"
MARCA = "# --- MODACOLOR1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado"); raise SystemExit
if "MODAMENU1" not in src:
    print("Falta aplicar parche_moda_menu1.py. No toco nada"); raise SystemExit
BLOQUE = r'''
# --- MODACOLOR1 ---
try:
    BT_MENU.pop(_bt_clave("\U0001F457 Moda"), None)
except Exception as e:
    print("error color moda", e, flush=True)
'''
fin = 'if __name__ == "__main__":'
if src.count(fin) != 1:
    print("No encuentro el sitio donde insertar, no toco nada"); raise SystemExit
bak = RUTA + ".bak_mc_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, bak)
open(RUTA, "w", encoding="utf-8").write(src.replace(fin, BLOQUE + "\n" + fin))
try:
    py_compile.compile(RUTA, doraise=True)
except Exception as e:
    shutil.copy(bak, RUTA); print("Error, restaurado:", e); raise SystemExit
print("Listo. Ahora: systemctl restart chivato")
