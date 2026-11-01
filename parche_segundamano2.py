import re, sys, time, shutil
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- SEGUNDAMANO_MENU ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("# --- SEGUNDAMANO ---", "def teclado_menu(", "BT_MENU"):
    if n not in src:
        print("ABORTO: no encuentro %s (aplica antes parche_segundamano1)" % n); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: anclaje final (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''# --- SEGUNDAMANO_MENU ---
_teclado_menu_pre_sm = teclado_menu

def teclado_menu():
    try:
        kb = json.loads(_teclado_menu_pre_sm())
        filas = kb["inline_keyboard"]
        nueva = [{"text": "\U0001f6cd️ Segunda mano", "callback_data": "m_segundamano"}]
        filas.insert(max(0, len(filas) - 1), nueva)
        return json.dumps(kb)
    except Exception as e:
        print("error menu segundamano", e, flush=True)
        return _teclado_menu_pre_sm()

try:
    BT_MENU[_bt_clave("\U0001f6cd️ Segunda mano")] = ("\U0001f6cd️ Segunda mano", "primary")
except Exception as e:
    print("error estilo boton segundamano", e, flush=True)

'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_smmenu_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Boton Segunda mano anadido al menu. Copia:", cp)
print("Ahora ejecuta: systemctl restart chivato")
print("Deshacer: cp", cp, RUTA, "&& systemctl restart chivato")
