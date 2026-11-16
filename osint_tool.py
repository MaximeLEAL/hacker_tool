#!/usr/bin/env python3
# language: Python 3, file: osint_tool.py, target: macOS
# ═══════════════════════════════════════════════════════════════════
#  OSINT DEEP — profiler une organisation / une personne · hacker_tool
#  powered by Maxime Leal
# ═══════════════════════════════════════════════════════════════════
import os, sys, subprocess, re, json, time, random, socket, shutil, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gt_lib
import urllib.request, urllib.parse, urllib.error

ROOT = os.path.dirname(os.path.abspath(__file__))
RAPPORTS = os.path.join(ROOT, "rapports")
os.makedirs(RAPPORTS, exist_ok=True)

C   = "\033[38;2;0;200;255m"   # cyan
CD  = "\033[38;2;0;110;150m"
W   = "\033[97m"
G   = "\033[38;2;74;214;109m"
R   = "\033[38;2;255;70;70m"
Y   = "\033[93m"
DIM = "\033[2m"
B   = "\033[1m"
RST = "\033[0m"
CLEAR = "\033[2J\033[H"

TARGET = {"domain": "", "username": ""}
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"

LOGO = r"""
       .-~~~~~~~-.
      /  ______  \
     |  / .--.  \ |
     | | | () | | |
     |  \ '--'  / |
      \  '------'  /
       '-.______.-'
"""

def matrix_rain(seconds=3.2, fps=16):
    cols, rows = shutil.get_terminal_size((80, 24))
    charset = "@#0123emailOSINT$%&"
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
    type_line("        O S I N T   D E E P", C, .03)
    type_line("   profiler organisations & personnes · hacker_tool", CD, .012)
    print()
    type_line("        ⚡ POWERED BY MAXIME LEAL ⚡", W, .02)
    time.sleep(.8)

def banner_title(txt):
    print(f"\n{B}{C}══════ {txt} ══════{RST}\n")

def http_get(url, timeout=12, as_json=False):
    return gt_lib.http_get(url, timeout=timeout, as_json=as_json)

def save_report(name, content):
    t = TARGET["domain"] or TARGET["username"]
    if not t: return
    path = os.path.join(RAPPORTS, f"osint_{t.replace('.', '_').replace('/', '_')}.txt")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*50}\n[{time.strftime('%d/%m/%Y %H:%M')}] {name}\n{'='*50}\n{content}\n")
    print(f"{DIM}[+] rapport : {path}{RST}")

