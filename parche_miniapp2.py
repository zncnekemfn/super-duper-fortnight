import re, shutil, time, sys, os

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- MINIAPP2 ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "# --- MINIAPP ---" not in src:
    print("ABORTO: falta aplicar antes parche_miniapp.py"); sys.exit(1)

HTML = '<!doctype html>\n<html lang="es"><head><meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n<title>Chivato de Ofertas</title>\n<script src="https://telegram.org/js/telegram-web-app.js"></script>\n<style>\n:root{--bg:#0b1433;--bg2:#12214f;--card:#16275a;--line:#2a3f7a;--tx:#fff;--mut:#9fb0d6;--or:#ff8f1f;--ok:#79e89a;--bad:#ff6b6b}\n*{box-sizing:border-box;margin:0;-webkit-tap-highlight-color:transparent}\nbody{background:linear-gradient(180deg,var(--bg),var(--bg2));color:var(--tx);font:16px/1.4 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;min-height:100vh;padding:0 16px 90px}\nheader{padding:18px 0 8px}\nh1{font-size:22px}h1 span{color:var(--or)}\n.sub{color:var(--mut);font-size:14px;margin-top:2px}\n.tabs{position:fixed;left:0;right:0;bottom:0;display:flex;background:#0a1230;border-top:1px solid var(--line);padding:8px 8px calc(8px + env(safe-area-inset-bottom));gap:6px;z-index:5}\n.tabs button{flex:1;background:none;border:0;color:var(--mut);font:600 12px system-ui;padding:8px 4px;border-radius:12px}\n.tabs button.on{background:var(--card);color:var(--or)}\n.chips{display:flex;gap:8px;overflow-x:auto;padding:10px 0;scrollbar-width:none}\n.chip{flex:none;background:var(--card);border:1px solid var(--line);color:var(--tx);border-radius:999px;padding:7px 14px;font:600 14px system-ui}\n.chip.on{background:var(--or);border-color:var(--or);color:#0b1433}\ninput.q{width:100%;background:var(--card);border:1px solid var(--line);border-radius:12px;color:var(--tx);padding:11px 14px;font-size:16px;margin-bottom:4px}\n.card{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:14px;margin:10px 0}\n.tt{font-weight:700;font-size:15px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}\n.row{display:flex;align-items:center;gap:12px;margin-top:10px}\n.now{font-size:28px;font-weight:800;color:var(--ok)}\n.old{color:var(--mut);text-decoration:line-through;font-size:15px}\n.pct{margin-left:auto;background:#e62832;border-radius:999px;padding:6px 12px;font-weight:800}\n.meta{color:var(--mut);font-size:12px;margin-top:6px}\n.btn{display:block;width:100%;margin-top:12px;background:var(--or);color:#0b1433;border:0;border-radius:12px;padding:12px;font:800 15px system-ui}\n.empty{color:var(--mut);text-align:center;padding:40px 10px}\n.legal{color:var(--mut);font-size:11.5px;margin:18px 0 6px;line-height:1.45}\n.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:12px 0}\n.st{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px}\n.st b{display:block;font-size:26px}.st span{color:var(--mut);font-size:13px}\n.sw{display:flex;align-items:center;justify-content:space-between;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:13px 14px;margin:8px 0}\n.sw button{width:52px;height:30px;border-radius:999px;border:0;background:#43527f;position:relative}\n.sw button:after{content:"";position:absolute;top:3px;left:3px;width:24px;height:24px;border-radius:50%;background:#fff;transition:.2s}\n.sw button.on{background:var(--ok)}.sw button.on:after{left:25px}\n.card{position:relative}\n.hb{position:absolute;top:8px;right:10px;background:none;border:0;color:var(--mut);font-size:24px;padding:4px 6px}\n.hb.on{color:#ff5d7a}\n.tt{padding-right:34px}\n.cat{display:inline-block;background:#0e1b44;border:1px solid var(--line);color:var(--mut);border-radius:999px;font-size:11px;padding:2px 9px;margin-right:6px}\n.two{display:flex;gap:8px;margin-top:12px}.two .btn{margin-top:0}\n.btn.sec{background:var(--bg2);color:var(--tx);border:1px solid var(--line);width:auto;flex:none;padding:12px 16px}\nselect.q{width:100%;background:var(--card);border:1px solid var(--line);border-radius:12px;color:var(--tx);padding:10px 12px;font-size:15px;margin:6px 0}\n.al{display:flex;align-items:center;justify-content:space-between;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px 14px;margin:8px 0;gap:10px}\n.al button{background:none;border:0;color:var(--bad);font-size:20px}\n.info{color:var(--mut);font-size:13px;margin:6px 0 10px}\nh2{font-size:17px;margin:16px 0 4px}\n.hide{display:none}\n</style></head><body>\n<header><h1>Chivato <span>de Ofertas</span></h1><div class="sub" id="sub">Ofertas filtradas, al momento</div></header>\n<section id="t-of"><input class="q" id="q" placeholder="Buscar producto…" inputmode="search">\n<div class="chips" id="chips"></div><div class="chips" id="cats"></div><select class="q" id="ord"><option value="r">Más recientes</option><option value="d">Mayor descuento</option><option value="p">Menor precio</option></select><div id="list"></div></section>\n<section id="t-fv" class="hide"><h2>Mis favoritos</h2><div id="favs"></div></section>\n<section id="t-al" class="hide"><h2>Mis alertas</h2><div class="info">Te aviso por el chat del bot cuando salga una oferta que coincida. Máximo 5.</div><input class="q" id="aq" placeholder="Producto (ej. auriculares)" maxlength="40"><select class="q" id="am"><option value="0">Cualquier descuento</option><option value="20">20% o más</option><option value="30">30% o más</option><option value="50">50% o más</option><option value="70">70% o más</option></select><button class="btn" id="aadd">Crear alerta</button><div id="als" style="margin-top:12px"></div></section>\n<section id="t-top" class="hide"><h2>Mayor descuento (24 h)</h2><div id="top"></div><h2>Más pulsadas en la app</h2><div id="clk"></div></section>\n<section id="t-ad" class="hide"><h2>Resumen</h2><div class="grid" id="stats"></div><h2>Funciones</h2><div id="sws"></div></section>\n<div class="legal" id="legal">Como afiliado de Amazon obtengo ingresos por las compras adscritas. Los precios corresponden al momento del aviso y pueden cambiar.</div>\n<nav class="tabs"><button class="on" data-t="of">Ofertas</button><button data-t="fv">Favoritos</button><button data-t="al">Alertas</button><button data-t="top">Top</button><button data-t="ad" id="adbtn" class="hide">Admin</button></nav>\n<script>\nconst tg=window.Telegram&&Telegram.WebApp;if(tg){tg.ready();tg.expand();try{tg.setHeaderColor("#0b1433");tg.setBackgroundColor("#0b1433")}catch(e){}}\nconst H={"X-Init":(tg&&tg.initData)||""};let ALL=[],MIN=0;\nconst eur=n=>Number(n).toFixed(2).replace(".",",")+" €";\nconst esc=s=>String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",\'"\':"&quot;"}[c]));\nfunction ago(ts){const m=Math.max(1,Math.round((Date.now()/1000-ts)/60));return m<60?`hace ${m} min`:m<1440?`hace ${Math.round(m/60)} h`:`hace ${Math.round(m/1440)} d`}\nlet FAV=new Set(),FAVL=[],CAT="Todas";\nfunction card(o){return `<div class="card"><button class="hb${FAV.has(o.asin)?" on":""}" data-h="${esc(o.asin)}">${FAV.has(o.asin)?"♥":"♡"}</button><div class="tt">${esc(o.t)}</div><div class="row"><div class="now">${eur(o.ahora)}</div><div class="old">${eur(o.antes)}</div><div class="pct">-${o.pct}%</div></div><div class="meta">${o.cat?`<span class="cat">${esc(o.cat)}</span>`:""}${ago(o.ts)}</div><div class="two"><button class="btn" data-a="${esc(o.asin)}" data-u="${esc(o.url)}">Ver oferta</button><button class="btn sec" data-s="${esc(o.url)}" data-n="${esc(o.t)} a ${o.ahora} € (-${o.pct}%)">Compartir</button></div></div>`}\nfunction draw(){const q=document.getElementById("q").value.toLowerCase();let l=ALL.filter(o=>o.pct>=MIN&&o.t.toLowerCase().includes(q)&&(CAT==="Todas"||o.cat===CAT));const s=document.getElementById("ord").value;if(s==="d")l.sort((a,b)=>b.pct-a.pct);else if(s==="p")l.sort((a,b)=>a.ahora-b.ahora);document.getElementById("list").innerHTML=l.length?l.map(card).join(""):\'<div class="empty">No hay ofertas con ese filtro todavía.</div>\';const cs=["Todas",...new Set(ALL.map(o=>o.cat).filter(Boolean))];document.getElementById("cats").innerHTML=cs.map(c=>`<button class="chip${c===CAT?" on":""}" data-c="${esc(c)}">${esc(c)}</button>`).join("")}\nfunction drawFav(){document.getElementById("favs").innerHTML=FAVL.length?FAVL.map(card).join(""):\'<div class="empty">Toca el corazón ♡ de una oferta para guardarla aquí.</div>\'}\nasync function post(p,b){const r=await fetch(p,{method:"POST",headers:{...H,"Content-Type":"application/json"},body:JSON.stringify(b)});return r.json().catch(()=>({}))}\nasync function loadFav(){try{const r=await fetch("/api/fav",{headers:H});if(!r.ok)return;const j=await r.json();FAVL=j.fav||[];FAV=new Set(FAVL.map(o=>o.asin));drawFav();draw()}catch(e){}}\nasync function loadAl(){try{const r=await fetch("/api/alertas",{headers:H});if(!r.ok){document.getElementById("als").innerHTML=\'<div class="empty">Abre la app desde el bot para usar las alertas.</div>\';return}const j=await r.json();document.getElementById("als").innerHTML=(j.al||[]).length?j.al.map((a,i)=>`<div class="al"><div>${a.q?esc(a.q):"Cualquier producto"} · ${a.min?a.min+"%+":"cualquier descuento"}</div><button data-d="${i}">✕</button></div>`).join(""):\'<div class="empty">Aún no tienes alertas.</div>\'}catch(e){}}\ndocument.addEventListener("click",async e=>{const hb=e.target.closest(".hb");if(hb){const r=await post("/api/fav",{asin:hb.dataset.h});if(r.ok)loadFav();return}const sh=e.target.closest("[data-s]");if(sh){const u="https://t.me/share/url?url="+encodeURIComponent(sh.dataset.s)+"&text="+encodeURIComponent(sh.dataset.n);tg?tg.openTelegramLink(u):window.open(u,"_blank");return}const ch=e.target.closest("[data-c]");if(ch){CAT=ch.dataset.c;draw();return}const dl=e.target.closest("[data-d]");if(dl){await post("/api/alertas/del",{i:+dl.dataset.d});loadAl();return}const b=e.target.closest(".btn");if(!b||!b.dataset.a)return;fetch("/api/click",{method:"POST",headers:{...H,"Content-Type":"application/json"},body:JSON.stringify({asin:b.dataset.a})}).catch(()=>{});tg?tg.openLink(b.dataset.u):window.open(b.dataset.u,"_blank")});\ndocument.getElementById("q").oninput=draw;document.getElementById("ord").onchange=draw;\ndocument.getElementById("aadd").onclick=async()=>{const q=document.getElementById("aq").value.trim(),m=+document.getElementById("am").value;if(!q&&m<50){alert("Escribe un producto o elige 50% o más.");return}const r=await post("/api/alertas",{q,min:m});if(!r.ok){alert(r.error||"No se pudo crear");return}document.getElementById("aq").value="";loadAl()};\n[["Todas",0],["30%+",30],["50%+",50],["70%+",70]].forEach(([n,v])=>{const c=document.createElement("button");c.className="chip"+(v===0?" on":"");c.textContent=n;c.onclick=()=>{MIN=v;document.querySelectorAll(".chip").forEach(x=>x.classList.remove("on"));c.classList.add("on");draw()};document.getElementById("chips").appendChild(c)});\ndocument.querySelectorAll(".tabs button").forEach(b=>b.onclick=()=>{document.querySelectorAll(".tabs button").forEach(x=>x.classList.remove("on"));b.classList.add("on");["of","fv","al","top","ad"].forEach(t=>document.getElementById("t-"+t).classList.toggle("hide",t!==b.dataset.t));if(b.dataset.t==="top")loadTop();if(b.dataset.t==="fv")loadFav();if(b.dataset.t==="al")loadAl();if(b.dataset.t==="ad")loadAdmin()});\nasync function load(){try{const r=await fetch("/api/ofertas",{headers:H});const j=await r.json();ALL=j.ofertas||[];if(j.admin)document.getElementById("adbtn").classList.remove("hide");document.getElementById("sub").textContent=ALL.length?`${ALL.length} ofertas recientes`:"Esperando nuevas ofertas";draw()}catch(e){document.getElementById("list").innerHTML=\'<div class="empty">No se pudo cargar. Inténtalo de nuevo.</div>\'}}\nasync function loadTop(){const r=await fetch("/api/top",{headers:H});const j=await r.json();document.getElementById("top").innerHTML=(j.descuento||[]).length?j.descuento.map(card).join(""):\'<div class="empty">Aún no hay datos.</div>\';document.getElementById("clk").innerHTML=(j.clicks||[]).length?j.clicks.map(c=>`<div class="card"><div class="tt">${esc(c.t)}</div><div class="meta">${c.n} pulsaciones</div></div>`).join(""):\'<div class="empty">Todavía nadie ha pulsado.</div>\'}\nasync function loadAdmin(){const r=await fetch("/api/admin",{headers:H});if(!r.ok)return;const j=await r.json();document.getElementById("stats").innerHTML=j.stats.map(s=>`<div class="st"><b>${esc(s[1])}</b><span>${esc(s[0])}</span></div>`).join("");document.getElementById("sws").innerHTML=j.toggles.map(t=>`<div class="sw"><div>${esc(t.nombre)}</div><button class="${t.on?"on":""}" data-k="${t.k}"></button></div>`).join("");document.querySelectorAll(".sw button").forEach(b=>b.onclick=async()=>{await fetch("/api/admin/toggle",{method:"POST",headers:{...H,"Content-Type":"application/json"},body:JSON.stringify({k:b.dataset.k})});loadAdmin()})}\nload();loadFav();setInterval(load,60000);\n</script></body></html>\n'

