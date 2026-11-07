import re, sys, time, shutil
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- HIST90B ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- HIST90A ---" not in src:
    print("ABORTO: primero aplica parche_historial90_1.py"); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: anclaje final (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''# --- HIST90B ---
# Sello "OFERTA REAL / DUDOSA / PRECIO INFLADO" comparando el precio "antes" con el historial de 90 dias.
_h9b_pre = _cn_frame

def _h9b_veredicto(serie, antes, ahora):
    vals = sorted(v for v in serie if v is not None)
    if len(vals) < 10 or not antes:
        return None
    med = vals[len(vals) // 2]
    mn = min(vals + [ahora])
    if med < 0.70 * antes:
        return ("PRECIO ANTES INFLADO", (255, 150, 120), (80, 30, 24, 200), (255, 150, 120, 200))
    if ahora <= mn * 1.03 and med >= 0.80 * antes:
        return ("OFERTA REAL · MÍNIMO 90 DÍAS", (130, 255, 220), (20, 70, 60, 200), (120, 255, 214, 200))
    if med >= 0.80 * antes:
        return ("DESCUENTO REAL", (150, 255, 225), (20, 64, 62, 180), (120, 255, 214, 160))
    return ("OFERTA DUDOSA", (255, 214, 120), (70, 54, 16, 200), (255, 214, 120, 200))

def _cn_frame(dat, t=0.0, total=6.0, still=True):
    img = _h9b_pre(dat, t, total, still)
    try:
        it = getattr(_cn_loc, "item", None) or {}
        mm = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", str(it.get("u") or ""))
        asin = (mm.group(1) if mm else None) or getattr(_cn_loc, "asin", None)
        c = _h9_series.get(asin) if asin else None
        serie = c[1] if c else None
        if not serie:
            return img
        v = _h9b_veredicto(serie, float(dat["antes"]), float(dat["ahora"]))
        if not v:
            return img
        a = 1.0 if still else _cn_ease((t - 2.2) / 0.6)
        if a <= 0:
            return img
        base = img.convert("RGBA")
        _cn_pill(base, (72 + 236, 500 + 2), v[0], _cn_sans(16), v[1], v[3], v[2], pad=16, alpha=a)
        return base.convert("RGB")
    except Exception as ex:
        print("error hist90b", str(ex)[:100], flush=True)
        return img
'''
bak = RUTA + ".bak_hist90b_" + time.strftime("%Y%m%d_%H%M%S")
shutil.copy(RUTA, bak)
nuevo = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: BLOQUE + "\n" + m.group(0), src, count=1, flags=re.M)
try:
    compile(nuevo, RUTA, "exec")
except SyntaxError as e:
    print("ABORTO: error de sintaxis", e); sys.exit(1)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Aplicado. Reinicia con: sudo systemctl restart chivato")
print("Para deshacer: cp %s %s && sudo systemctl restart chivato" % (bak, RUTA))