# ─────────────────────────── LES TOOLS ───────────────────────────
PLATFORMS = {
    "GitHub": "https://github.com/{}",
    "Twitter/X": "https://x.com/{}",
    "Instagram": "https://www.instagram.com/{}/",
    "Reddit": "https://www.reddit.com/user/{}",
    "TikTok": "https://www.tiktok.com/@{}",
    "Pinterest": "https://www.pinterest.com/{}/",
    "YouTube": "https://www.youtube.com/@{}",
    "Twitch": "https://www.twitch.tv/{}",
    "Steam": "https://steamcommunity.com/id/{}",
    "GitLab": "https://gitlab.com/{}",
    "Pastebin": "https://pastebin.com/u/{}",
    "Medium": "https://medium.com/@{}",
    "Spotify": "https://open.spotify.com/user/{}",
    "SoundCloud": "https://soundcloud.com/{}",
    "Flickr": "https://www.flickr.com/people/{}",
    "Behance": "https://www.behance.net/{}",
    "Dribbble": "https://dribbble.com/{}",
    "Keybase": "https://keybase.io/{}",
    "Telegram": "https://t.me/{}",
    "HackerNews": "https://news.ycombinator.com/user?id={}",
    "VK": "https://vk.com/{}",
    "OK.ru": "https://ok.ru/{}",
    "Bluesky": "https://bsky.app/profile/{}.bsky.social",
    "About.me": "https://about.me/{}",
    "Dev.to": "https://dev.to/{}",
    "DeviantArt": "https://{}.deviantart.com",
    "Codewars": "https://www.codewars.com/users/{}",
    "Codeforces": "https://codeforces.com/profile/{}",
    "Replit": "https://replit.com/@{}",
    "Giphy": "https://giphy.com/{}",
    "Imgur": "https://imgur.com/user/{}",
    "Last.fm": "https://www.last.fm/user/{}",
    "Letterboxd": "https://letterboxd.com/{}/",
    "Mixcloud": "https://www.mixcloud.com/{}/",
    "MyAnimeList": "https://myanimelist.net/profile/{}",
    "Trakt": "https://trakt.tv/users/{}",
    "Wattpad": "https://www.wattpad.com/user/{}",
    "TripAdvisor": "https://www.tripadvisor.com/profile/{}",
    "Etsy": "https://www.etsy.com/shop/{}",
    "Fiverr": "https://www.fiverr.com/{}",
    "Bandcamp": "https://{}.bandcamp.com",
    "Scribd": "https://www.scribd.com/{}",
    "Kickstarter": "https://www.kickstarter.com/profile/{}",
    "TryHackMe": "https://tryhackme.com/p/{}",
    "Kongregate": "https://www.kongregate.com/accounts/{}",
    "Roblox": "https://www.roblox.com/users/profile?username={}",
    "Scratch": "https://scratch.mit.edu/users/{}/",
    "Chess": "https://www.chess.com/member/{}",
    "Lichess": "https://lichess.org/@/{}",
    "Speedrun": "https://www.speedrun.com/user/{}",
    "Chess24": "https://chess24.com/en/profile/{}",
    "Dating?": "https://www.dating.com/user/{}",
    "Anchor.fm": "https://anchor.fm/{}",
    "Substack": "https://{}.substack.com",
    "Calendly": "https://calendly.com/{}",
    "Trello": "https://trello.com/{}",
    "Unsplash": "https://unsplash.com/@{}",
    "Slideshare": "https://www.slideshare.net/{}",
    "Speakerdeck": "https://speakerdeck.com/{}",
    "Read.cv": "https://read.cv/{}",
    "Gravatar": "https://gravatar.com/{}",
    "HiveMining": "https://hive.blog/@{}",
    "Steemit": "https://steemit.com/@{}",
    "Docker Hub": "https://hub.docker.com/u/{}",
    "NPM": "https://www.npmjs.com/~{}",
    "PyPI": "https://pypi.org/user/{}/",
    "Sourceforge": "https://sourceforge.net/u/{}/profile",
    "Codeberg": "https://codeberg.org/{}",
    "Flickr2": "https://flickr.com/people/{}",
    "500px": "https://500px.com/p/{}",
    "Docker": "https://hub.docker.com/u/{}",
    "Guns?": "https://www.reddit.com/user/{}",
    "Loyalty?": "https://www.twitch.tv/{}/about",
    "Odysee": "https://odysee.com/@{}",
    "Rumble": "https://rumble.com/user/{}",
    "Dailymotion": "https://www.dailymotion.com/{}",
    "Vimeo": "https://vimeo.com/{}",
}

def t_username():
    banner_title("USERNAME SHERLOCK — 300+ plateformes (base GitHub)")
    u = TARGET["username"] or input(f"{B}{C}username{RST} > ").strip()
    if not u: return
    TARGET["username"] = u
    try:
        sites = gt_lib.sherlock_sites()
    except Exception as e:
        sites = {}
    if sites:
        items = [(k, v) for k, v in sites.items()
                 if v.get("errorType") == "status_code" and "{}" in v.get("url", "")]
        print(f"{DIM}{len(items)} plateformes sherlock, 60 threads…{RST}")
        def check(pair):
            name, cfg_ = pair
            url = cfg_["url"].format(u)
            want = cfg_.get("errorCode", 404)
            try:
                req = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
                with urllib.request.urlopen(req, timeout=8) as r:
                    return (name, url, r.status != want)
            except urllib.error.HTTPError as e:
                return (name, url, e.code != want)
            except Exception:
                return None
        with ThreadPoolExecutor(60) as ex:
            results = [x for x in ex.map(check, items) if x and x[2]]
    else:
        print(f"{Y}hors-ligne — fallback natif 20 plateformes{RST}")
        results = []
        for name, url in PLATFORMS.items():
            try:
                req = urllib.request.Request(url.format(u), headers={"User-Agent": UA}, method="HEAD")
                try:
                    with urllib.request.urlopen(req, timeout=6) as r: code = r.status
                except urllib.error.HTTPError as e: code = e.code
                if code == 200: results.append((name, url.format(u), True))
            except Exception: continue
    print(f"\n{B}{len(results)} profil(s) trouvés :{RST}\n")
    for name, url, _ in sorted(results): print(f"  {G}✔ {name:<16}{RST} {DIM}{url}{RST}")
    if results: save_report("USERNAME SHERLOCK", "\n".join(f"{n} {u}" for n, u, _ in sorted(results)))

