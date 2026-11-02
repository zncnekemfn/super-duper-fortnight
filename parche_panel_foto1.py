import os, re, shutil, subprocess, sys, time
# Mensaje a todos CON FOTO (panel + bot). Ejecutar como root en el VPS.
PANEL = sys.argv[1] if len(sys.argv) > 1 else "/opt/panel"
BOT = sys.argv[2] if len(sys.argv) > 2 else "/opt/chivato/bot.py"
SRV = os.path.join(PANEL, "server.js"); IDX = os.path.join(PANEL, "public", "index.html")
MARCA_BOT = "# --- PANELFOTO1 ---"
for f in (SRV, IDX, BOT):
    if not os.path.isfile(f):
        print("ABORTO: no encuentro", f); sys.exit(1)
srv = open(SRV, encoding="utf-8").read(); idx = open(IDX, encoding="utf-8").read(); bot = open(BOT, encoding="utf-8").read()
if "chvFoto" in idx and "PANELFOTO1" in srv and MARCA_BOT in bot:
    print("Ya estaba aplicado. No hago nada."); sys.exit(0)

def cambiar(txt, viejo, nuevo, nombre):
    if txt.count(viejo) != 1:
        print("ABORTO: no encuentro (o hay mas de uno) el punto de enganche:", nombre); sys.exit(1)
    return txt.replace(viejo, nuevo, 1)

# ---------- server.js ----------
srv = cambiar(srv, 'try { chvOrden(await readBody(req)); return send(res, 200, { ok: true }); }',
              'try { chvOrden(await readBody(req, 8 * 1024 * 1024)); return send(res, 200, { ok: true }); }', "server: lectura del cuerpo")
srv = cambiar(srv, 'if (b.tipo === "mensaje") { o.texto = String(b.texto || "").trim().slice(0, 4000); if (!o.texto) throw new Error("El mensaje está vacío"); }',
'''if (b.tipo === "mensaje") { // PANELFOTO1
    o.texto = String(b.texto || "").trim().slice(0, 4000);
    const fm = /^data:image\\/(jpeg|png|webp);base64,([A-Za-z0-9+\\/=]+)$/.exec(String(b.foto || ""));
    if (b.foto && !fm) throw new Error("La foto no es válida");
    if (!o.texto && !fm) throw new Error("El mensaje está vacío");
    if (fm) {
      const buf = Buffer.from(fm[2], "base64");
      if (buf.length > 5 * 1024 * 1024) throw new Error("La foto pesa demasiado (máx. 5 MB)");
      fs.mkdirSync(CHV_ORD, { recursive: true });
      const nombre = `foto_${Date.now()}_${crypto.randomBytes(3).toString("hex")}.${fm[1] === "jpeg" ? "jpg" : fm[1]}`;
      fs.writeFileSync(path.join(CHV_ORD, nombre), buf);
      o.foto = nombre;
    }
  }''', "server: orden de mensaje")

# ---------- index.html ----------
idx = cambiar(idx, 'chvConfirm = null, chvDraft = "";', 'chvConfirm = null, chvDraft = "", chvFoto = "";', "web: variables")
idx = cambiar(idx, 'placeholder="Ej.: 🔥 Mañana empieza el Black Friday. Activa los avisos para no perderte nada."></textarea>',
'''placeholder="Ej.: 🔥 Mañana empieza el Black Friday. Activa los avisos para no perderte nada."></textarea>
    <div class="row" style="margin:8px 0"><label class="btn sm" style="cursor:pointer">📷 ${chvFoto ? "Cambiar foto" : "Añadir foto (opcional)"}<input type="file" id="chvFotoIn" accept="image/*" hidden></label>${chvFoto ? '<button class="btn sm" data-fotoquitar>Quitar foto</button>' : ""}</div>
    ${chvFoto ? `<img src="${chvFoto}" alt="" style="max-width:100%;max-height:220px;border-radius:12px;margin-bottom:8px">` : ""}''', "web: textarea")
idx = cambiar(idx, 'if (!chvDraft.trim()) { toast("Escribe el mensaje primero"); return; }',
              'if (!chvDraft.trim() && !chvFoto) { toast("Escribe el mensaje o añade una foto"); return; }', "web: comprobacion")
idx = cambiar(idx, 'chvOrden({ tipo: "mensaje", texto: chvDraft }, "Mensaje enviado a Chivato. Lo reparte en unos segundos.").then(ok => { if (ok) { chvDraft = ""; renderChivato(); } });',
              'chvOrden({ tipo: "mensaje", texto: chvDraft, foto: chvFoto }, "Mensaje enviado a Chivato. Lo reparte en unos segundos.").then(ok => { if (ok) { chvDraft = ""; chvFoto = ""; renderChivato(); } });', "web: envio")
