import re, shutil, time, sys, os

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/solradar/web/index.html"
src = open(RUTA, encoding="utf-8").read()
if 'id="grafico-auto"' in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if 'id="grafico-embed"' not in src:
    print("ABORTO: primero hay que aplicar parche_solradar_grafico2.py"); sys.exit(1)

BLOQUE = r"""<script id="grafico-auto">
(function () {
  function poner(card, h) {
    if (card.querySelector(".chartbox")) return;
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
  function revisar() {
    var cards = document.querySelectorAll("#radar .card");
    for (var i = 0; i < cards.length; i++) {
      var c = cards[i];
      if (c.getAttribute("data-gauto")) continue;
      var ls = c.querySelectorAll("a"), url = "";
      for (var j = 0; j < ls.length; j++) {
        if (/gr.fico/i.test(ls[j].textContent || "") && /^https?:\/\/dexscreener\.com\/solana\//i.test(ls[j].getAttribute("href") || "")) { url = ls[j].getAttribute("href"); break; }
      }
      if (!url) continue;
      c.setAttribute("data-gauto", "1");
      poner(c, url);
    }
  }
  new MutationObserver(revisar).observe(document.body, { childList: true, subtree: true });
  revisar();
})();
</script>
"""
if "</body>" in src:
    src = src.replace("</body>", BLOQUE + "</body>", 1)
else:
    src += "\n" + BLOQUE
copia = RUTA + ".bak_grafico3_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
print("Grafico automatico en Lanzamientos. Copia de seguridad:", copia)
print("No hace falta reiniciar. Cierra la app del todo y vuelve a abrirla.")
print("Para deshacerlo: cp", copia, RUTA)
