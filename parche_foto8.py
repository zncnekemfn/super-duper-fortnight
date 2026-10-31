import re, shutil, time, sys, os

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- MENU8 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- MENU7 ---" not in src:
    print("ABORTO: primero hay que aplicar parche_foto7.py"); sys.exit(1)

NUEVO = r'''_M7_NOMBRES = {  # --- MENU8 ---
    "propina cafe": "☕ Propina Café",
    "ultimas ofertas": "⚡ Últimas ofertas",
    "tablon": "\U0001f579 Tablón",
    "seguir": "\U0001f3af Seguir",
    "categorias": "\U0001f4a0 Categorías",
    "descuento": "\U0001f4a5 Descuento",
    "no molestar": "\U0001f319 Silencio",
    "resumen": "\U0001f4e1 Resumen",
    "mi estado": "\U0001f3ae Mi estado",
    "invitar amigos": "\U0001f381 Invitar amigos",
    "anunciar": "\U0001f4e2 Anunciar",
    "filtro": "\U0001f39b Filtro",
    "contacto": "\U0001f4ac Contacto",
    "suscribirme": "\U0001f7e2 Suscribirme",
    "parar avisos": "\U0001f534 Parar avisos",
    "ayuda": "\U0001f579 Ayuda",
    "actualizar": "\U0001f501 Actualizar",
}'''
src, n = re.subn(r"_M7_NOMBRES = \{.*?\n\}", lambda m: NUEVO, src, count=1, flags=re.S)
if n != 1:
    print("ABORTO: no encuentro la lista del menu"); sys.exit(1)
try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)
copia = RUTA + ".bak_menu8_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
