import re, shutil, time, sys

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()

if "# --- REGION ANUNCIOS ---" in src:
    print("Ya estaba aplicado. No hago nada.")
    sys.exit(0)
if "# --- ANUNCIOS DE PAGO ---" not in src:
    print("ABORTO: primero hay que aplicar parche_anuncios_pago.py")
    sys.exit(1)

def unico(patron, fn, nombre):
    global src
    n = len(re.findall(patron, src, re.M))
    if n != 1:
        print("ABORTO: ancla '%s' encontrada %d veces" % (nombre, n))
        sys.exit(1)
    src = re.sub(patron, fn, src, count=1, flags=re.M)

def opcional(patron, nuevo, nombre):
    global src
    if len(re.findall(patron, src, re.M)) == 1:
        src = re.sub(patron, lambda m: nuevo, src, count=1, flags=re.M)
    else:
        print("(aviso: texto '%s' no encontrado, se deja como estaba)" % nombre)

FUNC = r'''# --- REGION ANUNCIOS ---
def enviar_anuncio(d, cid, ad, aid, etiqueta):
    reg = str(ad.get("region") or "").strip()
    if reg and "\U0001F4CD" not in etiqueta:
        etiqueta = (etiqueta + " · " if etiqueta.strip() else "") + "\U0001F4CD " + reg
    return _enviar_anuncio_orig(d, cid, ad, aid, etiqueta)

'''

# 1) el envio original se envuelve: todos los anuncios (tablon, difusion, admin) muestran la region
unico(r'^def enviar_anuncio\(d, cid, ad, aid, etiqueta\):$', lambda m: 'def _enviar_anuncio_orig(d, cid, ad, aid, etiqueta):', "enviar_anuncio")
unico(r'^def procesar_updates\(d\):\n', lambda m: FUNC + m.group(0), "procesar_updates")

# 2) en el flujo de pago, 4.o campo opcional = region
unico(r'^    pk = sel\["pk"\]\n',
      lambda m: (m.group(0) +
                 '    _partes = [x.strip() for x in " ".join(args).split("|")]\n'
                 '    if len(_partes) > 3 and _partes[3]:\n'
                 '        dat["region"] = _partes[3][:30]\n'), "pk")

# 3) textos de ayuda (opcionales)
opcional(r'Para a\\u00f1adir una foto, escribe el comando en el pie de la foto\.\\n"',
         'Para a\\u00f1adir una foto, escribe el comando en el pie de la foto.\\n"\n'
         '            "Opcional: a\\u00f1ade al final | regi\\u00f3n (por ejemplo | Valencia) y tu anuncio mostrar\\u00e1 \\U0001F4CD Valencia.\\n"',
         "instrucciones")

try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)

copia = RUTA + ".bak_region_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
