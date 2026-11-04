import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- MENUORDEN2 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("def teclado_menu(", "# --- MENUORDEN1 ---", "# --- TIENDASBOTON1 ---", "# --- ADIVINA1 ---", "# --- TENDENCIAS1 ---"):
    if n not in src:
        print("ABORTO: no encuentro", n, "(instala antes ese parche)"); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''
# --- MENUORDEN2 ---
# Ultimos botones del menu en parejas y con icono propio:
# AliExpress + Tiendas, Tendencias + Adivina el precio, Ayuda + Actualizar.
_m2_tec_orig = teclado_menu

_M2_BOTONES = [("aliexpress", "\U0001f6d2"), ("tiendas", "\U0001f3ec"), ("tendencias", "\U0001f4c8"),
               ("adivina", "\U0001f3af"), ("ayuda", "❓"), ("actualizar", "\U0001f504")]

def teclado_menu():
    try:
        kb = json.loads(_m2_tec_orig())
        filas = kb["inline_keyboard"]
        piezas = {}; resto = []
        for f in filas:
            quedan = []
            for b in f:
                t = str(b.get("text", "")).lower()
                clave = None
                if not b.get("url"):
                    for k, _ in _M2_BOTONES:
                        if k in t:
                            clave = k; break
                if clave and clave not in piezas:
                    piezas[clave] = b
                else:
                    quedan.append(b)
            if quedan:
                resto.append(quedan)
        if not piezas:
            return json.dumps(kb)
        orden = []
        for k, ico in _M2_BOTONES:
            if k in piezas:
                b = dict(piezas[k])
                nombre = re.sub(r"^[^\w]+", "", str(b.get("text", ""))).strip()
                b["text"] = ico + " " + nombre
                orden.append(b)
        resto.extend(orden[i:i + 2] for i in range(0, len(orden), 2))
        kb["inline_keyboard"] = resto
        return json.dumps(kb)
    except Exception as e:
        print("error orden menu 2", str(e)[:80], flush=True)
        return _m2_tec_orig()
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_menuorden2_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy2(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Menu reordenado: botones finales en parejas y con icono.")
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato   y luego /menu")
print("Deshacer: cp %s %s && sudo systemctl restart chivato" % (cp, RUTA))
