#!/usr/bin/env python3
# language: Python 3, file: hunt_tool.py, target: macOS
# ═══════════════════════════════════════════════════════════════════
#  HUNT TOOL — bug bounty workflow · hacker_tool
#  powered by Maxime Leal
# ═══════════════════════════════════════════════════════════════════
import os, sys, subprocess, re, json, time, random, socket, shutil, hashlib, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gt_lib
import urllib.request, urllib.parse, urllib.error

ROOT = os.path.dirname(os.path.abspath(__file__))
RAPPORTS = os.path.join(ROOT, "rapports")
os.makedirs(RAPPORTS, exist_ok=True)

C   = "\033[38;2;245;197;24m"   # or
CD  = "\033[38;2;130;100;10m"
W   = "\033[97m"
G   = "\033[38;2;74;214;109m"
R   = "\033[38;2;255;70;70m"
Y   = "\033[93m"
CY  = "\033[96m"
H   = "\033[97m"   # blanc H-option
DIM = "\033[2m"
B   = "\033[1m"
RST = "\033[0m"
CLEAR = "\033[2J\033[H"

TARGET = {"domain": ""}
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"

LOGO = r"""
          ,--.
         ( ## )   H U N T
          '--'    BOUNTY
       ,--'  '--.
      (  ######  )
       '--.  .--'
          ,--.
         ( ## )
          '--'
"""

def matrix_rain(seconds=3.2, fps=16):
    cols, rows = shutil.get_terminal_size((80, 24))
    charset = "$€£¥01BOUNTY!#%&?"
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
    type_line("        H U N T   T O O L", C, .03)
    type_line("   bug bounty workflow · hacker_tool", CD, .012)
    print()
    type_line("        ⚡ POWERED BY MAXIME LEAL ⚡", W, .02)
    time.sleep(.8)

def banner_title(txt):
    print(f"\n{B}{C}══════ {txt} ══════{RST}\n")

def http_get(url, timeout=12, as_json=False, method="GET"):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    return json.loads(data) if as_json else data.decode("utf-8", "ignore")

def save_report(name, content):
    if not TARGET["domain"]: return
    path = os.path.join(RAPPORTS, f"hunt_{TARGET['domain'].replace('.', '_')}.txt")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*50}\n[{time.strftime('%d/%m/%Y %H:%M')}] {name}\n{'='*50}\n{content}\n")
    print(f"{DIM}[+] rapport : {path}{RST}")

# fingerprints de takeover : service → signature
TAKEOVER_FP = {
    "s3.amazonaws.com": "NoSuchBucket", "herokuapp.com": "No such app",
    "github.io": "404 Not Found", "azurewebsites.net": "404 Web Site not found",
    "cloudfront.net": "ERROR: The request could not be satisfied",
    "netlify.app": "Not Found", "vercel.app": "DEPLOYMENT_NOT_FOUND",
    "wordpress.com": "Do you want to register", "zendesk.com": "Help Center Closed",
    "shopify.com": "Sorry, this shop is currently unavailable",
    "fastly.net": "Fastly error: unknown domain", "pantheon.io": "The gods are wise",
    "tumblr.com": "Whatever you were looking for doesn't currently exist",
    "ghost.io": "The thing you were looking for is no longer here",
    "surge.sh": "project not found", "bitbucket.io": "Repository not found",
}

def get_subs():
    d = TARGET["domain"]
    try:
        data = http_get(f"https://crt.sh/?q=%25.{d}&output=json", timeout=25, as_json=True)
        subs = set()
        for e in data:
            for v in (e.get("common_name", ""), e.get("name_value", "")):
                for n in v.split("\n"):
                    n = n.strip().lower()
                    if n.endswith(d) and "*" not in n: subs.add(n)
        return sorted(subs)
    except Exception:
        return []

