import os, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
idx = os.path.join(os.path.dirname(os.path.abspath(RUTA)), "miniapp", "index.html")
if not os.path.exists(idx):
    print("ABORTO: no encuentro", idx); sys.exit(1)
h = open(idx, encoding="utf-8").read()
if "PULIDO1" in h:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
i = h.rfind("</style>")
j = h.lower().rfind("</body>")
if i < 0 or j < 0:
    print("ABORTO: estructura inesperada"); sys.exit(1)
CSS = ("/*PULIDO1*/"
 ".hero .tt{margin-top:58px!important;padding-right:0}"          # el -% ya no tapa el titulo
 ".hero .bg{top:16px}"
 ".card{padding:16px}.ph{height:124px;margin-bottom:10px}.ph img{max-height:112px}"
 ".two .btn{padding:11px 8px;font-size:14px}"                       # tarjetas mas compactas
 ".bar i{display:block;min-width:4px}"                              # la barra de descuento siempre se ve
 "#codigos-btn{bottom:calc(98px + env(safe-area-inset-bottom))!important;right:12px!important;padding:9px 14px!important;"
 "font-size:13px!important;transition:transform .3s,opacity .3s}"
 "#codigos-btn.oculto{transform:translateY(90px);opacity:0;pointer-events:none}")
JS = ("\n<!--PULIDO1-->\n<script>(function(){var b=document.getElementById('codigos-btn');if(!b)return;var y=0;"
      "window.addEventListener('scroll',function(){var n=window.scrollY||document.documentElement.scrollTop||0;"
      "if(n>y+6&&n>120)b.classList.add('oculto');else if(n<y-6)b.classList.remove('oculto');y=n},{passive:true})})();</script>\n")
bak = idx + ".bak_pulido1_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy2(idx, bak)
h = h[:i] + CSS + h[i:j] + JS + h[j:]
open(idx, "w", encoding="utf-8").write(h)
print("OK: mini app pulida (titulo/-%, tarjetas mas compactas, boton Codigos que se esconde al bajar)")
print("Rollback: cp", bak, idx)
