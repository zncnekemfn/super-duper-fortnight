import shutil, sys, time

# Parche SolRadar: mini gráfica + gráfica de DexScreener en las tarjetas de Lanzamientos.
# Uso: python3 parche_graficas.py    (no hace falta reiniciar; cierra y abre la app en Telegram)
RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/solradar/web/index.html"
MARCA = "/* SOLRADAR GRAFICAS LANZAMIENTOS */"
JS = r'''/* SOLRADAR GRAFICAS LANZAMIENTOS */
(function () {
  "use strict";
  var GT = "https://api.geckoterminal.com/api/v2/networks/solana";
  var cache = {};          // id -> Promise<{pool, mint, closes, chg}>
  var abierto = {};        // id -> true si la tarjeta está desplegada
  var css = document.createElement("style");
  css.textContent =
    ".srg-spark{display:block;width:100%;height:54px;margin-top:8px}" +
    ".srg-chg{font-weight:700;font-size:15px;margin-left:auto;white-space:nowrap}" +
    ".srg-hint{font-size:12px;color:#6f95ff;text-align:right;margin-top:4px;cursor:pointer;user-select:none}" +
    ".srg-box{margin-top:10px}" +
    ".srg-frame{width:100%;height:340px;border:0;border-radius:12px;background:#000;display:block}" +
    ".srg-btns{display:flex;gap:8px;margin-top:10px}" +
    ".srg-btns a,.srg-btns button{flex:1;text-align:center;padding:10px 6px;border-radius:12px;background:#1a1a1a;color:#f2f2f2;" +
    "font:600 13.5px/1.2 inherit;border:0;text-decoration:none;cursor:pointer}" +
    ".srg-btns .srg-p{background:#4f7df5;color:#fff}" +
    ".srg-src{font-size:11px;color:#777;text-align:right;margin-top:4px}" +
    ".srg-load{font-size:12px;color:#777;margin-top:8px}" +
    ".srg-tf{display:flex;gap:6px;margin:4px 0 6px}" +
    ".srg-tf button{font:500 12.5px inherit;padding:5px 11px;border-radius:999px;background:#1a1a1a;color:#9a9a9a;border:0;cursor:pointer}" +
    ".srg-tf button.on{background:#4f7df5;color:#fff}" +
    ".srg-px{font-size:14px;color:#cfcfcf;margin-bottom:2px}" +
    ".srg-c{display:block;width:100%;height:210px}" +
    ".srg-pct{display:block;font-weight:700;font-size:15px;text-align:right;white-space:nowrap}";
  document.head.appendChild(css);

  var tg = window.Telegram && window.Telegram.WebApp;
  function abrir(url) { try { if (tg && tg.openLink) return tg.openLink(url); } catch (e) {} window.open(url, "_blank"); }
  function aviso(t) { try { if (tg && tg.showPopup) return tg.showPopup({ message: t }); } catch (e) {} try { alert(t); } catch (e) {} }

  function idDeUrl(u) {
    var m = String(u || "").match(/dexscreener\.com\/solana\/([1-9A-HJ-NP-Za-km-z]{32,44})/i)
         || String(u || "").match(/geckoterminal\.com\/solana\/pools\/([1-9A-HJ-NP-Za-km-z]{32,44})/i)
         || String(u || "").match(/(?:birdeye\.so\/token|pump\.fun(?:\/coin)?|solscan\.io\/token)\/([1-9A-HJ-NP-Za-km-z]{32,44})/i);
    return m ? m[1] : null;
  }
  function getJSON(u) {
    return fetch(u, { headers: { Accept: "application/json" } }).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status); return r.json();
    });
  }
  // Acepta dirección de pool o de token; devuelve pool, mint y cierres de 15 min (antiguos -> recientes)
  function datos(id) {
    if (cache[id]) return cache[id];
    cache[id] = getJSON(GT + "/pools/" + id + "?include=base_token")
      .then(function (j) { return j.data; })
      .catch(function () {
        return getJSON(GT + "/tokens/" + id + "/pools?page=1").then(function (j) {
          if (!j.data || !j.data.length) throw new Error("sin pool"); return j.data[0];
        });
      })
      .then(function (pool) {
        var addr = pool.attributes.address;
        var base = (((pool.relationships || {}).base_token || {}).data || {}).id || "";
        var mint = base.replace(/^solana_/, "") || id;
        return getJSON(GT + "/pools/" + addr + "/ohlcv/minute?aggregate=15&limit=48").then(function (o) {
          var l = ((((o || {}).data || {}).attributes || {}).ohlcv_list || []).slice().reverse();
          var closes = l.map(function (c) { return +c[4]; }).filter(function (v) { return v > 0; });
          var chg = closes.length > 1 ? (closes[closes.length - 1] / closes[0] - 1) * 100 : null;
          return { pool: addr, mint: mint, closes: closes, chg: chg };
        });
      });
    cache[id].catch(function () { setTimeout(function () { delete cache[id]; }, 60000); });
    return cache[id];
  }
  function spark(vals, col) {
    if (!vals || vals.length < 2) return "";
    var W = 300, H = 54, mn = Math.min.apply(null, vals), mx = Math.max.apply(null, vals), rg = (mx - mn) || mx || 1;
    var pts = vals.map(function (v, i) { return [i / (vals.length - 1) * W, 4 + (1 - (v - mn) / rg) * (H - 8)]; });
    var d = pts.map(function (p, i) { return (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1); }).join(" ");
    var gid = "srg" + Math.random().toString(36).slice(2, 8), last = pts[pts.length - 1];
    return '<svg class="srg-spark" viewBox="0 0 ' + W + " " + H + '" preserveAspectRatio="none" aria-label="Precio últimas 12 horas">' +
      '<defs><linearGradient id="' + gid + '" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="' + col + '" stop-opacity=".35"/>' +
      '<stop offset="1" stop-color="' + col + '" stop-opacity="0"/></linearGradient></defs>' +
      '<path d="' + d + " L " + W + " " + H + " L 0 " + H + ' Z" fill="url(#' + gid + ')"/>' +
      '<path d="' + d + '" fill="none" stroke="' + col + '" stroke-width="2" vector-effect="non-scaling-stroke"/>' +
      '<circle cx="' + (last[0] - 3) + '" cy="' + last[1] + '" r="3.5" fill="' + col + '"/></svg>';
  }
  function tarjetasLanzamientos() {
    var h = [].slice.call(document.querySelectorAll("h1,h2,h3,h4")).filter(function (x) { return /lanzamientos/i.test(x.textContent); })[0];
    if (!h) return [];
    var siguiente = [].slice.call(document.querySelectorAll("h1,h2,h3,h4")).filter(function (x) {
      return x !== h && (h.compareDocumentPosition(x) & Node.DOCUMENT_POSITION_FOLLOWING);
    })[0];
    var out = [];
    [].slice.call(document.querySelectorAll("a[href]")).forEach(function (a) {
      if (!(h.compareDocumentPosition(a) & Node.DOCUMENT_POSITION_FOLLOWING)) return;
      if (siguiente && !(a.compareDocumentPosition(siguiente) & Node.DOCUMENT_POSITION_FOLLOWING)) return;
      var id = idDeUrl(a.getAttribute("href")); if (!id) return;
      var card = a.closest(".card") || a.closest("[class*='card']") || (a.parentElement && a.parentElement.parentElement);
      if (card && out.every(function (o) { return o.card !== card; })) out.push({ card: card, id: id });
    });
    return out;
  }
  function preparar(o) {
    var card = o.card, id = o.id;
    if (card.getAttribute("data-srg") === id) return;
    card.setAttribute("data-srg", id);
    var zona = document.createElement("div"); zona.className = "srg";
    zona.innerHTML = '<div class="srg-load">Cargando gráfica…</div>';
    card.appendChild(zona);
    var hint = document.createElement("div"); hint.className = "srg-hint";
    var box = document.createElement("div"); box.className = "srg-box"; box.hidden = true;
    card.appendChild(hint); card.appendChild(box);
    function pintarHint() { hint.textContent = abierto[id] ? "Cerrar gráfica ▴" : "Toca para ver la gráfica completa ▾"; }
    pintarHint();
    datos(id).then(function (d) {
      var col = d.chg == null || d.chg >= 0 ? "#3ec46d" : "#ef5350";
      zona.innerHTML = spark(d.closes, col) || "";
      if (d.chg != null && !card.querySelector(".srg-pct")) {
        var sp = document.createElement("span"); sp.className = "srg-pct"; sp.style.color = col;
        sp.title = "Cambio en las últimas 12 horas";
        sp.textContent = (d.chg >= 0 ? "+" : "−") + Math.abs(d.chg).toFixed(Math.abs(d.chg) < 10 ? 1 : 0).replace(".", ",") + "%";
        var hace = [].slice.call(card.querySelectorAll("*")).filter(function (e) {
          return !e.children.length && /^\s*hace\s/i.test(e.textContent || "");
        })[0];
        if (hace) { hace.style.textAlign = "right"; hace.insertBefore(sp, hace.firstChild); } else { sp.style.marginTop = "6px"; zona.insertBefore(sp, zona.firstChild); }
      }
      o.d = d;
      if (abierto[id]) desplegar(o, box);
    }).catch(function () { zona.innerHTML = ""; });
    function toggle(ev) {
      if (ev.target.closest("a,button,input,select,textarea,iframe,.srg-btns")) return;
      abierto[id] = !abierto[id]; pintarHint();
      if (abierto[id]) desplegar(o, box); else { box.hidden = true; box.innerHTML = ""; }
    }
    card.style.cursor = "pointer";
    card.addEventListener("click", toggle);
    if (abierto[id]) desplegar(o, box);
  }
  var TF = { "5 min": ["minute", 5, 60, "5 h"], "15 min": ["minute", 15, 48, "12 h"], "1 h": ["hour", 1, 48, "2 días"], "4 h": ["hour", 4, 42, "7 días"] };
  var tfSel = {}, velasCache = {};
  function velas(pool, tf) {
    var k = pool + "|" + tf, t = TF[tf];
    if (velasCache[k] && Date.now() - velasCache[k].t < 60000) return velasCache[k].p;
    var p = getJSON(GT + "/pools/" + pool + "/ohlcv/" + t[0] + "?aggregate=" + t[1] + "&limit=" + t[2]).then(function (o) {
      return ((((o || {}).data || {}).attributes || {}).ohlcv_list || []).slice().reverse().filter(function (c) { return c[4] > 0; });
    });
    velasCache[k] = { t: Date.now(), p: p }; p.catch(function () { delete velasCache[k]; });
    return p;
  }
  function precio(p) {
    if (!p) return "$0";
    if (p >= 1) return "$" + p.toLocaleString("es-ES", { maximumFractionDigits: 2 });
    var s = p.toFixed(12).replace(/0+$/, ""), m = s.match(/^0\.(0{3,})(\d+)/);
    if (m) return "$0,0" + String(m[1].length).split("").map(function (d) { return "₀₁₂₃₄₅₆₇₈₉"[d]; }).join("") + m[2].slice(0, 4);
    return "$" + s.replace(".", ",").slice(0, 9);
  }
  function velasSVG(cs) {
    if (!cs || cs.length < 2) return '<div class="srg-load">Todavía no hay datos para esta escala.</div>';
    var W = 334, H = 210, VH = 34, top = 8, ch = H - VH - top - 6, bw = W / cs.length;
    var mn = Math.min.apply(null, cs.map(function (c) { return c[3]; })), mx = Math.max.apply(null, cs.map(function (c) { return c[2]; }));
    var vmx = Math.max.apply(null, cs.map(function (c) { return c[5] || 0; })) || 1;
    var y = function (v) { return top + (1 - (v - mn) / ((mx - mn) || mx || 1)) * ch; };
    var g = "";
    for (var k = 1; k < 4; k++) g += '<line x1="0" x2="' + W + '" y1="' + (top + k * ch / 4) + '" y2="' + (top + k * ch / 4) + '" stroke="#222"/>';
    cs.forEach(function (c, i) {
      var up = c[4] >= c[1], col = up ? "#3ec46d" : "#ef5350", cx = i * bw + bw / 2;
      var y1 = y(Math.max(c[1], c[4])), y2 = y(Math.min(c[1], c[4]));
      g += '<line x1="' + cx + '" x2="' + cx + '" y1="' + y(c[2]) + '" y2="' + y(c[3]) + '" stroke="' + col + '"/>' +
           '<rect x="' + (cx - bw * .32) + '" y="' + y1 + '" width="' + (bw * .64) + '" height="' + Math.max(1.5, y2 - y1) + '" fill="' + col + '"/>';
      var vh = (c[5] || 0) / vmx * VH;
      g += '<rect x="' + (cx - bw * .32) + '" y="' + (H - vh) + '" width="' + (bw * .64) + '" height="' + vh + '" fill="' + col + '" opacity=".35"/>';
    });
    return '<svg class="srg-c" viewBox="0 0 ' + W + " " + H + '" preserveAspectRatio="none" role="img" aria-label="Gráfica de velas">' + g + "</svg>";
  }
  function desplegar(o, box) {
    var d = o.d || {}, pool = d.pool, mint = d.mint || o.id;
    box.hidden = false;
    if (!pool) { box.innerHTML = '<div class="srg-load">Cargando…</div>'; return; }
    var tf = tfSel[o.id] || "15 min";
    if (box.getAttribute("data-pool") !== pool) {
      box.setAttribute("data-pool", pool);
      box.innerHTML = '<div class="srg-px"></div><div class="srg-tf">' + Object.keys(TF).map(function (k) {
          return '<button data-tf="' + k + '">' + k + "</button>"; }).join("") + '</div><div class="srg-chart"></div>' +
        '<div class="srg-src">Datos: GeckoTerminal · <a href="https://dexscreener.com/solana/' + pool + '" data-ext="1" style="color:#6f95ff">abrir en DexScreener</a></div>' +
        '<div class="srg-btns"><button class="srg-p" data-a="buy">Comprar en Jupiter</button>' +
        '<button data-a="ca">Copiar CA</button><button data-a="share">Compartir</button></div>';
      box.addEventListener("click", function (ev) {
        var t = ev.target.closest("button,a"); if (!t) return; ev.stopPropagation();
        if (t.getAttribute("data-ext")) { ev.preventDefault(); return abrir(t.href); }
        if (t.getAttribute("data-tf")) { tfSel[o.id] = t.getAttribute("data-tf"); return pintar(); }
        var a = t.getAttribute("data-a");
        if (a === "buy") abrir("https://jup.ag/swap/SOL-" + mint);
        if (a === "ca") {
          var hecho = function () { t.textContent = "¡Copiado!"; setTimeout(function () { t.textContent = "Copiar CA"; }, 1500); };
          if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(mint).then(hecho, function () { aviso(mint); });
          else aviso(mint);
        }
        if (a === "share") {
          var u = "https://t.me/share/url?url=" + encodeURIComponent("https://dexscreener.com/solana/" + pool) +
                  "&text=" + encodeURIComponent("Mira este lanzamiento en SolRadar 📡 CA: " + mint);
          try { if (tg && tg.openTelegramLink) return tg.openTelegramLink(u); } catch (e) {}
          abrir(u);
        }
      });
    }
    function pintar() {
      var tf = tfSel[o.id] || "15 min";
      [].forEach.call(box.querySelectorAll("[data-tf]"), function (b) { b.classList.toggle("on", b.getAttribute("data-tf") === tf); });
      var zona = box.querySelector(".srg-chart"); zona.innerHTML = '<div class="srg-load">Cargando velas…</div>';
      velas(pool, tf).then(function (cs) {
        if ((tfSel[o.id] || "15 min") !== tf) return;
        zona.innerHTML = velasSVG(cs);
        if (cs.length > 1) {
          var ult = cs[cs.length - 1][4], ch = (ult / cs[0][1] - 1) * 100;
          box.querySelector(".srg-px").innerHTML = precio(ult) + ' · <span style="color:' + (ch >= 0 ? "#3ec46d" : "#ef5350") + '">' +
            (ch >= 0 ? "+" : "−") + Math.abs(ch).toFixed(Math.abs(ch) < 10 ? 1 : 0).replace(".", ",") + "% en " + TF[tf][3] + "</span>";
        }
      }).catch(function () { zona.innerHTML = '<div class="srg-load">No he podido cargar las velas. Prueba otra escala o ábrela en DexScreener.</div>'; });
    }
    pintar();
  }
  var pend = false;
  function revisar() { pend = false; try { tarjetasLanzamientos().forEach(preparar); } catch (e) { console.log("srg", e); } }
  new MutationObserver(function () { if (!pend) { pend = true; setTimeout(revisar, 150); } })
    .observe(document.body, { childList: true, subtree: true });
  revisar();
})();
'''

s = open(RUTA, encoding="utf-8").read()
if MARCA in s:
    i = s.find("<script>" + MARCA)
    j = s.find("</script>", i)
    if i >= 0 and j > i:
        s = s[:i] + s[j + len("</script>"):]
        print("Había una versión anterior del parche: la sustituyo.")
bloque = "<script>" + JS + "</script>\n"
pos = s.lower().rfind("</body>")
nuevo = s[:pos] + bloque + s[pos:] if pos >= 0 else s + "\n" + bloque
bak = RUTA + ".bak_graficas_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy2(RUTA, bak)
open(RUTA, "w", encoding="utf-8").write(nuevo)
print("Parche aplicado. Copia de seguridad: " + bak)
print("Cierra SolRadar en Telegram y vuelve a abrirlo (pestaña Radar).")
