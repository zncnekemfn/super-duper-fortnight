import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- MENUORDEN1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("def teclado_menu(", "# --- VENDEDOR1 ---", "# --- GRUPOBOTON1 ---"):
    if n not in src:
        print("ABORTO: no encuentro", n, "(aplica antes parche_vendedor1 y parche_grupo_boton1)"); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''
# --- MENUORDEN1 ---
# Ordena el menu: Segunda mano + Moda en una fila, Vendedor + grupo en otra (en vez de una fila por boton).
_mo_tec_orig = teclado_menu

def teclado_menu():
    try:
        kb = json.loads(_mo_tec_orig())
        filas = kb["inline_keyboard"]
        def clase(b):
            t = str(b.get("text", "")).lower(); cb = str(b.get("callback_data") or ""); u = str(b.get("url") or "")
            if "segunda mano" in t: return 0
            if "moda" in t or cb == "m_moda": return 1
            if cb == "m_vendedor": return 2
            if u.endswith("chivatoofertas"): return 3
            return None
        piezas = {}; resto = []
        for f in filas:
            if len(f) == 1 and clase(f[0]) is not None and clase(f[0]) not in piezas:
                piezas[clase(f[0])] = f[0]
            else:
                resto.append(f)
        if not piezas:
            return json.dumps(kb)
        orden = [piezas[k] for k in sorted(piezas)]
        nuevas = [orden[i:i + 2] for i in range(0, len(orden), 2)]
        pos = max(0, len(resto) - 1)
        resto[pos:pos] = nuevas
        kb["inline_keyboard"] = resto
        return json.dumps(kb)
    except Exception as e:
        print("error orden menu", e, flush=True)
        return _mo_tec_orig()
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_menuorden_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Menu reordenado. Copia:", cp)
print("Reinicia: sudo systemctl restart chivato   y luego /menu")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
