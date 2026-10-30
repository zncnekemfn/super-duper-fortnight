import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()

if "# --- BAJA2 ---" in src:
    print("Ya estaba aplicado. No hago nada.")
    sys.exit(0)
if "# --- BAJA ---" not in src:
    print("ABORTO: falta parche_baja.py"); sys.exit(1)

def unico(patron, fn, nombre):
    global src
    n = len(re.findall(patron, src, re.M))
    if n != 1:
        print("ABORTO: ancla '%s' encontrada %d veces" % (nombre, n)); sys.exit(1)
    src = re.sub(patron, fn, src, count=1, flags=re.M)

FUNC = r'''# --- BAJA2 ---
import json as _bj_json

def _bj_nombre(us):
    if not isinstance(us, dict):
        return ""
    n = (us.get("_nom") or "").strip()
    u = (us.get("_usr") or "").strip()
    t = n + ((" @" + u) if u else "")
    if not t:
        for k in ("username", "user", "nombre", "name", "first_name"):
            v = us.get(k)
            if v and isinstance(v, str):
                return v[:30]
    return t[:40]

def _bj_act(us):
    a = (us or {}).get("_act")
    if not a:
        return ""
    dias = int((time.time() - a) // 86400)
    return "hoy" if dias <= 0 else "hace %dd" % dias

def hook_nombres(d, u):
    try:
        for k in ("message", "callback_query"):
            x = u.get(k)
            if not x:
                continue
            f = x.get("from") or {}
            cid = str(f.get("id"))
            us = d["users"].get(cid)
            if us is None:
                return
            nom = ((f.get("first_name") or "") + " " + (f.get("last_name") or "")).strip()
            if nom:
                us["_nom"] = nom[:40]
            if f.get("username"):
                us["_usr"] = f["username"][:32]
            us["_act"] = int(time.time())
    except Exception:
        pass

def _bj_rellenar(d, destino):
    import threading
    ids = [k for k in d["users"].keys() if k != ADMIN and not (d["users"].get(k) or {}).get("_nom")]
    def _run():
        ok = 0
        for k in ids:
            try:
                r = requests.post(API + "/getChat", data={"chat_id": k}, timeout=15)
                if r.status_code == 200:
                    res = (r.json() or {}).get("result") or {}
                    us = d["users"].get(k)
                    if us is not None:
                        nom = ((res.get("first_name") or "") + " " + (res.get("last_name") or "")).strip()
                        if nom:
                            us["_nom"] = nom[:40]
                        if res.get("username"):
                            us["_usr"] = res["username"][:32]
                        ok += 1
            except Exception as ex:
                print("error getChat", ex, flush=True)
            time.sleep(0.06)
        enviar(destino, "✅ Nombres actualizados: %d de %d usuarios. Prueba /baja buscar nombre" % (ok, len(ids)))
    threading.Thread(target=_run, daemon=True).start()
    return len(ids)

def _bj_lista_texto(d, ids, pag, por=40):
    trozo = ids[(pag - 1) * por: pag * por]
    t = ["\U0001f465 USUARIOS %d-%d de %d" % ((pag - 1) * por + 1, (pag - 1) * por + len(trozo), len(ids)), ""]
    for k in trozo:
        us = d["users"].get(k) or {}
        n = _bj_nombre(us)
        a = _bj_act(us)
        t.append(k + ((" · " + n) if n else "") + ((" · " + a) if a else ""))
    t += ["", "Buscar: /baja buscar nombre", "Bloquear: /baja ID", "Siguiente: /baja lista %d" % (pag + 1)]
    return "\n".join(t)

def baja_buscar(d, cid, args):
    q = " ".join(args).lower().lstrip("@").strip()
    if not q:
        enviar(cid, "Uso: /baja buscar nombre   (o parte del nombre, o @usuario)")
        return
    res = []
    for k, us in d["users"].items():
        if k == ADMIN:
            continue
        txt = (k + " " + _bj_nombre(us)).lower()
        if q in txt:
            res.append((k, us))
    if not res:
        enviar(cid, "No encuentro a nadie con \"%s\". Si es la primera vez, ejecuta antes /baja nombres para cargar los nombres." % q)
        return
    kb = [[{"text": "\U0001f6ab %s" % ((_bj_nombre(us) or k)[:30]), "callback_data": "bj_p_" + k}] for k, us in res[:8]]
    t = "\U0001f50e %d resultado(s) para \"%s\":\n\n" % (len(res), q)
    for k, us in res[:8]:
        t += "%s · %s%s\n" % (k, _bj_nombre(us) or "sin nombre", (" · " + _bj_act(us)) if _bj_act(us) else "")
    t += "\nPulsa un nombre para bloquearlo (te pido confirmación)."
    enviar(cid, t, _bj_json.dumps({"inline_keyboard": kb}))

def hook_bajacb(d, u):
    cq = u.get("callback_query")
    if not cq or not str(cq.get("data") or "").startswith("bj_"):
        return False
    try:
        if str(cq["from"]["id"]) != ADMIN:
            return True
        _, acc, uid = (cq["data"].split("_", 2) + ["", ""])[:3]
        us = d["users"].get(uid) or {}
        nom = _bj_nombre(us) or uid
        aviso = "Hecho"
        if acc == "p":
            kb = [[{"text": "✅ Sí, bloquear", "callback_data": "bj_s_" + uid}, {"text": "❌ No", "callback_data": "bj_n_" + uid}]]
            enviar(ADMIN, "¿Bloquear a %s (%s)?\nDejará de recibir avisos y el bot ignorará lo que escriba." % (nom, uid), _bj_json.dumps({"inline_keyboard": kb}))
            aviso = "Confirma abajo"
        elif acc == "s":
            if uid == ADMIN:
                aviso = "No puedes bloquearte a ti"
            else:
                _bj_quitar(d, uid)
                bl = _bj_ids(d)
                if uid not in bl:
                    bl.append(uid)
                enviar(ADMIN, "\U0001f6ab Bloqueado: %s (%s)" % (nom, uid))
                aviso = "Bloqueado"
        elif acc == "n":
            aviso = "Cancelado"
        try:
            requests.post(API + "/answerCallbackQuery", data={"callback_query_id": cq["id"], "text": aviso}, timeout=10)
            m = cq.get("message") or {}
            requests.post(API + "/editMessageReplyMarkup", data={
                "chat_id": ADMIN, "message_id": m.get("message_id"), "reply_markup": _bj_json.dumps({"inline_keyboard": []})}, timeout=10)
        except Exception:
            pass
    except Exception as e:
        print("error baja cb", e, flush=True)
    return True

_baja_cmd_orig = baja_cmd
def baja_cmd(d, cid, args):
    a = args[0].lower() if args else ""
    if a in ("buscar", "b"):
        return baja_buscar(d, cid, args[1:])
    if a in ("nombres", "actualizar"):
        n = _bj_rellenar(d, cid)
        enviar(cid, "Cargando nombres de %d usuarios... te aviso al terminar (unos segundos)." % n)
        return
    if a in ("lista", "ver"):
        ids = [k for k in d["users"].keys() if k != ADMIN]
        pag = int(args[1]) if len(args) > 1 and args[1].isdigit() and int(args[1]) >= 1 else 1
        if not ids[(pag - 1) * 40: pag * 40]:
            enviar(cid, "No hay más usuarios en esa página (%d en total)." % len(ids))
            return
        enviar(cid, _bj_lista_texto(d, ids, pag))
        return
    return _baja_cmd_orig(d, cid, args)

'''

unico(r'^def comando\(d, cid, texto\):\n', lambda m: FUNC + m.group(0), "comando")
unico(r'^([ \t]+)if hook_anuncios_pago\(d, u\):\n',
      lambda m: m.group(1) + 'hook_nombres(d, u)\n' + m.group(1) + 'if hook_bajacb(d, u):\n' + m.group(1) + '    continue\n' + m.group(0), "hook")

try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)

copia = RUTA + ".bak_baja2_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
