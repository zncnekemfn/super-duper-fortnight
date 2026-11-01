import os, re, sys, shutil, time, glob, getpass, subprocess
try:
    import requests
except Exception:
    print("ABORTO: falta el modulo requests"); sys.exit(1)
BASE = os.environ.get("CHV_API", "https://api.telegram.org")
DIR = (sys.argv[1] if len(sys.argv) > 1 else "/opt/chivato").rstrip("/")
TOK = re.compile(r"\b\d{8,11}:[A-Za-z0-9_-]{30,}\b")
SIST = os.environ.get("CHV_NOSYSTEMD") != "1"

def getme(t):
    try:
        r = requests.get("%s/bot%s/getMe" % (BASE, t), timeout=15).json()
        return r["result"] if r.get("ok") else None
    except Exception:
        return None

cands = [os.path.join(DIR, "bot.py"), os.path.join(DIR, ".env")] + glob.glob(os.path.join(DIR, "*.env"))
if DIR == "/opt/chivato":
    cands += glob.glob("/etc/systemd/system/chivato*.service")
cands = [c for c in dict.fromkeys(cands) if os.path.isfile(c)]
texto = {c: open(c, encoding="utf-8", errors="ignore").read() for c in cands}
por_token = {}
for c, t in texto.items():
    for k in set(TOK.findall(t)):
        por_token.setdefault(k, []).append(c)
validos = {}
for k in por_token:
    me = getme(k)
    if me:
        validos[k] = me
if len(validos) != 1:
    print("ABORTO: esperaba encontrar 1 token valido y hay", len(validos))
    for k, me in validos.items():
        print("  -", "@" + me.get("username", "?"), "en", por_token[k])
    sys.exit(1)
viejo, me_v = list(validos.items())[0]
print("Bot antiguo encontrado: @%s  (en %s)" % (me_v["username"], ", ".join(os.path.basename(x) for x in por_token[viejo])))
nuevo = os.environ.get("CHV_NEW_TOKEN") or getpass.getpass("Pega el token del bot NUEVO (no se ve al pegar) y pulsa Enter: ").strip()
if nuevo == viejo or not TOK.fullmatch(nuevo):
    print("ABORTO: ese token no es valido o es el mismo del bot antiguo"); sys.exit(1)
me_n = getme(nuevo)
if not me_n:
    print("ABORTO: Telegram no reconoce ese token. Copialo otra vez desde BotFather"); sys.exit(1)
un_v, un_n = me_v["username"], me_n["username"]
print("Bot nuevo:  @%s  (%s)" % (un_n, me_n.get("first_name", "")))
ok = os.environ.get("CHV_CONFIRM") or input("Se pasara todo de @%s a @%s. Escribe SI para continuar: " % (un_v, un_n))
if ok.strip().upper() != "SI":
    print("Cancelado. No he cambiado nada."); sys.exit(0)
ts = time.strftime("%Y%m%d%H%M%S")
bak = DIR + "_bak_nuevobot_" + ts
os.makedirs(bak)
tocar = list(dict.fromkeys(por_token[viejo] + [os.path.join(DIR, "bot.py"), os.path.join(DIR, "miniapp", "index.html")]))
tocar = [f for f in tocar if os.path.isfile(f)]
for f in tocar:
    shutil.copy2(f, os.path.join(bak, f.strip("/").replace("/", "__")))
cambios = 0
for f in tocar:
    t = open(f, encoding="utf-8", errors="ignore").read()
    t2 = t.replace(viejo, nuevo)
    if f.endswith(("bot.py", "index.html")):
        t2 = re.sub(r"(?i)\b" + re.escape(un_v) + r"\b", un_n, t2)
    if t2 != t:
        cambios += 1
        open(f, "w", encoding="utf-8").write(t2)
print("Archivos actualizados:", cambios, "| copia en", bak)
try:
    bp = open(os.path.join(DIR, "bot.py"), encoding="utf-8", errors="ignore").read()
    compile(bp, "bot.py", "exec")
except SyntaxError as e:
    print("ABORTO: bot.py no compila, restauro", e)
    for f in tocar:
        shutil.copy2(os.path.join(bak, f.strip("/").replace("/", "__")), f)
    sys.exit(1)
# --- bot antiguo como puente de redireccion ---
VD = DIR + "_viejo"
os.makedirs(VD, exist_ok=True)
VIEJO = '''import requests, time, json
TOKEN = %r
NUEVO = %r
URL = "https://t.me/%s?start=mudanza"
API = "https://api.telegram.org/bot" + TOKEN
TXT = ("Nos hemos mudado!\\n\\nChivato de Ofertas ahora vive en @%s.\\n"
       "Pulsa el boton, toca Iniciar y seguiras recibiendo las mejores ofertas, gratis y sin spam.")
KB = json.dumps({"inline_keyboard": [[{"text": "Abrir el bot nuevo", "url": URL}]]})
def call(m, **k):
    try:
        return requests.post(API + "/" + m, data=k, timeout=40).json()
    except Exception:
        return {}
call("deleteWebhook")
off = 0
while True:
    r = call("getUpdates", offset=off, timeout=30)
    if not r.get("ok"):
        time.sleep(5); continue
    for u in r.get("result", []):
        off = u["update_id"] + 1
        m = u.get("message")
        cb = u.get("callback_query")
        if cb:
            call("answerCallbackQuery", callback_query_id=cb["id"])
            call("sendMessage", chat_id=cb["message"]["chat"]["id"], text=TXT, reply_markup=KB)
        elif m and m.get("chat", {}).get("type") == "private":
            call("sendMessage", chat_id=m["chat"]["id"], text=TXT, reply_markup=KB)
''' % (viejo, un_n, un_n, un_n)
vp = os.path.join(VD, "viejo.py")
open(vp, "w", encoding="utf-8").write(VIEJO)
os.chmod(vp, 0o600)
unit = ("[Unit]\nDescription=Chivato bot antiguo (redireccion)\nAfter=network-online.target\n\n[Service]\n"
        "ExecStart=%s %s\nRestart=always\nRestartSec=5\n\n[Install]\nWantedBy=multi-user.target\n" % (shutil.which("python3") or "/usr/bin/python3", vp))
if SIST:
    open("/etc/systemd/system/chivato-viejo.service", "w").write(unit)
    subprocess.call(["systemctl", "daemon-reload"])
    subprocess.call(["systemctl", "restart", "chivato"])
    time.sleep(4)
    subprocess.call(["systemctl", "enable", "--now", "chivato-viejo"])
    for s in ("chivato", "chivato-viejo"):
        print(s, "->", subprocess.run(["systemctl", "is-active", s], capture_output=True, text=True).stdout.strip())
else:
    print("(prueba) servicios no tocados")
bad = [l.strip()[:110] for l in bp.splitlines() if re.search(r"Forbidden|bot was blocked|chat not found|deactivated", l)]
print("\nLISTO. El bot principal ahora es @%s y @%s solo redirige." % (un_n, un_v))
if bad:
    print("Ojo: lineas del bot que tratan usuarios bloqueados (revisalas conmigo):")
    for l in bad[:6]:
        print("  ", l)
print("Deshacer: copia de seguridad en", bak)
