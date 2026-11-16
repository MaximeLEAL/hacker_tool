#!/usr/bin/env python3
# language: Python 3, file: dark_tool.py, target: macOS
# ═══════════════════════════════════════════════════════════════════
#  DARK TOOL — opérations Tor & services onion officiels · hacker_tool
#  powered by Maxime Leal
# ═══════════════════════════════════════════════════════════════════
import os, sys, subprocess, re, json, time, random, shutil, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gt_lib

ROOT = os.path.dirname(os.path.abspath(__file__))
RAPPORTS = os.path.join(ROOT, "rapports")
os.makedirs(RAPPORTS, exist_ok=True)

C   = "\033[38;2;125;70;152m"   # violet Tor officiel
CD  = "\033[38;2;70;40;95m"
W   = "\033[97m"
G   = "\033[38;2;74;214;109m"
R   = "\033[38;2;255;70;70m"
Y   = "\033[93m"
CY  = "\033[96m"
DIM = "\033[2m"
B   = "\033[1m"
RST = "\033[0m"
CLEAR = "\033[2J\033[H"

SOCKS = "socks5h://127.0.0.1:9050"

LOGO = r"""
     ____________________
    |  ________________  |
    | | D A R K  T O O L |
    | |_________________ |
    |__ TOR OPERATIONS __|
"""

def matrix_rain(seconds=3.2, fps=16):
    cols, rows = shutil.get_terminal_size((80, 24))
    charset = ".onionTORBROWSERrelayexitnode01#$%"
    drops = [random.randint(-rows, 0) for _ in range(cols)]
    for _ in range(int(seconds * fps)):
        screen = [[" "] * cols for _ in range(rows)]
        for x in range(cols):
            y = drops[x]
            for dy in range(random.randint(4, 13)):
                yy = y - dy
                if 0 <= yy < rows: screen[yy][x] = random.choice(charset)
            drops[x] = y + 1 if y < rows + 12 else random.randint(-12, 0)
        sys.stdout.write(C + "\033[H" + "\n".join("".join(r) for r in screen)); sys.stdout.flush()
        time.sleep(1 / fps)
    sys.stdout.write(RST)

def type_line(text, color=W, delay=.014):
    for c in text:
        sys.stdout.write(color + c); sys.stdout.flush(); time.sleep(delay)
    sys.stdout.write(RST + "\n")

def splash():
    sys.stdout.write(CLEAR)
    matrix_rain(3.2)
    sys.stdout.write(CLEAR)
    for line in LOGO.splitlines():
        print(C + line); time.sleep(.05)
    time.sleep(.4)
    type_line("        D A R K   T O O L", C, .03)
    type_line("   opérations Tor & services onion officiels · hacker_tool", CD, .012)
    print()
    type_line("        ⚡ POWERED BY MAXIME LEAL ⚡", W, .02)
    time.sleep(.8)

def banner_title(txt):
    print(f"\n{B}{C}══════ {txt} ══════{RST}\n")

def save_report(name, content):
    path = os.path.join(RAPPORTS, "dark_tool.txt")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*50}\n[{time.strftime('%d/%m/%Y %H:%M')}] {name}\n{'='*50}\n{content}\n")
    print(f"{DIM}[+] rapport : {path}{RST}")

def tor_running():
    try:
        with socket.create_connection(("127.0.0.1", 9050), timeout=2):
            return True
    except Exception:
        return False

def tor_fetch(url, timeout=45):
    """récupère une URL via le circuit Tor (socks5h)"""
    out = subprocess.run(["curl", "-s", "-L", "--socks5-hostname", "127.0.0.1:9050",
                          "-A", "Mozilla/5.0", "--max-time", str(timeout), url],
                         capture_output=True, text=True)
    return out.stdout

# ─────────────────────────── LES TOOLS ───────────────────────────
def t_status():
    banner_title("STATUT TOR")
    import socket
    running = False
    try:
        with socket.create_connection(("127.0.0.1", 9050), timeout=2):
            running = True
    except Exception:
        pass
    if running:
        print(f"  {G}✅ Tor tourne{RST} — SOCKS proxy sur 127.0.0.1:9050")
        try:
            ip = tor_fetch("https://api.ipify.org")
            print(f"  {G}IP de sortie{RST} : {ip[:80]}")
        except Exception:
            print(f"  {DIM}IP de sortie : non vérifiable pour l'instant{RST}")
    else:
        print(f"  {R}✘ Tor ne tourne pas{RST}")
        if shutil.which("tor"):
            print(f"  {DIM}→ option 2 pour le démarrer{RST}")
        else:
            print(f"  {DIM}→ option 2 pour l'installer{RST}")
    vers = subprocess.run(["tor", "--version"], capture_output=True, text=True).stdout.strip() if shutil.which("tor") else ""
    if vers: print(f"  {G}version{RST} : {vers[:60]}")

