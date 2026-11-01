import shutil, sys, time

# Parche SolRadar: tema caramelo + barra de pestañas abajo + tira de mercado + cajitas de datos.
# Uso:  python3 parche_caramelo.py          -> aplica (o actualiza) el tema
#       python3 parche_caramelo.py quitar   -> vuelve al aspecto anterior
args = [a for a in sys.argv[1:] if a != "quitar"]
RUTA = args[0] if args else "/opt/solradar/web/index.html"
INI, FIN = "<!-- SR CARAMELO INICIO -->", "<!-- SR CARAMELO FIN -->"
BLOQUE = INI + "\n" + r"""<style id="sr-caramelo">
/* SOLRADAR TEMA CARAMELO */
:root{--bg:#e8cba5;--card:#fbf1e3;--card2:#f1ddc3;--line:#dcbb92;--text:#3b2414;--muted:#8a6648;
  --accent:#b8692a;--accent2:#e0a15a;--accent-text:#ffffff;--green:#1e9b55;--yellow:#a86b00;--red:#d43f3f;--mg:#b8692a}
html,body{background:linear-gradient(180deg,#deb98a 0,#e6c69e 260px,#ebd1b0 100%) fixed!important;color:var(--text)!important}
body{font-family:"Segoe UI",Roboto,system-ui,-apple-system,sans-serif!important;font-size:15px!important}
body::before,body::after{display:none!important;content:none!important}
*{text-shadow:none!important}
header{background:transparent!important;border:0!important;box-shadow:none!important}
h1{color:var(--text)!important;letter-spacing:-.01em!important;font-weight:700!important}
h1 span{color:var(--accent)!important;background:none!important;-webkit-text-fill-color:var(--accent)!important}
.sub,.meta,.disc,small{color:var(--muted)!important}
h3{color:var(--text)!important}
a{color:var(--accent)!important}
main{padding-bottom:110px!important}
.card,.stat,.summary,.msg{background:var(--card)!important;border:1px solid var(--line)!important;border-radius:18px!important;
  box-shadow:0 2px 10px #b8692a14!important;color:var(--text)!important;backdrop-filter:none!important}
.stat b,.big,.x,.sym{color:var(--text)!important}
.up{color:var(--green)!important}.down{color:var(--red)!important}
.err{color:var(--red)!important}
.pill,.vpill{background:var(--card2)!important;color:var(--accent)!important;border:0!important;box-shadow:none!important}
.VERDE,.vp-VERDE{color:var(--green)!important;background:#e3f3e7!important;border-color:transparent!important;box-shadow:none!important}
.AMARILLO,.vp-AMARILLO{color:var(--yellow)!important;background:#fbe9c4!important;border-color:transparent!important;box-shadow:none!important}
.ROJO,.vp-ROJO{color:var(--red)!important;background:#fbe0dd!important;border-color:transparent!important;box-shadow:none!important}
.verdict{border-radius:14px!important;box-shadow:none!important}
.check{border-color:var(--line)!important}
.gauge{background:linear-gradient(90deg,#d43f3f,#e0a15a,#1e9b55)!important}
.gauge i{background:var(--text)!important;box-shadow:none!important}
input,textarea{background:#fffaf2!important;color:var(--text)!important;border:1px solid var(--line)!important;border-radius:12px!important;box-shadow:none!important}
input:focus,textarea:focus{outline:2px solid var(--accent)!important;outline-offset:1px}
.btn{background:var(--accent)!important;color:#fff!important;border:0!important;border-radius:12px!important;box-shadow:none!important}
.btn:disabled{opacity:.5}
.av,.avimg{border-radius:14px!important}
.lines li{color:var(--text)!important}
/* barra de pestañas abajo */
nav{position:fixed!important;left:12px!important;right:12px!important;bottom:calc(12px + env(safe-area-inset-bottom))!important;top:auto!important;z-index:50!important;
  display:flex!important;justify-content:space-around!important;align-items:center!important;gap:0!important;margin:0!important;
  background:#fbf1e3f2!important;border:1px solid var(--line)!important;border-radius:22px!important;padding:8px 6px!important;
  box-shadow:0 6px 24px #6b3d1a26!important;overflow:visible!important}
nav button{flex:1!important;display:flex!important;flex-direction:column!important;align-items:center!important;gap:2px!important;
  background:none!important;border:0!important;box-shadow:none!important;color:var(--muted)!important;font:500 11.5px "Segoe UI",Roboto,system-ui,sans-serif!important;
  padding:2px 0!important;min-width:0!important;border-radius:12px!important}
nav button::before{font-size:20px;line-height:1.1}
nav button[data-tab=calls]::before{content:"📣"}nav button[data-tab=radar]::before{content:"📡"}
nav button[data-tab=market]::before{content:"📊"}nav button[data-tab=scan]::before{content:"🛡️"}
nav button.on{color:var(--accent)!important;font-weight:700!important}
nav button[data-tab=calls]{order:1}nav button[data-tab=radar]{order:2}nav button[data-tab=new]{order:3}
nav button[data-tab=market]{order:4}nav button[data-tab=scan]{order:5}
nav button[data-tab=new]:not([hidden]){flex:0 0 54px!important;height:54px!important;margin-top:-30px!important;border-radius:17px!important;
  background:linear-gradient(135deg,var(--accent),var(--accent2))!important;color:#fff!important;font-size:0!important;box-shadow:0 8px 20px #b8692a55!important}
nav button[data-tab=new]:not([hidden])::before{content:"+";font-size:30px;font-weight:600;color:#fff;line-height:1}
nav button[hidden]{display:none!important}
/* tira de mercado */
.crm-tk{display:flex;gap:8px;margin:6px 0 10px}
.crm-tk div{flex:1;min-width:0;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:8px 10px}
.crm-tk span{display:block;color:var(--muted);font-size:11px}
.crm-tk b{font-size:15px;color:var(--text)}.crm-tk i{font-style:normal;font-size:12px;margin-left:4px}
/* datos en cajitas */
.crm-kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-top:10px}
.crm-kpis div{background:var(--card2);border-radius:10px;padding:6px 8px;min-width:0}
.crm-kpis span{display:block;font-size:10.5px;color:var(--muted)}.crm-kpis b{font-size:13px;color:var(--text);white-space:nowrap}
.crm-extra{font-size:12px;color:var(--muted);margin-top:6px}
/* gráficas de Lanzamientos en claro */
.srg-hint{color:var(--accent)!important}.srg-load,.srg-src{color:var(--muted)!important}.srg-px{color:var(--text)!important}
.srg-tf button{background:var(--card2)!important;color:var(--muted)!important}.srg-tf button.on{background:var(--accent)!important;color:#fff!important}
.srg-btns button{background:var(--card2)!important;color:var(--text)!important}.srg-btns .srg-p{background:var(--accent)!important;color:#fff!important}
.srg-c line{stroke:#ead7bd!important}
</style>
<script>
/* SOLRADAR TEMA CARAMELO JS */
(function () {
  var tg = window.Telegram && window.Telegram.WebApp;
  try { if (tg) { tg.setHeaderColor && tg.setHeaderColor("#deb98a"); tg.setBackgroundColor && tg.setBackgroundColor("#e8cba5");
    tg.setBottomBarColor && tg.setBottomBarColor("#ebd1b0"); } } catch (e) {}
  function n(x, d) { return x == null ? "–" : Number(x).toLocaleString("es-ES", { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 }); }
  function corto(x) { return x >= 1e3 ? "$" + (x / 1e3).toLocaleString("es-ES", { maximumFractionDigits: 1 }) + "K" : "$" + n(x); }
  function pct(v) { if (v == null) return ""; var c = v >= 0 ? "var(--green)" : "var(--red)"; return '<i style="color:' + c + '">' + (v >= 0 ? "+" : "−") + n(Math.abs(v), 1) + "%</i>"; }
  // Tira de mercado bajo la cabecera
  function tira() {
    var h = document.querySelector("header"); if (!h || document.querySelector(".crm-tk")) return;
    var d = document.createElement("div"); d.className = "crm-tk"; d.hidden = true; h.insertAdjacentElement("afterend", d);
    var demo = /[?&]demo/.test(location.search);
    if (demo || !tg || !tg.initData) return;
    fetch("/api/market", { headers: { "X-Init-Data": tg.initData } }).then(function (r) { return r.json(); }).then(function (r) {
      if (!r || r.error) return;
      var b = r.btc || {}, f = r.fng, g = r.global || {}, html = "";
      if (b.price) html += '<div><span>BTC</span><b>' + corto(b.price) + "</b>" + pct(b.chg_1d) + "</div>";
      if (f && f.value != null) html += '<div><span>Miedo/Codicia</span><b>' + f.value + '</b><i style="color:var(--yellow)">' + (f.label || "") + "</i></div>";
      if (g.btc_dominance != null) html += '<div><span>Dominancia BTC</span><b>' + n(g.btc_dominance, 1) + "%</b></div>";
      if (html) { d.innerHTML = html; d.hidden = false; }
    }).catch(function () {});
  }
  // "MC $1,1M · Liq $91,0K · Vol 1 h $94,7K · 19,8 h · gráfico" -> cajitas
  function cajitas() {
    [].forEach.call(document.querySelectorAll(".meta:not([data-crm])"), function (m) {
      var t = m.textContent || "";
      var mc = t.match(/MC\s*(\$[\d.,]+\s*[KMB]?)/i), lq = t.match(/Liq\s*(\$[\d.,]+\s*[KMB]?)/i), vo = t.match(/Vol\s*1\s*h\s*(\$[\d.,]+\s*[KMB]?)/i);
      if (!mc || !lq) return;
      m.setAttribute("data-crm", "1");
      var link = m.querySelector("a");
      var resto = t.replace(/MC\s*\$[\d.,]+\s*[KMB]?/i, "").replace(/Liq\s*\$[\d.,]+\s*[KMB]?/i, "").replace(/Vol\s*1\s*h\s*\$[\d.,]+\s*[KMB]?/i, "")
                   .replace(/gr[aá]fico/i, "").split("·").map(function (s) { return s.trim(); }).filter(Boolean).join(" · ");
      var k = document.createElement("div"); k.className = "crm-kpis";
      k.innerHTML = '<div><span>Market cap</span><b>' + mc[1] + '</b></div><div><span>Liquidez</span><b>' + lq[1] + '</b></div>' +
                    '<div><span>Vol. 1 h</span><b>' + (vo ? vo[1] : "–") + "</b></div>";
      var ex = document.createElement("div"); ex.className = "crm-extra"; ex.textContent = resto ? resto + (link ? " · " : "") : "";
      if (link) ex.appendChild(link);
      m.style.display = "none";
      m.parentNode.insertBefore(k, m.nextSibling); k.insertAdjacentElement("afterend", ex);
      if (!ex.textContent.trim()) ex.remove();
    });
  }
  var pend = false;
  function orden() { // mini gráfica encima de las cajitas
    [].forEach.call(document.querySelectorAll(".crm-kpis"), function (k) {
      var z = k.parentNode && k.parentNode.querySelector(":scope > .srg");
      if (z && (k.compareDocumentPosition(z) & Node.DOCUMENT_POSITION_FOLLOWING)) k.parentNode.insertBefore(z, k);
    });
  }
  function todo() { pend = false; try { tira(); cajitas(); orden(); } catch (e) { console.log("caramelo", e); } }
  new MutationObserver(function () { if (!pend) { pend = true; setTimeout(todo, 120); } }).observe(document.body, { childList: true, subtree: true });
  todo();
})();
</script>
""" + "\n" + FIN + "\n"

s = open(RUTA, encoding="utf-8").read()
i = s.find(INI)
if i >= 0:
    j = s.find(FIN, i)
    s = s[:i] + s[j + len(FIN):].lstrip("\n")
if "quitar" in sys.argv:
    shutil.copy2(RUTA, RUTA + ".bak_caramelo_" + time.strftime("%Y%m%d%H%M%S"))
    open(RUTA, "w", encoding="utf-8").write(s)
    print("Tema caramelo quitado. Cierra SolRadar y vuelve a abrirlo.")
    sys.exit(0)
pos = s.lower().rfind("</body>")
nuevo = s[:pos] + BLOQUE + s[pos:] if pos >= 0 else s + "\n" + BLOQUE
bak = RUTA + ".bak_caramelo_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy2(RUTA, bak)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Tema caramelo aplicado. Copia de seguridad: " + bak)
print("Cierra SolRadar del todo en Telegram y vuelve a abrirlo.")
print("Para volver al aspecto anterior: python3 parche_caramelo.py quitar")
