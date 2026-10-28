import sys
ruta = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
s = open(ruta, encoding="utf-8").read()
if "mins = int(args[1])" in s:
    print("Ya estaba aplicado.")
    sys.exit(0)

def cambiar(viejo, nuevo):
    global s
    if s.count(viejo) != 1:
        print("NO ENCONTRADO:", viejo[:70])
        sys.exit(1)
    s = s.replace(viejo, nuevo)

cambiar(r'''dias = int(args[1]) if len(args) > 1 and args[1].isdigit() else 7''',
        r'''mins = int(args[1]) if len(args) > 1 and args[1].isdigit() else 5''')
cambiar(r'''"exp": (time.time() + dias * 86400) if dias else 0''',
        r'''"exp": (time.time() + mins * 60) if mins else 0''')
cambiar(r'''cad = f"en {dias} días" if dias else "nunca"''',
        r'''cad = f"en {mins} minutos" if mins else "nunca"''')
cambiar(r'''time.strftime("%d/%m/%Y", time.localtime(v["exp"]))''',
        r'''time.strftime("%d/%m %H:%M", time.localtime(v["exp"]))''')

open(ruta, "w", encoding="utf-8").write(s)
print("Los códigos ahora duran 5 minutos por defecto")
