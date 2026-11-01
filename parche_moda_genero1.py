import shutil, time, py_compile
RUTA = "/opt/chivato/bot.py"
MARCA = "# --- MODAGENERO1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado"); raise SystemExit
BLOQUE = r'''
# --- MODAGENERO1 ---
import re as _mg_re
_MG_F = _mg_re.compile(r"\b(mujer|mujeres|femenin[oa]s?|se[ñn]ora|chicas?|ni[ñn]as?|women'?s?|woman|lady|ladies|dama|girls?)\b", _mg_re.I)
_MG_M = _mg_re.compile(r"\b(hombres?|masculin[oa]s?|caballeros?|chicos?|ni[ñn]os?|men'?s?|man|boys?)\b", _mg_re.I)

def _mg_bloquea(genero, titulo):
    t = str(titulo or "")
    f = bool(_MG_F.search(t)); m = bool(_MG_M.search(t))
    if f and m:
        return False
    if genero == "chico" and f:
        return True
    if genero == "chica" and m:
        return True
    return False

_mg_aviso_orig = enviar_aviso
def enviar_aviso(d, cid, item):
    try:
        if str(cid) != str(ADMIN):
            g = ((d.get("users") or {}).get(cid) or (d.get("users") or {}).get(str(cid)) or {}).get("genero", "")
            if g and _mg_bloquea(g, item.get("t")):
                return
    except Exception as e:
        print("error moda genero", e, flush=True)
    return _mg_aviso_orig(d, cid, item)

def _mg_teclado(g):
    mk = lambda t, k: {"text": ("✅ " if (g or "todo") == k else "") + t, "callback_data": "gen_" + k}
    return json.dumps({"inline_keyboard": [[mk("Todo", "todo"), mk("Chico", "chico"), mk("Chica", "chica")]]})

def _mg_texto(g):
    nom = {"": "Todo", "todo": "Todo", "chico": "Chico", "chica": "Chica"}.get(g or "", "Todo")
    return ("\U0001F457 MODA Y ROPA\n\nElige qué avisos quieres: Todo, solo Chico o solo Chica.\n"
            "Ocultamos los avisos cuyo título indica claramente el otro género; los unisex te llegan siempre.\n\nAhora: " + nom)

_mg_hook_orig = hook_anuncios_pago
def hook_anuncios_pago(d, u):
    try:
        cq = u.get("callback_query")
        if cq and str(cq.get("data") or "").startswith("gen_"):
            cid = str(cq["from"]["id"])
            try:
                requests.post(API + "/answerCallbackQuery", data={"callback_query_id": cq["id"]}, timeout=10)
            except Exception:
                pass
            k = cq["data"][4:]
            if k in ("todo", "chico", "chica"):
                us = d["users"].setdefault(cid, nuevo_usuario())
                us["genero"] = "" if k == "todo" else k
                requests.post(API + "/editMessageText", data={"chat_id": cid,
                    "message_id": (cq.get("message") or {}).get("message_id"),
                    "text": _mg_texto(us["genero"]), "reply_markup": _mg_teclado(us["genero"])}, timeout=15)
            return True
        m = u.get("message") or {}
        txt = (m.get("text") or "").strip().lower()
        if txt.split("@")[0].split(" ")[0] in ("/moda", "/genero"):
            cid = str(m["chat"]["id"])
            us = d["users"].get(cid) or {}
            g = us.get("genero", "")
            requests.post(API + "/sendMessage", data={"chat_id": cid, "text": _mg_texto(g),
                "reply_markup": _mg_teclado(g)}, timeout=15)
            return True
    except Exception as e:
        print("error moda genero hook", e, flush=True)
    return _mg_hook_orig(d, u)

try:
    AYUDA = AYUDA + "\n\n\U0001F457 /moda - Elige avisos de chico, chica o todo"
except Exception:
    pass
'''
fin = 'if __name__ == "__main__":'
for need in ("def enviar_aviso", "def hook_anuncios_pago", "def nuevo_usuario"):
    if need not in src:
        print("Falta", need, "- no toco nada"); raise SystemExit
if src.count(fin) != 1:
    print("No encuentro el sitio donde insertar, no toco nada"); raise SystemExit
bak = RUTA + ".bak_mg_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, bak)
open(RUTA, "w", encoding="utf-8").write(src.replace(fin, BLOQUE + "\n" + fin))
try:
    py_compile.compile(RUTA, doraise=True)
except Exception as e:
    shutil.copy(bak, RUTA); print("Error, restaurado:", e); raise SystemExit
print("Listo. Ahora: systemctl restart chivato")
