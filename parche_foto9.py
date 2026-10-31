import re, shutil, time, sys, os

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- MENU9 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if not re.search(r"^BT_MENU = \{", src, re.M):
    print("ABORTO: no encuentro BT_MENU en el bot"); sys.exit(1)

TAIL = r'''# --- MENU9 ---
# Nombres neon-gaming en la lista de botones del propio bot (se conservan los colores).
_M9_NOMBRES = {
    "propina cafe": "☕ Propina Café",
    "ultimas": "⚡ Últimas ofertas",
    "tablon": "\U0001f579 Tablón",
    "seguir": "\U0001f3af Seguir",
    "categorias": "\U0001f4a0 Categorías",
    "descuento": "\U0001f4a5 Descuento",
    "no molestar": "\U0001f319 Silencio",
    "resumen": "\U0001f4e1 Resumen",
    "mi estado": "\U0001f3ae Mi estado",
    "invitar": "\U0001f381 Invitar amigos",
    "anunciar": "\U0001f4e2 Anunciar",
    "filtro": "\U0001f39b Filtro",
    "contacto": "\U0001f4ac Contacto",
    "suscribir": "\U0001f7e2 Suscribirme",
    "parar": "\U0001f534 Parar avisos",
    "ayuda": "\U0001f579 Ayuda",
    "actualizar": "\U0001f501 Actualizar",
}
for _k9, _t9 in _M9_NOMBRES.items():
    try:
        if _k9 in BT_MENU:
            BT_MENU[_k9] = (_t9, BT_MENU[_k9][1])
    except Exception as _e9:
        print("error menu9", _e9, flush=True)

'''

n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
src = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), src, count=1, flags=re.M)
try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)
copia = RUTA + ".bak_menu9_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
