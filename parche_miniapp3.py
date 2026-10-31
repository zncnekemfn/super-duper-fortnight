import re, shutil, time, sys, os

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- MINIAPP3 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- MINIAPP2 ---" not in src:
    print("ABORTO: falta aplicar antes parche_miniapp2.py"); sys.exit(1)
if "def _vd_enviar(" not in src:
    print("AVISO: no encuentro el parche de videos; la pestaña Videos saldra vacia hasta que lo apliques.")

HTML = '<!doctype html>\n<html lang="es"><head><meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n<title>Chivato de Ofertas</title>\n<script src="https://telegram.org/js/telegram-web-app.js"></script>\n<style>\n:root{--bg:#070d26;--bg2:#101d4a;--card:#15265a;--card2:#1b3170;--line:#2c4283;--tx:#fff;--mut:#9fb0d6;--or:#ff8f1f;--or2:#ffb347;--ok:#6ff0a0;--bad:#ff4d5e;--pink:#ff5d7a}\n*{box-sizing:border-box;margin:0;-webkit-tap-highlight-color:transparent}\nhtml,body{background:var(--bg)}\nbody{background:radial-gradient(900px 420px at 85% -80px,rgba(255,143,31,.22),transparent 60%),radial-gradient(700px 380px at -10% 10%,rgba(70,110,255,.18),transparent 60%),linear-gradient(180deg,var(--bg),var(--bg2));background-attachment:fixed;color:var(--tx);font:16px/1.4 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;min-height:100vh;padding:0 16px 96px}\nheader{padding:16px 0 6px;display:flex;align-items:center;justify-content:space-between}\nh1{font-size:23px;letter-spacing:-.3px}h1 span{background:linear-gradient(90deg,var(--or),var(--or2));-webkit-background-clip:text;background-clip:text;color:transparent}\n.live{display:flex;align-items:center;gap:7px;color:var(--mut);font-size:13px;margin-top:3px}\n.dot{width:8px;height:8px;border-radius:50%;background:var(--ok);box-shadow:0 0 0 0 rgba(111,240,160,.7);animation:pulse 1.8s infinite}\n@keyframes pulse{70%{box-shadow:0 0 0 9px rgba(111,240,160,0)}100%{box-shadow:0 0 0 0 rgba(111,240,160,0)}}\n.gear{background:var(--card);border:1px solid var(--line);color:var(--mut);border-radius:12px;width:40px;height:40px;font-size:18px}\n.tabs{position:fixed;left:10px;right:10px;bottom:calc(10px + env(safe-area-inset-bottom));display:flex;background:rgba(10,18,48,.82);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border:1px solid var(--line);border-radius:22px;padding:6px;gap:2px;z-index:5}\n.tabs button{flex:1;background:none;border:0;color:var(--mut);font:600 11px system-ui;padding:7px 2px 6px;border-radius:16px;display:flex;flex-direction:column;align-items:center;gap:3px;transition:.2s}\n.tabs svg{width:22px;height:22px;stroke:currentColor;fill:none;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}\n.tabs button.on{background:linear-gradient(180deg,rgba(255,143,31,.28),rgba(255,143,31,.1));color:var(--or2)}\nsection{animation:fade .35s ease}\n@keyframes fade{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}\n.chips{display:flex;gap:8px;overflow-x:auto;padding:8px 0;scrollbar-width:none}\n.chip{flex:none;background:var(--card);border:1px solid var(--line);color:var(--tx);border-radius:999px;padding:7px 14px;font:600 14px system-ui;transition:.15s}\n.chip.on{background:linear-gradient(90deg,var(--or),var(--or2));border-color:transparent;color:#0b1433}\ninput.q,select.q{width:100%;background:rgba(21,38,90,.8);border:1px solid var(--line);border-radius:14px;color:var(--tx);padding:12px 14px;font-size:16px;margin-bottom:6px}\n.hero{position:relative;overflow:hidden;border-radius:24px;padding:18px;margin:10px 0 4px;background:linear-gradient(135deg,#ff8f1f 0%,#ff5d3a 55%,#c2185b 100%);box-shadow:0 14px 34px rgba(255,95,40,.28)}\n.hero:before{content:"";position:absolute;right:-40px;top:-40px;width:170px;height:170px;border-radius:50%;background:rgba(255,255,255,.14)}\n.hero small{font:800 11px system-ui;letter-spacing:1.4px;opacity:.95}\n.hero .tt{color:#fff;font-size:17px;margin-top:6px;-webkit-line-clamp:2}\n.hero .big{font-size:36px;font-weight:900;margin-top:8px}.hero .big s{font-size:16px;font-weight:600;opacity:.8;margin-left:8px}\n.hero .btn{background:#fff;color:#c2185b;margin-top:12px}\n.hero .bg{position:absolute;right:16px;top:16px;font-size:38px;font-weight:900;opacity:.95}\n.card{position:relative;background:linear-gradient(160deg,var(--card),var(--card2));border:1px solid var(--line);border-radius:20px;padding:15px;margin:12px 0;box-shadow:0 8px 22px rgba(0,0,0,.25);animation:fade .4s ease both}\n.tt{font-weight:700;font-size:15px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;padding-right:36px}\n.row{display:flex;align-items:center;gap:12px;margin-top:10px}\n.now{font-size:30px;font-weight:900;color:var(--ok);letter-spacing:-.5px}\n.old{color:var(--mut);text-decoration:line-through;font-size:15px}\n.pct{margin-left:auto;background:linear-gradient(135deg,#ff4d5e,#e0214a);border-radius:999px;padding:6px 13px;font-weight:900}\n.bar{height:6px;border-radius:99px;background:rgba(255,255,255,.1);margin-top:12px;overflow:hidden}\n.bar i{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,var(--or),var(--bad))}\n.meta{color:var(--mut);font-size:12.5px;margin-top:9px;display:flex;flex-wrap:wrap;gap:6px;align-items:center}\n.tag{border-radius:999px;font-size:11px;font-weight:800;padding:3px 9px;border:1px solid var(--line);background:#0e1b44;color:var(--mut)}\n.tag.hot{background:rgba(255,77,94,.16);border-color:rgba(255,77,94,.5);color:#ff8d98}\n.tag.new{background:rgba(111,240,160,.14);border-color:rgba(111,240,160,.5);color:var(--ok);animation:blink 1.6s infinite}\n@keyframes blink{50%{opacity:.55}}\n.sv{color:var(--ok);font-weight:700}\n.two{display:flex;gap:8px;margin-top:12px}.two .btn{margin-top:0}\n.btn{display:block;width:100%;background:linear-gradient(90deg,var(--or),var(--or2));color:#0b1433;border:0;border-radius:14px;padding:13px;font:800 15px system-ui;box-shadow:0 6px 16px rgba(255,143,31,.28);transition:transform .1s}\n.btn:active{transform:scale(.97)}\n.btn.sec{background:rgba(255,255,255,.06);color:var(--tx);border:1px solid var(--line);width:auto;flex:none;padding:13px 16px;box-shadow:none}\n.hb{position:absolute;top:9px;right:10px;background:none;border:0;color:var(--mut);font-size:25px;padding:4px 6px;transition:transform .2s}\n.hb.on{color:var(--pink)}.hb.pop{animation:pop .4s}\n@keyframes pop{40%{transform:scale(1.5)}}\n.empty{color:var(--mut);text-align:center;padding:38px 10px}\n.sk{height:150px;border-radius:20px;margin:12px 0;background:linear-gradient(100deg,rgba(255,255,255,.04) 30%,rgba(255,255,255,.13) 50%,rgba(255,255,255,.04) 70%);background-size:300% 100%;animation:sh 1.3s infinite}\n@keyframes sh{from{background-position:100% 0}to{background-position:-100% 0}}\n.legal{color:var(--mut);font-size:11.5px;margin:18px 0 6px;line-height:1.45}\n.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:12px 0}\n.st{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px}\n.st b{display:block;font-size:26px}.st span{color:var(--mut);font-size:13px}\n.sw{display:flex;align-items:center;justify-content:space-between;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:13px 14px;margin:8px 0}\n.sw button{width:52px;height:30px;border-radius:999px;border:0;background:#43527f;position:relative}\n.sw button:after{content:"";position:absolute;top:3px;left:3px;width:24px;height:24px;border-radius:50%;background:#fff;transition:.2s}\n.sw button.on{background:var(--ok)}.sw button.on:after{left:25px}\n.al{display:flex;align-items:center;justify-content:space-between;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px 14px;margin:8px 0;gap:10px}\n.al button{background:none;border:0;color:var(--bad);font-size:20px}\n.info{color:var(--mut);font-size:13px;margin:6px 0 10px}\nh2{font-size:18px;margin:16px 0 4px}\n.feed{height:calc(100dvh - 190px);min-height:420px;overflow-y:auto;scroll-snap-type:y mandatory;scrollbar-width:none;margin:8px -4px 0;border-radius:22px}\n.feed::-webkit-scrollbar{display:none}\n.vs{height:100%;scroll-snap-align:start;scroll-snap-stop:always;padding:4px;display:flex;flex-direction:column}\n.vbox{position:relative;border-radius:22px;overflow:hidden;background:#000;width:100%;border:1px solid var(--line);box-shadow:0 12px 30px rgba(0,0,0,.4)}\n.vbox video{width:100%;height:auto;max-height:calc(100dvh - 400px);object-fit:contain;margin:0 auto;display:block}\n.vbox .pc{position:absolute;left:12px;top:12px;background:linear-gradient(135deg,#ff4d5e,#e0214a);border-radius:999px;padding:6px 13px;font-weight:900}\n.vinfo{padding:12px 4px 0}.vinfo .tt{padding:0;font-size:16px}\n.hide{display:none!important}\n</style></head><body>\n<header><div><h1>Chivato <span>de Ofertas</span></h1><div class="live"><i class="dot"></i><span id="sub">Buscando ofertas…</span></div></div><button class="gear hide" id="adbtn" aria-label="Admin">⚙</button></header>\n<section id="t-of"><div id="hero"></div><input class="q" id="q" placeholder="Buscar producto…" inputmode="search">\n<div class="chips" id="chips"></div><div class="chips" id="cats"></div><select class="q" id="ord"><option value="r">Más recientes</option><option value="d">Mayor descuento</option><option value="p">Menor precio</option></select><div id="list"><div class="sk"></div><div class="sk"></div></div></section>\n<section id="t-vd" class="hide"><div class="feed" id="feed"></div></section>\n<section id="t-fv" class="hide"><h2>Mis favoritos</h2><div id="favs"></div></section>\n<section id="t-al" class="hide"><h2>Mis alertas</h2><div class="info">Te aviso por el chat del bot cuando salga una oferta que coincida. Máximo 5.</div><input class="q" id="aq" placeholder="Producto (ej. auriculares)" maxlength="40"><select class="q" id="am"><option value="0">Cualquier descuento</option><option value="20">20% o más</option><option value="30">30% o más</option><option value="50">50% o más</option><option value="70">70% o más</option></select><button class="btn" id="aadd">Crear alerta</button><div id="als" style="margin-top:12px"></div></section>\n<section id="t-top" class="hide"><h2>Mayor descuento (24 h)</h2><div id="top"></div><h2>Más pulsadas en la app</h2><div id="clk"></div></section>\n<section id="t-ad" class="hide"><h2>Resumen</h2><div class="grid" id="stats"></div><h2>Funciones</h2><div id="sws"></div></section>\n<div class="legal" id="legal">Como afiliado de Amazon obtengo ingresos por las compras adscritas. Los precios corresponden al momento del aviso y pueden cambiar.</div>\n<nav class="tabs">\n<button class="on" data-t="of"><svg viewBox="0 0 24 24"><path d="M3 12l9-8 9 8"/><path d="M5 10v10h14V10"/></svg>Ofertas</button>\n<button data-t="vd"><svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="3"/><path d="M10 9l5 3-5 3z"/></svg>Vídeos</button>\n<button data-t="fv"><svg viewBox="0 0 24 24"><path d="M12 20s-7-4.4-7-10a4 4 0 017-2.5A4 4 0 0119 10c0 5.6-7 10-7 10z"/></svg>Favoritos</button>\n<button data-t="al"><svg viewBox="0 0 24 24"><path d="M6 16V11a6 6 0 0112 0v5l2 2H4z"/><path d="M10 21h4"/></svg>Alertas</button>\n<button data-t="top"><svg viewBox="0 0 24 24"><path d="M8 4h8v5a4 4 0 01-8 0z"/><path d="M8 6H4v1a4 4 0 004 4M16 6h4v1a4 4 0 01-4 4M12 13v4M8 20h8"/></svg>Top</button>\n</nav>\n<script>\nconst tg=window.Telegram&&Telegram.WebApp;if(tg){tg.ready();tg.expand();try{tg.setHeaderColor("#070d26");tg.setBackgroundColor("#070d26")}catch(e){}}\nconst hap=(k)=>{try{tg&&tg.HapticFeedback&&(k==="s"?tg.HapticFeedback.notificationOccurred("success"):tg.HapticFeedback.impactOccurred("light"))}catch(e){}};\nconst H={"X-Init":(tg&&tg.initData)||""};let ALL=[],MIN=0,FAV=new Set(),FAVL=[],CAT="Todas",VID=[];\nconst eur=n=>Number(n).toFixed(2).replace(".",",")+" €";\nconst esc=s=>String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",\'"\':"&quot;"}[c]));\nfunction ago(ts){const m=Math.max(1,Math.round((Date.now()/1000-ts)/60));return m<60?`hace ${m} min`:m<1440?`hace ${Math.round(m/60)} h`:`hace ${Math.round(m/1440)} d`}\nfunction card(o,i){const mins=(Date.now()/1000-o.ts)/60;const tags=(o.pct>=50?\'<span class="tag hot">🔥 CHOLLO</span>\':"")+(mins<30?\'<span class="tag new">NUEVA</span>\':"")+(o.cat?`<span class="tag">${esc(o.cat)}</span>`:"");\nreturn `<div class="card" style="animation-delay:${Math.min(i||0,8)*45}ms"><button class="hb${FAV.has(o.asin)?" on":""}" data-h="${esc(o.asin)}">${FAV.has(o.asin)?"♥":"♡"}</button><div class="tt">${esc(o.t)}</div><div class="row"><div class="now">${eur(o.ahora)}</div><div class="old">${eur(o.antes)}</div><div class="pct">-${o.pct}%</div></div><div class="bar"><i style="width:${Math.min(100,o.pct)}%"></i></div><div class="meta">${tags}<span class="sv">Ahorras ${eur(o.antes-o.ahora)}</span><span>· ${ago(o.ts)}</span></div><div class="two"><button class="btn" data-a="${esc(o.asin)}" data-u="${esc(o.url)}">Ver oferta</button><button class="btn sec" data-s="${esc(o.url)}" data-n="${esc(o.t)} a ${o.ahora} € (-${o.pct}%)">Compartir</button></div></div>`}\nfunction heroHtml(){const lim=Date.now()/1000-86400;const c=ALL.filter(o=>o.ts>=lim);if(!c.length)return"";const o=c.reduce((a,b)=>b.pct>a.pct?b:a);return `<div class="hero"><small>⭐ OFERTA ESTRELLA DE HOY</small><div class="bg">-${o.pct}%</div><div class="tt" style="margin-top:30px">${esc(o.t)}</div><div class="big">${eur(o.ahora)}<s>${eur(o.antes)}</s></div><button class="btn" data-a="${esc(o.asin)}" data-u="${esc(o.url)}">Ver oferta</button></div>`}\nfunction draw(){const q=document.getElementById("q").value.toLowerCase();let l=ALL.filter(o=>o.pct>=MIN&&o.t.toLowerCase().includes(q)&&(CAT==="Todas"||o.cat===CAT));const s=document.getElementById("ord").value;if(s==="d")l.sort((a,b)=>b.pct-a.pct);else if(s==="p")l.sort((a,b)=>a.ahora-b.ahora);document.getElementById("hero").innerHTML=heroHtml();document.getElementById("list").innerHTML=l.length?l.map(card).join(""):\'<div class="empty">Aún no hay ofertas con ese filtro.<br>Crea una alerta y te aviso al momento.</div>\';const cs=["Todas",...new Set(ALL.map(o=>o.cat).filter(Boolean))];document.getElementById("cats").innerHTML=cs.map(c=>`<button class="chip${c===CAT?" on":""}" data-c="${esc(c)}">${esc(c)}</button>`).join("")}\nfunction drawFav(){document.getElementById("favs").innerHTML=FAVL.length?FAVL.map(card).join(""):\'<div class="empty">Toca el corazón ♡ de una oferta para guardarla aquí.</div>\'}\nfunction drawVid(){const f=document.getElementById("feed");if(!VID.length){f.innerHTML=\'<div class="empty" style="padding-top:90px">Los vídeos de las mejores ofertas aparecerán aquí.<br>Vuelve en un rato 🎬</div>\';return}\nf.innerHTML=VID.map(v=>`<div class="vs"><div class="vbox"><video src="${esc(v.v)}" muted loop playsinline preload="metadata"></video><div class="pc">-${v.pct}%</div></div><div class="vinfo"><div class="tt">${esc(v.t)}</div><div class="row" style="margin-top:6px"><div class="now">${eur(v.ahora)}</div><div class="old">${eur(v.antes)}</div></div><div class="two"><button class="btn" data-a="${esc(v.asin)}" data-u="${esc(v.url)}">Ver oferta</button><button class="btn sec" data-s="${esc(v.url)}" data-n="${esc(v.t)} a ${v.ahora} € (-${v.pct}%)">Compartir</button></div></div></div>`).join("");\nconst io=new IntersectionObserver(es=>es.forEach(e=>{const vi=e.target.querySelector("video");if(!vi)return;if(e.isIntersecting&&e.intersectionRatio>.6){const p=vi.play();p&&p.catch(()=>{})}else vi.pause()}),{root:f,threshold:[.6]});f.querySelectorAll(".vs").forEach(x=>io.observe(x))}\nasync function post(p,b){const r=await fetch(p,{method:"POST",headers:{...H,"Content-Type":"application/json"},body:JSON.stringify(b)});return r.json().catch(()=>({}))}\nasync function loadFav(){try{const r=await fetch("/api/fav",{headers:H});if(!r.ok)return;const j=await r.json();FAVL=j.fav||[];FAV=new Set(FAVL.map(o=>o.asin));drawFav();draw()}catch(e){}}\nasync function loadVid(){try{const r=await fetch("/api/videos",{headers:H});const j=await r.json();VID=j.videos||[];drawVid()}catch(e){}}\nasync function loadAl(){try{const r=await fetch("/api/alertas",{headers:H});if(!r.ok){document.getElementById("als").innerHTML=\'<div class="empty">Abre la app desde el bot para usar las alertas.</div>\';return}const j=await r.json();document.getElementById("als").innerHTML=(j.al||[]).length?j.al.map((a,i)=>`<div class="al"><div>${a.q?esc(a.q):"Cualquier producto"} · ${a.min?a.min+"%+":"cualquier descuento"}</div><button data-d="${i}">✕</button></div>`).join(""):\'<div class="empty">Aún no tienes alertas.</div>\'}catch(e){}}\ndocument.addEventListener("click",async e=>{const hb=e.target.closest(".hb");if(hb){hb.classList.add("pop");hap();const r=await post("/api/fav",{asin:hb.dataset.h});if(r.ok){hap("s");loadFav()}return}const sh=e.target.closest("[data-s]");if(sh){const u="https://t.me/share/url?url="+encodeURIComponent(sh.dataset.s)+"&text="+encodeURIComponent(sh.dataset.n);tg?tg.openTelegramLink(u):window.open(u,"_blank");return}const ch=e.target.closest("[data-c]");if(ch){CAT=ch.dataset.c;hap();draw();return}const dl=e.target.closest("[data-d]");if(dl){await post("/api/alertas/del",{i:+dl.dataset.d});loadAl();return}const b=e.target.closest(".btn");if(!b||!b.dataset.a)return;hap();fetch("/api/click",{method:"POST",headers:{...H,"Content-Type":"application/json"},body:JSON.stringify({asin:b.dataset.a})}).catch(()=>{});tg?tg.openLink(b.dataset.u):window.open(b.dataset.u,"_blank")});\ndocument.getElementById("q").oninput=draw;document.getElementById("ord").onchange=draw;\ndocument.getElementById("aadd").onclick=async()=>{const q=document.getElementById("aq").value.trim(),m=+document.getElementById("am").value;if(!q&&m<50){alert("Escribe un producto o elige 50% o más.");return}const r=await post("/api/alertas",{q,min:m});if(!r.ok){alert(r.error||"No se pudo crear");return}hap("s");document.getElementById("aq").value="";loadAl()};\n[["Todas",0],["30%+",30],["50%+",50],["70%+",70]].forEach(([n,v])=>{const c=document.createElement("button");c.className="chip"+(v===0?" on":"");c.textContent=n;c.onclick=()=>{MIN=v;hap();document.querySelectorAll("#chips .chip").forEach(x=>x.classList.remove("on"));c.classList.add("on");draw()};document.getElementById("chips").appendChild(c)});\nconst TABS=["of","vd","fv","al","top","ad"];\nfunction go(t){document.querySelectorAll(".tabs button").forEach(x=>x.classList.toggle("on",x.dataset.t===t));TABS.forEach(x=>document.getElementById("t-"+x).classList.toggle("hide",x!==t));document.getElementById("legal").classList.toggle("hide",t==="vd");hap();if(t==="top")loadTop();if(t==="fv")loadFav();if(t==="al")loadAl();if(t==="vd")loadVid();if(t==="ad")loadAdmin();if(t!=="vd")document.querySelectorAll("video").forEach(v=>v.pause())}\ndocument.querySelectorAll(".tabs button").forEach(b=>b.onclick=()=>go(b.dataset.t));document.getElementById("adbtn").onclick=()=>go("ad");\nasync function load(){try{const r=await fetch("/api/ofertas",{headers:H});const j=await r.json();ALL=j.ofertas||[];if(j.admin)document.getElementById("adbtn").classList.remove("hide");document.getElementById("sub").textContent=ALL.length?`${ALL.length} ofertas recientes · en directo`:"Esperando nuevas ofertas";draw()}catch(e){document.getElementById("list").innerHTML=\'<div class="empty">No se pudo cargar. Inténtalo de nuevo.</div>\'}}\nasync function loadTop(){const r=await fetch("/api/top",{headers:H});const j=await r.json();document.getElementById("top").innerHTML=(j.descuento||[]).length?j.descuento.map(card).join(""):\'<div class="empty">Aún no hay datos.</div>\';document.getElementById("clk").innerHTML=(j.clicks||[]).length?j.clicks.map(c=>`<div class="card"><div class="tt">${esc(c.t)}</div><div class="meta">${c.n} pulsaciones</div></div>`).join(""):\'<div class="empty">Todavía nadie ha pulsado.</div>\'}\nasync function loadAdmin(){const r=await fetch("/api/admin",{headers:H});if(!r.ok)return;const j=await r.json();document.getElementById("stats").innerHTML=j.stats.map(s=>`<div class="st"><b>${esc(s[1])}</b><span>${esc(s[0])}</span></div>`).join("");document.getElementById("sws").innerHTML=j.toggles.map(t=>`<div class="sw"><div>${esc(t.nombre)}</div><button class="${t.on?"on":""}" data-k="${t.k}"></button></div>`).join("");document.querySelectorAll(".sw button").forEach(b=>b.onclick=async()=>{await fetch("/api/admin/toggle",{method:"POST",headers:{...H,"Content-Type":"application/json"},body:JSON.stringify({k:b.dataset.k})});loadAdmin()})}\nload();loadFav();setInterval(load,60000);\n</script></body></html>\n'

