import shutil, sys, time

# Parche SolRadar: tarjeta "Previsión IA de BTC · 24 h" (Kronos) en la pestaña Mercado.
# Uso:  python3 parche_prevision.py          -> aplica (o actualiza)
#       python3 parche_prevision.py quitar   -> la quita
args = [a for a in sys.argv[1:] if a != "quitar"]
RUTA = args[0] if args else "/opt/solradar/web/index.html"
INI, FIN = "<!-- SR KRONOS INICIO -->", "<!-- SR KRONOS FIN -->"
BLOQUE = INI + "\n" + r"""<style id="sr-kronos">
/* SOLRADAR PREVISION KRONOS */
.krn{margin-top:12px}
.krn-h{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.krn-h b{font-size:16px}
.krn-tag{font-size:11px;font-weight:700;padding:2px 8px;border-radius:999px;background:var(--card2,#f1ddc3);color:var(--accent,#b8692a)}
.krn-big{font-size:24px;font-weight:800;margin-top:6px;color:var(--text,#3b2414)}
.krn-big i{font-style:normal;font-size:15px;margin-left:6px}
.krn-sub{font-size:13px;color:var(--muted,#8a6648)}
.krn svg{display:block;width:100%;height:170px;margin-top:8px}
.krn-ley{display:flex;gap:14px;font-size:12px;color:var(--muted,#8a6648);margin-top:4px;flex-wrap:wrap}
.krn-ley span{display:flex;align-items:center;gap:5px}
.krn-ley i{display:inline-block;width:14px;height:3px;border-radius:2px}
.krn-ac{display:grid;grid-template-columns:repeat(2,1fr);gap:6px;margin-top:10px}
.krn-ac div{background:var(--card2,#f1ddc3);border-radius:10px;padding:7px 9px}
.krn-ac span{display:block;font-size:10.5px;color:var(--muted,#8a6648)}.krn-ac b{font-size:14px;color:var(--text,#3b2414)}
.krn-aviso{font-size:11.5px;color:var(--muted,#8a6648);margin-top:8px;line-height:1.4}
</style>
<script>
/* SOLRADAR PREVISION KRONOS JS */
(function () {
  var URLS = ["https://raw.githubusercontent.com/zncnekemfn/super-duper-fortnight/main/kronos/btc.json",
              "https://api.github.com/repos/zncnekemfn/super-duper-fortnight/contents/kronos/btc.json"];
  var datos = null, cargando = false, ult = 0;
  function n(x, d) { return Number(x).toLocaleString("es-ES", { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 }); }
  function cargar() {
    if (cargando || (datos && Date.now() - ult < 10 * 60e3)) return; cargando = true;
    var intento = function (i) {
      if (i >= URLS.length) { cargando = false; return; }
      fetch(URLS[i] + (i === 0 ? "?t=" + Math.floor(Date.now() / 300000) : ""), { headers: i ? { Accept: "application/vnd.github.raw" } : {} })
        .then(function (r) { if (!r.ok) throw 0; return r.json(); })
        .then(function (j) { datos = j; ult = Date.now(); cargando = false; pintar(); })
        .catch(function () { intento(i + 1); });
    };
    intento(0);
  }
  function grafica(d) {
    var W = 340, H = 170, L = 6, R = 6, T = 10, B = 18;
    var pas = d.pasado || [], pr = d.prevision || [];
    if (pas.length < 2 || !pr.length) return "";
    var xs = pas.map(function (p) { return p[0]; }).concat(pr.map(function (p) { return p[0]; }));
    var ys = pas.map(function (p) { return p[1]; }).concat(pr.map(function (p) { return p[2]; }), pr.map(function (p) { return p[3]; }));
    var x0 = Math.min.apply(null, xs), x1 = Math.max.apply(null, xs), y0 = Math.min.apply(null, ys), y1 = Math.max.apply(null, ys);
    var pad = (y1 - y0) * .08 || 1; y0 -= pad; y1 += pad;
    var sx = function (t) { return L + (t - x0) / (x1 - x0) * (W - L - R); }, sy = function (v) { return T + (y1 - v) / (y1 - y0) * (H - T - B); };
    var lin = function (arr, k) { return arr.map(function (p, i) { return (i ? "L" : "M") + sx(p[0]).toFixed(1) + " " + sy(p[k]).toFixed(1); }).join(" "); };
    var ultimo = pas[pas.length - 1], conUlt = [[ultimo[0], ultimo[1], ultimo[1], ultimo[1]]].concat(pr);
    var banda = conUlt.map(function (p, i) { return (i ? "L" : "M") + sx(p[0]).toFixed(1) + " " + sy(p[3]).toFixed(1); }).join(" ") + " " +
      conUlt.slice().reverse().map(function (p) { return "L" + sx(p[0]).toFixed(1) + " " + sy(p[2]).toFixed(1); }).join(" ") + " Z";
    var sube = pr[pr.length - 1][1] >= ultimo[1], col = sube ? "var(--green,#1e9b55)" : "var(--red,#d43f3f)";
    var xn = sx(ultimo[0]);
    var f = function (t) { var dd = new Date(t * 1000); return dd.toLocaleDateString("es-ES", { day: "2-digit", month: "2-digit" }) + " " + dd.getHours() + "h"; };
    return '<svg viewBox="0 0 ' + W + " " + H + '" preserveAspectRatio="none" role="img" aria-label="Precio de BTC de las últimas 48 horas y previsión a 24 horas">' +
      '<path d="' + banda + '" fill="' + col + '" opacity=".15"/>' +
      '<line x1="' + xn + '" x2="' + xn + '" y1="' + T + '" y2="' + (H - B) + '" stroke="var(--line,#dcbb92)" stroke-dasharray="3 3"/>' +
      '<path d="' + lin(pas, 1) + '" fill="none" stroke="var(--text,#3b2414)" stroke-width="1.8" vector-effect="non-scaling-stroke"/>' +
      '<path d="' + lin(conUlt, 1) + '" fill="none" stroke="' + col + '" stroke-width="2.2" stroke-dasharray="5 4" vector-effect="non-scaling-stroke"/>' +
      '<circle cx="' + xn + '" cy="' + sy(ultimo[1]) + '" r="3.5" fill="var(--text,#3b2414)"/>' +
      '<text x="' + L + '" y="' + (H - 4) + '" font-size="10" fill="var(--muted,#8a6648)">' + f(pas[0][0]) + "</text>" +
      '<text x="' + xn + '" y="' + (H - 4) + '" font-size="10" text-anchor="middle" fill="var(--muted,#8a6648)">ahora</text>' +
      '<text x="' + (W - R) + '" y="' + (H - 4) + '" font-size="10" text-anchor="end" fill="var(--muted,#8a6648)">+24 h</text></svg>';
  }
  function html(d) {
    var pr = d.prevision || [], fin = pr[pr.length - 1] || [0, 0, 0, 0], ch = d.cambio_24h || 0;
    var col = ch >= 0 ? "var(--green,#1e9b55)" : "var(--red,#d43f3f)", ac = d.aciertos || {}, ev = ac.evaluadas || 0;
    var hace = Math.max(0, Math.round((Date.now() / 1000 - (d.generado || 0)) / 3600));
    return '<div class="card krn" id="krn">' +
      '<div class="krn-h"><b>🔮 Previsión IA de BTC · 24 h</b><span class="krn-tag">dato curioso</span></div>' +
      '<div class="krn-big">$' + n(fin[1]) + '<i style="color:' + col + '">' + (ch >= 0 ? "+" : "−") + n(Math.abs(ch), 1) + "%</i></div>" +
      '<div class="krn-sub">Ahora $' + n(d.precio) + " · margen probable $" + n(fin[2]) + " – $" + n(fin[3]) + "</div>" +
      grafica(d) +
      '<div class="krn-ley"><span><i style="background:var(--text,#3b2414)"></i>últimas 48 h</span><span><i style="background:' + col + '"></i>previsión</span><span><i style="background:' + col + ';opacity:.3;height:8px"></i>margen</span></div>' +
      '<div class="krn-ac"><div><span>Aciertos de dirección</span><b>' + (ev ? (ac.acertadas + " de " + ev + " (" + Math.round(100 * ac.acertadas / ev) + "%)") : "aún sin datos") + '</b></div>' +
      (d.paper ? '<div style="grid-column:1/-1"><span>Simulación 10.000 $ (de mentira)</span><b>Kronos ' + (d.paper.kronos_pct >= 0 ? "+" : "−") + n(Math.abs(d.paper.kronos_pct), 1) + '% · aguantar ' + (d.paper.aguantar_pct >= 0 ? "+" : "−") + n(Math.abs(d.paper.aguantar_pct), 1) + '%</b></div>' : "") +
      '<div><span>Actualizada</span><b>' + (hace < 1 ? "hace menos de 1 h" : "hace " + hace + " h") + "</b></div></div>" +
      '<div class="krn-aviso">Modelo open source Kronos (velas de ' + (d.fuente || "Kraken") + "). Es una estimación estadística, no una señal de compra ni de venta. " +
      (ev ? "Un 50% de aciertos sería igual que tirar una moneda." : "Los aciertos se cuentan 24 h después de cada previsión.") + "</div></div>";
  }
  function pintar() {
    var box = document.getElementById("market"); if (!box || !datos) return;
    if (box.querySelector(".msg")) return; // aún cargando el mercado
    var prev = document.getElementById("krn");
    var nuevo = document.createElement("div"); nuevo.innerHTML = html(datos); nuevo = nuevo.firstChild;
    if (prev) { if (prev.getAttribute("data-g") === String(datos.generado)) return; prev.replaceWith(nuevo); }
    else {
      var resumen = box.querySelector(".summary");
      if (resumen) resumen.insertAdjacentElement("afterend", nuevo); else box.insertBefore(nuevo, box.firstChild);
    }
    nuevo.setAttribute("data-g", String(datos.generado));
  }
  var pend = false;
  new MutationObserver(function () { if (!pend) { pend = true; setTimeout(function () { pend = false; cargar(); pintar(); }, 150); } })
    .observe(document.body, { childList: true, subtree: true });
  cargar();
})();
</script>
""" + "\n" + FIN + "\n"
s = open(RUTA, encoding="utf-8").read()
i = s.find(INI)
if i >= 0:
    j = s.find(FIN, i)
    s = s[:i] + s[j + len(FIN):].lstrip("\n")
bak = RUTA + ".bak_kronos_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy2(RUTA, bak)
if "quitar" in sys.argv:
    open(RUTA, "w", encoding="utf-8").write(s)
    print("Previsión IA quitada. Cierra SolRadar y vuelve a abrirlo.")
    sys.exit(0)
pos = s.lower().rfind("</body>")
open(RUTA, "w", encoding="utf-8").write(s[:pos] + BLOQUE + s[pos:] if pos >= 0 else s + "\n" + BLOQUE)
print("Previsión IA añadida a Mercado. Copia de seguridad: " + bak)
print("Cierra SolRadar del todo en Telegram y vuelve a abrirlo.")
