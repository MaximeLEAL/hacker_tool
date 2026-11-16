#!/usr/bin/env python3
# language: Python 3, file: recon_tool.py, target: macOS
# ═══════════════════════════════════════════════════════════════════
#  RECON TOOL — boîte à outils de reconnaissance · hacker_tool
#  powered by Maxime Leal
# ═══════════════════════════════════════════════════════════════════
#  Usage : python3 recon_tool.py
#  ⚠️  N'utilise que sur des cibles que tu es autorisé à tester.
import os, sys, subprocess, re, json, time, random, socket, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gt_lib
import urllib.request, urllib.parse, urllib.error
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.abspath(__file__))
RAPPORTS = os.path.join(ROOT, "rapports")
os.makedirs(RAPPORTS, exist_ok=True)

G   = "\033[38;2;0;255;70m"    # vert hacker
GD  = "\033[38;2;0;150;40m"    # vert sombre
W   = "\033[97m"
R   = "\033[38;2;255;70;70m"
CY  = "\033[96m"
Y   = "\033[93m"
H   = "\033[97m"   # blanc H-option
DIM = "\033[2m"
B   = "\033[1m"
RST = "\033[0m"
CLEAR = "\033[2J\033[H"

TARGET = {"domain": "", "ip": ""}
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

# ─────────────────────────── ANIMATION ───────────────────────────
MASK = r"""
        .-"      "-.
       /            \
      ;   POWERED    ;
      |   BY MAXIME  |
      |,  .-.  .-.  ,|
      | )(_o/  \o_)( |
      |/  LEAL  /\   \|
      (_     ^^     _)
       \__|IIIIII|__/
        | \IIIIII/ |
        \          /
         `--------`
"""

def matrix_rain(seconds=3.2, fps=16):
    cols, rows = shutil.get_terminal_size((80, 24))
    charset = "アイウエオカキクケコサシスセソタチツテトナニヌネノ01$#%&@!?+*"
    drops = [random.randint(-rows, 0) for _ in range(cols)]
    frames = int(seconds * fps)
    for _ in range(frames):
        screen = [[" "] * cols for _ in range(rows)]
        for x in range(cols):
            y = drops[x]
            for dy in range(random.randint(4, 13)):
                yy = y - dy
                if 0 <= yy < rows:
                    screen[yy][x] = random.choice(charset)
            drops[x] = y + 1 if y < rows + 12 else random.randint(-12, 0)
        frame = "\033[H" + "\n".join("".join(r) for r in screen)
        sys.stdout.write(G + frame); sys.stdout.flush()
        time.sleep(1 / fps)
    sys.stdout.write(RST)

def type_line(text, color=W, delay=.014):
    for c in text:
        sys.stdout.write(color + c); sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write(RST + "\n")

def splash():
    sys.stdout.write(CLEAR)
    matrix_rain(3.4)
    sys.stdout.write(CLEAR)
    for line in MASK.splitlines():
        print(G + line); time.sleep(.05)
    time.sleep(.4)
    type_line("        R E C O N   T O O L", G, .03)
    type_line("   boîte à outils de reconnaissance · hacker_tool", GD, .012)
    print()
    type_line("        ⚡ POWERED BY MAXIME LEAL ⚡", W, .02)
    time.sleep(.8)

# ─────────────────────────── HELPERS ───────────────────────────
def banner_title(txt):
    print(f"\n{B}{G}══════ {txt} ══════{RST}")
    print(f"{DIM}cible : {W}{TARGET['domain'] or TARGET['ip']}{RST}\n")

def http_get(url, timeout=10, as_json=False):
    return gt_lib.http_get(url, timeout=timeout, as_json=as_json)

def save_report(name, content):
    if not TARGET["domain"] and not TARGET["ip"]: return
    t = TARGET["domain"] or TARGET["ip"]
    path = os.path.join(RAPPORTS, f"{t.replace('.', '_')}.txt")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*50}\n[{time.strftime('%d/%m/%Y %H:%M')}] {name}\n{'='*50}\n{content}\n")
    print(f"{DIM}[+] rapport : {path}{RST}")

def ask_target():
    t = input(f"\n{B}{G}CIBLE {RST}(domaine ou IP) {G}> {RST}").strip()
    if not t:
        return False
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", t):
        TARGET["ip"], TARGET["domain"] = t, ""
    else:
        TARGET["domain"], TARGET["ip"] = t, ""
        try:
            TARGET["ip"] = socket.gethostbyname(t)
            print(f"{DIM}[+] résolu : {t} → {TARGET['ip']}{RST}")
        except Exception:
            print(f"{Y}[!] le domaine ne résout pas (whois/dns peuvent quand même fonctionner){RST}")
    return True

