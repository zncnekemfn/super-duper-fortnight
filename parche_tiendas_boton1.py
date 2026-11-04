import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- TIENDASBOTON1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("# --- TIENDAS1 ---", "def teclado_menu(", "def hook_menu("):
    if n not in src:
        print("ABORTO: falta", n, "(instala antes parche_tiendas1.py)"); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''
# --- TIENDASBOTON1 ---
# Boton "Tiendas" en el menu (abre lo mismo que /tiendas).
_tb_tec_orig = teclado_menu
def teclado_menu():
    try:
        kb = json.loads(_tb_tec_orig())
        filas = kb["inline_keyboard"]
        filas.insert(max(0, len(filas) - 1), [{"text": "\U0001f3ec Tiendas", "callback_data": "m_tiendas"}])
        return json.dumps(kb)
    except Exception as e:
        print("error menu tiendas", str(e)[:80], flush=True)
        return _tb_tec_orig()

_tb_hook_menu_orig = hook_menu
def hook_menu(d, u):
    try:
        cq = u.get("callback_query")
        if cq and cq.get("data") == "m_tiendas":
            try:
                requests.post(API + "/answerCallbackQuery", data={"callback_query_id": cq["id"]}, timeout=10)
            except Exception:
                pass
            cid = str(cq["from"]["id"])
            us = d["users"].setdefault(cid, nuevo_usuario())
            enviar(cq["from"]["id"], _ti_texto(us), _ti_teclado(us))
            return True
    except Exception as e:
        print("error boton tiendas", str(e)[:100], flush=True)
    return _tb_hook_menu_orig(d, u)
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_tiendasboton_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: boton '🏬 Tiendas' en el menu.")
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato   y luego /autotest")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
