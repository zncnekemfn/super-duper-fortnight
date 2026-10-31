import re, shutil, time, sys, os

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- FOTO5 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- FOTO2 ---" not in src:
    print("ABORTO: primero hay que aplicar parche_foto2.py"); sys.exit(1)

TAIL = r'''# --- FOTO5 ---
# Botones de debajo del aviso con texto corto estilo gaming: 👍 TOP · 👎 FLOJA · 🔕 MENOS
import json as _ft_js

def _ft_botones(mk):
    """Devuelve el teclado con los textos acortados; si algo no cuadra, lo deja igual."""
    try:
        era_str = isinstance(mk, str)
        o = _ft_js.loads(mk) if era_str else mk
        kb = o.get("inline_keyboard") if isinstance(o, dict) else None
        if not kb:
            return mk
        textos = [b.get("text", "") for fila in kb for b in fila]
        if not (any(x.startswith("\U0001f44d") for x in textos) and any(x.startswith("\U0001f44e") for x in textos)):
            return mk
        cambio = False
        for fila in kb:
            for b in fila:
                x = b.get("text", "")
                n = None
                if x.startswith("\U0001f44d"):
                    n = "\U0001f44d TOP"
                elif x.startswith("\U0001f44e"):
                    n = "\U0001f44e FLOJA"
                elif x.startswith("\U0001f515") or x.startswith("\U0001f514") or "Menos" in x:
                    n = "\U0001f515 MENOS"
                if n and n != x:
                    b["text"] = n; cambio = True
        if not cambio:
            return mk
        return _ft_js.dumps(o, ensure_ascii=False) if era_str else o
    except Exception as e:
        print("error botones foto", e, flush=True)
        return mk

class _FtBt:
    def __init__(self, real):
        object.__setattr__(self, "_real", real)
    def __getattr__(self, n):
        return getattr(self._real, n)
    def post(self, url, *a, **k):
        try:
            dat = k.get("data")
            if isinstance(dat, dict) and dat.get("reply_markup") and str(url).split("/")[-1] in ("sendMessage", "sendPhoto", "editMessageReplyMarkup"):
                nuevo = _ft_botones(dat["reply_markup"])
                if nuevo is not dat["reply_markup"]:
                    k = dict(k); k["data"] = dict(dat, reply_markup=nuevo)
        except Exception as e:
            print("error botones foto", e, flush=True)
        return self._real.post(url, *a, **k)

requests = _FtBt(requests)

'''

n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
src = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), src, count=1, flags=re.M)
try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)
copia = RUTA + ".bak_foto5_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
