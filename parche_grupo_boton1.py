import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- GRUPOBOTON1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("def teclado_menu(", "import json"):
    if n not in src:
        print("ABORTO: no encuentro", n); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''
# --- GRUPOBOTON1 ---
# Boton del menu "⚪ Únete al grupo" que abre el grupo. Sin color de Telegram (blanco/gris por defecto) y con circulo blanco.
_GR_URL = "https://t.me/chivatoofertas"
_gr_tec_orig = teclado_menu

def teclado_menu():
    try:
        kb = json.loads(_gr_tec_orig())
        filas = kb["inline_keyboard"]
        filas.insert(max(0, len(filas) - 1), [{"text": "⚪ Únete al grupo", "url": _GR_URL}])
        return json.dumps(kb)
    except Exception as e:
        print("error menu grupo", e, flush=True)
        return _gr_tec_orig()

if "_bt_boton" in globals():
    _gr_bt_prev = _bt_boton
    def _bt_boton(b):
        r = _gr_bt_prev(b)
        try:
            if isinstance(r, dict) and str(r.get("text", "")).startswith("⚪"):
                r.pop("style", None)
        except Exception:
            pass
        return r
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_grupo_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Boton '⚪ Únete al grupo' añadido al menu. Copia:", cp)
print("Reinicia: sudo systemctl restart chivato   y luego abre el menu")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