def t_gravatar():
    banner_title("GRAVATAR PAR EMAIL")
    email = input(f"{B}{C}email{RST} > ").strip()
    if not email: return
    h = hashlib.md5(email.strip().lower().encode()).hexdigest()
    try:
        req = urllib.request.Request(f"https://www.gravatar.com/{h}.json", headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=8) as r:
            d = json.loads(r.read())
        entry = d.get("entry", [{}])[0]
        print(f"  {G}✔ compte Gravatar existe{RST}")
        print(f"  pseudo : {entry.get('preferredUsername', '—')}")
        print(f"  nom    : {entry.get('displayName', '—')}")
        print(f"  bio    : {entry.get('aboutMe', '—')[:150]}")
        urls = [u.get("value") for u in entry.get("accounts", [])]
        if urls:
            print(f"  comptes liés :")
            for u in urls: print(f"    {CY}▸ {u}{RST}")
        save_report("GRAVATAR", json.dumps(d, ensure_ascii=False)[:500])
    except Exception:
        print(f"  {R}✘ pas de compte Gravatar pour cet email{RST}")

def t_github():
    banner_title("GITHUB OSINT")
    user = input(f"{B}{C}username github (ou Entrée pour chercher par domaine){RST} > ").strip()
    if user:
        try:
            d = http_get(f"https://api.github.com/users/{user}")
            print(f"\n  {W}{d.get('login')}{RST} · {d.get('name', '—')}")
            print(f"  {DIM}bio : {d.get('bio') or '—'}{RST}")
            print(f"  {DIM}localisation : {d.get('location') or '—'}{RST}")
            print(f"  {DIM}entreprise : {d.get('company') or '—'}{RST}")
            print(f"  {DIM}repos publics : {d.get('public_repos')} · followers : {d.get('followers')}{RST}")
            print(f"  {DIM}créé : {d.get('created_at','')[:10]}{RST}")
            repos = http_get(f"https://api.github.com/users/{user}/repos?per_page=10")
            for r_ in repos:
                print(f"  {G}▸ {r_.get('name')}{RST} {DIM}★{r_.get('stargazers_count')} · {r_.get('language') or '—'}{RST}")
            save_report("GITHUB", json.dumps(d, ensure_ascii=False)[:800])
        except Exception as e:
            print(f"  {R}✘ utilisateur introuvable ({e.__class__.__name__}){RST}")
        # emails dans les commits publics
        try:
            d = http_get(f"https://api.github.com/users/{user}/events/public?per_page=30")
            emails = set()
            for ev in d:
                for c in (ev.get("payload", {}).get("commits", [])):
                    e = c.get("author", {}).get("email", "")
                    if e and "noreply" not in e: emails.add(e)
            if emails:
                print(f"\n  {B}{Y}📧 emails révélés dans les commits publics :{RST}")
                for e in emails: print(f"    {G}▸ {e}{RST}")
                save_report("GITHUB EMAILS", "\n".join(emails))
        except Exception:
            pass

def t_org():
    banner_title("INFRASTRUCTURE & ORGANISATION DU DOMAINE")
    d = TARGET["domain"]
    if not d: print(f"{Y}[!] domaine requis (option c){RST}"); return
    whois = subprocess.run(["whois", d], capture_output=True, text=True).stdout
    for field in ("Registrant Organization", "Registrant Name", "Registrant Email",
                  "Registrar", "Creation Date", "Expiry Date", "Name Server"):
        for line in whois.splitlines():
            if field.lower() in line.lower() and ":" in line:
                print(f"  {G}{field:<22}{RST} {line.split(':', 1)[1].strip()[:80]}")
                break
    print(f"\n{B}INFRASTRUCTURE EMAIL :{RST}")
    for t in ("MX", "TXT"):
        r = subprocess.run(["dig", "+short", d, t], capture_output=True, text=True).stdout.strip()
        if r:
            print(f"  {CY}{t}{RST} {r.replace(chr(10), ' | ')}")
    mx = subprocess.run(["dig", "+short", d, "MX"], capture_output=True, text=True).stdout
    prov = "Google Workspace" if "google" in mx else "Microsoft 365" if "outlook" in mx or "protection.outlook" in mx else "autre"
    print(f"  {G}{'provider':<22}{RST} {prov}")
    save_report("ORG", whois[:1500])

