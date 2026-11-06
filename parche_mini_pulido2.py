import os, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
idx = os.path.join(os.path.dirname(os.path.abspath(RUTA)), "miniapp", "index.html")
if not os.path.exists(idx):
    print("ABORTO: no encuentro", idx); sys.exit(1)
h = open(idx, encoding="utf-8").read()
if "PULIDO2" in h:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
i = h.rfind("</style>")
if i < 0:
    print("ABORTO: estructura inesperada"); sys.exit(1)
CSS = ("/*PULIDO2*/.hb{background:rgba(13,10,9,.78)!important;border-radius:50%!important;width:40px;height:40px;"
       "display:flex;align-items:center;justify-content:center;line-height:1;z-index:2;top:26px!important;right:26px!important}"
       ".hb.on{color:#e8745c}")
bak = idx + ".bak_pulido2_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy2(idx, bak)
open(idx, "w", encoding="utf-8").write(h[:i] + CSS + h[i:])
print("OK: corazon legible sobre la foto")
print("Rollback: cp", bak, idx)