# ─────────────────────────── LES TOOLS ───────────────────────────
def t_whois():
    banner_title("WHOIS COMPLET")
    d = TARGET["domain"] or TARGET["ip"]
    out = subprocess.run(["whois", d], capture_output=True, text=True).stdout
    out = "\n".join(l for l in out.splitlines() if not l.startswith("%"))[:4000]
    print(CY + out)
    save_report("WHOIS", out)

def t_dns():
    banner_title("ENUMÉRATION DNS")
    if not TARGET["domain"]:
        print(f"{Y}[!] un domaine est requis (pas une IP seule){RST}"); return
    d = TARGET["domain"]
    all_out = ""
    for t in ("A", "AAAA", "MX", "NS", "TXT", "SOA", "CNAME"):
        r = subprocess.run(["dig", "+short", d, t], capture_output=True, text=True).stdout.strip()
        if r:
            print(f"{G}{t:<7}{RST} {r.replace(chr(10), f'{DIM} | {RST}')}")
            all_out += f"{t}: {r}\n"
        else:
            print(f"{DIM}{t:<7} —{RST}")
    save_report("DNS", all_out)

def t_subdomains():
    banner_title("SOUS-DOMAINES (Certificate Transparency · crt.sh)")
    d = TARGET["domain"]
    if not d: print(f"{Y}[!] domaine requis{RST}"); return
    try:
        data = http_get(f"https://crt.sh/?q=%25.{d}&output=json", timeout=25, as_json=True)
        subs = set()
        for e in data:
            for v in (e.get("common_name", ""), e.get("name_value", "")):
                for n in v.split("\n"):
                    n = n.strip().lower()
                    if n.endswith(d) and "*" not in n: subs.add(n)
        subs = sorted(subs)
        print(f"{B}{W}{len(subs)} sous-domaines trouvés :{RST}\n")
        for s in subs: print(f"  {G}▸ {RST}{s}")
        save_report("SOUS-DOMAINES", "\n".join(subs))
    except Exception as e:
        print(f"{R}[!] crt.sh indisponible : {e}{RST}")