def t_team():
    banner_title("PAGES ÉQUIPE / CONTACT — noms & emails")
    d = TARGET["domain"]
    if not d: print(f"{Y}[!] domaine requis{RST}"); return
    pages = ["/team", "/about", "/contact", "/equipe", "/a-propos", "/staff", "/company"]
    emails, names, linkedins = set(), set(), set()
    for p in pages:
        try:
            html = http_get(f"https://{d}{p}", timeout=8)
        except Exception:
            continue
        emails.update(re.findall(r"[\w.+-]+@" + re.escape(d) + r"|\w[\w.+-]*@(?:gmail|outlook|hotmail|protonmail)\.\w+", html))
        names.update(re.findall(r'>(?:[A-Z][a-zé]+\s){1,2}[A-Z][a-zé]+<', html))
        linkedins.update(re.findall(r'linkedin\.com/in/[\w-]+', html))
    print(f"{B}{len(emails)} email(s) d'organisation :{RST}")
    for e in sorted(emails): print(f"  {G}✉ {RST}{e}")
    print(f"\n{B}{len(names)} nom(s) potentiels :{RST}")
    for n in sorted(names)[:15]: print(f"  {G}▸ {RST}{n.strip('<>')}")
    print(f"\n{B}{len(linkedins)} LinkedIn(s) :{RST}")
    for l in sorted(linkedins)[:15]: print(f"  {CY}▸ https://{l}{RST}")
    if emails or names: save_report("TEAM", "\n".join(sorted(emails) + sorted(names)))

def t_maigret():
    banner_title("MAIGRET (300+ sites) — si installé")
    u = TARGET["username"] or input(f"{B}{C}username{RST} > ").strip()
    if not u: return
    import shutil as sh
    if not sh.which("maigret"):
        print(f"{Y}maigret n'est pas installé. Installation :{RST}")
        print(f"  {W}pip3 install maigret{RST}")
        return
    out = subprocess.run(["maigret", u, "--print-not-found=false", "--timeout=8"],
                         capture_output=True, text=True, timeout=300).stdout
    print(out[:5000] if out.strip() else "aucun résultat")
    if out.strip(): save_report("MAIGRET", out[:3000])

def t_github_dorks():
    banner_title("GITHUB DORKS — liens de recherche prêts à l'emploi")
    org = input(f"{B}{C}orga/user github{RST} > ").strip()
    if not org: return
    dorks = [
        ("Mots de passe", f"https://github.com/search?q=org%3A{org}+password&type=code"),
        ("Clés API", f"https://github.com/search?q=org%3A{org}+%22api_key%22&type=code"),
        ("Secrets", f"https://github.com/search?q=org%3A{org}+secret&type=code"),
        ("Tokens", f"https://github.com/search?q=org%3A{org}+token&type=code"),
        ("AWS", f"https://github.com/search?q=org%3A{org}+AKIA&type=code"),
        ("Private keys", f"https://github.com/search?q=org%3A{org}+BEGIN+PRIVATE+KEY&type=code"),
        ("Membres", f"https://github.com/orgs/{org}/people"),
        ("Gists", f"https://gist.github.com/{org}"),
    ]
    print(f"\n{B}dorks générés (ouvre-les dans le browser) :{RST}")
    for name, url in dorks:
        print(f"  {G}▸ {name}{RST}\n    {CY}{url}{RST}")
    save_report("GITHUB DORKS", "\n".join(f"{n}: {u}" for n, u in dorks))