def t_takeover():
    banner_title("SUBDOMAIN TAKEOVER — CNAMEs orphelins")
    subs = get_subs()
    if not subs: print(f"{R}aucun sous-domaine trouvé (crt.sh indisponible ?){RST}"); return
    print(f"{DIM}{len(subs)} sous-domaines à vérifier…{RST}\n")
    found = 0
    for s in subs[:40]:
        try:
            _, _, answers = socket.gethostbyname_ex(s)
            cname = answers[0] if answers else ""
        except socket.herror as e:
            # NXDOMAIN : le sous-domaine n'existe plus en DNS — orphelin potentiel
            print(f"  {R}NXDOMAIN{RST} {s}  {DIM}— pointé nulle part : VULNÉRABLE si DNS encore géré{RST}")
            found += 1; continue
        except Exception:
            continue
        if not cname: continue
        for svc, sig in TAKEOVER_FP.items():
            if svc in cname:
                try:
                    body = http_get(f"http://{s}", timeout=8)
                    if sig.lower() in body.lower():
                        print(f"  {B}{R}🎯 TAKEOVER POSSIBLE{RST} {s} → {cname} ({svc})")
                        found += 1
                    else:
                        print(f"  {G}service lié, contenu normal{RST} {s} → {cname}")
                except Exception:
                    print(f"  {Y}service lié, non joignable{RST} {s} → {cname}")
                break
    print(f"\n{B}{found} takeover(s) potentiel(s) — à confirmer manuellement{RST}")
    save_report("TAKEOVER", f"{found} potentiels sur {len(subs)}")

