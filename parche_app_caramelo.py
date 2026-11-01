import os, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
idx = os.path.join(os.path.dirname(os.path.abspath(RUTA)), "miniapp", "index.html")
if not os.path.exists(idx):
    print("ABORTO: no encuentro", idx); sys.exit(1)
h = open(idx, encoding="utf-8").read()
if "/*CARAMELO*/" in h:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "</style></head>" not in h:
    print("ABORTO: no encuentro el final del estilo"); sys.exit(1)
CSS = """/*CARAMELO*/
:root{--bg:#0d0a09;--bg2:#0d0a09;--card:#14100e;--card2:#14100e;--cy:#ecaa62;--mg:#ecaa62;--vd:#f3c58a;--rj:#e8745c;--mut:#a59b94;--tx:#fff;--line:#3e322c;--glow:none}
body{background:radial-gradient(120% 55% at 75% 0%,rgba(236,170,98,.14),transparent 62%),#0d0a09;font:500 16px/1.4 Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
body:before,body:after{display:none!important}
h1{font:800 25px/1.1 Playfair Display,Georgia,serif;letter-spacing:0;text-shadow:none;animation:none}
h1 span{color:var(--cy);text-shadow:none}
.live{font:500 12.5px ui-monospace,Menlo,Consolas,monospace;letter-spacing:1px}
.dot{background:var(--cy);box-shadow:none}
.gear{background:var(--card);border:1px solid #3e322c;color:#d9cec6;box-shadow:none;border-radius:14px}
.tabs{background:rgba(20,16,14,.95);border:1px solid #3e322c;box-shadow:none;border-radius:30px}
.tabs button{font:600 10px ui-monospace,Menlo,Consolas,monospace;letter-spacing:1px;color:#b9aea6}
.tabs button.on{color:var(--cy);background:rgba(236,170,98,.12);box-shadow:inset 0 0 0 1px rgba(236,170,98,.5);text-shadow:none;border-radius:24px}
.chip{background:var(--card);border:1px solid #3e322c;border-radius:20px;font:600 14px Inter,system-ui;letter-spacing:0;padding:7px 15px}
.chip.on{background:var(--cy);border-color:var(--cy);color:#1a0f06;box-shadow:none}
input.q,select.q{background:var(--card);border:1px solid #3e322c;border-radius:18px;font:500 16px Inter,system-ui;padding:13px 16px}
input.q:focus,select.q:focus{border-color:var(--cy);box-shadow:none}
.hero{background:radial-gradient(90% 70% at 72% 0%,rgba(236,170,98,.24),transparent 70%),#14100e;border:1px solid #3e322c;box-shadow:none;border-radius:28px;padding:22px}
.hero small{font:600 11px ui-monospace,Menlo,Consolas,monospace;color:var(--cy);text-shadow:none;letter-spacing:1.4px}
.hero .tt{font:700 19px Inter,system-ui}
.hero .big{font:800 42px Playfair Display,Georgia,serif;color:#fff;text-shadow:none;letter-spacing:-.5px}
.hero .big s{font:500 16px Inter,system-ui;color:var(--mut)}
.hero .bg{font:800 20px Inter,system-ui;color:var(--cy);text-shadow:none;border:1.5px solid var(--cy);border-radius:999px;padding:5px 13px;background:rgba(13,10,9,.7);top:44px;right:16px}
.hero .btn{background:var(--cy);color:#1a0f06;box-shadow:none}
.card{background:var(--card);border:1px solid #3e322c;border-radius:26px;box-shadow:none;padding:18px}
.tt{font:700 17px/1.25 Inter,system-ui}
.now{font:800 31px Playfair Display,Georgia,serif;color:#fff;text-shadow:none;letter-spacing:-.5px}
.old{font:500 16px Inter,system-ui;text-decoration-color:#8a7d74}
.pct{background:rgba(236,170,98,.12);border:1.5px solid var(--cy);color:var(--cy);box-shadow:none;text-shadow:none;font:800 16px Inter,system-ui;border-radius:999px;padding:5px 13px}
.bar{background:repeating-linear-gradient(90deg,rgba(255,255,255,.07) 0 8px,transparent 8px 11px)}
.bar i{background:linear-gradient(90deg,#9a6330,var(--cy));box-shadow:none}
.tag{font:600 11px ui-monospace,Menlo,Consolas,monospace;border-radius:999px;border:1px solid #4a3c35;background:transparent;color:#b9aea6;letter-spacing:.6px;padding:3px 10px}
.tag.hot{background:rgba(232,116,92,.12);border-color:#e8745c;color:#f2a592;box-shadow:none}
.tag.new{background:rgba(236,170,98,.12);border-color:var(--cy);color:var(--cy);box-shadow:none;animation:none}
.sv{color:var(--cy);font-weight:700}
.btn{background:var(--cy);color:#1a0f06;border-radius:999px;font:800 15px Inter,system-ui;letter-spacing:1px;box-shadow:none;text-shadow:none;padding:14px}
.btn.sec{background:transparent;color:#f3ebe4;border:1px solid #6b5648;box-shadow:none;text-shadow:none}
.hb{color:#9d9189}.hb.on{color:var(--cy);text-shadow:none}
.legal{color:#7d726b}
.st{background:var(--card);border:1px solid #3e322c;box-shadow:none;border-radius:22px;padding:16px}
.st b{font:800 32px Playfair Display,Georgia,serif;color:#fff;text-shadow:none}
.sw{background:var(--card);border:1px solid #3e322c;border-radius:20px}
.sw button{border:1px solid #6b5648;background:#241c18}
.sw button.on{background:rgba(236,170,98,.28);border-color:var(--cy);box-shadow:none}
.sw button.on:after{background:var(--cy);box-shadow:none}
.al{background:var(--card);border:1px solid #3e322c;border-radius:20px}
.al button{color:#e8745c;text-shadow:none}
h2{font:600 13px ui-monospace,Menlo,Consolas,monospace;color:var(--cy);text-shadow:none;letter-spacing:1.6px}
.sk{border:1px solid #2a211c;background:linear-gradient(100deg,rgba(236,170,98,.03) 30%,rgba(236,170,98,.12) 50%,rgba(236,170,98,.03) 70%);background-size:300% 100%}
.vbox{border:1px solid #3e322c;box-shadow:none;border-radius:26px}
.vbox .pc{background:rgba(13,10,9,.78);border:1.5px solid var(--cy);color:var(--cy);box-shadow:none;font:800 15px Inter,system-ui;border-radius:999px}
"""
CSS = CSS.replace("\n", "")
h2 = h.replace("family=Rajdhani:wght@500;600;700&family=Orbitron:wght@700;900", "family=Inter:wght@500;600;700;800&family=Playfair+Display:wght@700;800")
h2 = h2.replace("</style></head>", CSS + "</style></head>", 1)
h2 = h2.replace("#05030f", "#0d0a09")
shutil.copy(idx, idx + ".bak_caramelo_" + time.strftime("%Y%m%d%H%M%S"))
open(idx, "w", encoding="utf-8").write(h2)
print("Mini-app en caramelo aplicada en", idx)
print("No hace falta reiniciar. Cierra la app del todo y vuelve a abrirla.")
