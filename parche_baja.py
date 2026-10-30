import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()

if "# --- BAJA ---" in src:
    print("Ya estaba aplicado. No hago nada.")
    sys.exit(0)

def unico(patron, fn, nombre):
    global src
    n = len(re.findall(patron, src, re.M))
    if n != 1:
        print("ABORTO: ancla '%s' encontrada %d veces" % (nombre, n)); sys.exit(1)
    src = re.sub(patron, fn, src, count=1, flags=re.M)

FUNC = r'''# --- BAJA ---
import re
def _bj_ids(d):
    return d.setdefault("bloq", [])

def _bj_quitar(d, uid):
    uid = str(uid)
    d["users"].pop(uid, None)
    for k in ("seguir", "escudo"):
        if isinstance(d.get(k), dict):
            d[k].pop(uid, None)

def _bj_nombre(us):
    if not isinstance(us, dict):
        return ""
    for k in ("username", "user", "nombre", "name", "first_name"):
        v = us.get(k)
        if v and isinstance(v, str):
            return v[:20]
    return ""

def baja_cmd(d, cid, args):
    bl = _bj_ids(d)
    if args and args[0].lower() in ("lista", "ver"):
        ids = [k for k in d["users"].keys() if k != ADMIN]
        pag = int(args[1]) if len(args) > 1 and args[1].isdigit() and int(args[1]) >= 1 else 1
        por = 40
        trozo = ids[(pag - 1) * por: pag * por]
        if not trozo:
            enviar(cid, "No hay más usuarios en esa página (%d en total)." % len(ids))
            return
        t = ["\U0001f465 USUARIOS %d-%d de %d" % ((pag - 1) * por + 1, (pag - 1) * por + len(trozo), len(ids)), ""]
        for k in trozo:
            n = _bj_nombre(d["users"].get(k))
            t.append(k + ((" · " + n) if n else ""))
        t += ["", "Eliminar y bloquear: /baja ID", "Siguiente página: /baja lista %d" % (pag + 1)]
        enviar(cid, "\n".join(t))
        return
    ids = [a for a in args if re.fullmatch(r"\d{5,}", a)]
    if not ids:
        enviar(cid, "\U0001f6ab BAJA Y BLOQUEO DE USUARIOS\n\nTotal de usuarios: %d · Bloqueados: %d\n\n"
                    "/baja ID  (elimina y bloquea a ese usuario; puedes poner varios IDs separados por espacio)\n"
                    "/baja lista  (ver IDs de los usuarios)\n"
                    "/bloqueados  (ver bloqueados)\n"
                    "/desbloquear ID" % (len([k for k in d["users"] if k != ADMIN]), len(bl)))
        return
    hechos, saltados = [], []
    for u in ids:
        if u == ADMIN:
            saltados.append(u + " (eres tú)")
            continue
        _bj_quitar(d, u)
        if u not in bl:
            bl.append(u)
        hechos.append(u)
    t = ""
    if hechos:
        t += "\U0001f6ab Eliminados y bloqueados (%d): %s\nYa no recibirán avisos y el bot ignorará lo que escriban." % (len(hechos), ", ".join(hechos))
    if saltados:
        t += ("\n" if t else "") + "Omitidos: " + ", ".join(saltados)
    enviar(cid, t)

def bloqueados_cmd(d, cid, args):
    bl = _bj_ids(d)
    if not bl:
        enviar(cid, "No hay usuarios bloqueados.")
        return
    enviar(cid, "\U0001f6ab BLOQUEADOS (%d)\n\n%s\n\n/desbloquear ID" % (len(bl), "\n".join(bl[-60:])))

def desbloquear_cmd(d, cid, args):
    bl = _bj_ids(d)
    ids = [a for a in args if re.fullmatch(r"\d{5,}", a)]
    if not ids:
        enviar(cid, "Uso: /desbloquear ID")
        return
    quitados = [u for u in ids if u in bl]
    for u in quitados:
        bl.remove(u)
    enviar(cid, ("✅ Desbloqueados: " + ", ".join(quitados) + ". Podrán volver con /start.") if quitados else "Ese ID no estaba bloqueado.")

def hook_bloqueo(d, u):
    bl = d.get("bloq")
    if not bl:
        return False
    for k in ("message", "callback_query", "pre_checkout_query"):
        x = u.get(k)
        if x and str((x.get("from") or {}).get("id")) in bl:
            return True
    return False

'''

unico(r'^def comando\(d, cid, texto\):\n', lambda m: FUNC + m.group(0), "comando")
unico(r'^    elif cmd in \("/propina", "/premium"\):\n',
      lambda m: ('    elif cmd == "/baja" and cid == ADMIN:\n        baja_cmd(d, cid, args)\n'
                 '    elif cmd == "/bloqueados" and cid == ADMIN:\n        bloqueados_cmd(d, cid, args)\n'
                 '    elif cmd == "/desbloquear" and cid == ADMIN:\n        desbloquear_cmd(d, cid, args)\n') + m.group(0), "propina")
unico(r'^([ \t]+)if hook_anuncios_pago\(d, u\):\n',
      lambda m: m.group(1) + 'if hook_bloqueo(d, u):\n' + m.group(1) + '    continue\n' + m.group(0), "hook")

try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)

copia = RUTA + ".bak_baja_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
