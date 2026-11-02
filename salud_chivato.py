# Revision diaria de Chivato: comprueba que todo funciona y te lo manda por Telegram.
#   python3 salud_chivato.py            -> revisa y envia el resumen
#   python3 salud_chivato.py --instalar -> lo programa cada dia a las 8:30 (hora de Madrid) y envia uno de prueba
import json, os, re, shutil, subprocess, sys, time, urllib.request

ENV_FILE = "/opt/chivato/.env"
RUTA = "/opt/chivato/salud_chivato.py"
SERVICIOS = [("chivato", "Bot Chivato"), ("chivato-codigos", "Códigos"), ("caddy", "Caddy (HTTPS)")]
WEB = "https://chivato-ofertas.duckdns.org/"


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()


def leer_env():
    env = {}
    try:
        for l in open(ENV_FILE, encoding="utf-8"):
            l = l.strip()
            if l and not l.startswith("#") and "=" in l:
                k, v = l.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return env


def tg(token, metodo, datos):
    try:
        req = urllib.request.Request("https://api.telegram.org/bot%s/%s" % (token, metodo),
                                     data=json.dumps(datos).encode(), headers={"Content-Type": "application/json"})
        return json.load(urllib.request.urlopen(req, timeout=20))
    except Exception as e:
        return {"ok": False, "description": str(e)}


def http(url):
    try:
        return urllib.request.urlopen(url, timeout=20).status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def revisar():
    mal, info = [], []

    # 1) servicios (si alguno esta parado, se intenta arrancar)
    for svc, nombre in SERVICIOS:
        if sh("systemctl is-active %s" % svc) != "active":
            sh("systemctl restart %s" % svc)
            time.sleep(10)
            if sh("systemctl is-active %s" % svc) == "active":
                mal.append("%s estaba parado: lo he vuelto a arrancar ✅" % nombre)
            else:
                mal.append("%s está PARADO y no arranca ❌" % nombre)

    # 2) mini app y web
    if http("http://127.0.0.1:8765/") != 200:
        mal.append("La mini app no responde dentro del servidor ❌")
    if http(WEB) != 200:
        mal.append("La web %s no responde desde fuera ❌" % WEB)

    # 3) ofertas de las ultimas 24 h (registro del bot)
    log = sh('journalctl -u chivato --since "-24h" --no-pager -o cat')
    nuevos = sum(int(n) for n in re.findall(r"nuevos: (\d+)", log))
    avisos = sum(int(n) for n in re.findall(r"avisos: (\d+)", log))
    vueltas = len(re.findall(r"keepa ok", log))
    errores = len(re.findall(r"Traceback", log))
    if vueltas == 0:
        mal.append("Keepa no ha hecho ninguna búsqueda en 24 h ❌")
    info.append("Ofertas nuevas en 24 h: %d (avisos: %d)" % (nuevos, avisos))
    if errores:
        info.append("Errores en el registro: %d (míralo si sube mucho)" % errores)
    toks = re.findall(r"keepa tokens: (\d+)", log)
    if toks:
        info.append("Tokens de Keepa: %s" % toks[-1])

    # 4) codigos
    try:
        d = json.load(open("/opt/chivato/codigos/datos.json", encoding="utf-8"))["codigos"]
        pend = sum(1 for c in d if c.get("estado") == "pendiente" and (c.get("plan") != "top" or c.get("pagado")))
        activos = sum(1 for c in d if c.get("estado") == "aprobado")
        info.append("Códigos: %d publicados, %d pendientes de revisar" % (activos, pend))
    except (OSError, ValueError, KeyError):
        pass

    # 5) disco y memoria
    try:
        uso = shutil.disk_usage("/")
        pct = round(uso.used * 100 / uso.total)
        if pct >= 90:
            mal.append("Disco casi lleno: %d %% ❌" % pct)
        info.append("Disco: %d %%" % pct)
    except OSError:
        pass
    mem = sh("free -m | awk '/Mem:/{print $3\"/\"$2}'")
    if mem:
        info.append("Memoria: %s MB" % mem)

    if mal:
        texto = "⚠️ Chivato: revisa esto\n\n" + "\n".join("• " + m for m in mal)
    else:
        texto = "✅ Chivato funciona bien"
    texto += "\n\n" + "\n".join(info) + "\n\n" + time.strftime("Revisión del %d/%m a las %H:%M")
    return texto


def enviar(texto):
    env = leer_env()
    tokens = [v for k, v in env.items() if "TOKEN" in k.upper() and re.fullmatch(r"\d{5,}:[\w-]{30,}", v)]
    chat = env.get("CODIGOS_ADMIN") or env.get("TG_CHAT")
    if not tokens or not chat:
        print("No encuentro el token o tu ID en .env"); print(texto); return False
    token = tokens[0]
    for t in tokens:  # preferir el bot nuevo
        r = tg(t, "getMe", {})
        if r.get("ok") and r["result"].get("username", "").lower() == "chivatoofertas_bot":
            token = t
            break
    r = tg(token, "sendMessage", {"chat_id": chat, "text": texto})
    print("Enviado" if r.get("ok") else "No se pudo enviar: %s" % r.get("description"))
    return r.get("ok")


def instalar():
    if os.path.abspath(__file__) != RUTA:
        shutil.copy(os.path.abspath(__file__), RUTA)
    open("/etc/systemd/system/chivato-salud.service", "w").write(
        "[Unit]\nDescription=Chivato - revision diaria\n\n[Service]\nType=oneshot\nExecStart=/usr/bin/python3 %s\n" % RUTA)
    open("/etc/systemd/system/chivato-salud.timer", "w").write(
        "[Unit]\nDescription=Chivato - revision diaria 8:30 Madrid\n\n[Timer]\n"
        "OnCalendar=*-*-* 08:30:00 Europe/Madrid\nPersistent=true\n\n[Install]\nWantedBy=timers.target\n")
    sh("systemctl daemon-reload && systemctl enable --now chivato-salud.timer")
    print("Programado:", sh("systemctl list-timers chivato-salud.timer --no-pager | sed -n 2p"))


if __name__ == "__main__":
    if "--instalar" in sys.argv:
        instalar()
        print("Enviando una revisión de prueba...")
    enviar(revisar())
