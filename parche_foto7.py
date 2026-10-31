import re, shutil, time, sys, os

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- MENU7 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "requests.post(" not in src:
    print("ABORTO: no encuentro el envio a Telegram"); sys.exit(1)

TAIL = r'''# --- MENU7 ---
# Menu de botones estilo neon-gaming: mismos botones y funciones, solo cambia el texto.
import json as _m7_js, re as _m7_re, unicodedata as _m7_ud

_M7_NOMBRES = {
    "propina cafe": "☕ PROPINA CAFÉ",
    "ultimas ofertas": "⚡ ÚLTIMAS OFERTAS",
    "tablon": "\U0001f579 TABLÓN",
    "seguir": "\U0001f3af SEGUIR",
    "categorias": "\U0001f4a0 CATEGORÍAS",
    "descuento": "\U0001f4a5 DESCUENTO",
    "no molestar": "\U0001f319 SILENCIO",
    "resumen": "\U0001f4e1 RESUMEN",
    "mi estado": "\U0001f3ae MI ESTADO",
    "invitar amigos": "\U0001f381 INVITAR AMIGOS",
    "anunciar": "\U0001f4e2 ANUNCIAR",
    "filtro": "\U0001f39b FILTRO",
    "contacto": "\U0001f4ac CONTACTO",
    "suscribirme": "\U0001f7e2 SUSCRIBIRME",
    "parar avisos": "\U0001f534 PARAR AVISOS",
    "ayuda": "\U0001f579 AYUDA",
    "actualizar": "\U0001f501 ACTUALIZAR",
}

def _m7_norm(t):
    t = _m7_ud.normalize("NFD", str(t or ""))
    t = "".join(c for c in t if _m7_ud.category(c) != "Mn")
    t = _m7_re.sub(r"^[^A-Za-z0-9]+", "", t).strip().lower()
    return t

def _m7_menu(mk):
    try:
        era_str = isinstance(mk, str)
        o = _m7_js.loads(mk) if era_str else mk
        kb = o.get("inline_keyboard") if isinstance(o, dict) else None
        if not kb:
            return mk
        coinciden = sum(1 for fila in kb for b in fila if _m7_norm(b.get("text")) in _M7_NOMBRES)
        if coinciden < 3:
            return mk
        for fila in kb:
            for b in fila:
                n = _M7_NOMBRES.get(_m7_norm(b.get("text")))
                if n:
                    b["text"] = n
        return _m7_js.dumps(o, ensure_ascii=False) if era_str else o
    except Exception as e:
        print("error menu neon", e, flush=True)
        return mk

class _M7Req:
    def __init__(self, real):
        object.__setattr__(self, "_real", real)
    def __getattr__(self, n):
        return getattr(self._real, n)
    def post(self, url, *a, **k):
        try:
            dat = k.get("data")
            if isinstance(dat, dict) and dat.get("reply_markup") and str(url).split("/")[-1] in ("sendMessage", "sendPhoto", "editMessageText", "editMessageReplyMarkup", "editMessageCaption"):
                nuevo = _m7_menu(dat["reply_markup"])
                if nuevo is not dat["reply_markup"]:
                    k = dict(k); k["data"] = dict(dat, reply_markup=nuevo)
        except Exception as e:
            print("error menu neon", e, flush=True)
        return self._real.post(url, *a, **k)

requests = _M7Req(requests)

'''

n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
src = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), src, count=1, flags=re.M)
try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)
copia = RUTA + ".bak_menu7_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
