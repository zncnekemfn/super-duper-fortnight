import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- BOTONES2 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- BOTONES ---" not in src:
    print("ABORTO: primero hay que aplicar parche_botones.py"); sys.exit(1)

TAIL = r'''# --- BOTONES2 ---
import unicodedata as _bt_ud
import re

# clave (texto original sin emojis ni acentos, en minusculas) -> (texto nuevo, color)
BT_MENU = {
    "propina cafe": ("☕ Propina Café", "primary"),
    "ultimas": ("\U0001f525 Últimas ofertas", "success"),
    "tablon": ("\U0001f4cc Tablón", "primary"),
    "seguir": ("\U0001f514 Seguir producto", "primary"),
    "categorias": ("\U0001f4c1 Categorías", None),
    "descuento": ("\U0001f3af Descuento mínimo", None),
    "no molestar": ("\U0001f319 No molestar", None),
    "resumen": ("\U0001f5de️ Resumen diario", None),
    "mi estado": ("\U0001f4ca Mi estado", None),
    "invitar": ("\U0001f381 Invitar amigos", "success"),
    "anunciar": ("\U0001f4e2 Anunciar", "primary"),
    "filtro": ("\U0001f50e Filtro", None),
    "contacto": ("\U0001f4ac Contacto", None),
    "suscribir": ("✅ Suscribirme", "success"),
    "parar": ("\U0001f515 Parar avisos", "danger"),
    "ayuda": ("❓ Ayuda", None),
    "actualizar": ("\U0001f504 Actualizar", None),
}

def _bt_clave(t):
    t = _bt_ud.normalize("NFD", str(t or "").lower())
    t = "".join(c for c in t if _bt_ud.category(c)[0] in "LZ" or c == " ")
    return re.sub(r"\s+", " ", "".join(c for c in t if not _bt_ud.combining(c))).strip()

_bt_boton_v1 = _bt_boton

def _bt_boton(b):
    b = _bt_boton_v1(b)
    try:
        if isinstance(b, dict) and not b.get("style") and not str(b.get("callback_data") or "").startswith(("vo_", "fb_")):
            ya = BT_MENU.get(_bt_clave(b.get("text")))
            if ya:
                b["text"] = ya[0]
                if ya[1] and _bt_estado.get("estilo"):
                    b["style"] = ya[1]
    except Exception as e:
        print("error botones2", e, flush=True)
    return b

'''
n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
src = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), src, count=1, flags=re.M)
try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)
copia = RUTA + ".bak_botones2_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