def t_asn():
    banner_title("ASN & HÉBERGEMENT")
    d = TARGET["domain"]
    if not d: print(f"{Y}[!] domaine requis{RST}"); return
    try:
        ip = socket.gethostbyname(d)
        j = http_get(f"http://ip-api.com/json/{ip}?fields=isp,org,as,asname,reverse,mobile,proxy,hosting,query", as_json=True)
        for k, label in (("query","IP"),("isp","FAI"),("org","Organisation"),("asname","AS Name"),
                         ("as","AS"),("reverse","Reverse"),("hosting","Hébergement datacenter"),
                         ("proxy","Proxy/VPN"),("mobile","Mobile")):
            print(f"  {G}{label:<22}{RST} {j.get(k, '—')}")
        if str(j.get("hosting")).lower() == "true":
            print(f"  {Y}→ hébergé en datacenter : le site est probablement derrière un cloud/CDN{RST}")
        save_report("ASN", json.dumps(j))
    except Exception as e:
        print(f"{R}[!] {e}{RST}")


def t_dorks_osint():
    banner_title("DORKS OSINT SUR LA PERSONNE / L'ORGANISATION")
    t = TARGET["domain"] or TARGET["username"] or input(f"{B}{C}nom/domaine{RST} > ").strip()
    if not t: return
    dorks = [
        ("Documents", f'"{t}" filetype:pdf'),
        ("CV / resumes", f'"{t}" (filetype:pdf OR filetype:doc) CV'),
        ("Pastebin", f'site:pastebin.com "{t}"'),
        ("Gists", f'site:gist.github.com "{t}"'),
        ("LinkedIn", f'site:linkedin.com "{t}"'),
        ("Twitter/X", f'site:x.com "{t}"'),
        ("Contacts", f'"{t}" (email OR contact OR tel)'),
        ("Breach dumps", f'"{t}" (leak OR dump OR breach)'),
        ("Spreadsheets", f'"{t}" (filetype:xls OR filetype:xlsx OR filetype:csv)'),
        ("Photos", f'"{t}" filetype:jpg'),
    ]
    for name, q in dorks:
        print(f"  {G}▸ {name:<18}{RST} {CY}https://www.google.com/search?q={urllib.parse.quote(q)}{RST}")
    save_report("DORKS OSINT", "\n".join(f"{n}" for n, _ in dorks))

def t_phones():
    banner_title("TÉLÉPHONES & ADRESSES SUR LES PAGES")
    d = TARGET["domain"]
    if not d: print(f"{Y}[!] domaine requis{RST}"); return
    phones, addrs = set(), set()
    for p in ("/", "/contact", "/about", "/equipe"):
        try:
            html = http_get(f"https://{d}{p}", timeout=8)
            phones.update(re.findall(r"(?:\+33|0)[1-9](?:[\s.-]?\d{2}){4}", html))
            addrs.update(re.findall(r"\d{1,4}[\s,]+(?:rue|avenue|bd|boulevard|place|chemin)[\w\s,.-]{10,60}", html, re.I))
        except Exception: continue
    print(f"{B}{len(phones)} téléphone(s) :{RST}")
    for p in sorted(phones): print(f"  {G}☎ {RST}{p}")
    print(f"{B}{len(addrs)} adresse(s) potentielles :{RST}")
    for a in sorted(addrs)[:8]: print(f"  {G}▸ {RST}{a}")
    if phones: save_report("PHONES", "\n".join(sorted(phones)))

def t_cert_org():
    banner_title("ORGANISATION VIA LE CERTIFICAT TLS")
    d = TARGET["domain"]
    if not d: print(f"{Y}[!] domaine requis{RST}"); return
    out = subprocess.run(["openssl", "s_client", "-connect", f"{d}:443"],
                         capture_output=True, text=True, input="", timeout=15).stdout
    for tag in ("subject=", "issuer="):
        m = re.search(tag + r"([^\n]+)", out)
        if m: print(f"  {G}{tag[:-1]}{RST} {m.group(1)[:120]}")
    sans = re.findall(r"DNS:([\w.*.-]+)", out)
    if sans:
        print(f"  {G}SANs ({len(set(sans))}){RST} : {', '.join(sorted(set(sans))[:10])}")
        save_report("CERT ORG", "\n".join(sorted(set(sans))))

