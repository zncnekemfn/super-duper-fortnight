import os, shutil, sys, time
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
idx = os.path.join(os.path.dirname(os.path.abspath(RUTA)), "miniapp", "index.html")
if not os.path.exists(idx):
    print("ABORTO: no encuentro", idx); sys.exit(1)
h = open(idx, encoding="utf-8").read()
if "FOTOSMINI1" in h:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "function card(o,i){" not in h or "</style>" not in h:
    print("ABORTO: no encuentro la función card o el estilo"); sys.exit(1)
CSS = "/*FOTOSMINI1*/.ph{display:flex;align-items:center;justify-content:center;height:140px;margin:0 0 12px;border-radius:14px;background:#fff;overflow:hidden}.ph img{max-width:100%;max-height:128px;object-fit:contain}.ph.no{display:none}</style>"
NEW = r"""/*FOTOSMINI1*/function card(o,i){var s=card0(o,i);try{if(o.asin){var a=String(o.asin).replace(/[^A-Za-z0-9]/g,"");s=s.replace(/(<div class="card"[^>]*>)/,'$1<div class="ph"><img loading="lazy" decoding="async" alt="" src="https://m.media-amazon.com/images/P/'+a+'.01._SCLZZZZZZZ_.jpg" onload="if(this.naturalWidth<20)this.parentNode.className=\'ph no\'" onerror="this.parentNode.className=\'ph no\'"></div>')}}catch(e){}return s}
function card0(o,i){"""
bak = idx + ".bak_fotosmini1_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy2(idx, bak)
h = h.replace("function card(o,i){", NEW, 1).replace("</style>", CSS, 1)
open(idx, "w", encoding="utf-8").write(h)
print("OK: fotos de producto en la mini app")
print("Rollback: cp", bak, idx)