TAIL = r'''# --- MINIAPP2 ---
_MI_CATS = [
    ("Tecnologia", ["auricular", "movil", "smartphone", "tablet", "portatil", "ordenador", "monitor", "teclado", "raton", "cargador", "cable", "camara", "altavoz", "smartwatch", "reloj", "tv ", "television", "router", "ssd", "disco", "usb", "bluetooth", "samsung", "xiaomi", "apple", "sony", "kindle", "echo", "playstation", "xbox", "nintendo", "consola", "impresora", "gaming"]),
    ("Hogar", ["cafetera", "aspirador", "robot", "freidora", "cocina", "sarten", "olla", "colchon", "almohada", "sabana", "lampara", "silla", "mesa", "estanteria", "nevera", "microondas", "batidora", "plancha", "ventilador", "calefactor", "limpieza", "toalla", "cortina", "delonghi", "dyson", "cecotec", "taurus", "bosch"]),
    ("Juguetes", ["lego", "juguete", "muneca", "puzzle", "juego de mesa", "playmobil", "peluche", "nerf", "hot wheels", "barbie", "figura"]),
    ("Moda", ["zapatilla", "camiseta", "pantalon", "chaqueta", "vestido", "bolso", "mochila", "gafas", "cinturon", "sudadera", "reloj de", "nike", "adidas", "puma", "levi", "calcetin"]),
    ("Belleza", ["crema", "perfume", "champu", "maquillaje", "afeitadora", "cepillo", "secador", "plancha de pelo", "serum", "gillette", "oral-b", "braun", "philips"]),
    ("Deporte", ["bicicleta", "pesas", "mancuerna", "yoga", "running", "fitness", "tienda de campana", "patinete", "balon", "raqueta", "bandas elasticas"]),
]

def _mi_cat(t):
    import unicodedata
    s = unicodedata.normalize("NFD", str(t).lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn") + " "
    for nombre, kws in _MI_CATS:
        for k in kws:
            if k in s:
                return nombre
    return "Otros"

def _mi_publicas(d):
    campos = ("asin", "t", "ahora", "antes", "pct", "url", "ts")
    return [dict({k: o[k] for k in campos}, cat=_mi_cat(o["t"])) for o in _mi_d(d)["of"][:40]]

def _mi_limpio(t):
    return re.sub(r"[<>&]", "", str(t))[:100]

def _mi_alertas(d, o):
    m = _mi_d(d)
    tl = o["t"].lower()
    for uid, lst in list((m.get("al") or {}).items()):
        enviados = m.setdefault("alsent", {}).setdefault(uid, [])
        if o["asin"] in enviados:
            continue
        for a in lst:
            ws = a["q"].lower().split()
            if o["pct"] >= a["min"] and all(w in tl for w in ws) and (ws or a["min"] >= 50):
                try:
                    enviar(uid, "\U0001f514 Tu alerta: %s\n%.2f EUR (antes %.2f EUR, -%d%%)\n%s\nPrecio a la hora del aviso; puede cambiar." % (_mi_limpio(o["t"]), o["ahora"], o["antes"], o["pct"], o["url"]))
                except Exception as e:
                    print("error alerta", e, flush=True)
                enviados.append(o["asin"])
                del enviados[:-100]
                break

_enviar_aviso_pre_mi2 = enviar_aviso

def enviar_aviso(d, cid, item):
    r = _enviar_aviso_pre_mi2(d, cid, item)
    try:
        if not item.get("_al"):
            item["_al"] = True
            mm = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", str(item.get("u") or ""))
            if mm:
                lim = time.time() - 15
                for o in _mi_d(d)["of"][:3]:
                    if o["asin"] == mm.group(1) and o["ts"] >= lim:
                        _mi_alertas(d, o)
                        break
    except Exception as e:
        print("error miniapp alertas", e, flush=True)
    return r

_mi_get0 = _MiHandler.do_GET
_mi_post0 = _MiHandler.do_POST

def _mi_get1(self):
    p = self.path.split("?")[0]
    if p in ("/api/fav", "/api/alertas"):
        d = _mi["d"]
        if d is None:
            return self._json({"error": "arrancando"}, 503)
        uid = self._uid()
        if not uid:
            return self._json({"error": "no autorizado"}, 403)
        m = _mi_d(d)
        if p == "/api/fav":
            return self._json({"fav": [dict(o, cat=_mi_cat(o["t"])) for o in m.setdefault("fav", {}).get(uid, [])]})
        return self._json({"al": m.setdefault("al", {}).get(uid, [])})
    return _mi_get0(self)

def _mi_post1(self):
    p = self.path.split("?")[0]
    if p in ("/api/fav", "/api/alertas", "/api/alertas/del"):
        d = _mi["d"]
        try:
            n = min(int(self.headers.get("Content-Length", "0")), 2000)
            body = _mi_json.loads(self.rfile.read(n) or b"{}")
            uid = self._uid()
            if d is None:
                return self._json({"error": "arrancando"}, 503)
            if not uid:
                return self._json({"error": "no autorizado"}, 403)
            m = _mi_d(d)
            if p == "/api/fav":
                a = str(body.get("asin", ""))
                favs = m.setdefault("fav", {}).setdefault(uid, [])
                if any(o["asin"] == a for o in favs):
                    favs[:] = [o for o in favs if o["asin"] != a]
                else:
                    o = next((x for x in m["of"] if x["asin"] == a), None)
                    if o is None:
                        return self._json({"ok": False, "error": "oferta no disponible"})
                    favs.insert(0, {k: o[k] for k in ("asin", "t", "ahora", "antes", "pct", "url", "ts")})
                    del favs[50:]
                return self._json({"ok": True})
            lst = m.setdefault("al", {}).setdefault(uid, [])
            if p == "/api/alertas/del":
                i = int(body.get("i", -1))
                if 0 <= i < len(lst):
                    del lst[i]
                return self._json({"ok": True})
            q = re.sub(r"[^\w\s\-]", "", str(body.get("q", "")), flags=re.U).strip()[:40]
            mn = max(0, min(90, int(body.get("min", 0))))
            if not q and mn < 50:
                return self._json({"ok": False, "error": "Escribe un producto o elige 50% o mas"})
            if len(lst) >= 5:
                return self._json({"ok": False, "error": "Maximo 5 alertas"})
            lst.append({"q": q, "min": mn})
            return self._json({"ok": True})
        except Exception as e:
            print("error miniapp", e, flush=True)
            try:
                self._json({"ok": False, "error": "fallo"}, 500)
            except Exception:
                pass
            return
    return _mi_post0(self)

_MiHandler.do_GET = _mi_get1
_MiHandler.do_POST = _mi_post1

'''

n = len(re.findall(r'^if __name__ == ["\']__main__["\']:', src, re.M))
if n != 1:
    print("ABORTO: ancla main encontrada %d veces" % n); sys.exit(1)
src = re.sub(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), src, count=1, flags=re.M)
try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)
copia = RUTA + ".bak_miniapp2_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
carpeta = os.path.join(os.path.dirname(os.path.abspath(RUTA)), "miniapp")
os.makedirs(carpeta, exist_ok=True)
open(os.path.join(carpeta, "index.html"), "w", encoding="utf-8").write(HTML)
print("Parche aplicado. Copia de seguridad:", copia)
print("Ahora ejecuta: systemctl restart chivato")
