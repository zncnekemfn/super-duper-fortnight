import re, shutil, time, sys, os

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/solradar/web/index.html"
src = open(RUTA, encoding="utf-8").read()
if 'id="grafico-embed"' in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)

BLOQUE = r"""<style id="grafico-embed-css">
.chartbox{margin-top:10px;border-radius:12px;overflow:hidden;border:1px solid rgba(0,235,255,.4);box-shadow:0 0 14px rgba(0,235,255,.2)}
.chartbox iframe{display:block;width:100%;height:320px;border:0;background:#0b0620}
.chartbox .ext{display:block;text-align:center;padding:8px;font-size:13px;background:rgba(14,10,44,.95)}
</style>
<script id="grafico-embed">
(function () {
  function abrir(h) {
    try {
      if (window.Telegram && Telegram.WebApp && Telegram.WebApp.openLink) { Telegram.WebApp.openLink(h); return; }
    } catch (e) {}
    window.open(h, "_blank");
  }
  function alternar(a, h) {
    var card = a.closest(".card") || a.parentNode;
    var ya = card.querySelector(".chartbox");
    if (ya) { ya.remove(); return; }
    var box = document.createElement("div");
    box.className = "chartbox";
    var f = document.createElement("iframe");
    f.loading = "lazy";
    f.src = h + (h.indexOf("?") < 0 ? "?" : "&") + "embed=1&theme=dark&trades=0&info=0";
    var x = document.createElement("a");
    x.className = "ext"; x.href = h; x.textContent = "Abrir en DexScreener ↗";
    box.appendChild(f); box.appendChild(x);
    card.appendChild(box);
  }
  document.addEventListener("click", function (e) {
    var a = e.target.closest ? e.target.closest("a") : null;
    if (!a) return;
    var h = a.getAttribute("href") || "";
    if (!/^https?:\/\//i.test(h)) return;
    e.preventDefault();
    var esGrafico = /dexscreener\.com\/solana\//i.test(h) && /gr.fico/i.test(a.textContent || "") && !a.classList.contains("ext");
    if (esGrafico) alternar(a, h); else abrir(h);
  }, true);
})();
</script>
"""
if "</body>" in src:
    src = src.replace("</body>", BLOQUE + "</body>", 1)
elif "</html>" in src:
    src = src.replace("</html>", BLOQUE + "</html>", 1)
else:
    src += "\n" + BLOQUE
copia = RUTA + ".bak_grafico2_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Grafico dentro de la tarjeta y enlaces arreglados. Copia de seguridad:", copia)
print("No hace falta reiniciar. Cierra la app del todo y vuelve a abrirla.")
print("Para deshacerlo: cp", copia, RUTA)