TAIL = r'''# --- MINIAPP3 ---
MI_VMAX = 12

def _mi_vdir():
    return _mi_os.path.join(_mi_os.path.dirname(_mi_os.path.abspath(__file__)), "miniapp", "videos")

def _mi_publicar_video(d, ruta, texto):
    m = _mi_d(d)
    if not m.get("vidon", True):
        return
    if (d.get("video") or {}).get("foto"):
        return
    mm = re.search(r"oferta_([A-Z0-9]{10})\.mp4$", str(ruta))
    if not mm or "marca Amazon" in str(texto):
        return
    asin = mm.group(1)
    pr = re.search(r"(\d+(?:\.\d+)?) € \(antes (\d+(?:\.\d+)?) €\) · -(\d+)%", str(texto))
    ur = re.search(r"(https?://\S+)", str(texto))
    if not pr or not ur:
        return
    linea = str(texto).split("\n")[0]
    tit = re.sub(r"^[^\w]+", "", linea)
    tit = re.sub(r"(?i)\bamazon\b", "", tit)
    tit = re.sub(r"\s+", " ", tit).strip()[:110] or asin
    _mi_os.makedirs(_mi_vdir(), exist_ok=True)
    _mi_sh.copyfile(ruta, _mi_os.path.join(_mi_vdir(), asin + ".mp4"))
    lst = [v for v in m.setdefault("vid", []) if v["asin"] != asin]
    lst.insert(0, {"asin": asin, "t": tit, "ahora": float(pr.group(1)), "antes": float(pr.group(2)), "pct": int(pr.group(3)), "url": ur.group(1), "ts": int(time.time())})
    for v in lst[MI_VMAX:]:
        try:
            _mi_os.remove(_mi_os.path.join(_mi_vdir(), v["asin"] + ".mp4"))
        except Exception:
            pass
    m["vid"] = lst[:MI_VMAX]

if "_vd_enviar" in globals():
    _vd_enviar_pre_mi3 = _vd_enviar
    def _vd_enviar(cid, ruta, texto):
        ok = _vd_enviar_pre_mi3(cid, ruta, texto)
        try:
            if ok and _mi["d"] is not None:
                _mi_publicar_video(_mi["d"], ruta, texto)
        except Exception as e:
            print("error miniapp video", e, flush=True)
        return ok

_mi_tog0 = _mi_tog

def _mi_tog(d):
    m = _mi_d(d)
    return _mi_tog0(d) + [("vidapp", "Videos en la app (publico)", lambda: m.get("vidon", True), lambda x: m.__setitem__("vidon", x))]

def _mi_servir_video(self, asin):
    ruta = _mi_os.path.join(_mi_vdir(), asin + ".mp4")
    d = _mi["d"]
    if d is None or not _mi_os.path.exists(ruta) or not any(v["asin"] == asin for v in _mi_d(d).get("vid", [])):
        return self._json({"error": "no existe"}, 404)
    tam = _mi_os.path.getsize(ruta)
    ini, fin, code = 0, tam - 1, 200
    rng = self.headers.get("Range", "")
    if rng.startswith("bytes="):
        a, _, b = rng[6:].partition("-")
        try:
            if a == "":
                ini = max(0, tam - int(b))
            else:
                ini = int(a)
                fin = int(b) if b else tam - 1
            fin = min(fin, tam - 1)
            code = 206
        except Exception:
            ini, fin, code = 0, tam - 1, 200
        if ini > fin:
            self.send_response(416); self.send_header("Content-Range", "bytes */%d" % tam); self.end_headers(); return
    self.send_response(code)
    self.send_header("Content-Type", "video/mp4")
    self.send_header("Accept-Ranges", "bytes")
    self.send_header("Cache-Control", "public, max-age=3600")
    self.send_header("Content-Length", str(fin - ini + 1))
    if code == 206:
        self.send_header("Content-Range", "bytes %d-%d/%d" % (ini, fin, tam))
    self.end_headers()
    try:
        with open(ruta, "rb") as fh:
            fh.seek(ini)
            resto = fin - ini + 1
            while resto > 0:
                bloque = fh.read(min(65536, resto))
                if not bloque:
                    break
                self.wfile.write(bloque)
                resto -= len(bloque)
    except Exception:
        pass

_mi_get2_prev = _MiHandler.do_GET

def _mi_get3(self):
    p = self.path.split("?")[0]
    if p == "/api/videos":
        d = _mi["d"]
        if d is None:
            return self._json({"error": "arrancando"}, 503)
        m = _mi_d(d)
        vs = [dict(v, v="/v/%s.mp4?t=%d" % (v["asin"], v["ts"])) for v in m.get("vid", [])] if m.get("vidon", True) else []
        return self._json({"videos": vs})
    mm = re.fullmatch(r"/v/([A-Z0-9]{10})\.mp4", p)
    if mm:
        return _mi_servir_video(self, mm.group(1))
    return _mi_get2_prev(self)

_MiHandler.do_GET = _mi_get3
import shutil as _mi_sh

'''

n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
src = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), src, count=1, flags=re.M)
try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)
copia = RUTA + ".bak_miniapp3_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
carpeta = os.path.join(os.path.dirname(os.path.abspath(RUTA)), "miniapp")
os.makedirs(os.path.join(carpeta, "videos"), exist_ok=True)
open(os.path.join(carpeta, "index.html"), "w", encoding="utf-8").write(HTML)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