def t_tech():
    banner_title("TECHNOLOGIES DU SITE")
    d = TARGET["domain"]
    if not d: print(f"{Y}[!] domaine requis{RST}"); return
    try:
        home = http_get(f"https://{d}", timeout=12)
    except Exception as e:
        print(f"{R}[!] {e}{RST}"); return
    techs = []
    for pat, name in ((r"wp-content", "WordPress"), (r"shopify", "Shopify"), (r"react", "React"),
                      (r"vue\.js", "Vue"), (r"next\.js|__next", "Next.js"), (r"laravel_session", "Laravel"),
                      (r"cloudflare", "Cloudflare"), (r"cdn-cgi", "Cloudflare CDN"),
                      (r"googletagmanager|gtag", "GTM"), (r"stripe", "Stripe"),
                      (r"wix", "Wix"), (r"squarespace", "Squarespace"),
                      (r"shopware|prestashop|magento", "E-commerce")):
        if re.search(pat, home, re.I): techs.append(name)
    print(f"{B}détecté :{RST} {', '.join(techs) or '—'}")

def t_first_snapshot():
    banner_title("PREMIÈRE ARCHIVAGE WAYBACK (âge du site)")
    d = TARGET["domain"]
    if not d: print(f"{Y}[!] domaine requis{RST}"); return
    try:
        data = http_get(f"http://web.archive.org/cdx/search/cdx?url={d}&output=json&limit=3&filter=statuscode:200",
                        timeout=25, as_json=True)
        if len(data) > 1:
            first = data[1]
            print(f"  {G}premier archivage :{RST} {first[1][:10]}  {DIM}{first[2][:60]}{RST}")
            years = (time.time() - __import__("calendar").time.strptime(first[1][:10], "%Y%m%d").mktime()) / 86400 / 365
            print(f"  {G}âge ≈{RST} {years:.0f} ans")
        else:
            print(f"{Y}jamais archivé{RST}")
    except Exception as e:
        print(f"{R}[!] {e.__class__.__name__}{RST}")

def t_socials_all():
    banner_title("RÉSEAUX SOCIAUX SUR TOUTES LES PAGES")
    d = TARGET["domain"]
    if not d: print(f"{Y}[!] domaine requis{RST}"); return
    socials = set()
    for p in ("/", "/about", "/contact", "/team", "/a-propos"):
        try:
            html = http_get(f"https://{d}{p}", timeout=8)
            socials.update(re.findall(r'https?://(?:www\.)?(?:twitter\.com|x\.com|linkedin\.com|facebook\.com|instagram\.com|youtube\.com|tiktok\.com|github\.com|t\.me)/[\w/.-]+', html))
        except Exception: continue
    print(f"{B}{len(socials)} réseaux sociaux de l'organisation :{RST}")
    for s in sorted(socials): print(f"  {G}▸ {RST}{s}")
    if socials: save_report("SOCIALS", "\n".join(sorted(socials)))

def t_dnsdeep():
    banner_title("DNS PROFOND — fournisseurs détectés")
    d = TARGET["domain"]
    if not d: print(f"{Y}[!] domaine requis{RST}"); return
    txt = subprocess.run(["dig", "+short", "TXT", d], capture_output=True, text=True).stdout
    for line in txt.splitlines():
        if "google-site-verification" in line: print(f"  {G}▸ {RST}Google Search Console vérifié")
        if "facebook-domain-verification" in line: print(f"  {G}▸ {RST}Facebook vérifié")
        if "MS=" in line or "ms=" in line: print(f"  {G}▸ {RST}Microsoft 365 vérifié")
        if "v=spf1" in line:
            for inc in re.findall(r"include:(\S+)", line):
                print(f"  {G}▸ SPF include{RST} {inc}")
        if "_domainkey" in line: print(f"  {G}▸ {RST}DKIM {line[:60]}")
    ns = subprocess.run(["dig", "+short", "NS", d], capture_output=True, text=True).stdout
    print(f"  {G}▸ NS{RST} {', '.join(ns.split())}")
    save_report("DNS DEEP", "\n".join(txt.splitlines()[:10]))