def t_install():
    banner_title("INSTALLER / DÉMARRER TOR")
    if not shutil.which("tor"):
        print(f"{DIM}brew install tor…{RST}")
        out = subprocess.run(["brew", "install", "tor"], capture_output=True, text=True)
        if "Error" in out.stderr: print(f"{R}{out.stderr[:300]}{RST}")
    print(f"{DIM}démarrage du service…{RST}")
    subprocess.run(["brew", "services", "start", "tor"], capture_output=True, text=True)
    print(f"{DIM}attente du bootstrap (10 s)…{RST}")
    time.sleep(10)
    t_status()

def t_exitip():
    banner_title("IP DE SORTIE VIA TOR")
    if not tor_running(): print(f"{R}✘ Tor ne tourne pas — option 2{RST}"); return
    try:
        ip = tor_fetch("https://api.ipify.org")
        print(f"  {G}IP de sortie Tor{RST} : {W}{ip[:80]}{RST}")
        me = subprocess.run(["curl", "-s", "--max-time", "8", "https://api.ipify.org"], capture_output=True, text=True).stdout
        print(f"  {G}IP réelle{RST}        : {me[:80]}")
        print(f"  {DIM}→ différentes = anonymisation fonctionnelle{RST}")
        j = tor_fetch(f"http://ip-api.com/json/{ip}?fields=country,city,isp")
        if j and j.strip().startswith("{"):
            d = json.loads(j)
            print(f"  {G}localisation{RST} : {d.get('country')} · {d.get('city')} · {d.get('isp')}")
        save_report("EXIT IP", f"tor: {ip} · réel: {me}")
    except Exception as e:
        print(f"{R}[!] {e}{RST}")

