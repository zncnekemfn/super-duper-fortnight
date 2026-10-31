import re, shutil, time, sys, os

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/solradar/web/index.html"
src = open(RUTA, encoding="utf-8").read()
if 'id="neon-gaming"' in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "</head>" not in src:
    print("ABORTO: no encuentro </head> en la pagina"); sys.exit(1)

CSS = r"""<style id="neon-gaming">
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;800&family=Rajdhani:wght@500;600;700&display=swap');
:root{--bg:#07031a;--card:#0e0a2c;--text:#e8f6ff;--muted:#8f9ad6;--accent:#00ebff;--accent-text:#03101a;--green:#50ff96;--yellow:#ffd23f;--red:#ff325a;--mg:#ff28c8}
body{font-family:"Rajdhani",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;font-size:16px;
 background:linear-gradient(180deg,#07031a 0%,#12062e 70%,#1d0742 100%) fixed;min-height:100vh}
body::before{content:"";position:fixed;inset:0;pointer-events:none;z-index:0;opacity:.5;
 background-image:linear-gradient(rgba(255,40,200,.07) 1px,transparent 1px),linear-gradient(90deg,rgba(0,235,255,.06) 1px,transparent 1px);background-size:34px 34px}
body::after{content:"";position:fixed;inset:0;pointer-events:none;z-index:9;opacity:.12;
 background:repeating-linear-gradient(0deg,rgba(255,255,255,.5) 0 1px,transparent 1px 4px)}
header,main,nav{position:relative;z-index:1}
h1{font-family:"Orbitron",sans-serif;font-weight:800;letter-spacing:2px;color:#fff;text-shadow:0 0 6px #00ebff,0 0 18px rgba(0,235,255,.7)}
h1 span{color:var(--mg);text-shadow:0 0 6px var(--mg),0 0 18px rgba(255,40,200,.7)}
.sub{color:var(--muted)}
nav{background:rgba(7,3,26,.88);backdrop-filter:blur(6px);border-bottom:1px solid rgba(0,235,255,.25)}
nav button{background:rgba(14,10,44,.9);border:1px solid rgba(0,235,255,.35);color:#cfeaff;text-transform:uppercase;letter-spacing:.5px;font-family:inherit;font-weight:700;box-shadow:0 0 8px rgba(0,235,255,.15)}
nav button.on{background:linear-gradient(90deg,#00ebff,#ff28c8);color:#06020f;border-color:transparent;box-shadow:0 0 14px rgba(0,235,255,.6),0 0 22px rgba(255,40,200,.35)}
.card,.stat{background:linear-gradient(160deg,rgba(18,12,52,.95),rgba(10,6,34,.95));border:1px solid rgba(0,235,255,.35);box-shadow:0 0 12px rgba(0,235,255,.14),inset 0 0 18px rgba(255,40,200,.05)}
.stat{border-color:rgba(255,40,200,.4);box-shadow:0 0 12px rgba(255,40,200,.15)}
.stat b,.big,.x,.sym{font-family:"Orbitron",sans-serif;letter-spacing:.5px}
.stat b{text-shadow:0 0 8px currentColor}
h3{color:#fff;text-transform:uppercase;letter-spacing:1.5px;font-family:"Orbitron",sans-serif;font-size:14px;text-shadow:0 0 8px rgba(0,235,255,.8)}
.up{color:var(--green);text-shadow:0 0 8px rgba(80,255,150,.6)}.down{color:var(--red);text-shadow:0 0 8px rgba(255,50,90,.6)}
.pill{background:rgba(0,235,255,.12);border:1px solid rgba(0,235,255,.4)}
.vpill{border:1px solid currentColor;box-shadow:0 0 8px currentColor;letter-spacing:.5px}
.vp-VERDE{background:rgba(80,255,150,.14)}.vp-AMARILLO{background:rgba(255,210,63,.14)}
.VERDE{background:rgba(80,255,150,.14);border:1px solid var(--green);box-shadow:0 0 16px rgba(80,255,150,.35)}
.AMARILLO{background:rgba(255,210,63,.14);border:1px solid var(--yellow);box-shadow:0 0 16px rgba(255,210,63,.3)}
.ROJO{background:rgba(255,50,90,.14);border:1px solid var(--red);box-shadow:0 0 16px rgba(255,50,90,.35)}
.verdict{font-family:"Orbitron",sans-serif;letter-spacing:1px;text-shadow:0 0 10px currentColor}
input,textarea{background:rgba(8,5,30,.95);border:1px solid rgba(0,235,255,.4);color:#fff;font-family:inherit}
input:focus,textarea:focus{outline:none;border-color:var(--mg);box-shadow:0 0 12px rgba(255,40,200,.55)}
.btn{background:linear-gradient(90deg,#00ebff,#ff28c8);color:#06020f;text-transform:uppercase;letter-spacing:1px;font-family:inherit;font-weight:700;box-shadow:0 0 16px rgba(0,235,255,.5)}
a{color:var(--accent);text-shadow:0 0 6px rgba(0,235,255,.5)}
.check{border-bottom:1px solid rgba(0,235,255,.15)}
.summary{border-left:3px solid var(--mg)}
.gauge{box-shadow:0 0 10px rgba(0,235,255,.35)}
.msg,.disc,.meta{color:var(--muted)}
.av{box-shadow:0 0 0 2px rgba(0,235,255,.6),0 0 10px rgba(0,235,255,.5)}
</style>
"""
src = src.replace("</head>", CSS + "</head>", 1)
copia = RUTA + ".bak_neon_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Estilo neon-gaming aplicado. Copia de seguridad:", copia)
print("No hace falta reiniciar. Cierra la app del todo y vuelve a abrirla.")
print("Para deshacerlo: cp", copia, RUTA)
