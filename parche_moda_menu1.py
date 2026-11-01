import shutil, time, py_compile
RUTA = "/opt/chivato/bot.py"
MARCA = "# --- MODAMENU1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado"); raise SystemExit
BLOQUE = r'''
# --- MODAMENU1 ---
_mm_tec_orig = teclado_menu
def teclado_menu():
    try:
        kb = json.loads(_mm_tec_orig())
        filas = kb["inline_keyboard"]
        filas.insert(max(0, len(filas) - 1), [{"text": "\U0001F457 Moda", "callback_data": "m_moda"}])
        return json.dumps(kb)
    except Exception as e:
        print("error menu moda", e, flush=True)
        return _mm_tec_orig()

try:
    BT_MENU[_bt_clave("\U0001F457 Moda")] = ("\U0001F457 Moda", "primary")
except Exception as e:
    print("error estilo boton moda", e, flush=True)

_mm_hook_orig = hook_menu
def hook_menu(d, u):
    try:
        cq = u.get("callback_query")
        if cq and cq.get("data") == "m_moda":
            try:
                requests.post(API + "/answerCallbackQuery", data={"callback_query_id": cq["id"]}, timeout=10)
            except Exception:
                pass
            cid = str(cq["from"]["id"])
            g = (d["users"].get(cid) or {}).get("genero", "")
            requests.post(API + "/sendMessage", data={"chat_id": cid, "text": _mg_texto(g),
                "reply_markup": _mg_teclado(g)}, timeout=15)
            return True
    except Exception as e:
        print("error boton moda", e, flush=True)
    return _mm_hook_orig(d, u)
'''
for need in ("MODAGENERO1", "def teclado_menu", "def hook_menu"):
    if need not in src:
        print("Falta", need, "- aplica antes parche_moda_genero1.py. No toco nada"); raise SystemExit
fin = 'if __name__ == "__main__":'
if src.count(fin) != 1:
    print("No encuentro el sitio donde insertar, no toco nada"); raise SystemExit
bak = RUTA + ".bak_mm_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, bak)
open(RUTA, "w", encoding="utf-8").write(src.replace(fin, BLOQUE + "\n" + fin))
try:
    py_compile.compile(RUTA, doraise=True)
except Exception as e:
    shutil.copy(bak, RUTA); print("Error, restaurado:", e); raise SystemExit
print("Listo. Ahora: systemctl restart chivato")
