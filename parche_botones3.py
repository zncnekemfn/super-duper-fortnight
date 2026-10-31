import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- BOTONES3 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- BOTONES2 ---" not in src:
    print("ABORTO: primero hay que aplicar parche_botones2.py"); sys.exit(1)

TAIL = r'''# --- BOTONES3 ---
# Paleta simple: verde = acciones que traen ofertas, rojo = parar, azul = solo Propina, el resto sin color.
BT_MENU.update({
    "propina cafe": ("☕ Propina Café", "primary"),
    "ultimas": ("\U0001f525 Últimas ofertas", "success"),
    "suscribir": ("✅ Suscribirme", "success"),
    "parar": ("\U0001f515 Parar avisos", "danger"),
    "tablon": ("\U0001f4cc Tablón", None),
    "seguir": ("\U0001f514 Seguir", None),
    "descuento": ("\U0001f3af Descuento", None),
    "resumen": ("\U0001f5de️ Resumen", None),
    "invitar": ("\U0001f381 Invitar amigos", None),
    "anunciar": ("\U0001f4e2 Anunciar", None),
})
for _k in ("fb_up", "fb_dn", "fb_no"):
    BT_ESTILOS.pop(_k, None)

'''
n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
src = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), src, count=1, flags=re.M)
try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)
copia = RUTA + ".bak_botones3_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