def t_fetch():
    banner_title("FETCH VIA TOR (pages .onion et clearnet)")
    if not tor_running(): print(f"{R}✘ Tor ne tourne pas — option 2{RST}"); return
    url = input(f"{B}{C}URL à récupérer (.onion ou https){RST} > ").strip()
    if not url: return
    print(f"{DIM}récupération via le circuit Tor…{RST}")
    try:
        body = tor_fetch(url, timeout=60)
        if not body.strip():
            print(f"{R}réponse vide — l'adresse est peut-être morte ou lente{RST}"); return
        # strip tags léger pour lisibilité
        text = re.sub(r"<script.*?</script>|<style.*?</style>", "", body, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        print(f"\n{B}── contenu ({len(body):,} octets bruts) ──{RST}\n")
        print(f"{W}{text[:2500]}{RST}")
        save_report("FETCH", f"{url}\n{text[:1500]}")
    except Exception as e:
        print(f"{R}[!] {e}{RST}")

def t_securedrop():
    banner_title("SECUREDROP — systèmes de signalement des rédactions (officiel)")
    print(f"{DIM}annuaire officiel des journaux acceptant des leaks anonymes et chiffrés{RST}\n")
    try:
        import gt_lib
        data = json.loads(gt_lib.ressource("securedrop.json"))
        orgs = data if isinstance(data, list) else data.get("organizations", data)
        n = 0
        for org in (orgs if isinstance(orgs, list) else orgs.values()):
            name = org.get("title") or org.get("organization_name", "")
            onion = org.get("onion_address") or org.get("onion_url", "")
            if name and onion:
                print(f"  {G}▸ {name[:44]:<44}{RST} {CY}http://{onion}{RST}")
                n += 1
                if n >= 25: break
        print(f"\n{DIM}total affiché : {n} · source : dépôt officiel securedrop (freedomofpress){RST}")
        save_report("SECUREDROP", f"{n} rédactions listées")
    except Exception as e:
        print(f"{R}[!] {e}{RST}")

MIRRORS = [
    ("DuckDuckGo (moteur, no-log)", "duckduckgogg42xjoc72x3sjasiuoexinmd3jaa7y5jotslot6jb2n7mmad.onion"),
    ("BBC News (int'l)", "bbcnewsv2vjtpsuy.onion"),
    ("New York Times", "nytimes3xbfgragh.onion"),
    ("Facebook", "facebookcorewwwi.onion"),
    ("ProtonMail (mail chiffré)", "protonmailrmez3lotccwxhtgzpan36dkm4qkr4tcpknftc2ycpjzcq.onion"),
    ("Tor Project (officiel)", "2ndugpnd37twkw4jkm4ec5sqj7juheucn2zdsgrjv7nawgn7ck7nhid.onion"),
    ("Archive/README sécurité", "torproject.org → vérifie toujours l'adresse sur le site officiel"),
]

def t_mirrors():
    banner_title("MIROIRS ONION OFFICIELS (publiés par les organisations)")
    print(f"{DIM}vérifie TOUJOURS l'adresse sur le site officiel de l'organisation{RST}\n")
    for name, onion in MIRRORS:
        print(f"  {G}▸ {name:<36}{RST} {CY}{onion[:60]}{RST}")
    save_report("MIRRORS", "\n".join(f"{n}: {o}" for n, o in MIRRORS))

def t_check():
    banner_title("CHECK .ONION — joignable ?")
    url = input(f"{B}{C}URL .onion à tester{RST} > ").strip()
    if not url: return
    if not url.startswith("http"): url = "http://" + url
    if not tor_running(): print(f"{R}✘ Tor ne tourne pas — option 2{RST}"); return
    print(f"{DIM}test via Tor…{RST}")
    try:
        body = tor_fetch(url, timeout=45)
        size = len(body)
        title = re.search(r"<title[^>]*>([^<]{0,80})", body, re.I)
        print(f"  {G}✅ JOIGNABLE{RST} — {size:,} octets")
        if title: print(f"  {G}titre{RST} : {title.group(1)}")
        save_report("CHECK", f"{url} → {size} o")
    except Exception:
        print(f"  {R}✘ INJOIGNABLE — service mort ou lourd (réessaie avec option 2, Tor doit être amorcé){RST}")

def t_opsec():
    banner_title("OPSEC — les règles du dark web légal")
    print(f"""{W}Loi d'abord :{RST}
  {G}1.{RST} Le dark web n'est PAS une zone sans loi. Les marketplaces d'armes, drogues,
     données volées sont des crimes — et les ops de police y sont actives en permanence
  {G}2.{RST} Ce tool ne liste PAS de marketplaces — uniquement des services officiels
     (presse, mail chiffré, moteurs no-log, signalement journalistique)

{W}Technique :{RST}
  {G}3.{RST} Une machine dédiée (VM) pour le dark : jamais ta machine principale
  {G}4.{RST} Ne JAMAIS te connecter à tes comptes personnels via Tor
  {G}5.{RST} Le nœud de sortie voit le trafic — HTTPS obligatoire pour tout contenu sensible
  {G}6.{RST} Vérifie les adresses .onion sur le site officiel de l'organisation (phishing .onion = classique)
  {G}7.{RST} Tor Browser pour naviguer — ce tool sert aux opérations API/scripts uniquement
  {G}8.{RST} Les cascades VPN+Tor existent mais un mauvais setup est PIRE que Tor seul

{W}Usage légitime :{RST}
  {G}9.{RST} Journalisme, recherche en sécurité, vérification de leaks te concernant,
     signalement anonyme (SecureDrop), contournement de censure dans les pays bloqués""")

def t_report():
    p = os.path.join(RAPPORTS, "dark_tool.txt")
    print(CY + open(p).read()[-2000:] if os.path.exists(p) else f"{Y}aucun rapport{RST}")

def t_html():
    import gt_lib
    out = gt_lib.html_report(os.path.join(RAPPORTS, "dark_tool.txt"), "DARK TOOL", os.path.join(RAPPORTS, "dark_tool.html"), accent="#7d4698")
    print(f"{G}✓ rapport HTML : {out}{RST}" if out else f"{Y}aucun rapport à convertir{RST}")


def t_circuit():
    banner_title("CIRCUIT TOR — le chemin actuel")
    if not tor_running(): print(f"{R}✘ Tor ne tourne pas — option 2{RST}"); return
    try:
        import socket as sk
        s = sk.create_connection(("127.0.0.1", 9051), timeout=3)
        s.send(b'AUTHENTICATE "\r\n"')
        resp = s.recv(1024)
        if b"250" not in resp:
            print(f"  {Y}port de contrôle authentifié par cookie requis{RST}")
            print(f"  {DIM}active-le : tor --controlport 127.0.0.1:9051 --cookieauth 1{RST}")
            s.close(); return
        s.send(b"GETINFO circuit-status\r\n")
        resp = s.recv(8192).decode("utf-8", "ignore")
        for line in resp.splitlines():
            if line.startswith("circuit-status=") and "BUILT" in line:
                print(f"  {G}circuit établi :{RST}")
                path = re.search(r"\\sBUILD_FLAGS=.*?PURPOSE", line)
                nodes = re.findall(r"\\$([0-9a-fA-F]{8})", line)
                for i, n in enumerate(nodes[:6]):
                    role = ["entrée", "relais", "relais", "sortie"][min(i, 3)]
                    print(f"    {C}{role:<10}{RST} {DIM}{n}…{RST}")
        s.send(b"GETINFO status/bootstrap-phase\r\n")
        resp2 = s.recv(2048).decode("utf-8", "ignore")
        prog = re.search(r"PROGRESS=(\d+)", resp2)
        if prog: print(f"  {G}bootstrap{RST} : {prog.group(1)}%")
        s.close()
    except Exception as e:
        print(f"  {R}[!] {e.__class__.__name__}{RST}")

def t_newnym():
    banner_title("NEWNYM — changer de circuit (nouvelle identité réseau)")
    if not tor_running(): print(f"{R}✘ Tor ne tourne pas{RST}"); return
    try:
        import socket as sk
        s = sk.create_connection(("127.0.0.1", 9051), timeout=3)
        s.send(b'AUTHENTICATE "\r\n"')
        resp = s.recv(1024)
        if b"250" not in resp:
            print(f"{Y}port de contrôle non ouvert — relance Tor avec :{RST}")
            print(f"  {W}tor --controlport 127.0.0.1:9051 --cookieauth 1{RST}")
            return
        s.send(b"SIGNAL NEWNYM\r\n")
        resp = s.recv(256)
        print(f"  {G}✅ signal NEWNYM envoyé{RST} — le prochain circuit sera différent")
        print(f"  {DIM}attend ~10 s que le nouveau circuit s'établisse{RST}")
        s.close()
    except Exception as e:
        print(f"  {R}[!] {e.__class__.__name__}{RST}")

def t_log():
    banner_title("LOG TOR — les 20 dernières lignes")
    paths = ["/opt/homebrew/var/log/tor/tor.log", "/usr/local/var/log/tor/tor.log",
             os.path.expanduser("~/.tor/log"), "/opt/homebrew/etc/tor/torrc"]
    found = False
    for p in paths:
        if os.path.exists(p):
            print(f"  {DIM}{p}{RST}")
            tail = open(p, errors="ignore").read().splitlines()[-20:]
            for l in tail: print(f"  {W}{l[:130]}{RST}")
            found = True
            break
    if not found:
        print(f"  {Y}log introuvable — Tor via brew log : {DIM}brew services info tor{RST}")

def t_onioncheck():
    banner_title("VALIDER UN FORMAT .ONION (v2 / v3)")
    o = input(f"{B}{C}adresse .onion{RST} > ").strip().lower().replace("http://", "").replace("https://", "").split("/")[0]
    if not o.endswith(".onion"): print(f"{R}pas un .onion{RST}"); return
    name = o[:-6]
    if len(name) == 16:
        if all(c in "abcdefghijklmnopqrstuvwxyz234567" for c in name):
            print(f"  {Y}⚠️ format v2 (16 chars) — DÉPRÉCIÉ depuis 2021, la plupart sont morts{RST}")
        else:
            print(f"  {R}v2 invalide (charset base32 attendu){RST}")
    elif len(name) == 56:
        if all(c in "abcdefghijklmnopqrstuvwxyz234567" for c in name):
            print(f"  {G}✅ format v3 valide (56 chars base32) — adresse moderne{RST}")
        else:
            print(f"  {R}v3 invalide (charset base32 attendu){RST}")
    else:
        print(f"  {R}longueur invalide ({len(name)}) — ni v2 (16) ni v3 (56){RST}")

def t_latency():
    banner_title("LATENCE TOR vs DIRECT")
    if not tor_running(): print(f"{R}✘ Tor ne tourne pas{RST}"); return
    url = "https://www.google.com"
    t0 = time.time()
    try:
        subprocess.run(["curl", "-s", "-o", "/dev/null", "--max-time", "10", url], capture_output=True)
        dt = time.time() - t0
        print(f"  {G}direct{RST} : {dt:.2f}s")
    except Exception: pass
    t0 = time.time()
    try:
        tor_fetch(url, timeout=30)
        dt = time.time() - t0
        print(f"  {C}via Tor{RST} : {dt:.2f}s  {DIM}(3 relais : l'overhead est normal){RST}")
    except Exception: pass

def t_fuite():
    banner_title("TEST DE FUITE — ton anonymat est-il complet ?")
    if not tor_running(): print(f"{R}✘ Tor ne tourne pas{RST}"); return
    print(f"{DIM}1. IP via Tor…{RST}")
    ip_tor = tor_fetch("https://api.ipify.org").strip()
    print(f"   {C}{ip_tor}{RST}")
    print(f"{DIM}2. IP directe…{RST}")
    ip_real = subprocess.run(["curl", "-s", "--max-time", "8", "https://api.ipify.org"], capture_output=True, text=True).stdout.strip()
    print(f"   {C}{ip_real}{RST}")
    if ip_tor and ip_real and ip_tor.strip() == ip_real.strip():
        print(f"\n  {R}🚨 FUITE : même IP via Tor et en direct — Tor ne route pas !{RST}")
    elif ip_tor:
        print(f"\n  {G}✅ aucune fuite : les deux IP sont différentes{RST}")
    print(f"{DIM}3. User-Agent via Tor…{RST}")
    ua = tor_fetch("https://httpbin.org/user-agent")
    print(f"   {C}{ua.strip()[:120]}{RST}")
    save_report("FUITE", f"tor={ip_tor} direct={ip_real}")

def t_batch():
    banner_title("BATCH CHECK — plusieurs .onion d'un coup")
    pth = input(f"{DIM}fichier d'URLs (une par ligne, Entrée = démo){RST} > ").strip()
    urls = []
    if pth and os.path.exists(os.path.expanduser(pth)):
        urls = [l.strip() for l in open(os.path.expanduser(pth)) if l.strip()]
    else:
        urls = [m[1] for m in MIRRORS if ".onion" in m[1]]
    if not tor_running(): print(f"{R}✘ Tor ne tourne pas{RST}"); return
    print(f"{DIM}{len(urls)} URLs à tester…{RST}\n")
    alive, dead = 0, 0
    for u in urls:
        if not u.startswith("http"): u = "http://" + u
        try:
            body = tor_fetch(u, timeout=30)
            if body.strip():
                print(f"  {G}✅{RST} {u[:60]}  {DIM}{len(body):,} o{RST}")
                alive += 1
            else:
                print(f"  {R}✘{RST} {u[:60]}")
                dead += 1
        except Exception:
            print(f"  {R}✘{RST} {u[:60]}")
            dead += 1
        time.sleep(1)
    print(f"\n{B}{alive} vivants · {dead} morts{RST}")
    save_report("BATCH", f"{alive} vivants / {dead} morts")

def t_presse():
    banner_title("PRESSE INTERNATIONALE SUR LE DARK WEB (miroirs officiels)")
    presse = MIRRORS + [
        ("The Guardian", "guardian2zotugyefl6sa7d76xqmvbtw4zj4jvpflbqvb6vomuh5jv254uad.onion"),
        ("ProPublica (investigation)", "propublicadxzv4n23an6t66ipt5chhfe3cecp5ue4pjox5us3ikwxkjad.onion"),
        ("BuzzFeed News", "buwygjnlvbejelh4kp2pumuv3bqpd7zuz4e4zlpehy7z7rlpwhbtkqid.onion"),
    ]
    print(f"{DIM}les journaux publient leurs propres miroirs .onion pour la censure{RST}\n")
    for name, onion in presse:
        print(f"  {G}▸ {name:<34}{RST} {CY}{onion[:62]}{RST}")
    save_report("PRESSE", "\n".join(f"{n}: {o}" for n, o in presse))

def t_ahmia():
    banner_title("RECHERCHE AHMIA — le moteur du dark web qui filtre les abus (officiel)")
    kw = input(f"{B}{C}recherche (ex: security forum, ctf, journalism){RST} > ").strip() or "security"
    try:
        html = http_get(f"https://ahmia.fi/search/?q={urllib.parse.quote(kw)}", timeout=20)
        results = re.findall(r'href="(http[s]?://[a-z2-7]{16,56}\.onion[^"]*)"', html)
        titles = re.findall(r'<h4[^>]*>([^<]{5,90})</h4>', html)
        desc = re.findall(r'<p class="[^"]*description[^"]*">([^<]{10,200})</p>', html)
        seen = set()
        n = 0
        for i, u in enumerate(results[:20]):
            if u in seen: continue
            seen.add(u)
            t = titles[i] if i < len(titles) else ""
            print(f"  {G}▸ {t or '(sans titre)'}{RST}\n    {CY}{u[:70]}{RST}")
            if i < len(desc): print(f"    {DIM}{desc[i][:120]}{RST}")
            n += 1
        if n == 0:
            print(f"{Y}aucun résultat — Ahmia filtre le contenu abusif{RST}")
        else:
            print(f"\n{DIM}{n} résultats · source : ahmia.fi (moteur qui exclut les contenus abusifs){RST}")
            save_report("AHMIA", f"q={kw} · {n} résultats")
    except Exception as e:
        print(f"{R}[!] {e.__class__.__name__}{RST}")

def t_bridges():
    banner_title("BRIDGES — quand Tor est bloqué par ton FAI/pays")
    print(f"""{W}Le principe :{RST}
  {DIM}un bridge est un relais d'entrée NON-public — le FAI ne voit pas que c'est Tor{RST}

{W}Étapes :{RST}
  {G}1.{RST} Demande des bridges : {CY}https://bridges.torproject.org{RST}
       (ou email à bridges@torproject.org depuis gmail/riseup)
  {G}2.{RST} Choisis le type : {W}obfs4{RST} (recommandé) ou meek-azure (réseau cloud)
  {G}3.{RST} Dans torrc, ajoute :
       {W}UseBridges 1
       ClientTransportPlugin obfs4 exec /usr/local/bin/obfs4proxy
       Bridge obfs4 <ip:port> <cert> iat-mode=1{RST}
  {G}4.{RST} Redémarre : {W}brew services restart tor{RST}
  {G}5.{RST} Vérifie : option 1 de ce menu → IP de sortie ≠ ton IP

{W}Test si Tor est bloqué :{RST}
  {DIM}option 1 — si le bootstrap reste à 0%, ton FAI bloque les relais publics{RST}""")

def t_ctf():
    banner_title("LES CHALLENGES DARK WEB DANS LES CTFs")
    print(f"""{W}Comment les CTFs utilisent le dark web :{RST}

  {G}1.{RST} {B}ONION HIDDEN SERVICE{RST} — le challenge héberge son propre .onion :
     un hidden service Tor sur un serveur du CTF, l'URL est dans l'énoncé
     {DIM}→ technique : fetch via Tor (option 4), inspecter, trouver le flag{RST}

  {G}2.{RST} {B}ONION PÉNÉTRABLE{RST} — un hidden service avec une faille web
     {DIM}→ même méthodo que WOPR mais à travers Tor{RST}

  {G}3.{RST} {B}STEAGONO ONION{RST} — le flag est caché dans une page/une image du service
     {DIM}→ Stégano Studio (BatWeb) après le fetch{RST}

  {G}4.{RST} {B}FORMAT .ONION{RST} — le challenge donne une adresse v2/v3 à valider
     {DIM}→ option 9 de ce menu{RST}

  {G}5.{RST} {B}RECHERCHE AHMIA{RST} — le flag est indexé sur une page .onion publique
     {DIM}→ option 7 de ce menu{RST}

{W}Setup CTF typique :{RST}
  {DIM}option 2 (Tor lancé) → option 4 (fetch le .onion du challenge) → analyser → flag{RST}

{DIM}⚠️ tout ça se fait sur l'infrastructure du CTF — jamais sur de vrais services{RST}""")

def t_report_dark():
    banner_title("RÉSUMÉ DES RAPPORTS DARK")
    t_report()


def t_relays():
    banner_title("STATISTIQUES TOR — le réseau mondial (Onionoo officiel)")
    try:
        data = http_get("https://onionoo.torproject.org/details?type=relay&summary", timeout=25)
        relays = data.get("relays", [])
        print(f"{B}{len(relays)} relais publics dans le monde{RST}")
        countries = {}
        for r_ in relays:
            for c in r_.get("country", "?").split(","): countries[c] = countries.get(c, 0) + 1
        print(f"{B}top 10 pays :{RST}")
        for c, n in sorted(countries.items(), key=lambda x: -x[1])[:10]:
            print(f"  {C}{c:<8}{RST} {'█' * min(n // 8, 40)} {n}")
        exit_relays = sum(1 for r_ in relays if "Exit" in r_.get("flags", []))
        guards = sum(1 for r_ in relays if "Guard" in r_.get("flags", []))
        print(f"\n  {G}relais de sortie{RST} : {exit_relays}  ·  {G}gardiens{RST} : {guards}")
        save_report("RELAYS", f"{len(relays)} relais · {exit_relays} sortie · {guards} gardiens")
    except Exception as e:
        print(f"{R}[!] {e.__class__.__name__}{RST}")

TOOLS = [
    ("1", "STATUT TOR", t_status, "proxy actif ? IP de sortie ?"),
    ("2", "INSTALLER / DÉMARRER", t_install, "brew install + service + bootstrap"),
    ("3", "IP DE SORTIE TOR", t_exitip, "compare avec ton IP réelle"),
    ("4", "FETCH VIA TOR", t_fetch, "récupère une page .onion ou https"),
    ("5", "SECUREDROP", t_securedrop, "signalement anonyme aux rédactions (officiel)"),
    ("6", "MIROIRS OFFICIELS", t_mirrors, "BBC · NYT · DDG · ProtonMail…"),
    ("7", "CHECK .ONION", t_check, "un service est-il vivant ?"),
    ("8", "OPSEC", t_opsec, "les règles légales et techniques"),
    ("9", "VALIDER .ONION", t_onioncheck, "format v2/v3 base32"),
    ("a", "CIRCUIT TOR", t_circuit, "entrée · relais · sortie en direct"),
    ("b", "NEWNYM", t_newnym, "nouveau circuit = nouvelle identité"),
    ("c", "LOG TOR", t_log, "les dernières lignes du daemon"),
    ("d", "LATENCE TOR", t_latency, "direct vs circuit comparés"),
    ("e", "TEST DE FUITE", t_fuite, "ton anonymat est-il complet ?"),
    ("f", "BATCH CHECK", t_batch, "plusieurs .onion d'un coup"),
    ("g", "PRESSE INTERNATIONALE", t_presse, "Guardian · ProPublica · BuzzFeed"),
    ("h", "RECHERCHE AHMIA", t_ahmia, "le moteur dark web qui filtre les abus"),
    ("i", "BRIDGES", t_bridges, "quand le FAI bloque Tor"),
    ("j", "DARK WEB EN CTF", t_ctf, "comment les CTFs utilisent Tor"),
    ("k", "STATISTIQUES RÉSEAU", t_relays, "relais mondiaux via Onionoo officiel"),
]

def menu():
    print(CLEAR)
    for line in LOGO.splitlines():
        print(CD + line)
    print()
    print(gt_lib.bigtext("DARK", C))
    print(f"{DIM}       powered by Maxime Leal · services officiels uniquement{RST}\n")
    for n, name, _, desc in TOOLS:
        print(f"  {B}{C}{n}{RST}  {W}{name:<26}{RST} {DIM}{desc}{RST}")
    print(f"  {B}{C}H{RST}  {'RAPPORT HTML → .html':<26}{RST}")
    print(f"  {B}{C}r{RST}  {'VOIR LE RAPPORT':<26}{RST}")
    print(f"  {B}{C}q{RST}  {'QUITTER':<26}{RST}")
    print()

def show_report():
    t_report()

def main():
    splash()
    while True:
        try:
            menu()
            c = input(f"{B}{C}dark>{RST} ").strip().lower()
            if c == "q": break
            elif c == "r": show_report()
            elif c == "H": t_html()
            else:
                tool = next((t for t in TOOLS if t[0] == c), None)
                if tool: tool[2]()
                elif c: print(f"{Y}choix inconnu{RST}")
        except KeyboardInterrupt:
            print()
    print(f"{C}Au revoir — rapports dans rapports/{RST}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
