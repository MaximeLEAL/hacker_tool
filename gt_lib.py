#!/usr/bin/env python3
# language: Python 3, file: gt_lib.py, target: macOS
# GT_LIB — ressources GitHub partagées par tous les tools de hacker_tool
# télécharge une fois, met en cache, sert ensuite hors-ligne
import os, json, time, re, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(ROOT, "cache")
os.makedirs(CACHE, exist_ok=True)

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"

RESSOURCES = {
    # wordlists de SecLists (danielmiessler) — la référence publique
    "subdomains.txt": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/DNS/subdomains-top1million-5000.txt",
    "dirs-common.txt": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/common.txt",
    "dirs-big.txt": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/raft-large-directories.txt",
    "params.txt": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/burp-parameter-names.txt",
    "usernames-top.txt": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Usernames/Names/names.txt",
    "passwords-common.txt": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/Pwdb_top-1000000.txt",
    # la base de sherlock-project : 400+ plateformes d'OSINT
    "sherlock.json": "https://raw.githubusercontent.com/sherlock-project/sherlock/master/sherlock_project/resources/data.json",
    # annuaire officiel SecureDrop (freedom of the press foundation) — signalement journalistique
    "securedrop.json": "https://securedrop.org/api/v1/directory/",
}

def ressource(name, max_age_days=7):
    """renvoie le contenu du fichier cache, le télécharge depuis GitHub si absent/vieux"""
    path = os.path.join(CACHE, name)
    url = RESSOURCES.get(name)
    if not url: return None
    fresh = os.path.exists(path) and (time.time() - os.path.getmtime(path)) < max_age_days * 86400
    if not fresh:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
            with open(path, "wb") as f: f.write(data)
        except Exception as e:
            if not os.path.exists(path):
                raise RuntimeError(f"{name} : {e.__class__.__name__} (offline ?)")
    return open(path, encoding="utf-8", errors="ignore").read()

def lines(name):
    s = ressource(name)
    return [l.strip() for l in s.splitlines() if l.strip()] if s else []

def sherlock_sites():
    """la liste sherlock : {site: {url, errorCode, ...}}"""
    s = ressource("sherlock.json")
    if not s: return {}
    try: return json.loads(s)
    except Exception: return {}


def http_get(url, timeout=15, retries=3, as_json=False, headers=None):
    """HTTP avec retry/backoff sur les rate limits (429/5xx) — pro behavior"""
    import urllib.error
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers or {"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = r.read()
            return json.loads(d) if as_json else d.decode("utf-8", "ignore")
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 500):
                wait = 2 ** i * 2
                time.sleep(wait); last = e; continue
            raise
        except Exception as e:
            time.sleep(1); last = e
    raise last

def html_report(txt_path, title, out_path, accent="#e63022"):
    """convertit un rapport .txt en rapport HTML professionnel style Gotham"""
    import html as H
    if not os.path.exists(txt_path): return None
    content = open(txt_path, encoding="utf-8").read()
    # découpe en sections par les séparateurs =====
    parts = content.split("=" * 50)
    sections = []
    for p in parts:
        p = p.strip()
        if not p: continue
        lines = p.splitlines()
        header = ""
        body = lines
        m = re.match(r"^\[(\d{2}/\d{2}/\d{4} \d{2}:\d{2})\]\s*(.+)$", lines[0].strip())
        if m:
            header, body = lines[0].strip(), lines[1:]
        elif lines[0].strip():
            header = lines[0].strip()[:60]
        body_txt = H.escape("\n".join(body).strip())[:6000]
        if body_txt:
            sections.append({"header": H.escape(header), "body": body_txt})
    css = """:root{--bg:#06070c;--panel:#0c0e17;--panel2:#070810;--line:#1a1c2e;
  --txt:#c4c6d6;--muted:#6a6d86;--red:#e63022;--gold:#f5c518;
  --disp:"Anton",Impact,sans-serif;--mono:"JetBrains Mono",monospace;--sans:"Archivo",sans-serif}
*{box-sizing:border-box;margin:0}
body{background:var(--bg);color:var(--txt);font-family:var(--sans);padding:0}
.nav{padding:16px 30px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center}
.nav b{color:#fff;letter-spacing:3px}.nav b span{color:var(--red)}
.nav .meta{font-family:var(--mono);color:var(--muted);font-size:.68rem;letter-spacing:1px}
.hero{padding:44px 30px 26px;border-bottom:3px solid var(--accent)}
h1{font-family:var(--disp);color:#fff;font-size:2.6rem;letter-spacing:2px;text-transform:uppercase;margin:0}
h1 span{color:var(--accent)}
.sub{font-family:var(--mono);color:var(--muted);font-size:.68rem;letter-spacing:3px;margin-top:10px;text-transform:uppercase}
main{max-width:900px;margin:26px auto;padding:0 26px 50px}
.sec{background:linear-gradient(180deg,var(--panel),var(--panel2));border:1px solid var(--line);border-radius:6px;margin-bottom:14px;overflow:hidden}
.sech{display:flex;gap:12px;align-items:center;padding:11px 18px;border-bottom:1px solid var(--line);font-family:var(--mono);font-size:.68rem;letter-spacing:1px}
.sech .nm{color:var(--accent);font-weight:700;text-transform:uppercase}
.sech .dt{margin-left:auto;color:var(--dim)}
.secb{padding:14px 18px;font-family:var(--mono);font-size:.76rem;line-height:1.55;white-space:pre-wrap;color:var(--txt);overflow-x:auto}
footer{text-align:center;color:var(--muted);padding:34px;font-family:var(--mono);font-size:.62rem;letter-spacing:2px}
footer a{color:#9fb4ff}
"""
    secs_html = "".join(
        f'<div class="sec"><div class="sech"><span class="nm">{s["header"][:60]}</span></div>'
        f'<div class="secb">{s["body"]}</div></div>'
        for s in sections)
    page = f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<title>{H.escape(title)} — rapport</title>
