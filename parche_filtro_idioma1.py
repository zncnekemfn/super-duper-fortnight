import re, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
MARCA = "# --- FILTROIDIOMA1 ---"
src = open(RUTA, encoding="utf-8").read()
if MARCA in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
for n in ("def enviar_aviso(",):
    if n not in src:
        print("ABORTO: falta", n); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', src))
if len(anc) != 1:
    print("ABORTO: punto de entrada (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''
# --- FILTROIDIOMA1 ---
# No se avisa de: (1) libros (codigo de producto tipo ISBN, solo numeros) y (2) titulos claramente en otro idioma.
_FI_ES = set("el los las del y con para por una unos unas al que más mas sin su se es".split())
_FI_EXT = {
    "fr": set("le des du et les pour avec dans une est sur au aux thèse these présentée presentee soutenue faculté faculte".split()),
    "en": set("the and with for of your you is are from by in to".split()),
    "de": set("der die das und mit für fur von zum ein eine nicht".split()),
    "it": set("il per della gli che sono nel dei delle".split()),
    "pt": set("uma não nao com do da pelo dos".split()),
}

def _fi_es_libro(asin):
    return bool(re.match(r"^\d{9}[\dX]$", asin or ""))

def _fi_otro_idioma(titulo):
    pal = re.findall(r"[a-záéíóúüñàèêçßäöû]+", str(titulo).lower())
    if len(pal) < 4:
        return False
    es = sum(1 for p in pal if p in _FI_ES)
    mejor = max(sum(1 for p in pal if p in conj) for conj in _FI_EXT.values())
    return (mejor >= 2 and es == 0) or (mejor >= 4 and es <= 1)

_fi_aviso_orig = enviar_aviso
def enviar_aviso(d, cid, item):
    try:
        mm = re.search(r"/dp/([A-Z0-9]{10})", str(item.get("u") or ""))
        asin = mm.group(1) if mm else ""
        titulo = re.sub(r"\s+-\s*[\d.,]+\s*EUR\s*$", "", str(item.get("t") or ""))
        if _fi_es_libro(asin) or _fi_otro_idioma(titulo):
            if d.get("fi_ult") != (asin, titulo[:30]):
                d["fi_ult"] = (asin, titulo[:30])
                print("filtro: descartado (libro o idioma)", asin, titulo[:50], flush=True)
            return
    except Exception as e:
        print("error filtro idioma", str(e)[:80], flush=True)
    return _fi_aviso_orig(d, cid, item)
'''
nuevo = src[:anc[0].start()] + BLOQUE + "\n" + src[anc[0].start():]
try: compile(nuevo, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: no compila:", e); sys.exit(1)
cp = RUTA + ".bak_filtroidioma_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, cp)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado: no se avisa de libros ni de titulos en otro idioma.")
print("Copia:", cp)
print("Reinicia: sudo systemctl restart chivato   y luego /autotest")
print("Deshacer: cp", cp, RUTA, "&& sudo systemctl restart chivato")
