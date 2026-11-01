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
    ".srg-load{font-size:12px;color:#777;margin-top:8px}";
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
      if (d.chg != null) {
        var sp = document.createElement("span"); sp.className = "srg-chg"; sp.style.color = col;
        sp.textContent = (d.chg >= 0 ? "+" : "−") + Math.abs(d.chg).toFixed(Math.abs(d.chg) < 10 ? 1 : 0).replace(".", ",") + "% 12 h";
        zona.insertBefore(sp, zona.firstChild); sp.style.display = "block"; sp.style.textAlign = "right"; sp.style.marginTop = "6px";
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
  function desplegar(o, box) {
    var d = o.d || {}, pool = d.pool || o.id, mint = d.mint || o.id;
    box.hidden = false;
    if (box.getAttribute("data-pool") === pool) return;
    box.setAttribute("data-pool", pool);
    var src = "https://dexscreener.com/solana/" + pool + "?embed=1&theme=dark&trades=0&info=0&chartTheme=dark&chartLeftToolbar=0&chartDefaultOnMobile=1";
    box.innerHTML = '<iframe class="srg-frame" loading="lazy" title="Gráfica de precio" src="' + src + '"></iframe>' +
      '<div class="srg-src">Gráfica en directo · DexScreener</div>' +
      '<div class="srg-btns"><button class="srg-p" data-a="buy">Comprar en Jupiter</button>' +
      '<button data-a="ca">Copiar CA</button><button data-a="share">Compartir</button></div>';
    box.querySelector(".srg-btns").addEventListener("click", function (ev) {
      var b = ev.target.closest("button"); if (!b) return; ev.stopPropagation();
      var a = b.getAttribute("data-a");
      if (a === "buy") abrir("https://jup.ag/swap/SOL-" + mint);
      if (a === "ca") {
        var hecho = function () { b.textContent = "¡Copiado!"; setTimeout(function () { b.textContent = "Copiar CA"; }, 1500); };
        if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(mint).then(hecho, function () { aviso(mint); });
        else aviso(mint);
      }
      if (a === "share") {
        var url = "https://dexscreener.com/solana/" + pool;
        var t = "https://t.me/share/url?url=" + encodeURIComponent(url) + "&text=" + encodeURIComponent("Mira este lanzamiento en SolRadar 📡 CA: " + mint);
        try { if (tg && tg.openTelegramLink) return tg.openTelegramLink(t); } catch (e) {}
        abrir(t);
      }
    });
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
