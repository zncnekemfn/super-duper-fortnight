import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- ALIHOT1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("# --- ALIAUTO2 ---", "def _aa_buscar(", "def _aa_admin(", "def _aa_estado(", "def _al_api(", "def _al_resultado("):
    if n not in src:
        print("ABORTO: falta", n, "(instala antes parche_ali_auto1 y parche_ali_auto2)"); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''
# --- ALIHOT1 ---
# Segunda fuente para /aliauto: productos calientes (hotproduct.query). Mismos filtros. /aliauto hot on|off
_aa_buscar_orig_hot = _aa_buscar
def _aa_buscar(c, kw, pagina="1"):
    res = _aa_buscar_orig_hot(c, kw, pagina)
    if not c.get("hot", True):
        return res
    try:
        pg = str(1 + (c.get("i", 0) % 3))
        j = _al_api("aliexpress.affiliate.hotproduct.query", {"keywords": kw, "page_size": "50", "page_no": pg,
                    "ship_to_country": "ES", "target_currency": "EUR", "target_language": "ES", "tracking_id": _al_trk()})
        ps = [_al_prod(p) for p in (((_al_resultado(j).get("products") or {}).get("product")) or [])]
        vistos = set(c["vistos"]) | set(p["id"] for p in res)
        extra = [p for p in ps if p["id"] and p["id"] not in vistos and _aa_ok(p, c)]
        print("aliauto hot", kw, "->", len(extra), "candidatas", flush=True)
        res = res + extra
    except Exception as e:
        print("error aliauto hot", str(e)[:80], flush=True)
    return res

_aa_estado_orig_hot = _aa_estado
def _aa_estado(c):
    return _aa_estado_orig_hot(c) + "\nProductos calientes: " + ("SÍ" if c.get("hot", True) else "NO") + "  (/aliauto hot on|off)"

_aa_admin_orig_hot = _aa_admin
def _aa_admin(d, cid, args):
    if len(args) > 1 and args[0].lower() == "hot" and args[1].lower() in ("on", "off"):
        c = _aa_cargar()
        c["hot"] = (args[1].lower() == "on")
        _aa_guardar(c)
        enviar(cid, _aa_estado(c))
        return
    return _aa_admin_orig_hot(d, cid, args)
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: error de sintaxis", e); sys.exit(1)
cp = RUTA + ".bak_alihot_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy2(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: /aliauto usa tambien productos calientes.")
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato   y luego /aliauto probar")
print("Apagar la fuente: /aliauto hot off")
print("Deshacer: cp %s %s && sudo systemctl restart chivato" % (cp, RUTA))