<link href="https://fonts.googleapis.com/css2?family=Anton&family=JetBrains+Mono&family=Archivo&display=swap" rel="stylesheet">
<style>{css}</style></head><body>
<div class="nav"><b>GOTHAM <span>CITY</span></b><span class="meta">RAPPORT GÉNÉRÉ LE {time.strftime('%d/%m/%Y %H:%M')}</span></div>
<div class="hero" style="--accent:{accent}"><h1>{H.escape(title)} <span>· RAPPORT</span></h1>
<div class="sub">ARSENAL DC · HACKER_TOOL · POWERED BY MAXIME LEAL</div></div>
<main>{secs_html or '<p style="color:var(--muted)">rapport vide</p>'}</main>
<footer>RAPPORT HTML GÉNÉRÉ PAR HACKER_TOOL · <a href="https://github.com/MaximeLEAL/hacker_tool">GITHUB</a> · POWERED BY MAXIME LEAL</footer>
</body></html>"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(page)
    return out_path


# ── BIG FONT ANSI-SHADOW pour les logos des tools ──
BIGFONT = {
"A": [" █████╗ ", "██╔══██╗", "███████║", "██╔══██║", "██║  ██║", "╚═╝  ╚═╝"],
"C": [" ██████╗", "██╔════╝", "██║     ", "██║     ", "╚██████╗", " ╚═════╝"],
"D": ["██████╗ ", "██╔══██╗", "██║  ██║", "██║  ██║", "██████╔╝", "╚═════╝ "],
"E": ["███████╗", "██╔════╝", "█████╗  ", "██╔══╝  ", "███████╗", "╚══════╝"],
"F": ["███████╗", "██╔════╝", "█████╗  ", "██╔══╝  ", "██║     ", "╚═╝     "],
"H": ["██╗  ██╗", "██║  ██║", "███████║", "██╔══██║", "██║  ██║", "╚═╝  ╚═╝"],
"I": ["██╗", "██║", "██║", "██║", "██║", "╚═╝"],
"K": ["██╗  ██╗", "██║ ██╔╝", "█████╔╝ ", "██╔═██╗ ", "██║  ██╗", "╚═╝  ╚═╝"],
"L": ["██╗     ", "██║     ", "██║     ", "██║     ", "███████╗", "╚══════╝"],
"N": ["███╗   ██╗", "████╗  ██║", "██╔██╗ ██║", "██║╚██╗██║", "██║ ╚████║", "╚═╝  ╚═══╝"],
"O": [" ██████╗ ", "██╔═══██╗", "██║   ██║", "██║   ██║", "╚██████╔╝", " ╚═════╝ "],
"R": ["██████╗ ", "██╔══██╗", "██████╔╝", "██╔══██╗", "██║  ██║", "╚═╝  ╚═╝"],
"S": ["███████╗", "██╔════╝", "███████╗", "╚════██║", "███████║", "╚══════╝"],
"T": ["████████╗", "╚══██╔══╝", "   ██║   ", "   ██║   ", "   ██║   ", "   ╚═╝   "],
"U": ["██╗   ██╗", "██║   ██║", "██║   ██║", "██║   ██║", "╚██████╔╝", " ╚═════╝ "],
"V": ["██╗   ██╗", "██║   ██║", "██║   ██║", "╚██╗ ██╔╝", " ╚████╔╝ ", "  ╚═══╝  "],
"W": ["██╗    ██╗", "██║    ██║", "██║ █╗ ██║", "██║███╗██║", "╚███╔███╔╝", " ╚══╝╚══╝ "],
" ": ["  ", "  ", "  ", "  ", "  ", "  "],
"-": ["      ", "      ", "██████", "      ", "      ", "      "],
"·": ["  ", "  ", "██", "  ", "  ", "  "],
}

def bigtext(text, color=""):
    """rend un titre en ANSI-Shadow 6 lignes, coloré"""
    rows = ["", "", "", "", "", ""]
    for ch in text.upper():
        glyph = BIGFONT.get(ch, BIGFONT[" "])
        for i in range(6):
            rows[i] += glyph[i] + " "
    return "\n".join(color + r + "\033[0m" for r in rows)


KEYS_FILE = os.path.join(ROOT, "keys.json")
KEYS_DEFAULT = {
    "_instructions": "clés API GRATUITES à créer toi-même : liens dans le README",
    "virustotal": "",   # https://www.virustotal.com → profil → API key (gratuit)
    "shodan": "",       # https://account.shodan.io → API key (gratuit)
    "urlscan": "",      # https://urlscan.io → user → API (gratuit)
    "censys": "",       # https://search.censys.io → API (gratuit)
}

def load_keys():
    """les clés API de l'utilisateur — vide = options non disponibles"""
    try:
        d = json.load(open(KEYS_FILE, encoding="utf-8"))
        return {k: v for k, v in d.items() if v and not k.startswith("_")}
    except Exception:
        return {}

def pwned_password(password):
    """le mot de passe apparaît-il dans des fuites réelles ?
    k-anonymity : seuls les 5 premiers chars du SHA-1 quittent la machine"""
    import hashlib
    sha1 = hashlib.sha1(password.encode()).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    try:
        req = urllib.request.Request(f"https://api.pwnedpasswords.com/range/{prefix}",
                                     headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=10) as r:
            for line in r.read().decode().splitlines():
                parts = line.strip().split(":")
                if parts[0] == suffix:
                    return int(parts[1])
    except Exception:
        return -1
    return 0