def t_geoloc():
    banner_title("GÉOLOCALISATION IP")
    ip = TARGET["ip"]
    if not ip: print(f"{Y}[!] aucune IP (le domaine ne résout pas ?){RST}"); return
    try:
        d = http_get(f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,zip,lat,lon,timezone,isp,org,as,reverse", as_json=True)
        print(f"{W}IP      : {ip}{RST}")
        for k, label in (("country","Pays"),("regionName","Région"),("city","Ville"),("zip","Code postal"),
                         ("isp","FAI"),("org","Organisation"),("as","AS"),("reverse","Reverse DNS"),
                         ("timezone","Fuseau"),("lat","Latitude"),("lon","Longitude")):
            print(f"{G}{label:<12}{RST} {d.get(k, '—')}")
        print(f"{DIM}Carte : https://www.openstreetmap.org/?mlat={d.get('lat')}&mlon={d.get('lon')}#map=11{RST}")
        save_report("GEOLOC", json.dumps(d, indent=1, ensure_ascii=False))
    except Exception as e:
        print(f"{R}[!] {e}{RST}")

def t_headers():
    banner_title("HEADERS HTTP + AUDIT SÉCURITÉ")
    url = f"https://{TARGET['domain']}" if TARGET["domain"] else f"http://{TARGET['ip']}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=12) as r:
            status, headers = r.status, dict(r.headers)
    except Exception as e:
        print(f"{R}[!] {e}{RST}"); return
    print(f"{B}Status : {status} — {url}{RST}\n")
    for k, v in headers.items(): print(f"{G}{k:<22}{RST} {v[:100]}")
    print(f"\n{B}{Y}AUDIT DES HEADERS DE SÉCURITÉ :{RST}")
    sec = {"Strict-Transport-Security": "HTTPS forcé (HSTS)",
           "Content-Security-Policy": "protection XSS/injection",
           "X-Frame-Options": "anti-clickjacking",
           "X-Content-Type-Options": "anti-MIME-sniffing",
           "Referrer-Policy": "fuite de référent",
           "Permissions-Policy": "accès APIs navigateur"}
    for h, why in sec.items():
        print(f"  {'✅' if h in headers else '❌'} {G}{h:<30}{RST} {DIM}{why}{RST}")
    save_report("HEADERS", "\n".join(f"{k}: {v}" for k, v in headers.items()))

def t_fingerprint():
    banner_title("TECHNOLOGIES & FINGERPRINTING")
    base = f"https://{TARGET['domain']}" if TARGET["domain"] else f"http://{TARGET['ip']}"
    try:
        home = http_get(base, timeout=12)
    except Exception as e:
        print(f"{R}[!] {e}{RST}"); return
    techs = []
    gen = re.search(r'<meta name="generator" content="([^"]+)"', home, re.I)
    if gen: techs.append("Generator : " + gen.group(1))
    for pat, name in ((r"wp-content", "WordPress"), (r"Joomla", "Joomla"), (r"drupal", "Drupal"),
                      (r"shopify", "Shopify"), (r"react", "React"), (r"vue\.js|vuejs", "Vue.js"),
                      (r"next\.js|__next", "Next.js"), (r"cloudflare", "Cloudflare"),
                      (r"cdn-cgi", "Cloudflare CDN"), (r"google-analytics|gtag", "Google Analytics")):
        if re.search(pat, home, re.I): techs.append(name)
    print(f"{B}DÉTECTIONS :{RST}")
    for t in techs or ["(aucune signature classique)"]:
        print(f"  {G}▸ {RST}{t}")
    print(f"\n{B}SONDAGE DE CHEMINS COURANTS :{RST}")
    paths = ["/robots.txt", "/sitemap.xml", "/wp-login.php", "/wp-admin/", "/administrator/",
             "/admin", "/.git/HEAD", "/.env", "/phpinfo.php", "/login", "/api", "/.well-known/security.txt"]
    for p in paths:
        try:
            req = urllib.request.Request(base + p, headers={"User-Agent": UA}, method="HEAD")
            with urllib.request.urlopen(req, timeout=6) as r:
                code = r.status
        except urllib.error.HTTPError as e:
            code = e.code
        except Exception:
            continue
        if code < 400:
            color = G if code == 200 else Y
            print(f"  {color}{code}{RST} {p}")
            if p == "/robots.txt":
                try:
                    print(DIM + http_get(base + "/robots.txt", timeout=6)[:400].replace("\n", "\n   ") + RST)
                except Exception: pass
    save_report("FINGERPRINT", "\n".join(techs))

def t_ports():
    banner_title("SCAN DE PORTS (top 30)")
    ip = TARGET["ip"]
    if not ip: print(f"{Y}[!] aucune IP{RST}"); return
    ports = {21:"FTP",22:"SSH",23:"Telnet",25:"SMTP",53:"DNS",80:"HTTP",110:"POP3",143:"IMAP",
             443:"HTTPS",445:"SMB",465:"SMTPS",587:"SMTP-TLS",993:"IMAPS",1433:"MSSQL",
             3306:"MySQL",3389:"RDP",5432:"PostgreSQL",5900:"VNC",6379:"Redis",8080:"HTTP-alt",
             8443:"HTTPS-alt",8888:"HTTP-alt2",9200:"Elasticsearch",27017:"MongoDB",6443:"K8s",
             11211:"Memcached",161:"SNMP",1883:"MQTT"}
    def chk(args):
        p, s = args
        try:
            with socket.create_connection((ip, p), timeout=1.2): return (p, s)
        except Exception: return None
    with ThreadPoolExecutor(60) as ex:
        open_ports = [x for x in ex.map(chk, ports.items()) if x]
    print(f"{B}{len(open_ports)} port(s) ouvert(s) sur {len(ports)} testés :{RST}\n")
    for p, s in sorted(open_ports):
        print(f"  {B}{G}{p:<6}{RST} {CY}{s:<14}{RST}")
    save_report("PORTS", "\n".join(f"{p} {s}" for p, s in sorted(open_ports)))

def t_pingsweep():
    banner_title("PING SWEEP — appareils sur le réseau local")
    me = subprocess.run(["ipconfig", "getifaddr", "en0"], capture_output=True, text=True).stdout.strip() \
      or subprocess.run(["ipconfig", "getifaddr", "en1"], capture_output=True, text=True).stdout.strip()
    if not me: print(f"{R}[!] pas d'IP locale{RST}"); return
    base = ".".join(me.split(".")[:3])
    def ping(i):
        ip = f"{base}.{i}"
        return ip if subprocess.run(["ping", "-c", "1", "-W", "1", ip], capture_output=True).returncode == 0 else None
    with ThreadPoolExecutor(64) as ex:
        alive = [x for x in ex.map(ping, range(1, 255)) if x]
    print(f"{B}{len(alive)} appareil(s) vivant(s) sur {base}.0/24 :{RST}\n")
    for ip in alive: print(f"  {G}▸ {RST}{ip}" + (f"  {DIM}(toi){RST}" if ip == me else ""))
    save_report("PING SWEEP", "\n".join(alive))

def t_robots():
    banner_title("ROBOTS.TXT & SITEMAP")
    base = f"https://{TARGET['domain']}" if TARGET["domain"] else f"http://{TARGET['ip']}"
    try:
        rb = http_get(base + "/robots.txt", timeout=8)
        print(f"{G}── robots.txt ──{RST}\n{rb[:1200]}")
        save_report("ROBOTS.TXT", rb[:2000])
    except Exception:
        print(f"{Y}[!] pas de robots.txt accessible{RST}")
    try:
        sm = http_get(base + "/sitemap.xml", timeout=8)
        urls = re.findall(r"<loc>([^<]+)</loc>", sm)
        print(f"\n{G}── sitemap.xml ── {len(urls)} URLs{RST}")
        for u in urls[:20]: print(f"  {DIM}▸ {RST}{u}")
        if urls: save_report("SITEMAP", "\n".join(urls))
    except Exception:
        print(f"{DIM}pas de sitemap.xml accessible{RST}")

def t_emails():
    banner_title("EMAILS & RÉSEAUX SOCIAUX (page d'accueil)")
    base = f"https://{TARGET['domain']}" if TARGET["domain"] else f"http://{TARGET['ip']}"
    try:
        home = http_get(base, timeout=12)
    except Exception as e:
        print(f"{R}[!] {e}{RST}"); return
    emails = sorted(set(re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]{2,12}", home)))
    socials = sorted(set(re.findall(r'https?://(?:www\.)?(?:twitter\.com|x\.com|linkedin\.com|facebook\.com|instagram\.com|github\.com|youtube\.com|t\.me)/[\w/.-]+', home)))
    print(f"{B}{len(emails)} email(s) public(s) :{RST}")
    for e in emails: print(f"  {G}✉ {RST}{e}")
    print(f"\n{B}{len(socials)} réseau(x) social(aux) :{RST}")
    for s in socials: print(f"  {G}▸ {RST}{s}")
    if emails or socials: save_report("EMAILS/SOCIAUX", "\n".join(emails + socials))


# ─────────────────────── BOOST GITHUB — les 12 nouveaux ───────────────────────
def t_dnsbrute():
    banner_title("DNS BRUTE FORCE — wordlist SecLists 5000 (GitHub)")
    d = TARGET["domain"]
    if not d: print(f"{Y}[!] domaine requis{RST}"); return
    try:
        wl = gt_lib.lines("subdomains.txt")
    except Exception as e:
        print(f"{R}[!] {e}{RST}"); return
    print(f"{DIM}{len(wl)} candidats, 60 threads…{RST}")
    def chk(sub):
        try:
            ip = socket.gethostbyname(f"{sub}.{d}")
            return (sub, ip)
        except Exception: return None
    with ThreadPoolExecutor(60) as ex:
        found = [x for x in ex.map(chk, wl[:5000]) if x]
    print(f"\n{B}{len(found)} sous-domaine(s) RÉSOLU(S) :{RST}")
    for sub, ip in sorted(found): print(f"  {G}▸ {RST}{sub}.{d}  {DIM}{ip}{RST}")
    save_report("DNS BRUTE", "\n".join(f"{s}.{d} {i}" for s, i in sorted(found)))

def t_dirbrute():
    banner_title("DIRECTORY BRUTE FORCE — wordlist SecLists (GitHub)")
    base = f"https://{TARGET['domain']}" if TARGET["domain"] else f"http://{TARGET['ip']}"
    try:
        wl = gt_lib.lines("dirs-common.txt")
    except Exception as e:
        print(f"{R}[!] {e}{RST}"); return
    print(f"{DIM}{len(wl)} chemins testés, 40 threads…{RST}\n")
    def chk(p):
        try:
            req = urllib.request.Request(base + "/" + p, headers={"User-Agent": UA}, method="GET")
            with urllib.request.urlopen(req, timeout=5) as r:
                return (p, r.status, len(r.read())) if r.status < 400 else None
        except urllib.error.HTTPError as e:
            return (p, e.code, 0) if e.code < 400 else None
        except Exception: return None
    with ThreadPoolExecutor(40) as ex:
        hits = [x for x in ex.map(chk, wl) if x]
    print(f"{B}{len(hits)} chemin(s) trouvés :{RST}")
    for p, code, sz in sorted(hits):
        print(f"  {G}{code}{RST} /{p}  {DIM}{sz:,} o{RST}")
    save_report("DIR BRUTE", "\n".join(f"{c} /{p}" for p, c, s in sorted(hits)))

def t_tls():
    banner_title("CERTIFICAT TLS & PROTOCOLES")
    d = TARGET["domain"] or TARGET["ip"]
    try:
        out = subprocess.run(["openssl", "s_client", "-connect", f"{d}:443", "-brief"],
                             capture_output=True, text=True, input="", timeout=15)
        proto = re.search(r"Protocol version: (\S+)", out.stderr + out.stdout)
        cipher = re.search(r"Cipher\s*:\s*(\S+)", out.stderr + out.stdout)
        print(f"  {G}protocole{RST} {proto.group(1) if proto else '?'}  {G}cipher{RST} {cipher.group(1) if cipher else '?'}")
        full = subprocess.run(["openssl", "s_client", "-connect", f"{d}:443"],
                              capture_output=True, text=True, input="", timeout=15).stdout
        for tag in ("subject=", "issuer="):
            m = re.search(tag + r"([^\n]+)", full)
            if m: print(f"  {G}{tag[:-1]}{RST} {m.group(1)[:100]}")
        dates = re.findall(r"notBefore=(\S+ \S+ \d+ \d+:\d+:\d+ \S+)|notAfter=(\S+ \S+ \d+ \d+:\d+:\d+ \S+)", full)
        for a, b in dates[:1]:
            print(f"  {G}valide du{RST} {a or b[:24]}")
            print(f"  {G}valide au{RST} {b or a[:24]}")
        sans = re.findall(r"DNS:([\w.*.-]+)", full)
        if sans:
            print(f"  {G}SAN{RST} {', '.join(sans[:12])}")
        for v in ("tls1", "tls1_1", "tls1_2", "tls1_3"):
            r_ = subprocess.run(["openssl", "s_client", f"-{v}", "-connect", f"{d}:443", "-brief"],
                                capture_output=True, text=True, input="", timeout=10)
            ok = "CONNECTION ESTABLISHED" in (r_.stderr + r_.stdout)
            print(f"  {'✅' if ok else '❌'} {v}")
    except Exception as e:
        print(f"{R}[!] {e.__class__.__name__}{RST}")

def t_methods():
    banner_title("MÉTHODES HTTP AUTORISÉES")
    url = f"https://{TARGET['domain']}" if TARGET["domain"] else f"http://{TARGET['ip']}"
    try:
        req = urllib.request.Request(url, method="OPTIONS", headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=10) as r:
            allow = r.headers.get("Allow", "") or r.headers.get("Public", "")
    except urllib.error.HTTPError as e:
        allow = e.headers.get("Allow", "") if e.headers else ""
    except Exception as e:
        print(f"{R}[!] {e}{RST}"); return
    if allow:
        print(f"  {G}Allow{RST} {allow}")
        danger = [m for m in ("PUT", "DELETE", "TRACE", "CONNECT") if m in allow.upper()]
        if danger: print(f"  {R}⚠️ méthodes dangereuses exposées : {', '.join(danger)}{RST}")
    else:
        print(f"  {DIM}pas de header Allow (serveur verrouillé ou OPTIONS refusé){RST}")
    for m in ("TRACE", "PUT"):
        try:
            req = urllib.request.Request(url, method=m, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=8) as r:
                print(f"  {R}{m} accepté ({r.status}) — risqué{RST}")
        except urllib.error.HTTPError as e:
            print(f"  {G}{m} refusé ({e.code}){RST}")
        except Exception: pass

def t_cookies():
    banner_title("AUDIT DES COOKIES")
    url = f"https://{TARGET['domain']}" if TARGET["domain"] else f"http://{TARGET['ip']}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=12) as r:
            cookies = r.headers.get_all("Set-Cookie") or []
    except Exception as e:
        print(f"{R}[!] {e}{RST}"); return
    if not cookies: print(f"{Y}aucun cookie{RST}"); return
    for c in cookies:
        name = c.split("=")[0]
        flags = []
        if "httponly" in c.lower(): flags.append("HttpOnly ✅")
        else: flags.append("HttpOnly ❌")
        if "secure" in c.lower(): flags.append("Secure ✅")
        else: flags.append("Secure ❌")
        if "samesite" in c.lower(): flags.append("SameSite ✅")
        else: flags.append("SameSite ❌")
        print(f"  {B}{CY}{name:<20}{RST} {' · '.join(flags)}")

def t_wp():
    banner_title("ENUMÉRATION WORDPRESS")
    base = f"https://{TARGET['domain']}"
    try:
        users = http_get(base + "/wp-json/wp/v2/users", timeout=10, as_json=True)
        print(f"{B}{G}wp-json users ouverts :{RST}")
        for u in users if isinstance(users, list) else []:
            print(f"  ▸ id {u.get('id')} · {u.get('name')} · slug {u.get('slug')}")
    except Exception:
        print(f"{DIM}wp-json users fermé ou pas WordPress{RST}")
    for p, what in (("/xmlrpc.php", "xmlrpc (bruteforce possible)"),
                    ("/wp-login.php", "page de login"),
                    ("/wp-content/", "répertoire wp-content")):
        try:
            req = urllib.request.Request(base + p, headers={"User-Agent": UA}, method="GET")
            with urllib.request.urlopen(req, timeout=8) as r:
                if r.status == 200: print(f"  {G}✔ {what}{RST} {DIM}{r.status}{RST}")
        except urllib.error.HTTPError as e:
            print(f"  {DIM}✘ {what} ({e.code}){RST}")
        except Exception: pass

def t_apidocs():
    banner_title("DÉCOUVERTE DE LA DOCUMENTATION API")
    base = f"https://{TARGET['domain']}" if TARGET["domain"] else f"http://{TARGET['ip']}"
    paths = ["/openapi.json", "/swagger.json", "/api-docs", "/swagger/", "/swagger/ui",
             "/api/swagger.json", "/v1/openapi.json", "/graphql", "/graphiql", "/.well-known/openapi"]
    for p in paths:
        try:
            req = urllib.request.Request(base + p, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=6) as r:
                if r.status == 200:
                    body = r.read()[:200]
                    print(f"  {B}{G}✔ {p}{RST}  {DIM}{body[:100]}{RST}")
        except Exception: pass
    try:
        gq = http_get(base + "/graphql", timeout=8)
        print(f"  {B}{G}✔ /graphql répond{RST}  {DIM}{gq[:100]}{RST}")
    except Exception: pass

def t_js():
    banner_title("ENDPOINTS DANS LES FICHIERS JS")
    base = f"https://{TARGET['domain']}" if TARGET["domain"] else f"http://{TARGET['ip']}"
    try:
        home = http_get(base, timeout=12)
    except Exception as e:
        print(f"{R}[!] {e}{RST}"); return
    js_urls = set(re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', home))
    js_urls = {u if u.startswith("http") else urllib.parse.urljoin(base, u) for u in js_urls}
    endpoints = set()
    for u in list(js_urls)[:10]:
        try:
            js = http_get(u, timeout=8)
            endpoints.update(re.findall(r'["\']/(api/[\w/.-]+|v[12]/[\w/.-]+)', js))
        except Exception: continue
    eps = sorted(endpoints)
    print(f"{B}{len(eps)} endpoint(s) d'API trouvés dans {len(js_urls)} JS :{RST}")
    for e in eps[:40]: print(f"  {G}▸ {RST}/{e}")
    if eps: save_report("ENDPOINTS", "\n".join(eps))

def t_htmlcomments():
    banner_title("COMMENTAIRES HTML & CHAMPS CACHÉS")
    base = f"https://{TARGET['domain']}" if TARGET["domain"] else f"http://{TARGET['ip']}"
    try:
        home = http_get(base, timeout=12)
    except Exception as e:
        print(f"{R}[!] {e}{RST}"); return
    comments = re.findall(r"<!--(.*?)-->", home, re.S)
    comments = [c.strip() for c in comments if len(c.strip()) > 4][:15]
    hidden = re.findall(r'<input[^>]*type=["\']hidden["\'][^>]*name=["\']?([\w-]+)[^>]*value=["\']?([^"\'>]*)', home, re.I)
    print(f"{B}{len(comments)} commentaire(s) :{RST}")
    for c in comments: print(f"  {Y}<!-- {c[:120]} -->{RST}")
    print(f"\n{B}{len(hidden)} champ(s) caché(s) :{RST}")
    for n, v in hidden[:12]: print(f"  {G}{n}{RST} = {DIM}{v[:60]}{RST}")
    if comments or hidden: save_report("HTML", "\n".join(comments + [f"{n}={v}" for n, v in hidden]))

def t_emailsec():
    banner_title("SÉCURITÉ EMAIL — SPF · DKIM · DMARC (détail)")
    d = TARGET["domain"]
    if not d: print(f"{Y}[!] domaine requis{RST}"); return
    spf = subprocess.run(["dig", "+short", "TXT", d], capture_output=True, text=True).stdout
    for line in spf.splitlines():
        if "v=spf1" in line: print(f"  {G}SPF{RST}  {line}")
    dmarc = subprocess.run(["dig", "+short", "TXT", f"_dmarc.{d}"], capture_output=True, text=True).stdout.strip()
    if dmarc: print(f"  {G}DMARC{RST} {dmarc}")
    else: print(f"  {R}DMARC absent{RST}")
    sel = input(f"{DIM}sélecteur DKIM (défaut: default, google){RST} > ").strip() or "default"
    for s_ in [sel, "google", "default", "s1", "k1"]:
        r_ = subprocess.run(["dig", "+short", "TXT", f"{s_}._domainkey.{d}"], capture_output=True, text=True).stdout.strip()
        if r_:
            print(f"  {G}DKIM ({s_}){RST} {r_[:100]}")
            break
    else:
        print(f"  {Y}DKIM : aucun sélecteur trouvé{RST}")

def t_axfr():
    banner_title("ZONE TRANSFER (AXFR) & DNSSEC")
    d = TARGET["domain"]
    if not d: print(f"{Y}[!] domaine requis{RST}"); return
    ns = subprocess.run(["dig", "+short", "NS", d], capture_output=True, text=True).stdout.split()
    print(f"{DIM}{len(ns)} serveurs NS à tester…{RST}")
    for n in ns[:5]:
        r_ = subprocess.run(["dig", "AXFR", d, "@" + n], capture_output=True, text=True, timeout=12).stdout
        records = [l for l in r_.splitlines() if not l.startswith(";") and l.strip() and "failed" not in l.lower()]
        if len(records) > 2:
            print(f"  {B}{R}🎯 AXFR RÉUSSI sur {n} — {len(records)} records exposés !{RST}")
            for l in records[:10]: print(f"    {Y}{l}{RST}")
        else:
            print(f"  {G}✘ {n} refusé (bonne configuration){RST}")
    dnssec = subprocess.run(["dig", "+short", "DNSKEY", d], capture_output=True, text=True).stdout.strip()
    print(f"\n  {'✅' if dnssec else '❌'} DNSSEC {'activé' if dnssec else 'absent'}")

def t_rdns():
    banner_title("REVERSE DNS & NEIGHBORS")
    ip = TARGET["ip"]
    if not ip: print(f"{Y}[!] IP requise{RST}"); return
    rd = subprocess.run(["dig", "+short", "-x", ip], capture_output=True, text=True).stdout.strip()
    print(f"  {G}{ip}{RST} → {rd or '(pas de reverse)'}")
    whois_ = subprocess.run(["whois", ip], capture_output=True, text=True).stdout
    for line in whois_.splitlines():
        if re.search(r"(netname|orgname|org-name|country)", line, re.I):
            print(f"  {DIM}{line.strip()[:90]}{RST}")

def t_range():
    banner_title("SCAN DE PORTS PERSONNALISÉ")
    ip = TARGET["ip"]
    if not ip: print(f"{Y}[!] IP requise{RST}"); return
    rng = input(f"{DIM}plage (ex: 1-1000 ou 22,80,443,8080){RST} > ").strip() or "1-1000"
    ports = []
    for part in rng.split(","):
        if "-" in part:
            a, b = part.split("-"); ports.extend(range(int(a), int(b) + 1))
        elif part.isdigit(): ports.append(int(part))
    print(f"{DIM}{len(ports)} ports, 100 threads…{RST}")
    def chk(p):
        try:
            with socket.create_connection((ip, p), timeout=1): return p
        except Exception: return None
    with ThreadPoolExecutor(100) as ex:
        open_ = sorted(p for p in ex.map(chk, ports) if p)
    print(f"\n{B}{len(open_)} port(s) ouvert(s) :{RST}")
    for p in open_: print(f"  {G}{p}{RST}")
    save_report("PORTS CUSTOM", ", ".join(map(str, open_)))

TOOLS = [
    ("1", "WHOIS COMPLET", t_whois, "registre, registrar, dates, serveurs"),
    ("2", "ENUMÉRATION DNS", t_dns, "A · MX · NS · TXT · SOA · CNAME"),
    ("3", "SOUS-DOMAINES", t_subdomains, "certificats publics (crt.sh)"),
    ("4", "GÉOLOCALISATION IP", t_geoloc, "pays, ville, FAI, AS, carte"),
    ("5", "HEADERS + SÉCURITÉ", t_headers, "headers complets + audit des 6 security headers"),
    ("6", "FINGERPRINTING", t_fingerprint, "technos, CMS, chemins exposés"),
    ("7", "SCAN DE PORTS", t_ports, "les 30 ports les plus utilisés"),
    ("8", "PING SWEEP LAN", t_pingsweep, "appareils vivants sur ton réseau"),
    ("9", "ROBOTS & SITEMAP", t_robots, "ce que le site déclare aux crawlers"),
    ("0", "EMAILS & SOCIAUX", t_emails, "emails publics + réseaux sociaux liés"),
    ("a", "DNS BRUTE FORCE", t_dnsbrute, "wordlist SecLists 5000 subdomains (GitHub)"),
    ("b", "DIRECTORY BRUTE", t_dirbrute, "wordlist common.txt (GitHub)"),
    ("c", "TLS & CERTIFICAT", t_tls, "cipher, SAN, dates, protocoles activés"),
    ("d", "MÉTHODES HTTP", t_methods, "OPTIONS + PUT/TRACE dangereux"),
    ("e", "AUDIT COOKIES", t_cookies, "Secure, HttpOnly, SameSite"),
    ("f", "WORDPRESS ENUM", t_wp, "users, xmlrpc, plugins"),
    ("g", "DOCS API", t_apidocs, "swagger, openapi, graphql exposés"),
    ("h", "ENDPOINTS JS", t_js, "les /api/ cachés dans les fichiers JS"),
    ("i", "HTML COMMENTS", t_htmlcomments, "commentaires + champs cachés"),
    ("j", "EMAIL SECURITY", t_emailsec, "SPF, DKIM, DMARC en détail"),
    ("k", "ZONE TRANSFER", t_axfr, "AXFR sur les NS + DNSSEC"),
    ("l", "REVERSE DNS", t_rdns, "PTR + netblock"),
    ("m", "PORTS CUSTOM", t_range, "ta propre plage de ports"),
]

def menu():
    print(CLEAR)
    for line in MASK.splitlines():
        print(GD + line)
    print()
    print(f"{B}{G}  ╔═══════════════════════════════════════════════╗{RST}")
    print(f"{B}{G}  ║   R E C O N   T O O L  —  hacker_tool         ║{RST}")
    print(f"{B}{G}  ╚═══════════════════════════════════════════════╝{RST}")
    print(f"{DIM}       powered by Maxime Leal · usage : cibles autorisées uniquement{RST}\n")
    if TARGET["domain"] or TARGET["ip"]:
        print(f"  {B}CIBLE :{RST} {W}{TARGET['domain'] or TARGET['ip']}{RST} {DIM}(IP {TARGET['ip']}){RST}\n")
    else:
        print(f"  {Y}Aucune cible — entre 'c' pour définir la cible{RST}\n")
    for n, name, _, desc in TOOLS:
        print(f"  {B}{G}{n}{RST}  {W}{name:<24}{RST} {DIM}{desc}{RST}")
    print(f"  {B}{G}c{RST}  {'CHANGER / DÉFINIR LA CIBLE':<24}{RST}")
    print(f"  {B}{G}r{RST}  {'VOIR LE RAPPORT':<24}{RST}")
    print(f"  {B}{H}{RST}  {'RAPPORT HTML → .html':<24}{RST}")
    print(f"  {B}{G}q{RST}  {'QUITTER':<24}{RST}")
    print()

def show_report():
    t = TARGET["domain"] or TARGET["ip"]
    path = os.path.join(RAPPORTS, f"{t.replace('.', '_')}.txt") if t else None
    if path and os.path.exists(path):
        print(CY + open(path).read()[-3000:])
    else:
        print(f"{Y}aucun rapport pour cette cible{RST}")


def t_html():
    t = TARGET['domain'] or TARGET['ip']
    if not t: print(f'{Y}[!] cible requise{RST}'); return
    src = os.path.join(RAPPORTS, f"{t.replace('.', '_')}.txt")
    out = gt_lib.html_report(src, "RECON — {t}", src.replace(".txt", ".html"), accent="#00ff46")
    print(f"{G}✓ rapport HTML : {out}{RST}" if out else f"{Y}aucun rapport à convertir{RST}")

def main():
    splash()
    while True:
        try:
            menu()
            c = input(f"{B}{G}recon>{RST} ").strip().lower()
            if c == "q": break
            elif c == "c": ask_target()
            elif c == "r": show_report()
            else:
                tool = next((t for t in TOOLS if t[0] == c), None)
                if tool:
                    if not (TARGET["domain"] or TARGET["ip"]):
                        print(f"{Y}[!] définis d'abord une cible{RST}")
                        if not ask_target(): continue
                    tool[2]()
                elif c:
                    print(f"{Y}choix inconnu : {c}{RST}")
            input(f"{DIM}↩︎ Entrée pour continuer…{RST}")
        except KeyboardInterrupt:
            print()
    print(f"{G}Au revoir — les rapports sont dans rapports/{RST}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