def t_emailgen():
    banner_title("GÉNÉRATEUR D'ADRESSES PROBABLES (format entreprise)")
    d = TARGET["domain"]
    if not d: print(f"{Y}[!] domaine requis{RST}"); return
    fn = input(f"{B}{C}prénom{RST} > ").strip().lower()
    ln = input(f"{B}{C}nom{RST} > ").strip().lower()
    if not fn or not ln: return
    patterns = [f"{fn}.{ln}", f"{fn}{ln}", f"{fn[0]}{ln}", f"{fn[0]}.{ln}", f"{fn}_{ln}",
                f"{fn}.{ln[0]}", f"{ln}.{fn}", f"{ln}{fn[0]}", f"{fn}", f"{ln}"]
    print(f"{B}adresses probables :{RST}")
    for p in patterns:
        print(f"  {G}✉ {RST}{p}@{d}")
    print(f"\n{DIM}vérifie l'existence : Forensics Email après un test d'envoi, ou via le MX{RST}")
    save_report("EMAILGEN", f"\n".join(f"{p}@{d}" for p in patterns))

def t_report_osint():
    banner_title("RÉSUMÉ OSINT")
    t = TARGET["domain"] or TARGET["username"]
    path = os.path.join(RAPPORTS, f"osint_{t.replace('.', '_').replace('/', '_')}.txt") if t else None
    print(CY + open(path).read()[-2500:] if path and os.path.exists(path) else f"{Y}aucun rapport{RST}")

def t_html():
    t = TARGET["domain"] or TARGET["username"]
    if not t: print(f"{Y}[!] contexte requis{RST}"); return
    src = os.path.join(RAPPORTS, f"osint_{t.replace('.', '_').replace('/', '_')}.txt")
    out = gt_lib.html_report(src, f"OSINT — {t}", src.replace(".txt", ".html"), accent="#00c8ff")
    print(f"{G}✓ rapport HTML : {out}{RST}" if out else f"{Y}aucun rapport{RST}")


def t_wayback_timeline():
    banner_title("TIMELINE D'ARCHIVAGE (par année)")
    d = TARGET["domain"]
    if not d: print(f"{Y}[!] domaine requis{RST}"); return
    try:
        data = http_get(f"http://web.archive.org/cdx/search/cdx?url={d}&output=json&collapse=timestamp:4&fl=timestamp,statuscode",
                        timeout=30, as_json=True)
        years = {}
        for row in data[1:]:
            years[row[0][:4]] = years.get(row[0][:4], 0) + 1
        print(f"{B}{len(years)} années archivées :{RST}")
        for y in sorted(years): print(f"  {C}{y}{RST} {'█' * min(years.get(y, 1), 40)} {years[y]}")
    except Exception as e:
        print(f"{R}[!] {e.__class__.__name__}{RST}")

def t_people_links():
    banner_title("MOTEURS DE RECHERCHE PERSONNE — liens prêts")
    name = input(f"{B}{C}nom complet{RST} > ").strip()
    if not name: return
    q = urllib.parse.quote(f'"{name}"')
    engines = [
        ("Google", f"https://www.google.com/search?q={q}"),
        ("Bing", f"https://www.bing.com/search?q={q}"),
        ("Yandex", f"https://yandex.com/search/?text={q}"),
        ("DuckDuckGo", f"https://duckduckgo.com/?q={q}"),
        ("LinkedIn", f"https://www.google.com/search?q=site:linkedin.com/in+{q}"),
        ("Facebook", f"https://www.google.com/search?q=site:facebook.com+{q}"),
        ("Mastodon", f"https://www.google.com/search?q=site:mastodon.social+{q}"),
        ("Images", f"https://www.google.com/search?q={q}&tbm=isch"),
    ]
    for name_, url in engines:
        print(f"  {G}▸ {name_:<12}{RST} {CY}{url[:100]}{RST}")
    save_report("PEOPLE", f"{name}")

def t_card():
    banner_title("CARTE D'IDENTITÉ — résumé de tout l'OSINT")
    t = TARGET["domain"] or TARGET["username"]
    path = os.path.join(RAPPORTS, f"osint_{t.replace('.', '_').replace('/', '_')}.txt") if t else None
    if not path or not os.path.exists(path):
        print(f"{Y}lance d'abord quelques scans OSINT{RST}"); return
    content = open(path).read()
    emails = set(re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]{2,12}", content))
    socials = set(re.findall(r"https?://(?:x\.com|github\.com|linkedin\.com|instagram\.com|facebook\.com)/[\w/.-]+", content))
    print(f"{B}CIBLE :{RST} {t}")
    print(f"  {G}emails{RST}    : {', '.join(sorted(emails)[:8]) or '—'}")
    print(f"  {G}profils{RST}   : {len(socials)}")
    for s in sorted(socials)[:8]: print(f"    {CY}▸ {s[:70]}{RST}")
    print(f"  {DIM}rapport complet : {path}{RST}")