def t_secrets():
    banner_title("SECRETS EXPOSÉS DANS LES JS")
    base = f"https://{TARGET['domain']}"
    try:
        home = http_get(base, timeout=12)
    except Exception as e:
        print(f"{R}[!] {e}{RST}"); return
    js_urls = set(re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', home))
    js_urls = {u if u.startswith("http") else urllib.parse.urljoin(base, u) for u in js_urls}
    print(f"{DIM}{len(js_urls)} fichier(s) JS trouvés sur la page d'accueil{RST}\n")
    PATTERNS = {
        "AWS Access Key": r"AKIA[0-9A-Z]{16}",
        "Google API Key": r"AIza[0-9A-Za-z\-_]{35}",
        "Stripe sk_live": r"sk_live_[0-9a-zA-Z]{10,}",
        "Slack token": r"xox[bap]-[0-9a-zA-Z\-]{10,}",
        "GitHub token": r"ghp_[0-9A-Za-z]{36}",
        "Firebase": r"AIza[0-9A-Za-z\-_]{20,}\.firebaseio",
        "Private key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
        "JWT": r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.",
        "Cloudinary/other API key": r"api[_-]?key[\"'\s:=]+[A-Za-z0-9\-_]{16,}",
    }
    hits = []
    checked = 0
    for u in list(js_urls)[:15]:
        try:
            js = http_get(u, timeout=10)
            checked += 1
            for name, pat in PATTERNS.items():
                for m in re.finditer(pat, js):
                    snippet = m.group(0)[:60]
                    print(f"  {B}{R}🔑 {name}{RST}\n     {CY}{snippet}{RST}\n     {DIM}{u[:90]}{RST}")
                    hits.append(f"{name}: {snippet} @ {u}")
        except Exception:
            continue
    # aussi dans le HTML inline
    for name, pat in PATTERNS.items():
        for m in re.finditer(pat, home):
            print(f"  {B}{R}🔑 {name}{RST} {DIM}(html inline){RST} {CY}{m.group(0)[:60]}{RST}")
            hits.append(f"{name} (inline): {m.group(0)[:60]}")
    if not hits: print(f"{G}aucun secret exposé sur les fichiers analysés{RST}")
    print(f"{DIM}({checked} JS analysés sur {len(js_urls)}){RST}")
    if hits: save_report("SECRETS", "\n".join(hits))

def t_cors():
    banner_title("CORS MAL CONFIGURÉ")
    base = f"https://{TARGET['domain']}"
    for origin in ("https://evil.example.com", "null"):
        try:
            req = urllib.request.Request(base, headers={"User-Agent": UA, "Origin": origin})
            with urllib.request.urlopen(req, timeout=10) as r:
                acao = r.headers.get("Access-Control-Allow-Origin", "")
                acac = r.headers.get("Access-Control-Allow-Credentials", "")
            if acao:
                leak = acao == origin or acao == "*"
                col = R if leak and acac == "true" else Y if leak else G
                print(f"  {col}Origin testé : {origin}{RST}")
                print(f"    ACAO : {acao}  ·  credentials : {acac or 'non'}")
                if leak and acac == "true":
                    print(f"  {B}{R}🎯 CORS PERMISSIF AVEC CREDENTIALS — toute origine peut lire les données{RST}")
        except Exception as e:
            print(f"  {DIM}{e.__class__.__name__} sur {origin}{RST}")

def t_params():
    banner_title("PARAMÈTRES CACHÉS & FORMULAIRES")
    base = f"https://{TARGET['domain']}"
    try:
        home = http_get(base, timeout=12)
    except Exception as e:
        print(f"{R}[!] {e}{RST}"); return
    forms = re.findall(r"<form[^>]*>.*?</form>", home, re.S | re.I)
    print(f"{B}{len(forms)} formulaire(s) :{RST}")
    for i, f in enumerate(forms[:6]):
        action = re.search(r'action=["\']?([^"\'>\s]*)', f, re.I) or ("", "")
        inputs = re.findall(r'<input[^>]*name=["\']?([\w\[\]-]+)', f, re.I)
        method = re.search(r'method=["\']?(\w+)', f, re.I)
        print(f"  {CY}#{i+1} {method.group(1).upper() if method else 'GET'} {action[1] or '/'}{RST}")
        for inp in inputs: print(f"     {G}param → {RST}{inp}")
    params = sorted({m.group(1) for m in re.finditer(r'[?&](\w+)=', home)})
    if params:
        print(f"\n{B}params dans les liens :{RST} {', '.join(params[:20])}")
    save_report("PARAMS", f"{len(forms)} formulaires, params: {params[:20]}")

def t_wayback():
    banner_title("WAYBACK MACHINE — historique d'URLs")
    d = TARGET["domain"]
    try:
        data = http_get(f"http://web.archive.org/cdx/search/cdx?url=*.{d}/*&output=json&collapse=urlkey&limit=200",
                        timeout=30, as_json=True)
        if len(data) < 2: print(f"{Y}aucune URL archivée{RST}"); return
        urls = sorted({row[2] for row in data[1:]})
        interesting = [u for u in urls if re.search(r"(admin|backup|old|test|dev|config|api|\.sql|\.bak|\.zip|\.tar|login|panel)", u, re.I)]
        print(f"{B}{len(urls)} URLs archivées — {len(interesting)} intéressantes :{RST}\n")
        for u in interesting[:30]: print(f"  {G}▸ {RST}{u}")
        save_report("WAYBACK", "\n".join(interesting) or "rien d'intéressant")
    except Exception as e:
        print(f"{R}[!] {e}{RST}")

def t_scope():
    banner_title("AIDE-MÉMOIRE BOUNTY — avant de tirer")
    print(f"""{W}Règles d'or du bug bounty :{RST}
  {G}1.{RST} Lis le scope EXACT du programme (in-scope domains) — hors scope = interdiction
  {G}2.{RST} Lis les exclusions : certains tools de ce dossier sont interdits par certains programmes
     (automatisation agressive, scanning massif, tests social engineering…)
  {G}3.{RST} Pas de doS, pas de spam, pas de data mining lourd
  {G}4.{RST} Documente chaque étape (les rapports de ce dossier servent au rapport final)
  {G}5.{RST} Rapporte via la plateforme (HackerOne, Bugcrowd, Intigriti) — jamais en public
  {G}6.{RST} Les tools RECON/HUNT ci-dessus : à la vitesse 1 req/s max sur les cibles tierces

{W}Plateformes :{RST} hackerone.com · bugcrowd.com · intigriti.com · yeswehack.com
{W}Programmes :{RST} google.com/about/appsecurity · apple security bounty · microsoft msrc""")


def t_dirbrute():
    banner_title("DIRECTORY BRUTE FORCE — SecLists (GitHub)")
    base = f"https://{TARGET['domain']}"
    try: wl = gt_lib.lines("dirs-common.txt")
    except Exception as e: print(f"{R}[!] {e}{RST}"); return
    print(f"{DIM}{len(wl)} chemins, 40 threads…{RST}\n")
    def chk(p):
        try:
            req = urllib.request.Request(base + "/" + p, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=5) as r:
                return (p, r.status, len(r.read())) if r.status < 400 else None
        except urllib.error.HTTPError as e:
            return (p, e.code, 0) if e.code < 400 else None
        except Exception: return None
    with ThreadPoolExecutor(40) as ex:
        hits = [x for x in ex.map(chk, wl) if x]
    print(f"{B}{len(hits)} chemin(s) :{RST}")
    for p, c, sz in sorted(hits): print(f"  {G}{c}{RST} /{p}  {DIM}{sz:,} o{RST}")
    save_report("DIR BRUTE", "\n".join(f"{c} /{p}" for p, c, _ in sorted(hits)))

def t_redirect():
    banner_title("OPEN REDIRECT — params de redirection courants")
    base = f"https://{TARGET['domain']}"
    evil = "https://exemple-redirect-test.com"
    params = ["next", "url", "redirect", "redirect_to", "return", "returnTo", "return_url",
              "goto", "target", "dest", "destination", "continue", "link", "r", "u"]
    for p in params:
        try:
            req = urllib.request.Request(f"{base}/?{p}={urllib.parse.quote(evil)}", headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=8) as r:
                loc = r.url
            if evil in loc:
                print(f"  {B}{R}🎯 OPEN REDIRECT via '{p}' → {loc[:80]}{RST}")
        except Exception: continue
    print(f"{DIM}testé {len(params)} params — un redirect non bloqué apparaît ici{RST}")

def t_resolve():
    banner_title("SOUS-DOMAINES → IP → HÉBERGEUR")
    subs = get_subs()[:30]
    if not subs: print(f"{R}pas de sous-domaines{RST}"); return
    seen_ips = {}
    for s in subs[:25]:
        try:
            ip = socket.gethostbyname(s)
            seen_ips.setdefault(ip, []).append(s)
        except Exception: continue
    print(f"{B}{len(seen_ips)} IP(s) distinctes :{RST}")
    for ip, ss in seen_ips.items():
        try:
            j = http_get(f"http://ip-api.com/json/{ip}?fields=org,isp,as", as_json=True)
            org = f"{j.get('org') or j.get('isp') or '?'}"
        except Exception: org = "?"
        print(f"  {G}{ip:<16}{RST} {CY}{org[:40]}{RST}")
        for s in ss[:4]: print(f"      {DIM}▸ {s}{RST}")
    save_report("RESOLVE", "\n".join(f"{ip}: {', '.join(ss)}" for ip, ss in seen_ips.items()))

def t_archive_deep():
    banner_title("WAYBACK PROFOND — sous-domaines inclus")
    d = TARGET["domain"]
    try:
        data = http_get(f"http://web.archive.org/cdx/search/cdx?url=*.{d}/*&output=json&collapse=urlkey&limit=400",
                        timeout=40, as_json=True)
        urls = sorted({row[2] for row in data[1:]})
        print(f"{B}{len(urls)} URLs archivées{RST}\n")
        for u in urls[:50]: print(f"  {DIM}▸ {RST}{u}")
        save_report("WAYBACK DEEP", "\n".join(urls[:100]))
    except Exception as e:
        print(f"{R}[!] {e}{RST}")

def t_dorks():
    banner_title("GOOGLE DORKS POUR LA CIBLE")
    d = TARGET["domain"]
    dorks = [
        ("Documents exposés", f"site:{d} filetype:(pdf|doc|xls|csv|txt)"),
        ("Bases SQL", f"site:{d} ext:sql"),
        ("Backups", f"site:{d} (bak|old|backup|~)"),
        ("Confi files", f"site:{d} (env|config|ini|conf)"),
        ("Logins", f"site:{d} (login|signin|panel|admin)"),
        ("Pages d'erreur", f"site:{d} (warning|error|fatal)"),
        ("Emails", f'site:{d} intext:"@{d}"'),
        ("Répertoires ouverts", f'intitle:"index of" site:{d}'),
        ("Cloud keys", f'site:{d} "api_key"'),
        ("Wayback admin", f"site:web.archive.org {d} admin"),
    ]
    for name, q in dorks:
        url = "https://www.google.com/search?q=" + urllib.parse.quote(q)
        print(f"  {G}▸ {name:<24}{RST} {CY}{url}{RST}")
    save_report("DORKS", "\n".join(f"{n}: {u}" for n, u in dorks))

def t_headers_subs():
    banner_title("HEADERS DE SÉCURITÉ PAR SOUS-DOMAINE")
    subs = get_subs()[:12]
    sec = ["Strict-Transport-Security", "Content-Security-Policy", "X-Frame-Options", "X-Content-Type-Options"]
    for s in subs:
        try:
            req = urllib.request.Request(f"https://{s}", headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=6) as r:
                have = [h for h in sec if r.headers.get(h)]
                missing = [h for h in sec if h not in have]
            col = G if len(missing) <= 1 else R if len(missing) >= 3 else Y
            print(f"  {col}{s:<40}{RST} {G}{'✅'*len(have)}{R}{'❌'*len(missing)}{RST}")
        except Exception:
            print(f"  {DIM}{s:<40} injoignable{RST}")

def t_stack_subs():
    banner_title("STACK TECH PAR SOUS-DOMAINE")
    subs = get_subs()[:12]
    for s in subs:
        try:
            req = urllib.request.Request(f"https://{s}", headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=6) as r:
                h = dict(r.headers); body = r.read(5000).decode("utf-8", "ignore")
            stack = []
            if "server" in h: stack.append(h["server"][:30])
            if "x-powered-by" in h: stack.append(h["x-powered-by"][:30])
            for pat, name in ((r"wp-content", "WP"), (r"shopify", "Shopify"), (r"__next", "Next.js"),
                              (r"react", "React"), (r"vue", "Vue"), (r"laravel", "Laravel")):
                if re.search(pat, body, re.I): stack.append(name)
            print(f"  {C}{s:<40}{RST} {DIM}{', '.join(stack) or '—'}{RST}")
        except Exception:
            print(f"  {DIM}{s:<40} injoignable{RST}")

def t_meta():
    banner_title("MÉTADONNÉES DU SITE")
    base = f"https://{TARGET['domain']}"
    try:
        home = http_get(base, timeout=12)
    except Exception as e:
        print(f"{R}[!] {e}{RST}"); return
    for pat, label in ((r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)', "Description"),
                       (r'<meta[^>]*name=["\']keywords["\'][^>]*content=["\']([^"\']*)', "Keywords"),
                       (r'<meta[^>]*property=["\']og:site_name["\'][^>]*content=["\']([^"\']*)', "Site name"),
                       (r'<meta[^>]*name=["\']generator["\'][^>]*content=["\']([^"\']*)', "Generator"),
                       (r'<title>([^<]*)</title>', "Titre")):
        m = re.search(pat, home, re.I)
        if m and m.group(1): print(f"  {G}{label:<14}{RST} {W}{m.group(1)[:120]}{RST}")
    emails = sorted(set(re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]{2,12}", home)))
    phones = sorted(set(re.findall(r"(?:\+33|0)[1-9](?:[\s.-]?\d{2}){4}", home)))
    if emails: print(f"\n  {B}emails :{RST} {', '.join(emails[:8])}")
    if phones: print(f"  {B}téléphones :{RST} {', '.join(phones[:6])}")
    save_report("META", f"emails: {emails} · phones: {phones}")

def t_crawl():
    banner_title("MINI-CRAWLER (1 niveau depuis l'accueil)")
    base = f"https://{TARGET['domain']}"
    try:
        home = http_get(base, timeout=12)
    except Exception as e:
        print(f"{R}[!] {e}{RST}"); return
    links = sorted({urllib.parse.urljoin(base, l) for l in re.findall(r'href=["\']([^"\']+)', home)
                    if urllib.parse.urljoin(base, l).startswith(base)})
    print(f"{B}{len(links)} liens internes :{RST}")
    forms_total = 0
    for u in links[:15]:
        try:
            page = http_get(u, timeout=8)
            n_forms = len(re.findall(r"<form", page, re.I))
            n_logins = len(re.findall(r"type=[\"']?password", page, re.I))
            marker = f" {R}← FORMULAIRE{RST}" if n_forms else ""
            marker += f" {R}← LOGIN{RST}" if n_logins else ""
            print(f"  {DIM}▸ {RST}{u[:90]}{marker}")
            forms_total += n_forms
        except Exception: continue
    print(f"\n{DIM}{forms_total} formulaires au total{RST}")
    save_report("CRAWL", "\n".join(links[:40]))

def t_honeypot():
    banner_title("DÉTECTION DE HONEYPOT (heuristique)")
    ip = TARGET.get("domain")
    try: ip = socket.gethostbyname(TARGET["domain"]) if TARGET["domain"] else ""
    except Exception: ip = ""
    if not ip: print(f"{Y}[!] domaine requis{RST}"); return
    score = 0
    open_ports = 0
    def chk(p):
        try:
            with socket.create_connection((ip, p), timeout=1): return 1
        except Exception: return 0
    all_ports = [21,22,23,25,53,80,110,135,139,143,443,445,993,1433,3306,3389,5432,5900,6379,8080,8443,9200,27017,6443,11211]
    with ThreadPoolExecutor(25) as ex:
        open_ports = sum(ex.map(chk, all_ports))
    print(f"  ports ouverts sur 25 testés : {open_ports}")
    if open_ports > 15: score += 3; print(f"  {R}→ BEAUCOUP trop de ports ouverts (signature honeypot){RST}")
    for p in all_ports[:5]:
        try:
            with socket.create_connection((ip, p), timeout=1.5) as s:
                s.settimeout(1.5)
                if p == 80: s.send(b"GET /\r\n\r\n")
                b = s.recv(100)
        except Exception: continue
    print(f"  {DIM}score honeypot : {score}/3{' — probable honeypot' if score >= 2 else ' — probablement légitime'}{RST}")

def t_report():
    banner_title("RÉSUMÉ DES RAPPORTS HUNT")
    path = os.path.join(RAPPORTS, f"hunt_{TARGET['domain'].replace('.', '_')}.txt") if TARGET["domain"] else None
    print(CY + open(path).read()[-2500:] if path and os.path.exists(path) else f"{Y}aucun rapport{RST}")

def t_html():
    if not TARGET["domain"]: print(f"{Y}[!] cible requise{RST}"); return
    src = os.path.join(RAPPORTS, f"hunt_{TARGET['domain'].replace('.', '_')}.txt")
    out = gt_lib.html_report(src, f"HUNT — {TARGET['domain']}", src.replace(".txt", ".html"), accent="#f5c518")
    print(f"{G}✓ rapport HTML : {out}{RST}" if out else f"{Y}aucun rapport{RST}")


def t_xss_marker():
    banner_title("XSS RÉFLÉCHI (marqueur bénin — jamais de script réel)")
    base = f"https://{TARGET['domain']}"
    marker = "dcmarker123"
    params = ["q", "search", "s", "query", "keyword", "name", "id", "page"]
    for p in params:
        try:
            req = urllib.request.Request(f"{base}/?{p}={marker}", headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=8) as r:
                body = r.read().decode("utf-8", "ignore")
            if marker in body:
                print(f"  {Y}param '{p}' reflète la valeur — {R}testable manuellement dans le scope du programme{RST}")
        except Exception: continue
    print(f"{DIM}marqueur bénin uniquement — le PoC réel se fait manuellement{RST}")

def t_csp_audit():
    banner_title("AUDIT CSP DÉTAILLÉ")
    base = f"https://{TARGET['domain']}"
    try:
        req = urllib.request.Request(base, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=10) as r:
            csp = r.headers.get("Content-Security-Policy", "")
    except Exception as e:
        print(f"{R}[!] {e}{RST}"); return
    if not csp: print(f"{R}❌ aucune CSP{RST}"); return
    print(f"{W}{csp[:400]}{RST}\n")
    for directive, risk in (("unsafe-inline", "inline autorisé → XSS possible"),
                            ("unsafe-eval", "eval autorisé"),
                            ("*", "wildcard total")):
        if directive in csp:
            print(f"  {R}⚠️ '{directive}' présent — {risk}{RST}")
    for d_ in ("default-src", "script-src", "object-src", "base-uri", "frame-ancestors"):
        if d_ not in csp: print(f"  {Y}directive '{d_}' absente{RST}")

def t_sourcemaps():
    banner_title("SOURCE MAPS EXPOSÉES (artefacts de dev)")
    base = f"https://{TARGET['domain']}"
    try:
        home = http_get(base, timeout=12)
    except Exception as e:
        print(f"{R}[!] {e}{RST}"); return
    js_urls = set(re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', home))
    js_urls = {u if u.startswith("http") else urllib.parse.urljoin(base, u) for u in js_urls}
    n = 0
    for u in list(js_urls)[:12]:
        try:
            js = http_get(u, timeout=8)
            m = re.search(r'sourceMappingURL=([^\s]+\.map)', js)
            if m:
                map_url = urllib.parse.urljoin(u, m.group(1))
                try:
                    http_get(map_url, timeout=8)
                    print(f"  {B}{R}🗺️ SOURCE MAP EXPOSÉE{RST}\n     {CY}{map_url[:100]}{RST}")
                    n += 1
                except Exception: pass
        except Exception: continue
    if not n: print(f"{G}aucune source map exposée{RST}")


TOOLS = [
    ("1", "SUBDOMAIN TAKEOVER", t_takeover, "CNAMEs orphelins sur les 15 services connus"),
    ("2", "SECRETS DANS LES JS", t_secrets, "clés API oubliées : AWS, Google, Stripe, JWT…"),
    ("3", "CORS MAL CONFIGURÉ", t_cors, "origines permissives avec credentials"),
    ("4", "PARAMÈTRES & FORMS", t_params, "formulaires et params cachés du site"),
    ("5", "WAYBACK HISTORIQUE", t_wayback, "URLs archivées : backups, admin, api…"),
    ("6", "MÉMO BOUNTY", t_scope, "règles d'or et plateformes"),
    ("a", "DIRECTORY BRUTE", t_dirbrute, "wordlist SecLists (GitHub)"),
    ("b", "OPEN REDIRECT", t_redirect, "15 params de redirection testés"),
    ("c", "SOUS-DOMAINES → IP", t_resolve, "infra et hébergeurs des subs"),
    ("d", "WAYBACK PROFOND", t_archive_deep, "400 URLs archivées du domaine"),
    ("e", "GOOGLE DORKS", t_dorks, "10 dorks prêts pour la cible"),
    ("f", "HEADERS PAR SUB", t_headers_subs, "audit de sécurité par sous-domaine"),
    ("g", "STACK PAR SUB", t_stack_subs, "technos de chaque sous-domaine"),
    ("h", "MÉTADONNÉES", t_meta, "desc, keywords, emails, téléphones"),
    ("i", "MINI-CRAWLER", t_crawl, "1 niveau de liens + formulaires"),
    ("j", "DÉTECTEUR HONEYPOT", t_honeypot, "heuristique : 25 ports testés"),
    ("k", "RÉSUMÉ RAPPORTS", t_report, "relit tous tes scans hunt"),
    ("l", "XSS MARQUEUR", t_xss_marker, "params qui reflètent (marqueur bénin)"),
    ("m", "AUDIT CSP", t_csp_audit, "directives manquantes / unsafe"),
    ("n", "SOURCE MAPS", t_sourcemaps, "artefacts de dev exposés"),
]

def menu():
    print(CLEAR)
    for line in LOGO.splitlines():
        print(CD + line)
    print()
    print(gt_lib.bigtext("HUNT", C))
    print(f"{DIM}       powered by Maxime Leal · bug bounty workflow{RST}\n")
    if TARGET["domain"]:
        print(f"  {B}CIBLE :{RST} {W}{TARGET['domain']}{RST}\n")
    else:
        print(f"  {Y}Aucune cible — entre 'c'{RST}\n")
    for n, name, _, desc in TOOLS:
        print(f"  {B}{C}{n}{RST}  {W}{name:<26}{RST} {DIM}{desc}{RST}")
    print(f"  {B}{C}c{RST}  {'CHANGER / DÉFINIR LA CIBLE':<26}{RST}")
    print(f"  {B}{H}{RST}  {'RAPPORT HTML → .html':<26}{RST}")
    print(f"  {B}{C}q{RST}  {'QUITTER':<26}{RST}")
    print()

def main():
    splash()
    while True:
        try:
            menu()
            c = input(f"{B}{C}hunt>{RST} ").strip().lower()
            if c == "q": break
            elif c == "c":
                t = input(f"\n{B}{C}DOMAINE EN SCOPE{RST} > ").strip()
                TARGET["domain"] = t
            else:
                tool = next((t for t in TOOLS if t[0] == c), None)
                if tool:
                    if not TARGET["domain"]:
                        print(f"{Y}[!] définis d'abord une cible{RST}")
                        t = input(f"{B}{C}DOMAINE EN SCOPE{RST} > ").strip()
                        if not t: continue
                        TARGET["domain"] = t
                    tool[2]()
                elif c: print(f"{Y}choix inconnu{RST}")
            input(f"{DIM}↩︎ Entrée pour continuer…{RST}")
        except KeyboardInterrupt:
            print()
    print(f"{C}Au revoir — rapports dans rapports/{RST}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
