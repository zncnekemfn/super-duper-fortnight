#!/usr/bin/env bash
# Instalador del Centro de mando de bots (panel tipo Rerun) para tu VPS.
# Uso: bash instalar-panel.sh      (como root)
set -euo pipefail
D=/opt/panel
[ "$(id -u)" = 0 ] || { echo "Ejecutalo como root"; exit 1; }
command -v node >/dev/null || { echo "Falta Node.js (pm2 lo necesita)."; exit 1; }
command -v pm2  >/dev/null || { echo "Falta pm2: npm i -g pm2"; exit 1; }
NODE_MAJOR=$(node -p 'process.versions.node.split(".")[0]')
[ "$NODE_MAJOR" -ge 16 ] || { echo "Node $NODE_MAJOR es muy antiguo; hace falta 16 o mas."; exit 1; }
mkdir -p "$D/public"
cat > "$D/server.js" <<'__PANEL_EOF__'
// Panel de bots · servidor sin dependencias (Node >= 16)
// Lee pm2, transmite logs en directo, gestiona aprobaciones y sirve el panel.
"use strict";
const http = require("http");
const fs = require("fs");
const path = require("path");
const os = require("os");
const crypto = require("crypto");
const { execFile } = require("child_process");

const DIR = __dirname;

// ---------- configuración (.env) ----------
function loadEnv() {
  const f = path.join(DIR, ".env");
  if (!fs.existsSync(f)) return;
  for (const line of fs.readFileSync(f, "utf8").split("\n")) {
    const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/);
    if (m && !(m[1] in process.env)) process.env[m[1]] = m[2].replace(/^["']|["']$/g, "");
  }
}
loadEnv();
const PORT = parseInt(process.env.PANEL_PORT || "8080", 10);
const HOST = process.env.PANEL_HOST || "0.0.0.0";
const PASS = process.env.PANEL_PASS || "";
const BOT_KEY = process.env.PANEL_BOT_KEY || "";
const TG_TOKEN = process.env.PANEL_TG_TOKEN || "";
const TG_CHAT = process.env.PANEL_TG_CHAT || "";
const PANEL_URL = process.env.PANEL_URL || "";
const SELF = process.env.PANEL_PM2_NAME || "panel";
if (!PASS || PASS.length < 8) { console.error("Falta PANEL_PASS (mínimo 8 caracteres) en .env"); process.exit(1); }

// ---------- utilidades ----------
const sha = s => crypto.createHash("sha256").update(String(s)).digest();
const safeEq = (a, b) => crypto.timingSafeEqual(sha(a), sha(b));
function readJSON(file, def) { try { return JSON.parse(fs.readFileSync(path.join(DIR, file), "utf8")); } catch { return def; } }
function writeJSON(file, data) { const p = path.join(DIR, file); fs.writeFileSync(p + ".tmp", JSON.stringify(data, null, 2)); fs.renameSync(p + ".tmp", p); }
function send(res, code, body, headers = {}) {
  const isObj = typeof body === "object";
  res.writeHead(code, { "Content-Type": isObj ? "application/json; charset=utf-8" : "text/plain; charset=utf-8", "Cache-Control": "no-store", ...headers });
  res.end(isObj ? JSON.stringify(body) : body);
}
function readBody(req, max = 64 * 1024) {
  return new Promise((ok, ko) => {
    let n = 0; const chunks = [];
    req.on("data", c => { n += c.length; if (n > max) { ko(new Error("too big")); req.destroy(); } else chunks.push(c); });
    req.on("end", () => { try { ok(chunks.length ? JSON.parse(Buffer.concat(chunks).toString("utf8")) : {}); } catch { ko(new Error("bad json")); } });
    req.on("error", ko);
  });
}
function run(cmd, args, timeout = 15000) {
  return new Promise(ok => execFile(cmd, args, { timeout, maxBuffer: 20 * 1024 * 1024 }, (err, stdout, stderr) => ok({ err, stdout: String(stdout), stderr: String(stderr) })));
}
function clientIp(req) { return (req.socket.remoteAddress || "").replace(/^::ffff:/, ""); }

// ---------- sesiones ----------
const SESS_FILE = "sessions.json";
const sessions = new Map(Object.entries(readJSON(SESS_FILE, {})));
const SESSION_DAYS = 30;
function saveSessions() { writeJSON(SESS_FILE, Object.fromEntries(sessions)); }
function getSession(req) {
  const m = (req.headers.cookie || "").match(/(?:^|;\s*)psid=([a-f0-9]{64})/);
  if (!m) return null;
  const s = sessions.get(m[1]);
  if (!s || s.exp < Date.now()) { if (s) { sessions.delete(m[1]); saveSessions(); } return null; }
  return m[1];
}
const fails = new Map(); // ip -> {n, until}
function blocked(ip) { const f = fails.get(ip); return f && f.n >= 5 && f.until > Date.now(); }
function addFail(ip) { const f = fails.get(ip) || { n: 0, until: 0 }; if (f.until < Date.now()) f.n = 0; f.n++; f.until = Date.now() + 15 * 60 * 1000; fails.set(ip, f); }

// ---------- pm2 ----------
async function pm2List() {
  const r = await run("pm2", ["jlist"]);
  if (r.err) throw new Error("pm2 no responde: " + (r.stderr || r.err.message).slice(0, 200));
  const start = r.stdout.indexOf("[");
  const list = JSON.parse(r.stdout.slice(start));
  return list.map(p => ({
    name: p.name,
    id: p.pm_id,
    status: p.pm2_env.status,
    cpu: p.monit ? p.monit.cpu : 0,
    memory: p.monit ? p.monit.memory : 0,
    uptime: p.pm2_env.pm_uptime,
    restarts: p.pm2_env.restart_time,
    cwd: p.pm2_env.pm_cwd,
    script: p.pm2_env.pm_exec_path,
    interpreter: p.pm2_env.exec_interpreter,
    out: p.pm2_env.pm_out_log_path,
    errLog: p.pm2_env.pm_err_log_path
  }));
}

// ---------- estadísticas del servidor ----------
let lastCpu = null;
function cpuSnapshot() {
  const l = fs.readFileSync("/proc/stat", "utf8").split("\n")[0].trim().split(/\s+/).slice(1).map(Number);
  const idle = l[3] + (l[4] || 0); const total = l.reduce((a, b) => a + b, 0);
  return { idle, total };
}
function cpuPercent() {
  try {
    const now = cpuSnapshot();
    if (!lastCpu) { lastCpu = now; return Math.round(os.loadavg()[0] / os.cpus().length * 100); }
    const di = now.idle - lastCpu.idle, dt = now.total - lastCpu.total; lastCpu = now;
    return dt > 0 ? Math.max(0, Math.min(100, Math.round((1 - di / dt) * 100))) : 0;
  } catch { return Math.round(os.loadavg()[0] / os.cpus().length * 100); }
}
function memInfo() {
  try {
    const t = fs.readFileSync("/proc/meminfo", "utf8");
    const g = k => parseInt((t.match(new RegExp("^" + k + ":\\s+(\\d+)", "m")) || [0, 0])[1], 10) * 1024;
    return { total: g("MemTotal"), used: g("MemTotal") - g("MemAvailable") };
  } catch { return { total: os.totalmem(), used: os.totalmem() - os.freemem() }; }
}
async function diskInfo() {
  const r = await run("df", ["-B1", "/"]);
  const l = r.stdout.trim().split("\n")[1]; if (!l) return { total: 0, used: 0 };
  const p = l.split(/\s+/); return { total: +p[1], used: +p[2] };
}

// ---------- logs ----------
function tailFile(file, lines) {
  try {
    const st = fs.statSync(file); const len = Math.min(st.size, 64 * 1024);
    const fd = fs.openSync(file, "r"); const buf = Buffer.alloc(len);
    fs.readSync(fd, buf, 0, len, st.size - len); fs.closeSync(fd);
    const arr = buf.toString("utf8").split("\n"); if (len < st.size) arr.shift();
    return { lines: arr.filter(Boolean).slice(-lines), size: st.size };
  } catch { return { lines: [], size: 0 }; }
}
function readFrom(file, pos) {
  try {
    const st = fs.statSync(file);
    if (st.size < pos) pos = 0; // log rotado
    if (st.size === pos) return { text: "", pos };
    const len = Math.min(st.size - pos, 256 * 1024);
    const fd = fs.openSync(file, "r"); const buf = Buffer.alloc(len);
    fs.readSync(fd, buf, 0, len, st.size - len); fs.closeSync(fd);
    return { text: buf.toString("utf8"), pos: st.size };
  } catch { return { text: "", pos }; }
}
async function streamLogs(req, res, name) {
  const list = await pm2List();
  const p = list.find(x => x.name === name);
  if (!p) return send(res, 404, { error: "No existe ese proceso" });
  res.writeHead(200, { "Content-Type": "text/event-stream", "Cache-Control": "no-store", Connection: "keep-alive", "X-Accel-Buffering": "no" });
  const ev = (kind, line) => res.write(`data: ${JSON.stringify({ k: kind, l: line, t: Date.now() })}\n\n`);
  const files = [{ f: p.out, k: "out" }, { f: p.errLog, k: "err" }].filter(x => x.f && x.f !== "/dev/null");
  const initial = [];
  for (const x of files) { const t = tailFile(x.f, 150); x.pos = t.size; x.rest = ""; t.lines.forEach(l => initial.push({ k: x.k, l })); }
  initial.slice(-150).forEach(i => ev(i.k, i.l));
  const timer = setInterval(() => {
    for (const x of files) {
      const r = readFrom(x.f, x.pos); x.pos = r.pos; if (!r.text) continue;
      const parts = (x.rest + r.text).split("\n"); x.rest = parts.pop();
      parts.filter(Boolean).forEach(l => ev(x.k, l));
    }
  }, 1000);
  const ping = setInterval(() => res.write(": ping\n\n"), 25000);
  req.on("close", () => { clearInterval(timer); clearInterval(ping); });
}

// ---------- aprobaciones ----------
const APPR_FILE = "approvals.json";
let approvals = readJSON(APPR_FILE, []);
function saveApprovals() { approvals = approvals.slice(-300); writeJSON(APPR_FILE, approvals); }
function expireApprovals() {
  let changed = false;
  for (const a of approvals) if (a.status === "pending" && a.expires < Date.now()) { a.status = "expired"; a.decided = Date.now(); changed = true; }
  if (changed) saveApprovals();
}
setInterval(expireApprovals, 5000);
async function notifyTelegram(a) {
  if (!TG_TOKEN || !TG_CHAT) return;
  const text = `🟡 Aprobación pendiente\n${a.agent}: ${a.title}${a.amount ? "\nImporte: " + a.amount : ""}${PANEL_URL ? "\n\nRevisar: " + PANEL_URL + "#aprobaciones" : ""}`;
  const body = JSON.stringify({ chat_id: TG_CHAT, text, disable_web_page_preview: true });
  await new Promise(ok => {
    const r = require("https").request({ host: "api.telegram.org", path: `/bot${TG_TOKEN}/sendMessage`, method: "POST", headers: { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(body) }, timeout: 8000 }, s => { s.resume(); s.on("end", ok); });
    r.on("error", ok); r.on("timeout", () => { r.destroy(); ok(); }); r.end(body);
  });
}
function botAuthorized(req) { return BOT_KEY && req.headers["x-bot-key"] && safeEq(req.headers["x-bot-key"], BOT_KEY); }

// ---------- servidor ----------
const INDEX = path.join(DIR, "public", "index.html");
const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, "http://x");
  const p = url.pathname; const ip = clientIp(req);
  res.setHeader("X-Content-Type-Options", "nosniff");
  res.setHeader("X-Frame-Options", "DENY");
  res.setHeader("Referrer-Policy", "no-referrer");
  try {
    if (req.method === "GET" && (p === "/" || p === "/index.html")) {
      return send(res, 200, fs.readFileSync(INDEX, "utf8"), { "Content-Type": "text/html; charset=utf-8" });
    }
    if (p === "/api/login" && req.method === "POST") {
      if (blocked(ip)) return send(res, 429, { error: "Demasiados intentos. Espera 15 minutos." });
      const b = await readBody(req);
      if (!b.pass || !safeEq(b.pass, PASS)) { addFail(ip); return send(res, 401, { error: "Contraseña incorrecta" }); }
      fails.delete(ip);
      const sid = crypto.randomBytes(32).toString("hex");
      sessions.set(sid, { exp: Date.now() + SESSION_DAYS * 864e5, ip }); saveSessions();
      return send(res, 200, { ok: true }, { "Set-Cookie": `psid=${sid}; HttpOnly; SameSite=Strict; Path=/; Max-Age=${SESSION_DAYS * 86400}` });
    }
    if (p === "/api/logout" && req.method === "POST") {
      const sid = getSession(req); if (sid) { sessions.delete(sid); saveSessions(); }
      return send(res, 200, { ok: true }, { "Set-Cookie": "psid=; Path=/; Max-Age=0" });
    }

    // Endpoints para los bots (clave de bot)
    if (p === "/api/approvals" && req.method === "POST") {
      if (!botAuthorized(req)) return send(res, 401, { error: "Falta x-bot-key válida" });
      const b = await readBody(req);
      if (!b.agent || !b.title) return send(res, 400, { error: "agent y title son obligatorios" });
      const a = {
        id: crypto.randomBytes(6).toString("hex"), agent: String(b.agent).slice(0, 60), title: String(b.title).slice(0, 200),
        amount: b.amount ? String(b.amount).slice(0, 60) : "", preview: b.preview ? String(b.preview).slice(0, 1000) : "",
        checks: Array.isArray(b.checks) ? b.checks.slice(0, 12).map(c => [String(c[0]).slice(0, 120), c[1] ? "y" : "n"]) : [],
        status: "pending", created: Date.now(), expires: Date.now() + Math.min(Math.max(+b.timeout_s || 600, 30), 86400) * 1000
      };
      approvals.push(a); saveApprovals(); notifyTelegram(a).catch(() => {});
      return send(res, 200, { id: a.id, status: a.status });
    }
    const apOne = p.match(/^\/api\/approvals\/([a-f0-9]{12})$/);
    if (apOne && req.method === "GET" && botAuthorized(req)) {
      expireApprovals(); const a = approvals.find(x => x.id === apOne[1]);
      return a ? send(res, 200, { id: a.id, status: a.status }) : send(res, 404, { error: "No existe" });
    }

    // A partir de aquí, sesión obligatoria
    if (p.startsWith("/api/")) {
      if (!getSession(req)) return send(res, 401, { error: "Inicia sesión" });
    } else return send(res, 404, "No encontrado");

    if (p === "/api/me") return send(res, 200, { ok: true, self: SELF });
    if (p === "/api/agents" && req.method === "GET") {
      const meta = readJSON("agents.json", {});
      const list = await pm2List();
      return send(res, 200, list.map(x => ({ ...x, out: undefined, errLog: undefined, meta: meta[x.name] || null, pending: approvals.filter(a => a.status === "pending" && a.agent === x.name).length })));
    }
    const act = p.match(/^\/api\/agents\/([\w.\-]+)\/(restart|stop|start)$/);
    if (act && req.method === "POST") {
      const list = await pm2List();
      if (!list.some(x => x.name === act[1])) return send(res, 404, { error: "No existe ese proceso" });
      if (act[1] === SELF && act[2] === "stop") return send(res, 400, { error: "No puedes parar el propio panel desde aquí" });
      const r = await run("pm2", [act[2], act[1]], 30000);
      if (r.err) return send(res, 500, { error: (r.stderr || r.err.message).slice(0, 300) });
      run("pm2", ["save"]);
      return send(res, 200, { ok: true });
    }
    const lg = p.match(/^\/api\/logs\/([\w.\-]+)$/);
    if (lg && req.method === "GET") return streamLogs(req, res, lg[1]);
    if (p === "/api/stats") {
      return send(res, 200, { cpu: cpuPercent(), cores: os.cpus().length, mem: memInfo(), disk: await diskInfo(), load: os.loadavg(), uptime: os.uptime(), host: os.hostname() });
    }
    if (p === "/api/approvals" && req.method === "GET") {
      expireApprovals();
      return send(res, 200, approvals.slice().reverse().slice(0, 100));
    }
    const dec = p.match(/^\/api\/approvals\/([a-f0-9]{12})\/decide$/);
    if (dec && req.method === "POST") {
      const b = await readBody(req); const a = approvals.find(x => x.id === dec[1]);
      if (!a) return send(res, 404, { error: "No existe" });
      if (a.status !== "pending") return send(res, 409, { error: "Ya estaba decidida: " + a.status });
      a.status = b.decision === "approve" ? "approved" : "rejected"; a.decided = Date.now(); saveApprovals();
      return send(res, 200, { ok: true, status: a.status });
    }
    return send(res, 404, { error: "Ruta desconocida" });
  } catch (e) {
    console.error(e);
    if (!res.headersSent) send(res, 500, { error: e.message.slice(0, 300) });
  }
});
server.listen(PORT, HOST, () => console.log(`Panel escuchando en http://${HOST}:${PORT}`));