LIS = '''document.addEventListener("input", e => { if (e.target.id === "chvMsg") { chvDraft = e.target.value; const c = $("#msgCount"); if (c) c.textContent = chvDraft.length + "/4000"; } });'''
idx = cambiar(idx, LIS, LIS + '''
document.addEventListener("change", e => {
  if (e.target.id !== "chvFotoIn") return;
  const f = e.target.files && e.target.files[0]; if (!f) return;
  const rd = new FileReader();
  rd.onload = () => { const im = new Image();
    im.onload = () => { const k = Math.min(1, 1280 / Math.max(im.width, im.height)); const c = document.createElement("canvas");
      c.width = Math.round(im.width * k); c.height = Math.round(im.height * k);
      const g = c.getContext("2d"); g.fillStyle = "#fff"; g.fillRect(0, 0, c.width, c.height); g.drawImage(im, 0, 0, c.width, c.height);
      chvFoto = c.toDataURL("image/jpeg", 0.85); chvConfirm = null; renderChivato(); };
    im.onerror = () => toast("No se pudo leer la foto"); im.src = rd.result; };
  rd.readAsDataURL(f);
});
document.addEventListener("click", e => { if (e.target.closest("[data-fotoquitar]")) { chvFoto = ""; chvConfirm = null; renderChivato(); } });''', "web: escuchas")

# ---------- bot ----------
for n in ("def _pn_mensaje(", "def _pn_orden(", "PN_DIR", "def _vd_token(", "def _pn_destinos(", "def _pn_log("):
    if n not in bot:
        print("ABORTO: en bot.py no encuentro", n, "(falta el parche del panel)"); sys.exit(1)
anc = list(re.finditer(r'(?m)^if __name__ == ["\']__main__["\']:', bot))
if len(anc) != 1:
    print("ABORTO: punto de entrada del bot (%d)" % len(anc)); sys.exit(1)
BLOQUE = r'''
# --- PANELFOTO1 ---
# Mensaje a todos con foto (desde el panel)
def _pn_mensaje_foto(d, texto, nombre):
    texto = str(texto or "").strip()[:4000]
    ruta = os.path.join(PN_DIR, os.path.basename(str(nombre or "")))
    if not os.path.isfile(ruta):
        _pn_log(d, "Mensaje con foto: no encuentro la foto en el servidor.", False); return
    dest = [ADMIN] + _pn_destinos(d)
    _pn_log(d, "Enviando mensaje con foto a %d usuarios..." % len(dest))
    def _run():
        ok = mal = 0; fid = None
        try:
            datos = open(ruta, "rb").read()
        except Exception as e:
            _pn_log(d, "Mensaje con foto: no pude leer la foto (%s)." % e, False); return
        largo = len(texto) > 1000
        url = "https://api.telegram.org/bot%s/sendPhoto" % _vd_token()
        for cid in dest:
            st = 0
            try:
                data = {"chat_id": cid}
                if texto and not largo:
                    data["caption"] = texto
                if fid:
                    data["photo"] = fid
                    r = requests.post(url, data=data, timeout=60)
                else:
                    r = requests.post(url, data=data, files={"photo": ("foto.jpg", datos, "image/jpeg")}, timeout=60)
                st = r.status_code
                if st == 200 and not fid:
                    try: fid = r.json()["result"]["photo"][-1]["file_id"]
                    except Exception: fid = None
                if st == 200 and texto and largo:
                    enviar(cid, texto)
            except Exception:
                st = 0
            if st == 200: ok += 1
            else: mal += 1
            time.sleep(0.05)
        try: os.remove(ruta)
        except Exception: pass
        _pn_log(d, "Mensaje con foto terminado: %d entregados, %d fallidos." % (ok, mal), mal == 0)
    _pn_th.Thread(target=_run, daemon=True).start()

_pn_orden_pre_pf = _pn_orden

def _pn_orden(d, o):
    if o.get("tipo") == "mensaje" and o.get("foto"):
        return _pn_mensaje_foto(d, o.get("texto"), o.get("foto"))
    return _pn_orden_pre_pf(d, o)
'''
nbot = bot[:anc[0].start()] + BLOQUE + "\n" + bot[anc[0].start():]
try: compile(nbot, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: bot.py no compilaria:", e); sys.exit(1)

# comprobar JS antes de escribir nada
def node_ok(codigo, sufijo):
    try:
        t = os.path.join(PANEL, ".chk_" + str(os.getpid()) + sufijo)
        open(t, "w", encoding="utf-8").write(codigo)
        r = subprocess.run(["node", "--check", t], capture_output=True, text=True, timeout=30)
        os.remove(t)
        return r.returncode == 0, r.stderr[:300]
    except FileNotFoundError:
        return True, ""
ok1, e1 = node_ok(srv, ".js")
if not ok1:
    print("ABORTO: server.js no compilaria:", e1); sys.exit(1)
m = re.findall(r"<script[^>]*>(.*?)</script>", idx, re.S)
if m:
    ok2, e2 = node_ok(max(m, key=len), ".js")
    if not ok2:
        print("ABORTO: el JavaScript de la web no compilaria:", e2); sys.exit(1)

s = time.strftime("%Y%m%d%H%M%S")
for f in (SRV, IDX, BOT):
    shutil.copy(f, f + ".bak_panelfoto_" + s)
open(SRV, "w", encoding="utf-8").write(srv); open(IDX, "w", encoding="utf-8").write(idx); open(BOT, "w", encoding="utf-8").write(nbot)
print("Mensaje con foto instalado. Copias: *.bak_panelfoto_" + s)
print("Ahora ejecuta, una por una:")
print("  pm2 restart panel")
print("  sudo systemctl restart chivato")
print("Deshacer: cp %s.bak_panelfoto_%s %s ; cp %s.bak_panelfoto_%s %s ; cp %s.bak_panelfoto_%s %s ; pm2 restart panel ; sudo systemctl restart chivato" % (SRV, s, SRV, IDX, s, IDX, BOT, s, BOT))
