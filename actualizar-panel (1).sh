#!/usr/bin/env bash
# Actualiza el Centro de mando de bots: añade servicios de systemd (Chivato).
# Conserva .env (contraseña, puerto), agents.json y aprobaciones.
set -euo pipefail
D=/opt/panel
[ "$(id -u)" = 0 ] || { echo "Ejecutalo como root"; exit 1; }
[ -f "$D/.env" ] || { echo "No encuentro $D/.env: instala primero el panel"; exit 1; }
B="$D/backup_$(date +%Y%m%d%H%M%S)"; mkdir -p "$B"; cp -r "$D/server.js" "$D/public" "$D/panel_aprobar.py" "$B/" 2>/dev/null || true
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
const PORT = parseInt(process.env.PANEL_PORT || "8081", 10);
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
    errLog: p.pm2_env.pm_err_log_path,
    kind: "pm2"
  }));
}

// ---------- systemd ----------
const SD_UNITS = (process.env.PANEL_SYSTEMD || "").split(",").map(s => s.trim()).filter(s => /^[\w@.\-]+$/.test(s));
const cpuPrev = new Map(); // unit -> {ns, t}
async function sdList() {
  const out = [];
  for (let i = 0; i < SD_UNITS.length; i++) {
    const u = SD_UNITS[i];
    const r = await run("systemctl", ["show", u, "--no-pager", "-p", "ActiveState,SubState,MainPID,ExecMainStartTimestampMonotonic,NRestarts,MemoryCurrent,CPUUsageNSec,WorkingDirectory,ExecStart,LoadState"]);
    const kv = {}; r.stdout.split("\n").forEach(l => { const i = l.indexOf("="); if (i > 0) kv[l.slice(0, i)] = l.slice(i + 1); });
    if (kv.LoadState === "not-found") { out.push({ name: u, id: 100 + i, status: "no encontrado", cpu: 0, memory: 0, uptime: 0, restarts: 0, cwd: "", script: "", interpreter: "", kind: "systemd" }); continue; }
    const st = kv.ActiveState === "active" ? "online" : kv.ActiveState === "inactive" ? "stopped" : kv.ActiveState === "failed" ? "errored" : kv.ActiveState;
    const mono = +kv.ExecMainStartTimestampMonotonic || 0;
    const uptime = st === "online" && mono ? Date.now() - (os.uptime() * 1e6 - mono) / 1000 : 0;
    let cpu = 0; const ns = +kv.CPUUsageNSec;
    if (Number.isFinite(ns)) { const p = cpuPrev.get(u); const now = Date.now(); if (p && now > p.t) cpu = Math.max(0, Math.round((ns - p.ns) / 1e6 / (now - p.t) * 100)); cpuPrev.set(u, { ns, t: now }); }
    const mem = +kv.MemoryCurrent; const exec = (kv.ExecStart || "").match(/argv\[\]=([^;]*)/);
    out.push({ name: u, id: 100 + i, status: st, cpu, memory: Number.isFinite(mem) && mem < 1e15 ? mem : 0, uptime, restarts: +kv.NRestarts || 0,
      cwd: kv.WorkingDirectory || "", script: exec ? exec[1].trim() : "", interpreter: "systemd", kind: "systemd" });
  }
  return out;
}
async function allProcs() {
  let pm = [];
  try { pm = await pm2List(); } catch (e) { if (!SD_UNITS.length) throw e; }
  return pm.concat(await sdList());
}
function streamJournal(req, res, unit) {
  res.writeHead(200, { "Content-Type": "text/event-stream", "Cache-Control": "no-store", Connection: "keep-alive", "X-Accel-Buffering": "no" });
  const child = require("child_process").spawn("journalctl", ["-u", unit, "-n", "150", "-f", "-o", "json", "--no-pager"]);
  let rest = "";
  child.stdout.on("data", d => {
    const parts = (rest + d.toString("utf8")).split("\n"); rest = parts.pop();
    for (const line of parts) {
      try {
        const j = JSON.parse(line); let m = j.MESSAGE;
        if (Array.isArray(m)) m = Buffer.from(m).toString("utf8");
        if (m == null) continue;
        String(m).split("\n").filter(Boolean).forEach(l => res.write(`data: ${JSON.stringify({ k: +j.PRIORITY <= 3 ? "err" : "out", l, t: Math.round(+j.__REALTIME_TIMESTAMP / 1000) || Date.now() })}\n\n`));
      } catch {}
    }
  });
  child.on("error", () => res.write(`data: ${JSON.stringify({ k: "err", l: "No se pudo leer journalctl", t: Date.now() })}\n\n`));
  const ping = setInterval(() => res.write(": ping\n\n"), 25000);
  req.on("close", () => { clearInterval(ping); child.kill(); });
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
  const list = await allProcs();
  const p = list.find(x => x.name === name);
  if (!p) return send(res, 404, { error: "No existe ese proceso" });
  if (p.kind === "systemd") return streamJournal(req, res, p.name);
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

// ---------- Chivato (lee data.json, deja órdenes en panel_ordenes) ----------
const CHV = process.env.PANEL_CHIVATO_DIR || "/opt/chivato";
const CHV_ORD = path.join(CHV, "panel_ordenes");
const CHV_VID = path.join(CHV, "panel_videos");
const dayMad = ts => new Intl.DateTimeFormat("sv-SE", { timeZone: "Europe/Madrid" }).format(new Date(ts));
function chvResumen() {
  let d;
  try { d = JSON.parse(fs.readFileSync(path.join(CHV, "data.json"), "utf8")); }
  catch (e) { return { error: "No puedo leer " + path.join(CHV, "data.json") + ": " + e.message }; }
  const now = Date.now(), hoyM = dayMad(now), hoyU = new Date(now).toISOString().slice(0, 10);
  const users = d.users || {}, aut = d.autorizados || {};
  const dias14 = []; for (let i = 13; i >= 0; i--) dias14.push(dayMad(now - i * 864e5));
  const altas = Object.fromEntries(dias14.map(k => [k, 0])); let previo = 0;
  for (const a of Object.values(aut)) {
    if (!a || !a.ts || a.codigo === "previo") { previo++; continue; }
    const k = dayMad(a.ts * 1000); if (k in altas) altas[k]++;
  }
  let activosHoy = 0, avisosHoy = 0;
  for (const u of Object.values(users)) if (u && (u.dia === hoyM || u.dia === hoyU)) { activosHoy++; avisosHoy += +u.n || 0; }
  const apoyo = d.apoyo || {}; const apoyantes = Object.values(apoyo).filter(v => v === -1 || v * 1000 > now).length;
  const tips = d.tips || [], ventas = d.ventas_ads || [];
  const ofertas = Object.fromEntries(dias14.slice(-7).map(k => [k, 0]));
  for (const v of Object.values(d.dia_top || {})) { const k = v && v.ts ? dayMad(v.ts * 1000) : null; if (k in ofertas) ofertas[k]++; }
  const nombres = d.cat_nombres || {};
  const cats = Object.entries(d.cat_vistas || {}).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([k, n]) => ({ k, nombre: nombres[k] || k, n }));
  const anuncios = Object.entries(d.anuncios || {}).map(([id, a]) => ({
    id, tipo: a.tipo || "", estado: a.estado || "", texto: String(a.texto || "").slice(0, 400), enlace: a.enlace || "", boton: a.boton || "",
    region: a.region || "", pk: a.pk || "", env: +a.env || 0, clics: +a.clics || 0, unicos: Object.keys(a.u || {}).length,
    fin: a.fin ? a.fin * 1000 : 0, ts: (a.pago_ts || a.ts || 0) * 1000, autor: a.autor || "", foto: !!a.foto
  })).sort((a, b) => b.ts - a.ts);
  const recent = (d.recent || []).slice(-30).reverse().map(x => ({ t: String(x.t || ""), u: x.u || "", d: +x.d || 0, ts: (x.ts || 0) * 1000 }));
  const p = d.panel || null;
  let videos = [];
  try {
    videos = fs.readdirSync(CHV_VID).filter(f => /^[\w.-]+\.mp4$/.test(f)).sort().reverse().slice(0, 15).map(f => {
      let texto = ""; try { texto = fs.readFileSync(path.join(CHV_VID, f.slice(0, -4) + ".txt"), "utf8"); } catch {}
      const st = fs.statSync(path.join(CHV_VID, f)); return { f, texto, ts: st.mtimeMs, size: st.size };
    });
  } catch {}
  let pendientes = 0; try { pendientes = fs.readdirSync(CHV_ORD).filter(f => f.endsWith(".json")).length; } catch {}
  const err = d.err || {};
  return {
    parcheado: !!p, actualizado: fs.statSync(path.join(CHV, "data.json")).mtimeMs,
    stats: {
      usuarios: Object.keys(users).length, autorizados: Object.keys(aut).length, previo, nuevosHoy: altas[hoyM] || 0,
      nuevos7: dias14.slice(-7).reduce((s, k) => s + altas[k], 0), activosHoy, avisosHoy, apoyantes,
      propinas: { n: tips.length, stars: tips.reduce((s, t) => s + (+t.n || 0), 0) },
      ventasAds: { n: ventas.length, stars: ventas.reduce((s, t) => s + (+t.n || 0), 0) },
      fb: { up: +(d.fb || {}).up || 0, dn: +(d.fb || {}).dn || 0 },
      errores: { on: err.on !== false, todos: !!err.todos, n: +err.n || 0, pct: err.pct, min: err.min },
      altas: dias14.map(k => [k, altas[k]]), ofertas: Object.entries(ofertas), cats,
      codigos: Object.keys(d.codigos || {}).length
    },
    anuncios, recent, videos, ordenesPendientes: pendientes,
    panel: p ? { err_espera: p.err_espera !== false, err_cola: (p.err_cola || []).map(x => ({ id: x.id, ts: (x.ts || 0) * 1000, t: String((x.item || {}).t || ""), u: (x.item || {}).u || "", d: +(x.item || {}).d || 0 })).reverse(), log: (p.log || []).slice(-20).reverse().map(x => ({ ...x, ts: x.ts * 1000 })) } : null,
    destinatarios: Object.keys(aut).filter(c => users[c] && !["parado", "pausa", "pausado", "off", "stop"].some(k => users[c][k])).length
  };
}
const CHV_TIPOS = new Set(["err_enviar", "err_descartar", "err_espera", "mensaje", "ad_pausar", "ad_reanudar", "ad_finalizar"]);
function chvOrden(b) {
  if (!CHV_TIPOS.has(b.tipo)) throw new Error("Orden no válida");
  const o = { tipo: b.tipo, ts: Date.now() };
  if (b.id != null) o.id = String(b.id).slice(0, 20);
  if (b.aid != null) o.aid = String(b.aid).slice(0, 20);
  if (b.on != null) o.on = !!b.on;
  if (b.tipo === "mensaje") { o.texto = String(b.texto || "").trim().slice(0, 4000); if (!o.texto) throw new Error("El mensaje está vacío"); }
  fs.mkdirSync(CHV_ORD, { recursive: true });
  const f = path.join(CHV_ORD, `${Date.now()}_${crypto.randomBytes(3).toString("hex")}.json`);
  fs.writeFileSync(f + ".tmp", JSON.stringify(o)); fs.renameSync(f + ".tmp", f);
}
function chvVideo(req, res, name) {
  if (!/^[\w.-]+\.mp4$/.test(name)) return send(res, 400, { error: "Nombre no válido" });
  const f = path.join(CHV_VID, name); let st;
  try { st = fs.statSync(f); } catch { return send(res, 404, { error: "No existe" }); }
  const range = /bytes=(\d*)-(\d*)/.exec(req.headers.range || "");
  const head = { "Content-Type": "video/mp4", "Accept-Ranges": "bytes", "Cache-Control": "private, max-age=3600" };
  if (new URL(req.url, "http://x").searchParams.get("dl")) head["Content-Disposition"] = `attachment; filename="${name}"`;
  if (range) {
    const start = range[1] ? +range[1] : st.size - +range[2], end = range[1] && range[2] ? Math.min(+range[2], st.size - 1) : st.size - 1;
    if (start >= st.size || start < 0) { res.writeHead(416, { "Content-Range": `bytes */${st.size}` }); return res.end(); }
    res.writeHead(206, { ...head, "Content-Range": `bytes ${start}-${end}/${st.size}`, "Content-Length": end - start + 1 });
    return fs.createReadStream(f, { start, end }).pipe(res);
  }
  res.writeHead(200, { ...head, "Content-Length": st.size });
  fs.createReadStream(f).pipe(res);
}