__PANEL_EOF__
cat > "$D/public/index.html" <<'__PANEL_EOF__'
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#2747d6">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>Centro de mando de bots</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=Sora:wght@600;700&display=swap" rel="stylesheet">
<style>
/* Layout: barra lateral de navegación + lista de agentes + panel de detalle con registro en vivo; en móvil, pestañas abajo y el detalle como hoja. */
:root{
  --bg:#f3f4f7; --surface:#ffffff; --surface-2:#eceef3; --line:#d9dce4;
  --ink:#151a26; --ink-2:#5a6275; --accent:#2747d6; --accent-ink:#ffffff; --accent-soft:#e3e8fc;
  --ok:#14804a; --ok-soft:#dcf3e6; --warn:#a85f00; --warn-soft:#fdf0d9; --bad:#c4321f; --bad-soft:#fbe3df;
  --log-bg:#0f1420; --log-ink:#cdd6ea; --log-dim:#6b7792;
  --display:"Sora", "Segoe UI", system-ui, sans-serif;
  --body:"IBM Plex Sans", "Segoe UI", system-ui, sans-serif;
  --mono:"IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, monospace;
  color-scheme: light;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#0d111a; --surface:#151b27; --surface-2:#1c2433; --line:#273145;
    --ink:#e8ecf5; --ink-2:#97a1b6; --accent:#7d93ff; --accent-ink:#0d111a; --accent-soft:#1f2a4d;
    --ok:#4cc985; --ok-soft:#14301f; --warn:#f0a83a; --warn-soft:#352610; --bad:#ff7a66; --bad-soft:#3a1a16;
    --log-bg:#080b12; --log-ink:#cdd6ea; --log-dim:#5c6780;
    color-scheme: dark;
  }
}
:root[data-theme="dark"]{
  --bg:#0d111a; --surface:#151b27; --surface-2:#1c2433; --line:#273145;
  --ink:#e8ecf5; --ink-2:#97a1b6; --accent:#7d93ff; --accent-ink:#0d111a; --accent-soft:#1f2a4d;
  --ok:#4cc985; --ok-soft:#14301f; --warn:#f0a83a; --warn-soft:#352610; --bad:#ff7a66; --bad-soft:#3a1a16;
  --log-bg:#080b12; --log-ink:#cdd6ea; --log-dim:#5c6780;
  color-scheme: dark;
}
*{box-sizing:border-box}
html,body{height:100%;margin:0}
body{background:var(--bg);color:var(--ink);font:15px/1.5 var(--body);-webkit-font-smoothing:antialiased}
button{font:inherit;color:inherit;cursor:pointer}
button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
h1,h2,h3{font-family:var(--display);margin:0;text-wrap:balance;letter-spacing:-.01em}
.num{font-variant-numeric:tabular-nums}

