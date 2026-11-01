import shutil, time, py_compile
RUTA = "/opt/chivato/bot.py"
MARCA = "# --- MUDANZACONT1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado"); raise SystemExit
BLOQUE = '''
# --- MUDANZACONT1 ---
_mc_hook_orig = hook_anuncios_pago

def hook_anuncios_pago(d, u):
    try:
        m = u.get("message") or (u.get("callback_query") or {}).get("message") and u["callback_query"]
        quien = None
        if u.get("message"):
            quien = u["message"].get("from", {}).get("id")
        elif u.get("callback_query"):
            quien = u["callback_query"].get("from", {}).get("id")
        if quien is not None and str(quien) != str(ADMIN):
            mu = d.setdefault("mudanza", {})
            if str(quien) not in mu:
                mu[str(quien)] = time.strftime("%Y-%m-%d %H:%M")
        msg = u.get("message") or {}
        txt = (msg.get("text") or "").strip().lower()
        if txt.startswith("/mudanza") and str(msg.get("chat", {}).get("id")) == str(ADMIN):
            us = set(str(k) for k in d.get("users", {}).keys())
            mu = d.get("mudanza", {})
            movidos = [k for k in mu if k in us]
            total = len(us)
            hoy_ = time.strftime("%Y-%m-%d")
            hoy_n = len([k for k in movidos if mu[k].startswith(hoy_)])
            t = ("\\U0001F69A MUDANZA AL BOT NUEVO\\n\\n"
                 "Usuarios totales: %d\\n"
                 "Ya han escrito al bot nuevo: %d (%d%%)\\n"
                 "Hoy: %d\\n"
                 "Pendientes: %d\\n\\n"
                 "Cuenta a quien ha escrito o pulsado algo desde que se instal\\u00f3 este contador."
                 % (total, len(movidos), (100 * len(movidos) // total) if total else 0, hoy_n, total - len(movidos)))
            requests.post(API + "/sendMessage", data=prot({"chat_id": msg["chat"]["id"], "text": t}, msg["chat"]["id"]), timeout=30)
            return True
    except Exception as e:
        print("error mudanza conteo", e, flush=True)
    return _mc_hook_orig(d, u)
'''
fin = 'if __name__ == "__main__":'
if src.count(fin) != 1:
    print("No encuentro el sitio (", src.count(fin), ")"); raise SystemExit
if "def hook_anuncios_pago" not in src:
    print("Falta hook_anuncios_pago, no aplico"); raise SystemExit
bak = RUTA + ".bak_mc_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, bak)
open(RUTA, "w", encoding="utf-8").write(src.replace(fin, BLOQUE + "\n" + fin))
try:
    py_compile.compile(RUTA, doraise=True)
except Exception as e:
    shutil.copy(bak, RUTA); print("Error, restaurado:", e); raise SystemExit
print("Listo. Ahora: systemctl restart chivato")