// ---------- Analizador de wallets (Helius) + wallets de Memebot ----------
const MB_DIR = process.env.PANEL_MEMEBOT_DIR || "/root/memebot";
const SOL_MINT = "So11111111111111111111111111111111111111112";
const B58 = /^[1-9A-HJ-NP-Za-km-z]{32,44}$/;
function readEnvFile(f) {
  const o = {};
  try { for (const l of fs.readFileSync(f, "utf8").split("\n")) { const m = l.match(/^\s*([A-Za-z0-9_]+)\s*=\s*(.*)\s*$/); if (m) o[m[1]] = m[2].replace(/^["']|["']$/g, ""); } } catch {}
  return o;
}
function heliusKey() { return process.env.PANEL_HELIUS_KEY || readEnvFile(path.join(MB_DIR, ".env")).HELIUS_API_KEY || ""; }
const HEL_API = process.env.PANEL_HELIUS_API || "https://api.helius.xyz";
const HEL_RPC = process.env.PANEL_HELIUS_RPC || "https://mainnet.helius-rpc.com";
async function hget(url) {
  const r = await fetch(url, { signal: AbortSignal.timeout(20000) });
  const t = await r.text(); let j; try { j = JSON.parse(t); } catch { j = null; }
  if (!r.ok) throw new Error(`Helius ${r.status}: ${String((j && (j.error || j.message)) || t).slice(0, 160)}`);
  return j;
}
async function hrpc(method, params) {
  const r = await fetch(`${HEL_RPC}/?api-key=${heliusKey()}`, { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ jsonrpc: "2.0", id: 1, method, params }), signal: AbortSignal.timeout(20000) });
  const j = await r.json(); if (j.error) throw new Error(j.error.message || "RPC"); return j.result;
}
const walletCache = new Map();
async function analizarWallet(addr, paginas) {
  const key = heliusKey();
  if (!key) throw new Error("No encuentro HELIUS_API_KEY en " + path.join(MB_DIR, ".env"));
  const c = walletCache.get(addr);
  if (c && Date.now() - c.t < 10 * 60e3) return c.r;
  const txs = []; let before = "";
  for (let i = 0; i < paginas; i++) {
    const q = `${HEL_API}/v0/addresses/${addr}/transactions?api-key=${key}&limit=100` + (before ? `&before=${before}&before-signature=${before}` : "");
    const page = await hget(q);
    if (!Array.isArray(page) || !page.length) break;
    txs.push(...page); before = page[page.length - 1].signature;
    if (page.length < 100) break;
  }
  // Cambios de SOL y tokens de la wallet en cada transacción
  const trades = [];
  for (const tx of txs) {
    if (tx.transactionError) continue;
    let sol = 0; const tok = {};
    for (const a of tx.accountData || []) {
      if (a.account === addr) sol += (+a.nativeBalanceChange || 0) / 1e9;
      for (const b of a.tokenBalanceChanges || []) {
        if (b.userAccount !== addr) continue;
        const raw = b.rawTokenAmount || {}; const v = (+raw.tokenAmount || 0) / Math.pow(10, +raw.decimals || 0);
        if (b.mint === SOL_MINT) sol += v; else tok[b.mint] = (tok[b.mint] || 0) + v;
      }
    }
    const mints = Object.keys(tok).filter(m => Math.abs(tok[m]) > 0);
    if (mints.length !== 1 || Math.abs(sol) < 1e-6) continue; // solo swaps simples SOL <-> token
    const m = mints[0];
    if (tok[m] > 0 && sol < 0) trades.push({ ts: tx.timestamp * 1000, mint: m, lado: "compra", sol: -sol, cant: tok[m], src: tx.source || "" });
    else if (tok[m] < 0 && sol > 0) trades.push({ ts: tx.timestamp * 1000, mint: m, lado: "venta", sol, cant: -tok[m], src: tx.source || "" });
  }
  trades.sort((a, b) => a.ts - b.ts);
  const pos = {}; const curva = []; let acum = 0;
  for (const t of trades) {
    const p = pos[t.mint] || (pos[t.mint] = { mint: t.mint, gastado: 0, recibido: 0, comprado: 0, vendido: 0, n: 0, primera: t.ts, ultima: t.ts });
    p.n++; p.ultima = t.ts;
    if (t.lado === "compra") { p.gastado += t.sol; p.comprado += t.cant; }
    else {
      p.recibido += t.sol; p.vendido += t.cant;
      if (p.comprado > 0) { // beneficio de esta venta = lo recibido - coste medio de lo vendido
        const costeVenta = (p.gastado / p.comprado) * Math.min(t.cant, p.comprado);
        acum += t.sol - costeVenta; curva.push([t.ts, +acum.toFixed(4)]);
      }
    }
  }
  const lista = Object.values(pos).filter(p => p.comprado > 0);
  const cerradas = lista.filter(p => p.vendido >= p.comprado * 0.9);
  const ganadoras = cerradas.filter(p => p.recibido > p.gastado);
  const pnlTok = cerradas.map(p => ({ mint: p.mint, pnl: p.recibido - p.gastado, gastado: p.gastado, x: p.gastado ? p.recibido / p.gastado : 0, hold: p.ultima - p.primera, n: p.n }));
  const pnlCerrado = pnlTok.reduce((s, p) => s + p.pnl, 0);
  const positivo = pnlTok.filter(p => p.pnl > 0).reduce((s, p) => s + p.pnl, 0);
  const mejor = pnlTok.reduce((m, p) => (p.pnl > (m ? m.pnl : -Infinity) ? p : m), null);
  const desde = trades.length ? trades[0].ts : 0, hasta = trades.length ? trades[trades.length - 1].ts : 0;
  const dias = Math.max(1, (hasta - desde) / 864e5);
  const porDia = {};
  for (const t of trades) { const k = new Date(t.ts).toISOString().slice(0, 10); porDia[k] = (porDia[k] || 0) + 1; }
  const holds = pnlTok.map(p => p.hold).sort((a, b) => a - b);
  const r = {
    addr, txs: txs.length, trades: trades.length, desde, hasta, dias: +dias.toFixed(1), tradesDia: +(trades.length / dias).toFixed(1),
    tokens: lista.length, cerradas: cerradas.length, abiertas: lista.length - cerradas.length,
    winRate: cerradas.length ? Math.round(100 * ganadoras.length / cerradas.length) : null,
    pnlSol: +pnlCerrado.toFixed(3), gastadoMedio: lista.length ? +(lista.reduce((s, p) => s + p.gastado, 0) / lista.length).toFixed(3) : 0,
    concentracion: positivo > 0 && mejor && mejor.pnl > 0 ? Math.round(100 * mejor.pnl / positivo) : null,
    holdMediano: holds.length ? holds[Math.floor(holds.length / 2)] : null,
    ultimoTrade: hasta, curva, porDia: Object.entries(porDia).sort(),
    top: pnlTok.sort((a, b) => b.pnl - a.pnl).slice(0, 5).concat(pnlTok.slice(-5).reverse()).filter((v, i, a) => a.findIndex(x => x.mint === v.mint) === i),
    abiertasLista: lista.filter(p => p.vendido < p.comprado * 0.9).sort((a, b) => b.ultima - a.ultima).slice(0, 5).map(p => ({ mint: p.mint, gastado: +p.gastado.toFixed(3), ts: p.ultima }))
  };
  try { r.saldo = +((await hrpc("getBalance", [addr])).value / 1e9).toFixed(3); } catch { r.saldo = null; }
  const mintsVer = [...new Set(r.top.map(t => t.mint).concat(r.abiertasLista.map(t => t.mint)))].slice(0, 30);
  r.simbolos = {};
  if (mintsVer.length) {
    try {
      const as = await hrpc("getAssetBatch", { ids: mintsVer });
      for (const a of as || []) if (a && a.id) r.simbolos[a.id] = ((a.content || {}).metadata || {}).symbol || ((a.token_info || {}).symbol) || "";
    } catch {}
  }
  r.checks = [
    ["Muestra suficiente (10+ tokens cerrados)", cerradas.length >= 10, `${cerradas.length} cerrados`],
    ["Ritmo copiable (≤ 10 trades/día)", r.tradesDia <= 10, `${r.tradesDia}/día${r.tradesDia > 50 ? " · parece un bot" : ""}`],
    ["Acierto ≥ 55%", r.winRate != null && r.winRate >= 55, r.winRate == null ? "sin datos" : r.winRate + "%"],
    ["Beneficio cerrado positivo", r.pnlSol > 0, (r.pnlSol > 0 ? "+" : "") + r.pnlSol + " SOL"],
    ["No depende de un solo golpe (≤ 50%)", r.concentracion != null && r.concentracion <= 50, r.concentracion == null ? "sin datos" : r.concentracion + "% del beneficio en 1 token"],
    ["Activa (operó en los últimos 3 días)", hasta > Date.now() - 3 * 864e5, hasta ? new Date(hasta).toLocaleDateString("es-ES") : "nunca"]
  ];
  const ok = r.checks.filter(c => c[1]).length;
  const clave = r.checks[1][1] && r.checks[2][1] && r.checks[3][1];
  r.veredicto = ok === 6 ? "buena" : clave && ok >= 4 ? "dudosa" : "no";
  walletCache.set(addr, { t: Date.now(), r });
  return r;
}
function memebotWallets() {
  const envW = (readEnvFile(path.join(MB_DIR, ".env")).WALLETS || "").split(",").map(s => s.trim()).filter(Boolean);
  const f = path.join(MB_DIR, "wallets.txt"); const fichero = [];
  try {
    for (const l of fs.readFileSync(f, "utf8").split("\n")) {
      const [a, ...nota] = l.split("#"); const w = a.trim().split(/[\s,]+/)[0];
      if (w) fichero.push({ addr: w, nota: nota.join("#").trim() });
    }
  } catch {}
  return [...envW.map(a => ({ addr: a, nota: "en .env", fijo: true })), ...fichero.filter(x => !envW.includes(x.addr))];
}
async function memebotReiniciar() { const r = await run("pm2", ["restart", "memebot"], 30000); if (r.err) throw new Error((r.stderr || r.err.message).slice(0, 200)); }
async function walletAnadir(addr, nota) {
  if (!B58.test(addr)) throw new Error("Esa dirección no parece de Solana");
  if (memebotWallets().some(w => w.addr === addr)) throw new Error("Memebot ya vigila esa wallet");
  const f = path.join(MB_DIR, "wallets.txt");
  let prev = ""; try { prev = fs.readFileSync(f, "utf8"); } catch {}
  const linea = `${addr}  # panel ${new Date().toISOString().slice(0, 10)}${nota ? " · " + String(nota).replace(/[\r\n#]/g, " ").slice(0, 80) : ""}`;
  fs.writeFileSync(f, (prev && !prev.endsWith("\n") ? prev + "\n" : prev) + linea + "\n");
  await memebotReiniciar();
}
async function walletQuitar(addr) {
  const f = path.join(MB_DIR, "wallets.txt"); let prev = "";
  try { prev = fs.readFileSync(f, "utf8"); } catch { throw new Error("No hay wallets.txt"); }
  const lineas = prev.split("\n"); const nuevas = lineas.filter(l => l.split("#")[0].trim().split(/[\s,]+/)[0] !== addr);
  if (nuevas.length === lineas.length) throw new Error("Esa wallet no está en wallets.txt (si está en el .env, quítala de ahí)");
  fs.copyFileSync(f, f + ".bak"); fs.writeFileSync(f, nuevas.join("\n"));
  await memebotReiniciar();
}

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
      const list = await allProcs();
      return send(res, 200, list.map(x => ({ ...x, out: undefined, errLog: undefined, meta: meta[x.name] || null, pending: approvals.filter(a => a.status === "pending" && a.agent === x.name).length })));
    }
    const act = p.match(/^\/api\/agents\/([\w.\-]+)\/(restart|stop|start)$/);
    if (act && req.method === "POST") {
      const list = await allProcs();
      const proc = list.find(x => x.name === act[1]);
      if (!proc) return send(res, 404, { error: "No existe ese proceso" });
      if (act[1] === SELF && act[2] === "stop") return send(res, 400, { error: "No puedes parar el propio panel desde aquí" });
      const r = proc.kind === "systemd" ? await run("systemctl", [act[2], act[1]], 30000) : await run("pm2", [act[2], act[1]], 30000);
      if (r.err) return send(res, 500, { error: (r.stderr || r.err.message).slice(0, 300) });
      if (proc.kind !== "systemd") run("pm2", ["save"]);
      return send(res, 200, { ok: true });
    }
    const lg = p.match(/^\/api\/logs\/([\w.\-]+)$/);
    if (lg && req.method === "GET") return streamLogs(req, res, lg[1]);
    if (p === "/api/stats") {
      return send(res, 200, { cpu: cpuPercent(), cores: os.cpus().length, mem: memInfo(), disk: await diskInfo(), load: os.loadavg(), uptime: os.uptime(), host: os.hostname() });
    }
    if (p === "/api/chivato" && req.method === "GET") return send(res, 200, chvResumen());
    if (p === "/api/chivato/orden" && req.method === "POST") {
      try { chvOrden(await readBody(req)); return send(res, 200, { ok: true }); }
      catch (e) { return send(res, 400, { error: e.message }); }
    }
    const vid = p.match(/^\/api\/chivato\/video\/([\w.-]+)$/);
    if (vid && req.method === "GET") return chvVideo(req, res, vid[1]);
    const wa = p.match(/^\/api\/wallet\/([1-9A-HJ-NP-Za-km-z]{32,44})$/);
    if (wa && req.method === "GET") {
      try { return send(res, 200, await analizarWallet(wa[1], Math.min(10, Math.max(1, +url.searchParams.get("p") || 5)))); }
      catch (e) { return send(res, 502, { error: e.message }); }
    }
    if (p === "/api/memebot/wallets" && req.method === "GET") return send(res, 200, { wallets: memebotWallets(), helius: !!heliusKey() });
    if (p === "/api/memebot/wallets" && req.method === "POST") {
      try { const b = await readBody(req); await walletAnadir(String(b.addr || "").trim(), b.nota); return send(res, 200, { ok: true }); }
      catch (e) { return send(res, 400, { error: e.message }); }
    }
    if (p === "/api/memebot/wallets/quitar" && req.method === "POST") {
      try { const b = await readBody(req); await walletQuitar(String(b.addr || "").trim()); return send(res, 200, { ok: true }); }
      catch (e) { return send(res, 400, { error: e.message }); }
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
[hidden]{display:none!important}
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
  .mobnav .badge{position:absolute;top:0;right:4px}
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
.seg{display:flex;gap:6px;overflow-x:auto;padding-bottom:2px}
.seg button{border:1px solid var(--line);background:var(--surface);border-radius:999px;padding:7px 14px;font-size:14px;font-weight:500;white-space:nowrap;display:inline-flex;gap:6px;align-items:center}
.seg button[aria-selected="true"]{background:var(--ink);color:var(--surface);border-color:var(--ink)}
.seg .badge{display:inline-block}
#chvBody{display:flex;flex-direction:column;gap:16px}
.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px}
.bars{display:flex;align-items:flex-end;gap:4px;height:120px;padding-top:16px}
.bars div{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%;gap:4px;min-width:0}
.bars i{display:block;width:100%;max-width:28px;background:var(--accent);border-radius:4px 4px 0 0;min-height:2px}
.bars b{font-size:11px;font-weight:600;color:var(--ink)}
.bars span{font-size:10.5px;color:var(--ink-2);white-space:nowrap}
.hbar{display:grid;grid-template-columns:minmax(90px,1fr) 2fr auto;gap:8px;align-items:center;font-size:13.5px}
.hbar i{display:block;height:8px;border-radius:4px;background:var(--accent)}
.warn{background:var(--warn-soft);color:var(--warn);border-radius:10px;padding:12px 14px;font-size:14px}
.txt{white-space:pre-wrap;font-size:14px;line-height:1.45;background:var(--surface-2);border-radius:8px;padding:10px 12px;overflow-wrap:anywhere}
.row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.row .mini{margin-left:auto}
.switch{display:flex;gap:10px;align-items:center;font-weight:500}
.switch input{width:20px;height:20px}
textarea.msg{width:100%;min-height:150px;padding:12px;border:1px solid var(--line);border-radius:10px;background:var(--bg);color:var(--ink);font:15px/1.45 var(--body);resize:vertical}
.vids{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}
.vids video{width:100%;border-radius:8px;background:#000;aspect-ratio:1}
.box a.lnk{color:var(--accent);overflow-wrap:anywhere;font-size:13.5px}
.waIn{width:100%;padding:11px 12px;border:1px solid var(--line);border-radius:10px;background:var(--bg);color:var(--ink);font:14px var(--mono)}
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
      <a href="#chivato" data-route="chivato">Chivato <span class="badge" data-badge-chv></span></a>
      <a href="#wallets" data-route="wallets">Wallets</a>
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
        <div class="stat"><span>Procesos en marcha</span><b class="num" id="sRun">–</b><em>pm2 + systemd</em></div>
        <div class="stat"><span>Reinicios totales</span><b class="num" id="sRest">–</b><em>desde el último arranque de pm2</em></div>
        <div class="stat"><span>Esperando tu OK</span><b class="num" id="sAppr">–</b><em>aprobaciones</em></div>
        <div class="stat"><span>RAM de los bots</span><b class="num" id="sMem">–</b><em id="sMemSub">suma de procesos</em></div>
      </div>
      <div class="split">
        <div class="list" id="agentList"><div class="empty">Cargando procesos de pm2…</div></div>
        <article class="detail" id="detail"><div class="empty">Elige un agente para ver su registro.</div></article>
      </div>
    </section>

    <section class="view" id="v-chivato" hidden>
      <div class="seg" id="chvTabs" role="tablist"></div>
      <div id="chvBody"><div class="empty">Cargando datos de Chivato…</div></div>
    </section>

    <section class="view" id="v-wallets" hidden>
      <div id="waBody" style="display:flex;flex-direction:column;gap:16px"></div>
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
  <a href="#chivato" data-route="chivato">Chivato <span class="badge" data-badge-chv></span></a>
  <a href="#wallets" data-route="wallets">Wallets</a>
  <a href="#aprobaciones" data-route="aprobaciones">Aprobar <span class="badge" data-badge></span></a>
  <a href="#conectar" data-route="conectar">Más</a>
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
      <div><h2>${esc(m.title || a.name)}</h2><p>${a.kind==="systemd" ? "systemd" : "pm2"} · ${esc(a.name)}${a.kind==="systemd" ? "" : " (id "+a.id+")"}${m.control ? " · "+esc(m.control) : ""}</p></div>
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
  await Promise.all([refreshAgents(), refreshStats(), refreshApprovals(), refreshChivato()]);
  if(selected && !es) openLogs(selected);
}

// ---------- Chivato ----------
let chv = null, chvTab = "resumen", chvConfirm = null, chvDraft = "";
const PAQ = { t7: "Tablón 7 días", t30: "Tablón 30 días", dif: "Difusión a todos" };
const EST = { activo: ["run", "Activo"], tablon: ["run", "En el tablón"], pausado: ["pause", "Pausado"], finalizado: ["pause", "Terminado"],
  difundido: ["pause", "Enviado"], revision: ["wait", "En revisión"], esperando_pago: ["wait", "Pendiente de pago"], rechazado: ["err", "Rechazado"],
  pendiente: ["wait", "Pendiente"], borrador: ["pause", "Borrador"] };
function fecha(ts){ return ts ? new Date(ts).toLocaleString("es-ES",{day:"2-digit",month:"2-digit",hour:"2-digit",minute:"2-digit"}) : "–"; }
function copyText(t){
  try { if (navigator.clipboard && window.isSecureContext) { navigator.clipboard.writeText(t).then(()=>toast("Copiado"), ()=>copyOld(t)); return; } } catch(e){}
  copyOld(t);
}
function copyOld(t){
  const ta = document.createElement("textarea"); ta.value = t; ta.setAttribute("readonly",""); ta.style.position="fixed"; ta.style.top="0"; ta.style.opacity="0";
  document.body.appendChild(ta); ta.select(); ta.setSelectionRange(0, t.length);
  let ok = false; try { ok = document.execCommand("copy"); } catch(e){}
  ta.remove(); toast(ok ? "Copiado" : "No se pudo copiar: mantén pulsado el texto para copiarlo");
}
async function chvOrden(o, msg){
  try { await api("/api/chivato/orden", { method:"POST", body: JSON.stringify(o) }); toast(msg || "Enviado a Chivato. Se aplica en unos segundos."); }
  catch(e){ toast(e.message); return false; }
  chvConfirm = null; setTimeout(refreshChivato, 2500); setTimeout(refreshChivato, 12000); setTimeout(refreshChivato, 30000);
  return true;
}
async function refreshChivato(force){
  try {
    chv = await api("/api/chivato");
    const n = chv.panel ? chv.panel.err_cola.length : 0;
    document.querySelectorAll("[data-badge-chv]").forEach(b => { b.textContent = n || ""; b.dataset.n = n; });
    const typing = document.activeElement && document.activeElement.closest && document.activeElement.closest("#chvBody");
    if (!$("#v-chivato").hidden && (force || !typing)) renderChivato();
  } catch(e){}
}
function xPost(o){
  const tags = "\n\n#ofertas #chollos #amazon";
  const lineas = o.t.split("\n").map(s => s.trim()).filter(Boolean);
  let cuerpo = (lineas[0] && /POSIBLE ERROR/i.test(lineas[0]) ? "🚨 ¡Posible error de precio!\n" + lineas.slice(1).join("\n") : "🔥 " + lineas.join("\n"));
  const max = 280 - 23 - tags.length - 4;
  if (cuerpo.length > max) cuerpo = cuerpo.slice(0, max - 1) + "…";
  return cuerpo + "\n\n👉 " + o.u + tags;
}
function bars(pares, fmt){
  const mx = Math.max(1, ...pares.map(p => p[1]));
  return `<div class="bars">${pares.map(([k,v]) => `<div title="${esc(k)}: ${v}"><b class="num">${v||""}</b><i style="height:${Math.round(v/mx*100)}%"></i><span>${esc(fmt(k))}</span></div>`).join("")}</div>`;
}
function renderChivato(){
  const n = chv && chv.panel ? chv.panel.err_cola.length : 0;
  const tabs = [["resumen","Resumen"],["errores","Errores de precio" + (n ? ` <span class="badge">${n}</span>` : "")],["mensaje","Mensaje a todos"],["anuncios","Anuncios"],["x","Para X"]];
  $("#chvTabs").innerHTML = tabs.map(([k,l]) => `<button role="tab" aria-selected="${k===chvTab}" data-chvtab="${k}">${l}</button>`).join("");
  const b = $("#chvBody");
  if (!chv) { b.innerHTML = '<div class="empty">Cargando datos de Chivato…</div>'; return; }
  if (chv.error) { b.innerHTML = `<div class="warn">${esc(chv.error)}</div>`; return; }
  const aviso = chv.parcheado ? "" : `<div class="warn">Chivato todavía no tiene el parche del panel. Puedes ver las estadísticas, pero los botones (enviar errores, mensaje a todos, pausar anuncios) no harán nada hasta que apliques <b>parche_panel.py</b>.</div>`;
  const cola = chv.ordenesPendientes ? `<div class="mini">${chv.ordenesPendientes} orden(es) esperando a que Chivato las recoja…</div>` : "";
  b.innerHTML = aviso + cola + ({ resumen: chvResumen, errores: chvErrores, mensaje: chvMensaje, anuncios: chvAnuncios, x: chvX }[chvTab])();
  const ta = $("#chvMsg"); if (ta) ta.value = chvDraft;
}
function chvResumen(){
  const s = chv.stats, upd = chv.actualizado ? `Datos de ${fecha(chv.actualizado)}` : "";
  const tile = (l, v, e) => `<div class="stat"><span>${l}</span><b class="num">${v}</b>${e ? `<em>${e}</em>` : ""}</div>`;
  const fmtDia = k => k.slice(8,10) + "/" + k.slice(5,7);
  const mxc = Math.max(1, ...s.cats.map(c => c.n));
  const log = chv.panel && chv.panel.log.length ? chv.panel.log.map(x => `<div class="row" style="font-size:13.5px"><span class="${x.ok?"y":"n"}" style="color:var(--${x.ok?"ok":"bad"})">${x.ok?"✓":"✕"}</span><span>${esc(x.t)}</span><span class="mini">${fecha(x.ts)}</span></div>`).join("") : '<p class="mini">Aquí verás lo que vaya haciendo Chivato con tus órdenes.</p>';
  return `
    <div class="tiles">
      ${tile("Usuarios", s.usuarios, `${s.autorizados} con acceso`)}
      ${tile("Nuevos hoy", s.nuevosHoy, `${s.nuevos7} en 7 días`)}
      ${tile("Activos hoy", s.activosHoy, `${s.avisosHoy} avisos recibidos`)}
      ${tile("Apoyantes", s.apoyantes, `${s.propinas.n} propinas`)}
      ${tile("Stars ganadas", (s.propinas.stars + s.ventasAds.stars).toLocaleString("es-ES"), `${s.ventasAds.n} anuncios vendidos`)}
      ${tile("Valoraciones", `👍 ${s.fb.up} · 👎 ${s.fb.dn}`, s.fb.up + s.fb.dn ? `${Math.round(100*s.fb.up/(s.fb.up+s.fb.dn))}% positivas` : "")}
      ${tile("Errores de precio", s.errores.n, s.errores.on ? "caza activada" : "caza apagada")}
      ${tile("Códigos invitación", s.codigos, "creados")}
    </div>
    <div class="box"><h2>Altas de usuarios · 14 días</h2>${bars(s.altas, fmtDia)}<p class="mini">${s.previo} usuarios son de antes del modo privado. ${upd}</p></div>
    <div class="box"><h2>Ofertas del top diario · 7 días</h2>${bars(s.ofertas, fmtDia)}</div>
    ${s.cats.length ? `<div class="box"><h2>Categorías más vistas</h2>${s.cats.map(c => `<div class="hbar"><span>${esc(c.nombre)}</span><i style="width:${Math.round(c.n/mxc*100)}%"></i><b class="num">${c.n}</b></div>`).join("")}</div>` : ""}
    <div class="box"><h2>Registro del panel</h2>${log}</div>`;
}
function chvErrores(){
  const p = chv.panel;
  if (!p) return '<div class="empty">Aplica el parche para retener los errores de precio aquí.</div>';
  const sw = `<div class="box"><label class="switch"><input type="checkbox" id="errEspera" ${p.err_espera?"checked":""}> Revisar los errores antes de enviarlos a todos</label>
    <p>${p.err_espera ? "Te llegan solo a ti por Telegram y esperan aquí. Si no los envías en 6 horas, se descartan solos." : "Se envían solos, como antes, a quien tenga activados los avisos de errores."}</p></div>`;
  if (!p.err_cola.length) return sw + '<div class="empty">No hay errores de precio esperando.</div>';
  return sw + `<div class="appr">${p.err_cola.map(x => {
    const queda = Math.max(0, Math.round((x.ts + 6*3600e3 - Date.now())/3600e3*10)/10);
    const conf = chvConfirm === "err_" + x.id;
    return `<article class="ap"><div class="ap-h"><b>-${x.d}%</b><span class="mini">hace ${ago(x.ts)} · caduca en ${String(queda).replace(".",",")} h</span></div>
      <div class="txt">${esc(x.t)}</div><a class="lnk" href="${esc(x.u)}" target="_blank" rel="noopener">Ver en Amazon ↗</a>
      <div class="ap-f"><button class="btn ok sm" data-errsend="${x.id}">${conf ? `Confirmar: enviar a ${chv.destinatarios}` : "Enviar a todos"}</button>
      <button class="btn danger sm" data-errdel="${x.id}">Descartar</button></div></article>`; }).join("")}</div>`;
}
function chvMensaje(){
  const conf = chvConfirm === "msg";
  return `<div class="box"><h2>Mensaje a todos los usuarios</h2>
    <p>Lo envía Chivato desde @ChivatoAmazon_bot a ${chv.destinatarios} usuarios (los que tienen la pausa puesta no lo reciben) y una copia a ti.</p>
    <label for="chvMsg" class="mini">Texto del mensaje</label>
    <textarea class="msg" id="chvMsg" maxlength="4000" placeholder="Ej.: 🔥 Mañana empieza el Black Friday. Activa los avisos para no perderte nada."></textarea>
    <div class="row"><button class="btn ${conf ? "ok" : "primary"}" data-msgsend>${conf ? `Confirmar: enviar a ${chv.destinatarios} usuarios` : "Enviar a todos"}</button>
    ${conf ? '<button class="btn" data-msgcancel>Cancelar</button>' : ""}<span class="mini" id="msgCount">${chvDraft.length}/4000</span></div></div>`;
}
function chvAnuncios(){
  if (!chv.anuncios.length) return '<div class="empty">Todavía no hay anuncios.</div>';
  return `<div class="appr">${chv.anuncios.map(a => {
    const [cls, lab] = EST[a.estado] || ["pause", a.estado || "–"];
    const ctr = a.env ? (100*a.clics/a.env).toFixed(1).replace(".",",") + "%" : "–";
    const vivo = a.estado === "activo" || a.estado === "tablon", pausado = a.estado === "pausado";
    const conf = chvConfirm === "fin_" + a.id;
    return `<article class="ap ${vivo||pausado ? "" : "done"}" style="border-left-color:var(--${vivo?"ok":pausado?"warn":"line"})">
      <div class="ap-h"><div><b>${esc(a.id)}</b> <span class="mini">· ${esc(PAQ[a.pk] || a.tipo)}${a.region ? " · 📍 " + esc(a.region) : ""}${a.foto ? " · con foto" : ""}</span></div><span class="pill ${cls}">${esc(lab)}</span></div>
      <div class="txt">${esc(a.texto)}</div>
      ${a.enlace ? `<a class="lnk" href="${esc(a.enlace)}" target="_blank" rel="noopener">${esc(a.enlace)}</a>` : ""}
      <div class="checks"><span>Enviado a <b class="num">${a.env}</b></span><span>Clics <b class="num">${a.clics}</b> (${a.unicos} personas)</span><span>Clics por envío <b class="num">${ctr}</b></span>
        ${a.fin ? `<span>${a.fin > Date.now() ? "Activo hasta" : "Terminó el"} ${new Date(a.fin).toLocaleDateString("es-ES")}</span>` : ""}</div>
      ${vivo || pausado ? `<div class="ap-f">${vivo ? `<button class="btn sm" data-ad="ad_pausar" data-aid="${esc(a.id)}">Pausar</button>` : `<button class="btn ok sm" data-ad="ad_reanudar" data-aid="${esc(a.id)}">Reanudar</button>`}
        <button class="btn danger sm" data-ad="ad_finalizar" data-aid="${esc(a.id)}">${conf ? "Confirmar: terminar ya" : "Terminar"}</button></div>` : ""}
    </article>`; }).join("")}</div>`;
}
function chvX(){
  const v = chv.videos.length ? `<div class="vids">${chv.videos.map(x => `<div class="box" style="padding:12px">
      <video controls playsinline preload="metadata" src="/api/chivato/video/${encodeURIComponent(x.f)}"></video>
      <div class="txt" style="max-height:120px;overflow:auto">${esc(x.texto)}</div>
      <div class="row"><button class="btn sm primary" data-copy="${esc(x.texto)}">Copiar texto</button><a class="btn sm" href="/api/chivato/video/${encodeURIComponent(x.f)}?dl=1">Descargar vídeo</a><span class="mini">${fecha(x.ts)}</span></div></div>`).join("")}</div>`
    : `<p class="mini">${chv.parcheado ? "Aún no hay vídeos guardados. Los próximos que genere Chivato aparecerán aquí." : "Con el parche, los vídeos que genera Chivato aparecerán aquí."}</p>`;
  const o = chv.recent.slice(0, 15).map(r => { const t = xPost(r); return `<div class="box" style="padding:12px">
      <div class="row"><b>-${r.d}%</b><span class="mini">${fecha(r.ts)}</span></div><div class="txt">${esc(t)}</div>
      <div class="row"><button class="btn sm primary" data-copy="${esc(t)}">Copiar post</button><a class="btn sm" href="https://twitter.com/intent/tweet?text=${encodeURIComponent(t)}" target="_blank" rel="noopener">Abrir en X</a><span class="mini">${t.length - r.u.length + 23}/280</span></div></div>`; }).join("");
  return `<div class="box"><h2>Vídeos de ofertas</h2>${v}</div><div class="box"><h2>Últimas ofertas · post listo para X</h2><p>Texto con tu enlace de afiliado. Cópialo o ábrelo directamente en X.</p></div>${o || '<div class="empty">No hay ofertas recientes.</div>'}`;
}
document.addEventListener("click", e => {
  const t = e.target.closest("[data-chvtab]"); if (t) { chvTab = t.dataset.chvtab; chvConfirm = null; renderChivato(); return; }
  const c = e.target.closest("[data-copy]"); if (c) { copyText(c.dataset.copy); return; }
  const es_ = e.target.closest("[data-errsend]");
  if (es_) { const k = "err_" + es_.dataset.errsend; if (chvConfirm !== k) { chvConfirm = k; renderChivato(); } else chvOrden({ tipo: "err_enviar", id: es_.dataset.errsend }, "Enviando a todos…"); return; }
  const ed = e.target.closest("[data-errdel]"); if (ed) { chvOrden({ tipo: "err_descartar", id: ed.dataset.errdel }, "Descartado"); return; }
  const ms = e.target.closest("[data-msgsend]");
  if (ms) {
    if (!chvDraft.trim()) { toast("Escribe el mensaje primero"); return; }
    if (chvConfirm !== "msg") { chvConfirm = "msg"; renderChivato(); return; }
    chvOrden({ tipo: "mensaje", texto: chvDraft }, "Mensaje enviado a Chivato. Lo reparte en unos segundos.").then(ok => { if (ok) { chvDraft = ""; renderChivato(); } });
    return;
  }
  if (e.target.closest("[data-msgcancel]")) { chvConfirm = null; renderChivato(); return; }
  const ad = e.target.closest("[data-ad]");
  if (ad) {
    if (ad.dataset.ad === "ad_finalizar" && chvConfirm !== "fin_" + ad.dataset.aid) { chvConfirm = "fin_" + ad.dataset.aid; renderChivato(); return; }
    chvOrden({ tipo: ad.dataset.ad, aid: ad.dataset.aid });
  }
});
document.addEventListener("input", e => { if (e.target.id === "chvMsg") { chvDraft = e.target.value; const c = $("#msgCount"); if (c) c.textContent = chvDraft.length + "/4000"; } });
document.addEventListener("change", e => { if (e.target.id === "errEspera") chvOrden({ tipo: "err_espera", on: e.target.checked }); });
setInterval(() => { if (!$("#app").hidden && (!$("#v-chivato").hidden || Math.random() < .3)) refreshChivato(); }, 15000);

// ---------- Analizador de wallets ----------
let wa = { addr: "", data: null, loading: false, err: "", paginas: 5 }, mbw = null, waConfirm = null;
const corto = a => a ? a.slice(0, 4) + "…" + a.slice(-4) : "";
function dur(ms){ if (ms == null) return "–"; const m = ms / 60000; if (m < 60) return Math.round(m) + " min"; if (m < 1440) return (m / 60).toFixed(1).replace(".", ",") + " h"; return (m / 1440).toFixed(1).replace(".", ",") + " d"; }
function sol(v, signo){ const s = (+v).toFixed(Math.abs(v) < 10 ? 3 : 1).replace(".", ","); return (signo && v > 0 ? "+" : "") + s + " SOL"; }
function lineChart(pts){
  if (pts.length < 2) return '<p class="mini">Pocas ventas para dibujar la gráfica.</p>';
  const W = 360, H = 200, L = 44, R = 10, T = 12, B = 24;
  const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
  const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(0, ...ys), y1 = Math.max(0, ...ys);
  const sx = x => L + (x - x0) / Math.max(1, x1 - x0) * (W - L - R), sy = y => T + (y1 - y) / Math.max(1e-9, y1 - y0) * (H - T - B);
  const d = pts.map((p, i) => (i ? "L" : "M") + sx(p[0]).toFixed(1) + " " + sy(p[1]).toFixed(1)).join(" ");
  const fin = ys[ys.length - 1], col = fin >= 0 ? "var(--ok)" : "var(--bad)";
  const area = d + ` L ${sx(x1).toFixed(1)} ${sy(0).toFixed(1)} L ${sx(x0).toFixed(1)} ${sy(0).toFixed(1)} Z`;
  const f = t => new Date(t).toLocaleDateString("es-ES", { day: "2-digit", month: "2-digit" });
  const lbl = v => (v > 0 ? "+" : "") + (Math.abs(v) < 10 ? v.toFixed(2) : v.toFixed(0)).replace(".", ",");
  return `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Beneficio acumulado en SOL" style="display:block">
    <line x1="${L}" x2="${W - R}" y1="${sy(0)}" y2="${sy(0)}" stroke="var(--line)" stroke-dasharray="4 4"/>
    <line x1="${L}" x2="${W - R}" y1="${sy(y1)}" y2="${sy(y1)}" stroke="var(--line)" opacity=".5"/>
    <line x1="${L}" x2="${W - R}" y1="${sy(y0)}" y2="${sy(y0)}" stroke="var(--line)" opacity=".5"/>
    <text x="${L - 6}" y="${sy(y1) + 4}" text-anchor="end" font-size="12" fill="var(--ink-2)">${lbl(y1)}</text>
    <text x="${L - 6}" y="${sy(0) + 4}" text-anchor="end" font-size="12" fill="var(--ink-2)">0</text>
    ${y0 < 0 ? `<text x="${L - 6}" y="${sy(y0) + 4}" text-anchor="end" font-size="12" fill="var(--ink-2)">${lbl(y0)}</text>` : ""}
    <path d="${area}" fill="${col}" opacity=".12"/>
    <path d="${d}" fill="none" stroke="${col}" stroke-width="2.2" stroke-linejoin="round"/>
    <circle cx="${sx(x1)}" cy="${sy(fin)}" r="4" fill="${col}"/>
    <text x="${L}" y="${H - 6}" font-size="12" fill="var(--ink-2)">${f(x0)}</text>
    <text x="${W - R}" y="${H - 6}" text-anchor="end" font-size="12" fill="var(--ink-2)">${f(x1)}</text>
  </svg>`;
}
async function waAnalizar(addr){
  addr = (addr || "").trim();
  if (!/^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(addr)) { toast("Eso no parece una dirección de Solana"); return; }
  wa = { ...wa, addr, data: null, loading: true, err: "" }; waConfirm = null; renderWallets();
  try { wa.data = await api(`/api/wallet/${addr}?p=${wa.paginas}`); }
  catch (e) { wa.err = e.message; }
  wa.loading = false; renderWallets();
  const r = $("#waRes"); if (r) r.scrollIntoView({ behavior: "smooth", block: "start" });
}
async function refreshMbw(){ try { mbw = await api("/api/memebot/wallets"); if (!$("#v-wallets").hidden) renderWallets(); } catch(e){} }
function renderWallets(){
  const el = $("#waBody"); if (!el) return;
  const r = wa.data;
  const V = { buena: ["run", "Buena para copiar", "var(--ok)"], dudosa: ["wait", "Dudosa: vigílala antes", "var(--warn)"], no: ["err", "No copiar", "var(--bad)"] };
  let res = "";
  if (wa.loading) res = '<div class="box"><div class="empty">Analizando la wallet… (10-30 segundos)</div></div>';
  else if (wa.err) res = `<div class="warn">${esc(wa.err)}</div>`;
  else if (r) {
    const [cls, txt, col] = V[r.veredicto];
    const yaEsta = mbw && mbw.wallets.some(w => w.addr === r.addr);
    const sym = m => (r.simbolos && r.simbolos[m]) || corto(m);
    const nota = `win ${r.winRate ?? "?"}% · ${r.pnlSol} SOL · ${r.tradesDia}/día`;
    res = `<div id="waRes" class="box" style="border-left:4px solid ${col}">
      <div class="row"><h2 style="font-size:17px">${corto(r.addr)}</h2><span class="pill ${cls}">${txt}</span></div>
      <p>Analizadas ${r.txs} transacciones · ${r.trades} compras/ventas en ${String(r.dias).replace(".", ",")} días${r.saldo != null ? ` · saldo ${sol(r.saldo)}` : ""}</p>
      <div style="display:flex;flex-direction:column;gap:8px">${r.checks.map(([t, ok, det]) => `<div style="display:grid;grid-template-columns:20px 1fr;gap:6px;font-size:14px"><b style="color:var(--${ok ? "ok" : "bad"})">${ok ? "✓" : "✕"}</b><div>${esc(t)}<div class="mini">${esc(det)}</div></div></div>`).join("")}</div>
      <div class="row">${yaEsta ? '<span class="pill run">Memebot ya la vigila</span>' :
        `<button class="btn ${waConfirm === "add" ? "ok" : "primary"}" data-waadd="${r.addr}" data-nota="${esc(nota)}">${waConfirm === "add" ? "Confirmar: añadir y reiniciar Memebot" : "Añadir a Memebot"}</button>`}
        <a class="btn" href="https://gmgn.ai/sol/address/${r.addr}" target="_blank" rel="noopener">Ver en GMGN ↗</a>
        <button class="btn" data-copy="${r.addr}">Copiar dirección</button></div>
    </div>
    <div class="tiles">
      <div class="stat"><span>Beneficio cerrado</span><b class="num" style="color:${r.pnlSol >= 0 ? "var(--ok)" : "var(--bad)"}">${sol(r.pnlSol, true)}</b><em>${r.cerradas} tokens cerrados</em></div>
      <div class="stat"><span>Acierto</span><b class="num">${r.winRate ?? "–"}%</b><em>tokens con ganancia</em></div>
      <div class="stat"><span>Trades al día</span><b class="num">${String(r.tradesDia).replace(".", ",")}</b><em>${r.trades} en total</em></div>
      <div class="stat"><span>Aguanta (mediana)</span><b class="num">${dur(r.holdMediano)}</b><em>de compra a venta</em></div>
      <div class="stat"><span>Gasta por token</span><b class="num">${sol(r.gastadoMedio)}</b><em>de media</em></div>
      <div class="stat"><span>Abiertas</span><b class="num">${r.abiertas}</b><em>sin vender</em></div>
    </div>
    <div class="box"><h2>Beneficio acumulado (SOL)</h2>${lineChart(r.curva)}<p class="mini">Suma lo ganado o perdido en cada venta. Si sube de forma constante, la wallet es buena; si da un salto y luego baja, fue suerte.</p></div>
    ${r.porDia.length ? `<div class="box"><h2>Compras y ventas por día</h2>${bars(r.porDia.slice(-14), k => k.slice(8, 10) + "/" + k.slice(5, 7))}</div>` : ""}
    ${r.top.length ? `<div class="box"><h2>Mejores y peores tokens</h2>${r.top.map(t => `<div class="hbar" style="grid-template-columns:1fr auto auto"><a class="lnk" href="https://gmgn.ai/sol/token/${t.mint}" target="_blank" rel="noopener">${esc(sym(t.mint))}</a><span class="mini">${(t.x).toFixed(1).replace(".", ",")}x · ${dur(t.hold)}</span><b class="num" style="color:var(--${t.pnl >= 0 ? "ok" : "bad"})">${sol(t.pnl, true)}</b></div>`).join("")}</div>` : ""}
    ${r.abiertasLista.length ? `<div class="box"><h2>Lo que tiene ahora sin vender</h2>${r.abiertasLista.map(t => `<div class="hbar" style="grid-template-columns:1fr auto auto"><a class="lnk" href="https://gmgn.ai/sol/token/${t.mint}" target="_blank" rel="noopener">${esc(sym(t.mint))}</a><span class="mini">${fecha(t.ts)}</span><b class="num">${sol(t.gastado)}</b></div>`).join("")}</div>` : ""}`;
  }
  const lista = mbw ? mbw.wallets.map(w => `<div class="row" style="border-top:1px solid var(--line);padding-top:8px">
      <code style="font-size:13px">${corto(w.addr)}</code><span class="mini" style="margin-left:0">${esc(w.nota || "")}</span>
      <span style="margin-left:auto;display:flex;gap:6px"><button class="btn sm" data-waver="${w.addr}">Analizar</button>
      ${w.fijo ? "" : `<button class="btn sm danger" data-waquitar="${w.addr}">${waConfirm === "q_" + w.addr ? "Confirmar" : "Quitar"}</button>`}</span></div>`).join("") : '<p class="mini">Cargando…</p>';
  el.innerHTML = `
    ${mbw && !mbw.helius ? '<div class="warn">No encuentro la clave de Helius de Memebot (HELIUS_API_KEY en /root/memebot/.env).</div>' : ""}
    <div class="box"><h2>Analizar una wallet de Solana</h2>
      <p>Pega la dirección (la de GMGN, Birdeye, Solscan…). Miro sus últimas operaciones con Helius y te digo si merece la pena copiarla.</p>
      <input id="waAddr" class="waIn" placeholder="Dirección de la wallet" autocomplete="off" autocapitalize="off" spellcheck="false" value="${esc(wa.addr)}" aria-label="Dirección de la wallet">
      <div class="row"><button class="btn primary" data-waanalizar ${wa.loading ? "disabled" : ""}>Analizar</button>
        <label class="mini" style="margin-left:0;display:flex;gap:6px;align-items:center"><input type="checkbox" id="waProf" ${wa.paginas > 5 ? "checked" : ""}> Análisis profundo (1.000 tx, más créditos)</label></div>
    </div>
    ${res}
    <div class="box"><h2>Wallets que vigila Memebot (${mbw ? mbw.wallets.length : "…"})</h2>${lista}
      <p class="mini">Al añadir o quitar, Memebot se reinicia solo y actualiza el webhook de Helius.</p></div>`;
}
document.addEventListener("click", async e => {
  if (e.target.closest("[data-waanalizar]")) { waAnalizar($("#waAddr").value); return; }
  const v = e.target.closest("[data-waver]"); if (v) { $("#waAddr").value = v.dataset.waver; waAnalizar(v.dataset.waver); return; }
  const a = e.target.closest("[data-waadd]");
  if (a) {
    if (waConfirm !== "add") { waConfirm = "add"; renderWallets(); return; }
    a.disabled = true;
    try { await api("/api/memebot/wallets", { method: "POST", body: JSON.stringify({ addr: a.dataset.waadd, nota: a.dataset.nota }) }); toast("Añadida. Memebot se está reiniciando."); }
    catch (err) { toast(err.message); }
    waConfirm = null; await refreshMbw(); renderWallets(); return;
  }
  const q = e.target.closest("[data-waquitar]");
  if (q) {
    const k = "q_" + q.dataset.waquitar;
    if (waConfirm !== k) { waConfirm = k; renderWallets(); return; }
    q.disabled = true;
    try { await api("/api/memebot/wallets/quitar", { method: "POST", body: JSON.stringify({ addr: q.dataset.waquitar }) }); toast("Quitada. Memebot se está reiniciando."); }
    catch (err) { toast(err.message); }
    waConfirm = null; await refreshMbw(); return;
  }
});
document.addEventListener("change", e => { if (e.target.id === "waProf") wa.paginas = e.target.checked ? 10 : 5; });
document.addEventListener("keydown", e => { if (e.target.id === "waAddr" && e.key === "Enter") waAnalizar(e.target.value); });

const TITLES = { agentes:["Mis agentes","Procesos de pm2 y servicios de systemd en tu VPS, en directo."], aprobaciones:["Aprobaciones","Acciones que tus bots no hacen sin tu OK."], conectar:["Conectar bots","Cómo hacer que tus bots pidan permiso al panel."], chivato:["Chivato","Estadísticas, errores de precio, mensajes, anuncios y contenido para X."], wallets:["Wallets","Analiza una wallet de Solana antes de copiarla con Memebot."] };
function route(){
  const r = (location.hash.slice(1) in TITLES) ? location.hash.slice(1) : "agentes";
  Object.keys(TITLES).forEach(k => $("#v-"+k).hidden = k!==r);
  document.querySelectorAll("[data-route]").forEach(a => { if(a.dataset.route===r) a.setAttribute("aria-current","page"); else a.removeAttribute("aria-current"); });
  $("#pageTitle").textContent = TITLES[r][0]; $("#pageSub").textContent = TITLES[r][1];
  if(r==="aprobaciones") renderApprovals();
  if(r==="chivato"){ renderChivato(); refreshChivato(true); }
  if(r==="wallets"){ renderWallets(); refreshMbw(); }
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
    port = os.environ.get("PANEL_PORT") or env.get("PANEL_PORT", "8081")
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

if ! grep -q '^PANEL_SYSTEMD=' "$D/.env"; then echo "PANEL_SYSTEMD=chivato" >> "$D/.env"; fi
PORT=$(grep '^PANEL_PORT=' "$D/.env" | cut -d= -f2- || true); PORT=${PORT:-8081}
pm2 restart panel >/dev/null && pm2 save >/dev/null
sleep 2
echo
echo "============  PANEL ACTUALIZADO  ============"
if curl -s --max-time 5 "http://127.0.0.1:$PORT/" | grep -q "Centro de mando"; then echo " Funciona: si (puerto $PORT)"; else echo " NO responde: mira 'pm2 logs panel'"; fi
echo " Servicios systemd vigilados: $(grep '^PANEL_SYSTEMD=' "$D/.env" | cut -d= -f2-)"
systemctl is-active chivato >/dev/null 2>&1 && echo " chivato: activo" || echo " chivato: NO activo o con otro nombre (systemctl list-units --type=service)"
echo " Copia de la version anterior en: $B"
echo "============================================="
