#!/usr/bin/env python3
# language: Python 3, file: hunt_tool.py, target: macOS
# ═══════════════════════════════════════════════════════════════════
#  HUNT TOOL — bug bounty workflow · hacker_tool
#  powered by Maxime Leal
# ═══════════════════════════════════════════════════════════════════
import os, sys, subprocess, re, json, time, random, socket, shutil, hashlib
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

TOOLS = [
    ("1", "SUBDOMAIN TAKEOVER", t_takeover, "CNAMEs orphelins sur les 15 services connus"),
    ("2", "SECRETS DANS LES JS", t_secrets, "clés API oubliées : AWS, Google, Stripe, JWT…"),
    ("3", "CORS MAL CONFIGURÉ", t_cors, "origines permissives avec credentials"),
    ("4", "PARAMÈTRES & FORMS", t_params, "formulaires et params cachés du site"),
    ("5", "WAYBACK HISTORIQUE", t_wayback, "URLs archivées : backups, admin, api…"),
    ("6", "MÉMO BOUNTY", t_scope, "règles d'or et plateformes"),
]

def menu():
    print(CLEAR)
    for line in LOGO.splitlines():
        print(CD + line)
    print()
    print(f"{B}{C}  ╔═══════════════════════════════════════════════╗{RST}")
    print(f"{B}{C}  ║   H U N T   T O O L  —  hacker_tool           ║{RST}")
    print(f"{B}{C}  ╚═══════════════════════════════════════════════╝{RST}")
    print(f"{DIM}       powered by Maxime Leal · bug bounty workflow{RST}\n")
    if TARGET["domain"]:
        print(f"  {B}CIBLE :{RST} {W}{TARGET['domain']}{RST}\n")
    else:
        print(f"  {Y}Aucune cible — entre 'c'{RST}\n")
    for n, name, _, desc in TOOLS:
        print(f"  {B}{C}{n}{RST}  {W}{name:<26}{RST} {DIM}{desc}{RST}")
    print(f"  {B}{C}c{RST}  {'CHANGER / DÉFINIR LA CIBLE':<26}{RST}")
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
