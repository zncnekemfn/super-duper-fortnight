import re, shutil, time, sys, os

RUTA = sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato/bot.py"
src = open(RUTA, encoding="utf-8").read()
if "# --- MINIAPP ---" in src:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)
if "def comando(d, cid, texto):" not in src:
    print("ABORTO: no encuentro la funcion comando"); sys.exit(1)

HTML = '<!doctype html>\n<html lang="es"><head><meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n<title>Chivato de Ofertas</title>\n<script src="https://telegram.org/js/telegram-web-app.js"></script>\n<style>\n:root{--bg:#0b1433;--bg2:#12214f;--card:#16275a;--line:#2a3f7a;--tx:#fff;--mut:#9fb0d6;--or:#ff8f1f;--ok:#79e89a;--bad:#ff6b6b}\n*{box-sizing:border-box;margin:0;-webkit-tap-highlight-color:transparent}\nbody{background:linear-gradient(180deg,var(--bg),var(--bg2));color:var(--tx);font:16px/1.4 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;min-height:100vh;padding:0 16px 90px}\nheader{padding:18px 0 8px}\nh1{font-size:22px}h1 span{color:var(--or)}\n.sub{color:var(--mut);font-size:14px;margin-top:2px}\n.tabs{position:fixed;left:0;right:0;bottom:0;display:flex;background:#0a1230;border-top:1px solid var(--line);padding:8px 8px calc(8px + env(safe-area-inset-bottom));gap:6px;z-index:5}\n.tabs button{flex:1;background:none;border:0;color:var(--mut);font:600 13px system-ui;padding:8px 4px;border-radius:12px}\n.tabs button.on{background:var(--card);color:var(--or)}\n.chips{display:flex;gap:8px;overflow-x:auto;padding:10px 0;scrollbar-width:none}\n.chip{flex:none;background:var(--card);border:1px solid var(--line);color:var(--tx);border-radius:999px;padding:7px 14px;font:600 14px system-ui}\n.chip.on{background:var(--or);border-color:var(--or);color:#0b1433}\ninput.q{width:100%;background:var(--card);border:1px solid var(--line);border-radius:12px;color:var(--tx);padding:11px 14px;font-size:16px;margin-bottom:4px}\n.card{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:14px;margin:10px 0}\n.tt{font-weight:700;font-size:15px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}\n.row{display:flex;align-items:center;gap:12px;margin-top:10px}\n.now{font-size:28px;font-weight:800;color:var(--ok)}\n.old{color:var(--mut);text-decoration:line-through;font-size:15px}\n.pct{margin-left:auto;background:#e62832;border-radius:999px;padding:6px 12px;font-weight:800}\n.meta{color:var(--mut);font-size:12px;margin-top:6px}\n.btn{display:block;width:100%;margin-top:12px;background:var(--or);color:#0b1433;border:0;border-radius:12px;padding:12px;font:800 15px system-ui}\n.empty{color:var(--mut);text-align:center;padding:40px 10px}\n.legal{color:var(--mut);font-size:11.5px;margin:18px 0 6px;line-height:1.45}\n.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:12px 0}\n.st{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px}\n.st b{display:block;font-size:26px}.st span{color:var(--mut);font-size:13px}\n.sw{display:flex;align-items:center;justify-content:space-between;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:13px 14px;margin:8px 0}\n.sw button{width:52px;height:30px;border-radius:999px;border:0;background:#43527f;position:relative}\n.sw button:after{content:"";position:absolute;top:3px;left:3px;width:24px;height:24px;border-radius:50%;background:#fff;transition:.2s}\n.sw button.on{background:var(--ok)}.sw button.on:after{left:25px}\nh2{font-size:17px;margin:16px 0 4px}\n.hide{display:none}\n</style></head><body>\n<header><h1>Chivato <span>de Ofertas</span></h1><div class="sub" id="sub">Ofertas filtradas, al momento</div></header>\n<section id="t-of"><input class="q" id="q" placeholder="Buscar producto…" inputmode="search">\n<div class="chips" id="chips"></div><div id="list"></div></section>\n<section id="t-top" class="hide"><h2>Mayor descuento (24 h)</h2><div id="top"></div><h2>Más pulsadas en la app</h2><div id="clk"></div></section>\n<section id="t-ad" class="hide"><h2>Resumen</h2><div class="grid" id="stats"></div><h2>Funciones</h2><div id="sws"></div></section>\n<div class="legal" id="legal">Como afiliado de Amazon obtengo ingresos por las compras adscritas. Los precios corresponden al momento del aviso y pueden cambiar.</div>\n<nav class="tabs"><button class="on" data-t="of">Ofertas</button><button data-t="top">Top</button><button data-t="ad" id="adbtn" class="hide">Admin</button></nav>\n<script>\nconst tg=window.Telegram&&Telegram.WebApp;if(tg){tg.ready();tg.expand();try{tg.setHeaderColor("#0b1433");tg.setBackgroundColor("#0b1433")}catch(e){}}\nconst H={"X-Init":(tg&&tg.initData)||""};let ALL=[],MIN=0;\nconst eur=n=>Number(n).toFixed(2).replace(".",",")+" €";\nconst esc=s=>String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",\'"\':"&quot;"}[c]));\nfunction ago(ts){const m=Math.max(1,Math.round((Date.now()/1000-ts)/60));return m<60?`hace ${m} min`:m<1440?`hace ${Math.round(m/60)} h`:`hace ${Math.round(m/1440)} d`}\nfunction card(o){return `<div class="card"><div class="tt">${esc(o.t)}</div><div class="row"><div class="now">${eur(o.ahora)}</div><div class="old">${eur(o.antes)}</div><div class="pct">-${o.pct}%</div></div><div class="meta">${ago(o.ts)}</div><button class="btn" data-a="${esc(o.asin)}" data-u="${esc(o.url)}">Ver oferta</button></div>`}\nfunction draw(){const q=document.getElementById("q").value.toLowerCase();const l=ALL.filter(o=>o.pct>=MIN&&o.t.toLowerCase().includes(q));document.getElementById("list").innerHTML=l.length?l.map(card).join(""):\'<div class="empty">No hay ofertas con ese filtro todavía.</div>\'}\ndocument.addEventListener("click",e=>{const b=e.target.closest(".btn");if(!b)return;fetch("/api/click",{method:"POST",headers:{...H,"Content-Type":"application/json"},body:JSON.stringify({asin:b.dataset.a})}).catch(()=>{});tg?tg.openLink(b.dataset.u):window.open(b.dataset.u,"_blank")});\ndocument.getElementById("q").oninput=draw;\n[["Todas",0],["30%+",30],["50%+",50],["70%+",70]].forEach(([n,v])=>{const c=document.createElement("button");c.className="chip"+(v===0?" on":"");c.textContent=n;c.onclick=()=>{MIN=v;document.querySelectorAll(".chip").forEach(x=>x.classList.remove("on"));c.classList.add("on");draw()};document.getElementById("chips").appendChild(c)});\ndocument.querySelectorAll(".tabs button").forEach(b=>b.onclick=()=>{document.querySelectorAll(".tabs button").forEach(x=>x.classList.remove("on"));b.classList.add("on");["of","top","ad"].forEach(t=>document.getElementById("t-"+t).classList.toggle("hide",t!==b.dataset.t));if(b.dataset.t==="top")loadTop();if(b.dataset.t==="ad")loadAdmin()});\nasync function load(){try{const r=await fetch("/api/ofertas",{headers:H});const j=await r.json();ALL=j.ofertas||[];if(j.admin)document.getElementById("adbtn").classList.remove("hide");document.getElementById("sub").textContent=ALL.length?`${ALL.length} ofertas recientes`:"Esperando nuevas ofertas";draw()}catch(e){document.getElementById("list").innerHTML=\'<div class="empty">No se pudo cargar. Inténtalo de nuevo.</div>\'}}\nasync function loadTop(){const r=await fetch("/api/top",{headers:H});const j=await r.json();document.getElementById("top").innerHTML=(j.descuento||[]).length?j.descuento.map(card).join(""):\'<div class="empty">Aún no hay datos.</div>\';document.getElementById("clk").innerHTML=(j.clicks||[]).length?j.clicks.map(c=>`<div class="card"><div class="tt">${esc(c.t)}</div><div class="meta">${c.n} pulsaciones</div></div>`).join(""):\'<div class="empty">Todavía nadie ha pulsado.</div>\'}\nasync function loadAdmin(){const r=await fetch("/api/admin",{headers:H});if(!r.ok)return;const j=await r.json();document.getElementById("stats").innerHTML=j.stats.map(s=>`<div class="st"><b>${esc(s[1])}</b><span>${esc(s[0])}</span></div>`).join("");document.getElementById("sws").innerHTML=j.toggles.map(t=>`<div class="sw"><div>${esc(t.nombre)}</div><button class="${t.on?"on":""}" data-k="${t.k}"></button></div>`).join("");document.querySelectorAll(".sw button").forEach(b=>b.onclick=async()=>{await fetch("/api/admin/toggle",{method:"POST",headers:{...H,"Content-Type":"application/json"},body:JSON.stringify({k:b.dataset.k})});loadAdmin()})}\nload();setInterval(load,60000);\n</script></body></html>\n'

