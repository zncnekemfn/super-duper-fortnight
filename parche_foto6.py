import re, shutil, time, sys, os

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- FOTO6 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- FOTO2 ---" not in src:
    print("ABORTO: primero hay que aplicar parche_foto2.py"); sys.exit(1)

TAIL = r'''# --- FOTO6 ---
# /foto prueba -> te manda SOLO a ti un aviso de ejemplo con foto, texto y botones.
import json as _ft6_js

_comando_pre_ft6 = comando

def comando(d, cid, texto):
    p = str(texto or "").split()
    if len(p) > 1 and p[0].split("@")[0].lower() == "/foto" and p[1].lower() in ("prueba", "test") and str(cid) == str(ADMIN):
        msg = ("\U0001f525 ~-46%\nZapatillas running de ejemplo - 34.50 EUR\n"
               "\U0001f4ca \U0001f4c9 Mínimo de los últimos 90 días · Media 90 días: 63.89 EUR (46% menos)\n"
               "https://www.amazon.es/dp/B000000000\n\n"
               "(Como afiliado de Amazon obtengo ingresos por las compras adscritas.)")
        mk = _ft6_js.dumps({"inline_keyboard": [[
            {"text": "\U0001f44d", "callback_data": "ft_prueba"},
            {"text": "\U0001f44e", "callback_data": "ft_prueba"},
            {"text": "\U0001f515 Menos de esta categoría", "callback_data": "ft_prueba"}]]})
        enviar(cid, msg, mk)
        return
    return _comando_pre_ft6(d, cid, texto)

'''

n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
src = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), src, count=1, flags=re.M)
try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)
copia = RUTA + ".bak_foto6_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
