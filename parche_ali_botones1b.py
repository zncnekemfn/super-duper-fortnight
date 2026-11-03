import shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- ALIBOTONES1 ---" not in src:
    print("ABORTO: primero instala parche_ali_botones1.py"); sys.exit(1)
a = ''',
        {"text": "\\U0001f515 MENOS", "callback_data": "aly_no_" + pid}]]})'''
b = ''']]})'''
if a not in src:
    print("El botón MENOS ya no estaba. No hago nada."); sys.exit(0)
nuevo = src.replace(a, b)
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_alibotones1b_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Botón MENOS eliminado de las ofertas de AliExpress.")
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