def unico(patron, fn, nombre):
    global src
    n = len(re.findall(patron, src, re.M))
    if n != 1:
        print("ABORTO: ancla '%s' encontrada %d veces" % (nombre, n)); sys.exit(1)
    src = re.sub(patron, fn, src, count=1, flags=re.M)

TAIL = r'''# --- MINIAPP ---
import os as _mi_os, hmac as _mi_hmac, hashlib as _mi_hash, json as _mi_json, threading as _mi_th
import urllib.parse as _mi_up
from http.server import BaseHTTPRequestHandler as _MiH, ThreadingHTTPServer as _MiS

MI_PORT = int(_mi_os.environ.get("MINIAPP_PORT", "8765"))
MI_MAX = 80
_mi = {"d": None, "srv": None}

def _mi_d(d):
    m = d.setdefault("mini", {})
    m.setdefault("of", [])
    m.setdefault("clicks", {})
    m.setdefault("url", "")
    return m

def _mi_precios(texto, pct):
    t = str(texto or "")
    nums = [float(x.replace(",", ".")) for x in re.findall(r"(\d+[.,]\d\d) ?(?:EUR|€)", t)]
    if not nums:
        return None
    ahora = nums[0]
    antes = nums[1] if len(nums) > 1 and nums[1] > nums[0] else None
    if antes is None and pct and 0 < pct < 95:
        antes = round(ahora / (1 - pct / 100.0), 2)
    return (ahora, antes) if antes else None

def _mi_registrar(d, item):
    m = _mi_d(d)
    asin = ""
    mm = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", str(item.get("u") or ""))
    if mm:
        asin = mm.group(1)
    pct = int(item.get("d") or 0)
    pre = _mi_precios(item.get("t"), pct)
    if not asin or not pre or pct <= 0:
        return
    tit = re.sub(r" - \d+[.,]\d\d.*", "", str(item.get("t") or ""), flags=re.S).strip()
    tit = re.sub(r"(?i)\bamazon\b", "", tit)
    tit = re.sub(r"\s+", " ", tit).strip() or asin
    if any(o["asin"] == asin for o in m["of"][:15]):
        return
    m["of"].insert(0, {"asin": asin, "t": tit[:110], "ahora": pre[0], "antes": pre[1], "pct": pct, "url": str(item.get("u")), "ts": int(time.time())})
    del m["of"][MI_MAX:]

def _mi_auth(init):
    """Valida initData de Telegram y devuelve el id de usuario o None."""
    try:
        tok = globals().get("TG_TOKEN") or globals().get("TOKEN") or globals().get("BOT_TOKEN")
        if not init or not tok:
            return None
        datos = dict(_mi_up.parse_qsl(init, keep_blank_values=True))
        h = datos.pop("hash", "")
        dcs = "\n".join("%s=%s" % (k, datos[k]) for k in sorted(datos))
        sec = _mi_hmac.new(b"WebAppData", str(tok).encode(), _mi_hash.sha256).digest()
        calc = _mi_hmac.new(sec, dcs.encode(), _mi_hash.sha256).hexdigest()
        if not _mi_hmac.compare_digest(calc, h):
            return None
        if time.time() - int(datos.get("auth_date", "0")) > 86400:
            return None
        return str(_mi_json.loads(datos.get("user", "{}")).get("id"))
    except Exception:
        return None

def _mi_es_admin(uid):
    return uid is not None and str(uid) == str(ADMIN)

def _mi_publicas(d):
    return [{k: o[k] for k in ("asin", "t", "ahora", "antes", "pct", "url", "ts")} for o in _mi_d(d)["of"][:40]]

def _mi_tog(d):
    q = d.setdefault("q", {}); v = d.setdefault("video", {})
    return [("calidad", "Filtro de calidad", lambda: q.get("on", True), lambda x: q.__setitem__("on", x)),
            ("video", "Videos automaticos", lambda: v.get("on", False), lambda x: v.__setitem__("on", x)),
            ("gato", "Gato animado en videos", lambda: v.get("gato", True), lambda x: v.__setitem__("gato", x)),
            ("foto", "Fotos en videos (uso privado)", lambda: v.get("foto", False), lambda x: v.__setitem__("foto", x))]

class _MiHandler(_MiH):
    def log_message(self, *a):
        pass
    def _json(self, obj, code=200):
        b = _mi_json.dumps(obj).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def _uid(self):
        return _mi_auth(self.headers.get("X-Init", ""))
    def do_GET(self):
        d = _mi["d"]
        try:
            if self.path in ("/", "/index.html"):
                ruta = _mi_os.path.join(_mi_os.path.dirname(_mi_os.path.abspath(__file__)), "miniapp", "index.html")
                b = open(ruta, "rb").read()
                self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b); return
            if d is None:
                return self._json({"error": "arrancando"}, 503)
            if self.path.startswith("/api/ofertas"):
                return self._json({"ofertas": _mi_publicas(d), "admin": _mi_es_admin(self._uid())})
            if self.path.startswith("/api/top"):
                m = _mi_d(d); lim = time.time() - 86400
                top = sorted([o for o in m["of"] if o["ts"] >= lim], key=lambda o: -o["pct"])[:10]
                nom = {o["asin"]: o["t"] for o in m["of"]}
                cl = sorted(m["clicks"].items(), key=lambda x: -x[1])[:10]
                return self._json({"descuento": [{k: o[k] for k in ("asin", "t", "ahora", "antes", "pct", "url", "ts")} for o in top],
                                   "clicks": [{"t": nom.get(a, a), "n": n} for a, n in cl]})
            if self.path.startswith("/api/admin"):
                if not _mi_es_admin(self._uid()):
                    return self._json({"error": "no autorizado"}, 403)
                m = _mi_d(d); lim = time.time() - 86400; q = d.get("q") or {}
                st = [["Usuarios", len(d.get("users") or {})], ["Ofertas 24 h", sum(1 for o in m["of"] if o["ts"] >= lim)],
                      ["Pulsaciones app", sum(m["clicks"].values())], ["Rechazadas por calidad", q.get("no", 0)]]
                return self._json({"stats": st, "toggles": [{"k": k, "nombre": n, "on": bool(g())} for k, n, g, s in _mi_tog(d)]})
            self._json({"error": "no existe"}, 404)
        except Exception as e:
            print("error miniapp", e, flush=True)
            try:
                self._json({"error": "fallo"}, 500)
            except Exception:
                pass
    def do_POST(self):
        d = _mi["d"]
        try:
            n = min(int(self.headers.get("Content-Length", "0")), 2000)
            body = _mi_json.loads(self.rfile.read(n) or b"{}")
            uid = self._uid()
            if d is None:
                return self._json({"error": "arrancando"}, 503)
            if self.path == "/api/click":
                a = str(body.get("asin", ""))
                if uid and re.fullmatch(r"[A-Z0-9]{10}", a):
                    c = _mi_d(d)["clicks"]; c[a] = c.get(a, 0) + 1
                return self._json({"ok": True})
            if self.path == "/api/admin/toggle":
                if not _mi_es_admin(uid):
                    return self._json({"error": "no autorizado"}, 403)
                for k, nombre, g, s in _mi_tog(d):
                    if k == body.get("k"):
                        s(not g())
                return self._json({"ok": True})
            self._json({"error": "no existe"}, 404)
        except Exception as e:
            print("error miniapp", e, flush=True)
            try:
                self._json({"error": "fallo"}, 500)
            except Exception:
                pass

def _mi_arrancar():
    if _mi["srv"] is not None:
        return
    try:
        s = _MiS(("127.0.0.1", MI_PORT), _MiHandler)
        _mi["srv"] = s
        _mi_th.Thread(target=s.serve_forever, daemon=True).start()
        print("miniapp escuchando en 127.0.0.1:%d" % MI_PORT, flush=True)
    except Exception as e:
        print("no se pudo arrancar la miniapp", e, flush=True)

def mini_cmd(d, cid, args):
    m = _mi_d(d)
    if args and args[0].lower() == "url" and str(cid) == str(ADMIN):
        if len(args) > 1 and args[1].startswith("https://"):
            m["url"] = args[1].rstrip("/")
            enviar(cid, "URL de la app guardada: %s" % m["url"])
        else:
            enviar(cid, "Usa: /app url https://tu-direccion (tiene que empezar por https://)")
        return
    if not m["url"]:
        enviar(cid, "La app todavia no esta lista." + ("\nConfigura la direccion con: /app url https://..." if str(cid) == str(ADMIN) else ""))
        return
    kb = {"inline_keyboard": [[{"text": "\U0001f4f1 Abrir Chivato de Ofertas", "web_app": {"url": m["url"]}}]]}
    enviar(cid, "\U0001f4f1 La app del Chivato: ofertas filtradas, buscador y ranking en un solo sitio.", _mi_json.dumps(kb))

_enviar_aviso_pre_mi = enviar_aviso

def enviar_aviso(d, cid, item):
    _mi["d"] = d
    _mi_arrancar()
    r = _enviar_aviso_pre_mi(d, cid, item)
    try:
        q = item.get("_q")
        if not item.get("_mi") and not (q and not q[0]):
            item["_mi"] = True
            _mi_registrar(d, item)
    except Exception as e:
        print("error miniapp registro", e, flush=True)
    return r

_comando_pre_mi = comando

def comando(d, cid, texto):
    _mi["d"] = d
    _mi_arrancar()
    return _comando_pre_mi(d, cid, texto)

'''

unico(r'^    elif cmd in \("/propina", "/premium"\):\n',
      lambda m: '    elif cmd == "/app":\n        mini_cmd(d, cid, args)\n' + m.group(0), "propina")
unico(r'^if __name__ == ["\']__main__["\']:', lambda m: TAIL + m.group(0), "main")
try:
    compile(src, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: el resultado no compila:", e); sys.exit(1)
copia = RUTA + ".bak_miniapp_" + time.strftime("%Y%m%d%H%M%S")
shutil.copy(RUTA, copia)
open(RUTA, "w", encoding="utf-8").write(src)
carpeta = os.path.join(os.path.dirname(os.path.abspath(RUTA)), "miniapp")
os.makedirs(carpeta, exist_ok=True)
open(os.path.join(carpeta, "index.html"), "w", encoding="utf-8").write(HTML)
print("Parche aplicado. Copia de seguridad:", copia)
print("App guardada en:", carpeta)
print("Ahora ejecuta: systemctl restart chivato")