TOOLS = [
    ("1", "USERNAME 20 PLATEFORMES", t_username, "twitter, github, instagram, reddit…"),
    ("2", "GRAVATAR PAR EMAIL", t_gravatar, "le compte gravatar révèle le profil"),
    ("3", "GITHUB OSINT", t_github, "profil, repos, emails dans les commits"),
    ("4", "ORG & INFRA", t_org, "whois org, provider email, NS"),
    ("5", "PAGES ÉQUIPE", t_team, "emails, noms, LinkedIn des /team /about"),
    ("6", "ASN & HÉBERGEMENT", t_asn, "datacenter ? proxy ? organisation réelle"),
    ("7", "MAIGRET (300+ sites)", t_maigret, "le tool OSINT de référence — si pip3 install maigret"),
    ("8", "GITHUB DORKS", t_github_dorks, "recherches secrets/clés prêtes dans l'orga"),
    ("a", "DORKS OSINT", t_dorks_osint, "10 dorks prêts pour la personne/l'orga"),
    ("b", "TÉLÉPHONES & ADRESSES", t_phones, "extraits des pages publiques"),
    ("c", "ORG VIA CERTIFICAT", t_cert_org, "le cert TLS révèle l'organisation"),
    ("d", "TECHNOLOGIES", t_tech, "le stack du site"),
    ("e", "ÂGE DU SITE", t_first_snapshot, "premier archivage wayback"),
    ("f", "RÉSEAUX SOCIAUX ALL", t_socials_all, "sur toutes les pages"),
    ("g", "DNS PROFOND", t_dnsdeep, "vérifications et fournisseurs"),
    ("h", "EMAILS PROBABLES", t_emailgen, "formats d'adresses de l'entreprise"),
    ("i", "RÉSUMÉ OSINT", t_report_osint, "relit tous tes scans"),
    ("j", "TIMELINE WAYBACK", t_wayback_timeline, "l'âge du site année par année"),
    ("k", "MOTEURS PERSONNE", t_people_links, "8 moteurs de recherche prêts"),
    ("l", "CARTE D'IDENTITÉ", t_card, "résumé de tout l'OSINT"),
]

def menu():
    print(CLEAR)
    for line in LOGO.splitlines():
        print(CD + line)
    print()
    print(f"{B}{C}  ╔═══════════════════════════════════════════════╗{RST}")
    print(f"{B}{C}  ║   O S I N T   D E E P  —  hacker_tool         ║{RST}")
    print(f"{B}{C}  ╚═══════════════════════════════════════════════╝{RST}")
    print(f"{DIM}       powered by Maxime Leal · sources publiques uniquement{RST}\n")
    if TARGET["domain"] or TARGET["username"]:
        print(f"  {B}CONTEXTE :{RST} {W}{TARGET['domain'] or TARGET['username']}{RST}\n")
    for n, name, _, desc in TOOLS:
        print(f"  {B}{C}{n}{RST}  {W}{name:<26}{RST} {DIM}{desc}{RST}")
    print(f"  {B}{C}d{RST}  {'DÉFINIR LE DOMAINE':<26}{RST}")
    print(f"  {B}{C}u{RST}  {'DÉFINIR UN USERNAME':<26}{RST}")
    print(f"  {B}{H}{RST}  {'RAPPORT HTML → .html':<26}{RST}")
    print(f"  {B}{C}q{RST}  {'QUITTER':<26}{RST}")
    print()

def main():
    splash()
    while True:
        try:
            menu()
            c = input(f"{B}{C}osint>{RST} ").strip().lower()
            if c == "q": break
            elif c == "d": TARGET["domain"] = input(f"{B}{C}domaine{RST} > ").strip()
            elif c == "u": TARGET["username"] = input(f"{B}{C}username{RST} > ").strip()
            else:
                tool = next((t for t in TOOLS if t[0] == c), None)
                if tool: tool[2]()
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
