import re, shutil, time, sys, os

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/solradar/web/index.html"
ALTO = 240   # alto del grafico en pixeles (antes 320)
src = open(RUTA, encoding="utf-8").read()
if 'id="grafico-alto"' in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if 'id="grafico-embed"' not in src:
    print("ABORTO: primero hay que aplicar parche_solradar_grafico2.py"); sys.exit(1)

BLOQUE = '<style id="grafico-alto">.chartbox iframe{height:%dpx !important}</style>\n' % ALTO
if "</body>" in src:
    src = src.replace("</body>", BLOQUE + "</body>", 1)
else:
    src += "\n" + BLOQUE
copia = RUTA + ".bak_grafico4_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Grafico mas bajo (%d px). Copia de seguridad: %s" % (ALTO, copia))
print("No hace falta reiniciar. Cierra la app del todo y vuelve a abrirla.")
print("Para deshacerlo: cp", copia, RUTA)
