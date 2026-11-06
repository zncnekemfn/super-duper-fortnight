import re, shutil, time, sys
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- BAJASREG1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "def hook_anuncios_pago(" not in src:
    print("ABORTO: no encuentro hook_anuncios_pago"); sys.exit(1)

BLOQUE = r'''
# --- BAJASREG1 ---
# Registra quien bloquea o vuelve a activar el bot (Telegram avisa con my_chat_member) y /bajas lo cuenta (solo admin).
_br_pre = hook_anuncios_pago

def _br_nombre(us):
    try:
        n = us.get("username")
        return ("@" + n) if n else (us.get("first_name") or "")[:20]
    except Exception:
        return ""

def _br_resumen(d):
    import time as _t
    bj = d.get("bajas") or {}
    ahora = _t.time()
    h24 = sum(1 for v in bj.values() if ahora - v.get("ts", 0) < 86400)
    d7 = sum(1 for v in bj.values() if ahora - v.get("ts", 0) < 7 * 86400)
    vu = d.get("bajas_vueltas", 0)
    desde = d.get("bajas_desde")
    desde_txt = _t.strftime("%d/%m %H:%M", _t.localtime(desde)) if desde else "hoy"
    return ("\U0001f4c9 BAJAS DEL BOT\n"
            "Registro desde: %s\n"
            "Han bloqueado/parado el bot: %d\n"
            "  · ultimas 24 h: %d\n"
            "  · ultimos 7 dias: %d\n"
            "Han vuelto a activarlo: %d\n"
            "Usuarios actuales en el bot: %d\n\n"
            "Nota: Telegram solo avisa de las bajas a partir de ahora; las anteriores no se pueden saber."
            % (desde_txt, len(bj), h24, d7, vu, len(d.get("users", {}))))

def hook_anuncios_pago(d, u):
    try:
        mc = u.get("my_chat_member")
        if mc:
            ch = mc.get("chat") or {}
            if ch.get("type") == "private":
                import time as _t
                uid = str(ch.get("id"))
                est = ((mc.get("new_chat_member") or {}).get("status") or "")
                d.setdefault("bajas_desde", _t.time())
                bj = d.setdefault("bajas", {})
                if est in ("kicked", "left"):
                    bj[uid] = {"ts": _t.time(), "n": _br_nombre(mc.get("from") or {})}
                elif est == "member" and uid in bj:
                    bj.pop(uid, None)
                    d["bajas_vueltas"] = d.get("bajas_vueltas", 0) + 1
            return True
        m = u.get("message")
        t = ((m.get("text") or "") if m else "").strip()
        if m and t and t.lower().split("@")[0].split()[0] == "/bajas" and str(m["chat"]["id"]) == str(ADMIN):
            d.setdefault("bajas_desde", time.time())
            enviar(m["chat"]["id"], _br_resumen(d))
            return True
    except Exception as e:
        print("error bajasreg", e, flush=True)
    return _br_pre(d, u)
'''
n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
nuevo = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: BLOQUE + "\n" + m.group(0), src, count=1, flags=re.M)
# pedir a Telegram los avisos my_chat_member
if '"my_chat_member"' not in nuevo.split("# --- BAJASREG1 ---")[0]:
    pat = r'\["message", "callback_query", "pre_checkout_query", "channel_post"\]'
    if len(re.findall(pat, nuevo)) != 1:
        print("ABORTO: no encuentro la lista allowed_updates esperada"); sys.exit(1)
    nuevo = re.sub(pat, '["message", "callback_query", "pre_checkout_query", "channel_post", "my_chat_member"]', nuevo, count=1)
try:
    compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: error de sintaxis", e); sys.exit(1)
copia = RUTA + ".bak_bajasreg1_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: el bot ahora registra las bajas. Usa /bajas en Telegram.")
print("Copia:", copia)
print("Reinicia: sudo systemctl restart chivato")
print("Deshacer: cp %s %s && sudo systemctl restart chivato" % (copia, RUTA))
