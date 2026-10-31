import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- BOTONES ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)

def unico(patron, fn, nombre):
    global src
    n = len(re.findall(patron, src, re.M))
    if n != 1:
        print("ABORTO: ancla '%s' encontrada %d veces" % (nombre, n)); sys.exit(1)
    src = re.sub(patron, fn, src, count=1, flags=re.M)

TAIL = r'''# --- BOTONES ---
import json as _bt_json

# Textos nuevos segun el callback_data del boton. Edita aqui para cambiar el aspecto.
BT_TEXTOS = {
    "vo_": "\U0001f525 VER OFERTA AHORA",
    "fb_up": "\U0001f44d Me interesa",
    "fb_dn": "\U0001f44e No me gusta",
    "fb_no": "\U0001f6ab No mas de esto",
}
# Estilos de color de Telegram: primary (azul), success (verde), danger (rojo)
BT_ESTILOS = {"vo_": "success", "fb_up": "primary", "fb_dn": "danger", "fb_no": "danger"}
BT_METODOS = ("sendMessage", "sendPhoto", "editMessageReplyMarkup", "editMessageText", "editMessageCaption")
_bt_estado = {"on": True, "estilo": True}

def _bt_boton(b):
    if not isinstance(b, dict):
        return b
    cb = str(b.get("callback_data") or "")
    for pref, txt in BT_TEXTOS.items():
        if cb == pref or (pref.endswith("_") and cb.startswith(pref)):
            b["text"] = txt
            if _bt_estado["estilo"] and pref in BT_ESTILOS:
                b["style"] = BT_ESTILOS[pref]
            return b
    if b.get("url") and _bt_estado["estilo"]:
        b.setdefault("style", "primary")
    return b

def _bt_markup(m):
    esstr = isinstance(m, str)
    try:
        mk = _bt_json.loads(m) if esstr else m
        kb = mk.get("inline_keyboard") if isinstance(mk, dict) else None
        if not kb:
            return m
        kb = [[_bt_boton(dict(b)) for b in fila] for fila in kb]
        kb.sort(key=lambda f: 0 if any(str(b.get("callback_data") or "").startswith("vo_") for b in f) else 1)
        mk = dict(mk); mk["inline_keyboard"] = kb
        return _bt_json.dumps(mk) if esstr else mk
    except Exception as e:
        print("error botones", e, flush=True)
        return m

class _BtReq(object):
    def __init__(self, real):
        self._real = real
    def __getattr__(self, n):
        return getattr(self._real, n)
    def post(self, url, *a, **kw):
        try:
            if _bt_estado["on"] and any(("/" + m) in str(url) for m in BT_METODOS):
                for campo in ("json", "data"):
                    c = kw.get(campo)
                    if isinstance(c, dict) and c.get("reply_markup"):
                        c = dict(c); c["reply_markup"] = _bt_markup(c["reply_markup"]); kw[campo] = c
        except Exception as e:
            print("error botones", e, flush=True)
        return self._real.post(url, *a, **kw)

if not isinstance(requests, _BtReq):
    requests = _BtReq(requests)

def botones_cmd(d, cid, args):
    a = args[0].lower() if args else ""
    if a in ("on", "off"):
        _bt_estado["on"] = (a == "on")
    elif a == "color":
        _bt_estado["estilo"] = not _bt_estado["estilo"]
    d["bt_on"], d["bt_estilo"] = _bt_estado["on"], _bt_estado["estilo"]
    enviar(cid, "\U0001f3a8 ASPECTO DE BOTONES\n\nNuevo aspecto: %s\nColores de Telegram: %s\n\n/botones on · /botones off\n/botones color (activa o desactiva colores)" % (
        "ACTIVADO" if _bt_estado["on"] else "APAGADO", "SI" if _bt_estado["estilo"] else "NO"))

'''

unico(r'^def comando\(d, cid, texto\):\n', lambda m: "", "comando") if False else None
unico(r'^    elif cmd in \("/propina", "/premium"\):\n',
      lambda m: '    elif cmd == "/botones" and cid == ADMIN:\n        botones_cmd(d, cid, args)\n' + m.group(0), "propina")
unico(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), "main")
try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)
copia = RUTA + ".bak_botones_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