.app{display:grid;grid-template-columns:232px 1fr;height:100%}
.side{background:var(--surface);border-right:1px solid var(--line);display:flex;flex-direction:column;gap:24px;padding:20px 14px}
.brand{display:flex;align-items:center;gap:10px;padding:0 8px}
.brand-mark{width:30px;height:30px;border-radius:8px;background:var(--accent);display:grid;place-items:center;color:var(--accent-ink);font:700 15px var(--display)}
.brand b{font:700 16px var(--display)}
.brand small{display:block;color:var(--ink-2);font-size:12px}
.nav{display:flex;flex-direction:column;gap:2px}
.nav a{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:9px 10px;border-radius:8px;color:var(--ink-2);text-decoration:none;font-weight:500}
.nav a:hover{background:var(--surface-2);color:var(--ink)}
.nav a[aria-current="page"]{background:var(--accent-soft);color:var(--accent)}
.badge{min-width:20px;padding:0 6px;border-radius:10px;background:var(--bad);color:#fff;font-size:12px;font-weight:600;text-align:center}
.badge:empty,.badge[data-n="0"]{display:none}
.host{margin-top:auto;border:1px solid var(--line);border-radius:10px;padding:12px;display:flex;flex-direction:column;gap:8px;font-size:13px}
.host-h{display:flex;justify-content:space-between;align-items:center;font-weight:600}
.bar{height:6px;border-radius:3px;background:var(--surface-2);overflow:hidden}
.bar i{display:block;height:100%;background:var(--accent);border-radius:3px}
.host-row{display:flex;justify-content:space-between;color:var(--ink-2)}

.main{overflow:auto;min-width:0}
.top{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:20px 28px 0;flex-wrap:wrap}
.top h1{font-size:24px}
.top p{margin:2px 0 0;color:var(--ink-2);font-size:14px}
.sim{font:500 12px var(--mono);color:var(--warn);background:var(--warn-soft);padding:4px 8px;border-radius:6px}
.btn{text-decoration:none;color:var(--ink);border:1px solid var(--line);background:var(--surface);border-radius:8px;padding:8px 14px;font-weight:500;display:inline-flex;align-items:center;gap:6px}
.btn:hover{border-color:var(--ink-2)}
.btn.primary{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
.btn.primary:hover{filter:brightness(1.08)}
.btn.ok{background:var(--ok);border-color:var(--ok);color:#fff}
.btn.danger{color:var(--bad);border-color:var(--bad)}
.btn.sm{padding:5px 10px;font-size:13px}
.view{padding:20px 28px 40px;display:flex;flex-direction:column;gap:20px}
.view[hidden]{display:none}

.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
.stat{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.stat span{color:var(--ink-2);font-size:13px}
.stat b{display:block;font:600 24px var(--display);margin-top:2px}
.stat em{font-style:normal;font-size:12px;color:var(--ink-2)}

.split{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.15fr);gap:20px;align-items:start}
.list{display:flex;flex-direction:column;gap:10px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px 16px;display:grid;grid-template-columns:auto 1fr auto;gap:4px 14px;align-items:center;text-align:left;width:100%;position:relative}
.card:hover{border-color:var(--ink-2)}
.card[aria-pressed="true"]{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent)}
.av{width:40px;height:40px;border-radius:10px;display:grid;place-items:center;font:700 15px var(--display);grid-row:span 2}
.card h3{font-size:15px}
.card .sub{grid-column:2;color:var(--ink-2);font-size:13px}
.card svg{grid-row:span 2}
.pill{display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:600;padding:2px 9px;border-radius:999px;white-space:nowrap}
.pill::before{content:"";width:7px;height:7px;border-radius:50%;background:currentColor}
.pill.run{color:var(--ok);background:var(--ok-soft)}
.pill.run::before{animation:pulse 1.6s infinite}
.pill.pause{color:var(--ink-2);background:var(--surface-2)}
.pill.wait{color:var(--warn);background:var(--warn-soft)}
.pill.err{color:var(--bad);background:var(--bad-soft)}
@keyframes pulse{50%{opacity:.3}}
.flag{grid-column:1/-1;margin-top:8px;font-size:12.5px;color:var(--bad);background:var(--bad-soft);border-radius:8px;padding:6px 10px}

.detail{background:var(--surface);border:1px solid var(--line);border-radius:14px;display:flex;flex-direction:column;overflow:hidden;position:sticky;top:20px}
.d-head{padding:16px 18px;display:flex;gap:12px;align-items:flex-start;justify-content:space-between;border-bottom:1px solid var(--line);flex-wrap:wrap}
.d-head h2{font-size:19px}
.d-head p{margin:2px 0 0;color:var(--ink-2);font-size:13px}
.d-actions{display:flex;gap:8px;flex-wrap:wrap}
.tabs{display:flex;gap:4px;padding:8px 12px 0;border-bottom:1px solid var(--line)}
.tabs button{border:0;background:none;padding:8px 10px;color:var(--ink-2);font-weight:500;border-bottom:2px solid transparent;margin-bottom:-1px}
.tabs button[aria-selected="true"]{color:var(--ink);border-color:var(--accent)}
.log{background:var(--log-bg);color:var(--log-ink);font:12.5px/1.65 var(--mono);height:360px;overflow:auto;padding:12px 14px}
.log div{display:grid;grid-template-columns:64px 1fr;gap:10px;animation:in .25s ease-out}
.log time{color:var(--log-dim)}
.log .t-ok{color:#5fd896}.log .t-warn{color:#f3b553}.log .t-bad{color:#ff8b78}.log .t-ai{color:#9fb0ff}
@keyframes in{from{opacity:.2;transform:translateY(3px)}}
.cfg{padding:16px 18px;display:flex;flex-direction:column;gap:14px}
.cfg dl{display:grid;grid-template-columns:150px 1fr;gap:8px 14px;margin:0;font-size:14px}
.cfg dt{color:var(--ink-2)}
.cfg dd{margin:0}
.rules{display:flex;flex-direction:column;gap:6px;margin:0;padding:0;list-style:none;font-size:14px}
.rules li{display:flex;gap:8px;align-items:baseline}
.rules li::before{content:"";flex:none;width:6px;height:6px;border-radius:2px;background:var(--accent);transform:translateY(-2px)}
.rules li.off{color:var(--bad)}
.rules li.off::before{background:var(--bad)}
.mini{font-size:12px;color:var(--ink-2)}
.empty{padding:40px 18px;text-align:center;color:var(--ink-2)}

.appr{display:flex;flex-direction:column;gap:12px}
.ap{background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--warn);border-radius:12px;padding:16px 18px;display:flex;flex-direction:column;gap:10px}
.ap.done{border-left-color:var(--line);opacity:.7}
.ap-h{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;align-items:center}
.ap-h b{font-size:15px}
.checks{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:6px;font-size:13.5px}
.checks span{display:flex;gap:6px}
.checks .y{color:var(--ok)}.checks .n{color:var(--bad)}
.ap-f{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.ap-f .mini{margin-left:auto}

.lib{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}
.tpl{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px;display:flex;flex-direction:column;gap:8px}
.tpl h3{font-size:15px}
.tpl p{margin:0;color:var(--ink-2);font-size:13.5px;flex:1}
.tpl .meta{display:flex;justify-content:space-between;align-items:center;gap:8px}
.tag{font:500 11.5px var(--mono);color:var(--ink-2);background:var(--surface-2);padding:2px 7px;border-radius:5px}
.filter{display:flex;gap:6px;flex-wrap:wrap}
.filter button{border:1px solid var(--line);background:var(--surface);border-radius:999px;padding:5px 12px;font-size:13px}
.filter button[aria-pressed="true"]{background:var(--ink);color:var(--surface);border-color:var(--ink)}

.toast{position:fixed;left:50%;bottom:24px;transform:translate(-50%,20px);background:var(--ink);color:var(--surface);padding:10px 16px;border-radius:10px;font-size:14px;opacity:0;transition:.2s;pointer-events:none;z-index:50}
.toast.show{opacity:1;transform:translate(-50%,0)}
.mobnav{display:none}
.close-detail{display:none}

@media (max-width:1100px){.split{grid-template-columns:1fr}.detail{position:static}}
@media (max-width:760px){
  .app{grid-template-columns:1fr}
  .side{display:none}
  .top{padding:16px 16px 0}
  .view{padding:16px 16px 90px}
  .stats{grid-template-columns:repeat(2,minmax(0,1fr))}
  .stat b{font-size:20px}
  .card svg{display:none}
  .detail{position:fixed;inset:auto 0 0 0;max-height:88%;border-radius:16px 16px 0 0;z-index:30;transform:translateY(105%);transition:transform .25s ease;box-shadow:0 -10px 40px rgba(0,0,0,.25)}
  .detail.open{transform:none}
  .detail .log{height:300px}
  .close-detail{display:inline-flex}
  .cfg dl{grid-template-columns:1fr}
  .cfg dt{margin-top:6px}
  .mobnav{display:flex;position:fixed;bottom:0;left:0;right:0;background:var(--surface);border-top:1px solid var(--line);z-index:20;padding:6px 8px calc(6px + env(safe-area-inset-bottom))}
  .mobnav a{flex:1;display:flex;flex-direction:column;align-items:center;gap:2px;padding:6px;color:var(--ink-2);text-decoration:none;font-size:12px;font-weight:500;border-radius:8px;position:relative}
  .mobnav a[aria-current="page"]{color:var(--accent);background:var(--accent-soft)}
  .mobnav .badge{position:absolute;top:2px;right:calc(50% - 26px)}
}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}

.login{min-height:100%;display:grid;place-items:center;padding:20px}
.login form{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:28px;width:100%;max-width:360px;display:flex;flex-direction:column;gap:14px}
.login label{font-size:13px;color:var(--ink-2);font-weight:500}
.login input{width:100%;padding:10px 12px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink);font:inherit;margin-top:4px}
.err-msg{color:var(--bad);font-size:13.5px;min-height:20px;margin:0}
.log .t-err{color:#ff8b78}
.pill.err::before{animation:none}
.code{background:var(--log-bg);color:var(--log-ink);font:12.5px/1.6 var(--mono);padding:14px;border-radius:10px;overflow-x:auto;white-space:pre;margin:0}
.box{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:18px;display:flex;flex-direction:column;gap:10px;max-width:820px}
.box h2{font-size:17px}
.box p{margin:0;color:var(--ink-2);font-size:14px;max-width:68ch}
.logbar{display:flex;gap:8px;align-items:center;padding:8px 12px;border-bottom:1px solid var(--line);flex-wrap:wrap}
.logbar input[type=search]{flex:1;min-width:120px;padding:6px 10px;border:1px solid var(--line);border-radius:7px;background:var(--bg);color:var(--ink);font:13px var(--body)}
.logbar label{font-size:13px;color:var(--ink-2);display:flex;gap:5px;align-items:center}
</style>
</head>
<body>
<div class="login" id="login" hidden>
  <form id="loginForm">
    <div class="brand" style="padding:0"><div class="brand-mark">A</div><div><b>Alex Ops</b><small>Centro de mando</small></div></div>
    <div><label for="pass">Contraseña del panel</label><input id="pass" type="password" autocomplete="current-password" required></div>
    <p class="err-msg" id="loginErr"></p>
    <button class="btn primary" type="submit" style="justify-content:center">Entrar</button>
  </form>
</div>

<div class="app" id="app" hidden>
  <aside class="side">
    <div class="brand"><div class="brand-mark">A</div><div><b>Alex Ops</b><small>Centro de mando</small></div></div>
    <nav class="nav" aria-label="Secciones">
      <a href="#agentes" data-route="agentes">Mis agentes</a>
      <a href="#aprobaciones" data-route="aprobaciones">Aprobaciones <span class="badge" data-badge></span></a>
      <a href="#conectar" data-route="conectar">Conectar bots</a>
    </nav>
    <div class="host" aria-label="Estado del servidor">
      <div class="host-h"><span id="hostName">VPS</span><span class="pill run" id="hostPill">online</span></div>
      <div class="host-row"><span>CPU</span><span class="num" id="cpuTxt">–</span></div>
      <div class="bar"><i id="cpuBar" style="width:0"></i></div>
      <div class="host-row"><span>RAM</span><span class="num" id="ramTxt">–</span></div>
      <div class="bar"><i id="ramBar" style="width:0"></i></div>
      <div class="host-row"><span>Disco</span><span class="num" id="diskTxt">–</span></div>
      <div class="bar"><i id="diskBar" style="width:0"></i></div>
      <div class="mini" id="hostUp"></div>
      <button class="btn sm" id="logout" type="button">Cerrar sesión</button>
    </div>
  </aside>

  <main class="main">
    <div class="top">
      <div><h1 id="pageTitle">Mis agentes</h1><p id="pageSub"></p></div>
    </div>

    <section class="view" id="v-agentes">
      <div class="stats">
        <div class="stat"><span>Procesos en marcha</span><b class="num" id="sRun">–</b><em>según pm2</em></div>
        <div class="stat"><span>Reinicios totales</span><b class="num" id="sRest">–</b><em>desde el último arranque de pm2</em></div>
        <div class="stat"><span>Esperando tu OK</span><b class="num" id="sAppr">–</b><em>aprobaciones</em></div>
        <div class="stat"><span>RAM de los bots</span><b class="num" id="sMem">–</b><em id="sMemSub">suma de procesos</em></div>
      </div>
      <div class="split">
        <div class="list" id="agentList"><div class="empty">Cargando procesos de pm2…</div></div>
        <article class="detail" id="detail"><div class="empty">Elige un agente para ver su registro.</div></article>
      </div>
    </section>

    <section class="view" id="v-aprobaciones" hidden>
      <div class="appr" id="apprList"></div>
    </section>

    <section class="view" id="v-conectar" hidden>
      <div class="box">
        <h2>Pedir aprobación desde un bot en Python</h2>
        <p>Copia <code>panel_aprobar.py</code> (está en <code>/opt/panel</code>) junto al bot, e importa la función. El bot se queda esperando hasta que apruebes o rechaces aquí. Si no respondes a tiempo, cuenta como rechazada.</p>
<pre class="code">from panel_aprobar import pedir_aprobacion

ok = pedir_aprobacion(
    agente="memebot",                # nombre del proceso en pm2
    titulo="Comprar $TURBO",
    importe="2,7 SOL",
    checks=[("Top 10 holders 18%", True), ("Tamaño 90% > regla 2%", False)],
    espera_s=600,
)
if ok:
    comprar()</pre>
        <p>En bots asíncronos (python-telegram-bot, aiohttp) usa <code>await pedir_aprobacion_async(...)</code>, que no bloquea el bucle.</p>
      </div>
      <div class="box">
        <h2>Descripción y reglas de cada agente</h2>
        <p>Edita <code>/opt/panel/agents.json</code>. La clave es el nombre del proceso en pm2. Los cambios se ven al recargar el panel, sin reiniciar nada.</p>
      </div>
    </section>
  </main>
</div>

<nav class="mobnav" id="mobnav" aria-label="Secciones" hidden>
  <a href="#agentes" data-route="agentes">Agentes</a>
  <a href="#aprobaciones" data-route="aprobaciones">Aprobar <span class="badge" data-badge></span></a>
  <a href="#conectar" data-route="conectar">Conectar</a>
</nav>
<div class="toast" id="toast" role="status"></div>

<script>
const $ = s => document.querySelector(s);
const COLORS = ["#7a3df0","#e0671b","#1a8f8a","#2747d6","#c2367a","#5d8a1f","#b8860b"];
let agents = [], approvals = [], selected = null, tab = "log", es = null, logLines = [], selfName = "panel";
let filterTxt = "", onlyErr = false;

function esc(s){ return String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }
function toast(msg){ const t=$("#toast"); t.textContent=msg; t.classList.add("show"); clearTimeout(toast.h); toast.h=setTimeout(()=>t.classList.remove("show"),2600); }
function mb(b){ return b >= 1073741824 ? (b/1073741824).toFixed(1).replace(".",",")+" GB" : Math.round(b/1048576)+" MB"; }
function ago(ts){ if(!ts) return "–"; const s=Math.floor((Date.now()-ts)/1000); if(s<60) return s+" s"; if(s<3600) return Math.floor(s/60)+" min"; if(s<86400) return Math.floor(s/3600)+" h"; return Math.floor(s/86400)+" d"; }
function initials(n){ return n.replace(/[^a-zA-Z0-9 _-]/g,"").split(/[ _-]+/).filter(Boolean).map(w=>w[0]).join("").slice(0,2).toUpperCase() || n.slice(0,2).toUpperCase(); }
function colorFor(a){ return (a.meta && a.meta.color) || COLORS[a.id % COLORS.length]; }

async function api(path, opts={}){
  const r = await fetch(path, { credentials:"same-origin", headers:{"Content-Type":"application/json"}, ...opts });
  if(r.status === 401 && !path.includes("login")){ showLogin(); throw new Error("Sesión caducada"); }
  const data = await r.json().catch(()=>({}));
  if(!r.ok) throw new Error(data.error || ("Error " + r.status));
  return data;
}

function showLogin(){ $("#app").hidden = true; $("#mobnav").hidden = true; $("#login").hidden = false; if(es){ es.close(); es=null; } setTimeout(()=>$("#pass").focus(),50); }
function showApp(){ $("#login").hidden = true; $("#app").hidden = false; $("#mobnav").hidden = false; route(); refresh(); }

$("#loginForm").addEventListener("submit", async e => {
  e.preventDefault(); $("#loginErr").textContent = "";
  try { await api("/api/login", { method:"POST", body: JSON.stringify({ pass: $("#pass").value }) }); $("#pass").value=""; showApp(); }
  catch(err){ $("#loginErr").textContent = err.message; }
});
$("#logout").addEventListener("click", async () => { await api("/api/logout",{method:"POST"}).catch(()=>{}); showLogin(); });

function statusPill(a){
  if(a.pending) return '<span class="pill wait">Esperando OK</span>';
  if(a.status === "online") return '<span class="pill run">En marcha</span>';
  if(a.status === "stopped") return '<span class="pill pause">Parado</span>';
  return `<span class="pill err">${esc(a.status)}</span>`;
}

function renderList(){
  if(!agents.length){ $("#agentList").innerHTML = '<div class="empty">pm2 no tiene procesos.</div>'; return; }
  $("#agentList").innerHTML = agents.map(a => {
    const c = colorFor(a), m = a.meta || {};
    return `<button class="card" aria-pressed="${a.name===selected}" data-agent="${esc(a.name)}">
      <div class="av" style="background:${c}22;color:${c}">${esc(m.initials || initials(m.title || a.name))}</div>
      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap"><h3>${esc(m.title || a.name)}</h3>${statusPill(a)}</div>
      <div class="num" style="grid-row:span 2;text-align:right;font-size:12.5px;color:var(--ink-2)">${a.cpu}% CPU<br>${mb(a.memory)}</div>
      <div class="sub">${esc(m.desc || a.script || "")} · ${a.status==="online" ? "activo hace "+ago(a.uptime) : "parado"} · ${a.restarts} reinicios</div>
      ${m.flag ? `<div class="flag">${esc(m.flag)}</div>` : ""}
    </button>`;
  }).join("");
}

function renderDetail(){
  const a = agents.find(x=>x.name===selected);
  if(!a){ $("#detail").innerHTML = '<div class="empty">Elige un agente para ver su registro.</div>'; return; }
  const m = a.meta || {};
  const isSelf = a.name === selfName;
  $("#detail").innerHTML = `
    <div class="d-head">
      <div><h2>${esc(m.title || a.name)}</h2><p>pm2 · ${esc(a.name)} (id ${a.id})${m.control ? " · "+esc(m.control) : ""}</p></div>
      <div class="d-actions">
        ${a.pending ? `<a class="btn sm" href="#aprobaciones">Revisar ${a.pending} pendiente${a.pending>1?"s":""}</a>` : ""}
        ${isSelf ? "" : (a.status==="online" ? `<button class="btn sm" data-act="stop">Parar</button>` : `<button class="btn sm" data-act="start">Arrancar</button>`)}
        <button class="btn sm" data-act="restart">Reiniciar</button>
        <button class="btn sm close-detail" data-act="close">Cerrar</button>
      </div>
    </div>
    <div class="tabs" role="tablist">
      <button role="tab" aria-selected="${tab==='log'}" data-tab="log">Registro en vivo</button>
      <button role="tab" aria-selected="${tab==='cfg'}" data-tab="cfg">Detalles y reglas</button>
    </div>
    ${tab==="log" ? `
      <div class="logbar"><input id="logFilter" type="search" placeholder="Filtrar líneas…" value="${esc(filterTxt)}" aria-label="Filtrar líneas del registro">
      <label><input type="checkbox" id="onlyErr" ${onlyErr?"checked":""}> Solo errores</label></div>
      <div class="log" id="log" tabindex="0" aria-label="Registro de ${esc(a.name)}"></div>` : `
    <div class="cfg">
      <dl>
        <dt>Estado</dt><dd>${esc(a.status)}</dd>
        <dt>Script</dt><dd><code>${esc(a.script)}</code></dd>
        <dt>Carpeta</dt><dd><code>${esc(a.cwd)}</code></dd>
        <dt>Intérprete</dt><dd>${esc(a.interpreter)}</dd>
        ${m.trigger ? `<dt>Disparador</dt><dd>${esc(m.trigger)}</dd>` : ""}
        ${m.model ? `<dt>Modelo</dt><dd>${esc(m.model)}</dd>` : ""}
      </dl>
      ${m.rules && m.rules.length ? `<div><h3 style="font-size:14px;margin-bottom:8px">Reglas</h3>
      <ul class="rules">${m.rules.map(r => { const [t,ok] = Array.isArray(r) ? r : [r,true]; return `<li class="${ok?"":"off"}">${esc(t)}</li>`; }).join("")}</ul></div>` : `<p class="mini">Añade descripción y reglas en /opt/panel/agents.json.</p>`}
    </div>`}`;
  if(tab==="log"){ paintLog(true); }
}

function openLogs(name){
  if(es){ es.close(); es=null; } logLines = [];
  es = new EventSource("/api/logs/" + encodeURIComponent(name));
  es.onmessage = ev => { const d = JSON.parse(ev.data); logLines.push(d); if(logLines.length>800) logLines.splice(0, logLines.length-800); schedulePaint(); };
  es.onerror = () => { /* EventSource reintenta solo */ };
}
let paintPending = false;
function schedulePaint(){ if(paintPending) return; paintPending = true; requestAnimationFrame(()=>{ paintPending=false; paintLog(false); }); }
function lineClass(d){
  if(d.k==="err" || /error|exception|traceback|failed|fall[oó]/i.test(d.l)) return "t-err";
  if(/warn|aviso|descart|skip/i.test(d.l)) return "t-warn";
  if(/\b(ok|compra|vend|enviad|success|approved|aprobad)/i.test(d.l)) return "t-ok";
  return "";
}
function paintLog(force){
  const el = $("#log"); if(!el) return;
  const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
  const f = filterTxt.toLowerCase();
  const rows = logLines.filter(d => (!onlyErr || lineClass(d)==="t-err") && (!f || d.l.toLowerCase().includes(f))).slice(-400);
  el.innerHTML = rows.length ? rows.map(d => `<div><time>${new Date(d.t).toLocaleTimeString("es-ES",{hour:"2-digit",minute:"2-digit",second:"2-digit"})}</time><span class="${lineClass(d)}">${esc(d.l)}</span></div>`).join("")
    : `<div><time></time><span style="color:var(--log-dim)">${logLines.length ? "Ninguna línea coincide con el filtro." : "Esperando líneas de log…"}</span></div>`;
  if(force || atBottom) el.scrollTop = el.scrollHeight;
}

function renderApprovals(){
  const el = $("#apprList");
  if(!approvals.length){ el.innerHTML = '<div class="empty">Todavía no hay aprobaciones. Mira "Conectar bots" para que tus bots las pidan.</div>'; return; }
  const label = { approved:["run","Aprobada"], rejected:["err","Rechazada"], expired:["pause","Caducada"] };
  el.innerHTML = approvals.slice().sort((a,b)=>(a.status!=="pending")-(b.status!=="pending")).map(p => {
    const ag = agents.find(x=>x.name===p.agent); const c = ag ? colorFor(ag) : "#2747d6";
    const done = p.status !== "pending";
    const left = Math.max(0, Math.round((p.expires - Date.now())/60000));
    return `<article class="ap ${done?"done":""}">
      <div class="ap-h"><div style="display:flex;gap:10px;align-items:center">
        <div class="av" style="width:32px;height:32px;font-size:12px;background:${c}22;color:${c}">${esc(initials(p.agent))}</div>
        <div><b>${esc(p.title)}</b><div class="mini">${esc(p.agent)} · hace ${ago(p.created)}</div></div></div>
        <span class="num" style="font-weight:600">${esc(p.amount)}</span></div>
      ${p.checks && p.checks.length ? `<div class="checks">${p.checks.map(([c,s])=>`<span class="${s}">${s==="y"?"✓":"✕"} ${esc(c)}</span>`).join("")}</div>` : ""}
      ${p.preview ? `<div style="background:var(--surface-2);border-radius:8px;padding:10px 12px;font-size:14px;white-space:pre-wrap">${esc(p.preview)}</div>` : ""}
      <div class="ap-f">${done ? `<span class="pill ${label[p.status][0]}">${label[p.status][1]}</span>`
        : `<button class="btn ok sm" data-ap="${p.id}" data-v="approve">Aprobar</button><button class="btn danger sm" data-ap="${p.id}" data-v="reject">Rechazar</button>
           <span class="mini">Caduca en ${left} min</span>`}</div>
    </article>`;
  }).join("");
}

function updateCounters(){
  const n = approvals.filter(a=>a.status==="pending").length;
  document.querySelectorAll("[data-badge]").forEach(b=>{ b.textContent = n || ""; b.dataset.n = n; });
  $("#sAppr").textContent = n;
  $("#sRun").textContent = `${agents.filter(a=>a.status==="online").length} / ${agents.length}`;
  $("#sRest").textContent = agents.reduce((s,a)=>s+a.restarts,0);
  $("#sMem").textContent = mb(agents.reduce((s,a)=>s+a.memory,0));
  document.title = n ? `(${n}) Centro de mando de bots` : "Centro de mando de bots";
}

async function refreshAgents(){
  try {
    agents = await api("/api/agents");
    if(!selected && agents.length) selected = (agents.find(a=>a.name!==selfName) || agents[0]).name;
    const typing = document.activeElement && document.activeElement.id === "logFilter";
    if(!document.querySelector(".card:hover")) renderList();
    if(!typing && !$("#log")) renderDetail();
    else if(!typing){ /* refresca cabecera sin tocar el log */ const keep = $("#log").scrollTop; renderDetail(); const l=$("#log"); if(l) l.scrollTop = keep; }
    updateCounters();
  } catch(e){ if(e.message !== "Sesión caducada") toast(e.message); }
}
async function refreshStats(){
  try {
    const s = await api("/api/stats");
    $("#hostName").textContent = s.host; $("#cpuTxt").textContent = s.cpu + "%"; $("#cpuBar").style.width = s.cpu + "%";
    $("#ramTxt").textContent = `${mb(s.mem.used)} / ${mb(s.mem.total)}`; $("#ramBar").style.width = (s.mem.used/s.mem.total*100) + "%";
    $("#diskTxt").textContent = `${mb(s.disk.used)} / ${mb(s.disk.total)}`; $("#diskBar").style.width = (s.disk.used/s.disk.total*100) + "%";
    $("#hostUp").textContent = `Encendido hace ${ago(Date.now() - s.uptime*1000)} · ${s.cores} vCPU`;
    $("#sMemSub").textContent = `de ${mb(s.mem.total)} del servidor`;
    $("#hostPill").className = "pill run"; $("#hostPill").textContent = "online";
  } catch(e){ $("#hostPill").className = "pill err"; $("#hostPill").textContent = "sin conexión"; }
}
async function refreshApprovals(){
  try { approvals = await api("/api/approvals"); if(!$("#v-aprobaciones").hidden) renderApprovals(); updateCounters(); } catch(e){}
}
async function refresh(){
  try { const me = await api("/api/me"); selfName = me.self; } catch(e){ return; }
  await Promise.all([refreshAgents(), refreshStats(), refreshApprovals()]);
  if(selected && !es) openLogs(selected);
}

const TITLES = { agentes:["Mis agentes","Procesos de pm2 en tu VPS, en directo."], aprobaciones:["Aprobaciones","Acciones que tus bots no hacen sin tu OK."], conectar:["Conectar bots","Cómo hacer que tus bots pidan permiso al panel."] };
function route(){
  const r = (location.hash.slice(1) in TITLES) ? location.hash.slice(1) : "agentes";
  Object.keys(TITLES).forEach(k => $("#v-"+k).hidden = k!==r);
  document.querySelectorAll("[data-route]").forEach(a => { if(a.dataset.route===r) a.setAttribute("aria-current","page"); else a.removeAttribute("aria-current"); });
  $("#pageTitle").textContent = TITLES[r][0]; $("#pageSub").textContent = TITLES[r][1];
  if(r==="aprobaciones") renderApprovals();
  $("#detail").classList.remove("open");
}
window.addEventListener("hashchange", route);

document.addEventListener("input", e => {
  if(e.target.id==="logFilter"){ filterTxt = e.target.value; paintLog(true); }
});
document.addEventListener("change", e => {
  if(e.target.id==="onlyErr"){ onlyErr = e.target.checked; paintLog(true); }
});
document.addEventListener("click", async e => {
  const card = e.target.closest("[data-agent]");
  if(card){ if(selected !== card.dataset.agent){ selected = card.dataset.agent; tab="log"; filterTxt=""; onlyErr=false; openLogs(selected); } renderList(); renderDetail(); $("#detail").classList.add("open"); return; }
  const t = e.target.closest("[data-tab]"); if(t){ tab = t.dataset.tab; renderDetail(); return; }
  const act = e.target.closest("[data-act]");
  if(act){
    if(act.dataset.act==="close"){ $("#detail").classList.remove("open"); return; }
    act.disabled = true;
    const verbs = { restart:"reiniciado", stop:"parado", start:"arrancado" };
    try { await api(`/api/agents/${encodeURIComponent(selected)}/${act.dataset.act}`, { method:"POST" }); toast(`${selected} ${verbs[act.dataset.act]}`); }
    catch(err){ toast(err.message); }
    await refreshAgents(); return;
  }
  const ap = e.target.closest("[data-ap]");
  if(ap){
    ap.disabled = true;
    try { const r = await api(`/api/approvals/${ap.dataset.ap}/decide`, { method:"POST", body: JSON.stringify({ decision: ap.dataset.v }) });
      toast(r.status==="approved" ? "Aprobado. El bot sigue." : "Rechazado. El bot no lo hará."); }
    catch(err){ toast(err.message); }
    await refreshApprovals(); await refreshAgents();
  }
});

setInterval(() => { if(!$("#app").hidden){ refreshAgents(); refreshStats(); } }, 5000);
setInterval(() => { if(!$("#app").hidden) refreshApprovals(); }, 3000);

api("/api/me").then(showApp).catch(()=>{});
</script>
</body>
</html>

__PANEL_EOF__
cat > "$D/panel_aprobar.py" <<'__PANEL_EOF__'
"""Pide aprobación al panel antes de una acción delicada.

Uso:
    from panel_aprobar import pedir_aprobacion
    if pedir_aprobacion("memebot", "Comprar $TURBO", importe="2,7 SOL",
                        checks=[("Top 10 holders 18%", True)]):
        comprar()

Lee PANEL_BOT_KEY (y opcionalmente PANEL_URL_LOCAL) del entorno o de /opt/panel/.env.
Solo usa la librería estándar. Si el panel no responde, devuelve False (no se hace nada).
"""
import asyncio
import json
import os
import time
import urllib.request

_ENV_FILE = "/opt/panel/.env"


def _conf():
    env = {}
    try:
        with open(_ENV_FILE, encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.lstrip().startswith("#"):
                    k, v = line.strip().split("=", 1)
                    env[k] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    key = os.environ.get("PANEL_BOT_KEY") or env.get("PANEL_BOT_KEY", "")
    port = os.environ.get("PANEL_PORT") or env.get("PANEL_PORT", "8080")
    url = os.environ.get("PANEL_URL_LOCAL") or f"http://127.0.0.1:{port}"
    return url, key


def _call(method, path, body=None, timeout=8):
    url, key = _conf()
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url + path, data=data, method=method,
                                 headers={"Content-Type": "application/json", "x-bot-key": key})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def pedir_aprobacion(agente, titulo, importe="", checks=None, preview="", espera_s=600, cada_s=3):
    """Bloquea hasta que apruebes/rechaces en el panel. True solo si apruebas."""
    try:
        r = _call("POST", "/api/approvals", {
            "agent": agente, "title": titulo, "amount": importe, "preview": preview,
            "checks": [[c, bool(ok)] for c, ok in (checks or [])], "timeout_s": espera_s,
        })
    except Exception as e:  # panel caído: por seguridad, no se aprueba
        print(f"[panel] no se pudo pedir aprobación: {e}")
        return False
    fin = time.time() + espera_s + 10
    while time.time() < fin:
        try:
            estado = _call("GET", f"/api/approvals/{r['id']}")["status"]
        except Exception:
            estado = "pending"
        if estado != "pending":
            return estado == "approved"
        time.sleep(cada_s)
    return False


async def pedir_aprobacion_async(*args, **kwargs):
    """Versión para bots asíncronos: no bloquea el bucle de eventos."""
    return await asyncio.to_thread(pedir_aprobacion, *args, **kwargs)


if __name__ == "__main__":
    print("Mira el panel y aprueba o rechaza la prueba…")
    print("Resultado:", pedir_aprobacion("prueba", "Aprobación de prueba", importe="0 €",
                                          checks=[("Conexión con el panel", True)], espera_s=120))

__PANEL_EOF__
if [ ! -f "$D/agents.json" ]; then
cat > "$D/agents.json" <<'__PANEL_EOF__'
{
  "memebot": {
    "title": "Memebot",
    "initials": "MB",
    "color": "#7a3df0",
    "desc": "Caza memecoins en Solana (pump.fun) y copia smart wallets",
    "control": "Telegram: Memebot",
    "trigger": "Continuo (Helius)",
    "model": "Claude puntúa cada token",
    "flag": "Riesgo alto: compra con el 90% del saldo por operación. Con stop en -35%, una sola pérdida se lleva casi un tercio de la cuenta.",
    "rules": [
      ["Entra solo si momentum pump.fun y compra de wallets top coinciden", true],
      ["Top 10 holders (sin curva/LP) <= 25%", true],
      ["Dev <= 5% y sin ventas en los primeros 10 min", true],
      ["Descarta tokens con más de 6 h sin nuevo ATH", true],
      ["Vende 50% a 2x, stop en -35%", true],
      ["No opera después de la 1:00 (Madrid)", true],
      ["Tamaño por operación: 90% del saldo (tu regla original era 2%)", false]
    ]
  },
  "chivato": {
    "title": "Chivato Ofertas",
    "initials": "CH",
    "color": "#e0671b",
    "desc": "@ChivatoAmazon_bot: ofertas -80%, errores de precio y anuncios",
    "control": "Telegram: @ChivatoAmazon_bot",
    "trigger": "Keepa Starter (20 tokens/min)",
    "rules": [
      ["Descuento >= 80% o posible error de precio", true],
      ["Enlaces de Amazon.es con tu ID de afiliado", true],
      ["Anuncios: máx. 3 al día por usuario, con región visible", true]
    ]
  },
  "jev-trader": {
    "title": "Trading Jev",
    "initials": "TJ",
    "color": "#1a8f8a",
    "desc": "BTC/USD en Alpaca (paper), estrategia de Opus",
    "trigger": "Cada vela",
    "model": "Opus 5.5 + Jev SDK",
    "rules": [
      ["Alpaca cripto, cuenta paper", true],
      ["Órdenes > 100 USD necesitan tu aprobación", true]
    ]
  },
  "panel": {
    "title": "Panel (este)",
    "initials": "AO",
    "color": "#2747d6",
    "desc": "El propio centro de mando"
  }
}

__PANEL_EOF__
fi

IP=$(curl -s -4 --max-time 5 https://ifconfig.me || hostname -I | awk '{print $1}')
PORT=8080
if [ ! -f "$D/.env" ]; then
  PASS=$(openssl rand -base64 24 | tr -dc 'A-Za-z0-9' | head -c 16)
  KEY=$(openssl rand -hex 24)
  {
    echo "PANEL_PASS=$PASS"
    echo "PANEL_BOT_KEY=$KEY"
    echo "PANEL_PORT=$PORT"
    echo "PANEL_URL=http://$IP:$PORT/"
    echo "# Opcional: aviso por Telegram de cada aprobacion pendiente"
    echo "PANEL_TG_TOKEN="
    echo "PANEL_TG_CHAT="
  } > "$D/.env"
  chmod 600 "$D/.env"
  NUEVA=1
else
  PASS=$(grep '^PANEL_PASS=' "$D/.env" | cut -d= -f2-)
  PORT=$(grep '^PANEL_PORT=' "$D/.env" | cut -d= -f2- || true)
  PORT=${PORT:-8080}
  NUEVA=0
fi

if command -v ufw >/dev/null && ufw status | grep -q "Status: active"; then ufw allow "$PORT"/tcp >/dev/null && echo "Puerto $PORT abierto en ufw"; fi

if pm2 describe panel >/dev/null 2>&1; then pm2 restart panel --update-env >/dev/null; else (cd "$D" && pm2 start server.js --name panel --max-memory-restart 120M >/dev/null); fi
pm2 save >/dev/null
sleep 2
if curl -s --max-time 5 "http://127.0.0.1:$PORT/" | grep -q "Centro de mando"; then OK="si"; else OK="NO (mira: pm2 logs panel)"; fi

echo
echo "================  PANEL INSTALADO  ================"
echo " Funciona en el servidor: $OK"
echo " Abre en el movil:  http://$IP:$PORT/"
if [ "$NUEVA" = 1 ]; then echo " Contrasena:        $PASS   (guardala; esta en $D/.env)"; fi
echo
echo " Procesos que ve pm2 ahora mismo:"
pm2 jlist 2>/dev/null | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{JSON.parse(s.slice(s.indexOf("["))).forEach(p=>console.log("   - "+p.name+" ("+p.pm2_env.status+")"))}catch(e){}})'
echo
echo " Si los nombres no son memebot / chivato / jev-trader, cambia"
echo " las claves en $D/agents.json para que salgan con su ficha."
echo " Si no carga desde el movil, abre el puerto $PORT/TCP en el"
echo " cortafuegos de Clouding (Red > Firewall)."
echo "===================================================="
