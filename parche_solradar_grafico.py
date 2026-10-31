import re, shutil, time, sys, os, subprocess

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/solradar/radar/launches.py"
src = open(RUTA, encoding="utf-8").read()
if "# GRAFICO1" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)

DEX = 'https://dexscreener.com/solana/'
# 1) enlace que se guarda en la senal (lo que ensena la app)
a_viejo = 'url=t.get("url"))'
a_nuevo = 'url=(t.get("url") or "%s" + str(c["mint"])))  # GRAFICO1' % DEX
if src.count(a_viejo) != 1:
    print("ABORTO: no encuentro el enlace de la senal (%d veces)" % src.count(a_viejo)); sys.exit(1)
src = src.replace(a_viejo, a_nuevo)

# 2) enlace del mensaje de Telegram
pat = re.compile(r'\+ \(f"\\n<a href=\\"\{t\[\'url\'\]\}\\">Ver gr.fico</a>" if t\.get\("url"\) else ""\)')
n = len(pat.findall(src))
if n != 1:
    print("ABORTO: no encuentro el enlace del mensaje de Telegram (%d veces)" % n); sys.exit(1)
nuevo = '+ ("\\n<a href=\\"" + (t.get("url") or "%s" + str(c["mint"])) + "\\">Ver gráfico</a>")' % DEX
src = pat.sub(lambda m: nuevo, src, count=1)

try:
    compile(src, "launches.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)
copia = RUTA + ".bak_grafico_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Parche aplicado. Copia de seguridad:", copia)
try:
    o = subprocess.run("systemctl list-unit-files --type=service --no-legend | grep -i radar", shell=True, capture_output=True, text=True).stdout.split()
    srv = [x for x in o if x.endswith(".service")]
    print("Reinicia con: systemctl restart " + (srv[0] if srv else "NOMBRE_DEL_SERVICIO"))
except Exception:
    print("Reinicia el servicio de SolRadar (systemctl restart ...)")
