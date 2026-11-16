#!/usr/bin/env python3
# language: Python 3, file: vuln_tool.py, target: macOS
# ═══════════════════════════════════════════════════════════════════
#  VULN TOOL — radar de vulnérabilités · hacker_tool
#  powered by Maxime Leal
# ═══════════════════════════════════════════════════════════════════
#  Usage : python3 vuln_tool.py
import os, sys, subprocess, re, json, time, random, socket, shutil, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
RAPPORTS = os.path.join(ROOT, "rapports")
os.makedirs(RAPPORTS, exist_ok=True)

# ── IDENTITÉ : VULN = ROUGE ────────────────────────────────────────
C   = "\033[38;2;255;42;42m"   # rouge vuln
CD  = "\033[38;2;150;25;25m"
W   = "\033[97m"
G   = "\033[38;2;74;214;109m"
Y   = "\033[93m"
CY  = "\033[96m"
DIM = "\033[2m"
B   = "\033[1m"
RST = "\033[0m"
CLEAR = "\033[2J\033[H"

TARGET = {"ip": "", "domain": ""}
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"

NVD = "https://services.nvd.nist.gov/rest/json/cves/2.0"
KEV = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"

SKULL = r"""
        ______
     .-"      "-.
    /            \
   |              |
   |,  .-.  .-.  ,|
   | )(__/  \__)( |
   |/     /\     \|
   (_     ^^     _)
    \__|IIIIII|__/
     | \IIIIII/ |
     \          /
      `--------`
"""

def matrix_rain(seconds=3.2, fps=16):
    cols, rows = shutil.get_terminal_size((80, 24))
    charset = "01CVE-EXPLOIT!#%&@!?+*"
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
        sys.stdout.write(C + "\033[H" + "\n".join("".join(r) for r in screen)); sys.stdout.flush()
        time.sleep(1 / fps)
    sys.stdout.write(RST)

def type_line(text, color=W, delay=.014):
    for ch in text:
        sys.stdout.write(color + ch); sys.stdout.flush(); time.sleep(delay)
    sys.stdout.write(RST + "\n")

def splash():
    sys.stdout.write(CLEAR)
    matrix_rain(3.4)
    sys.stdout.write(CLEAR)
    for line in SKULL.splitlines():
        print(C + line); time.sleep(.05)
    time.sleep(.4)
    type_line("        V U L N   T O O L", C, .03)
    type_line("   radar de vulnérabilités · hacker_tool", CD, .012)
    print()
    type_line("        ⚡ POWERED BY MAXIME LEAL ⚡", W, .02)
    time.sleep(.8)

# ─────────────────────────── HELPERS ───────────────────────────
def http_get(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())

def save_report(name, content):
    t = TARGET["domain"] or TARGET["ip"]
    if not t: return
    path = os.path.join(RAPPORTS, f"vuln_{t.replace('.', '_')}.txt")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*50}\n[{time.strftime('%d/%m/%Y %H:%M')}] {name}\n{'='*50}\n{content}\n")
    print(f"{DIM}[+] rapport : {path}{RST}")

def banner_title(txt):
    print(f"\n{B}{C}══════ {txt} ══════{RST}")
    if TARGET["ip"] or TARGET["domain"]:
        print(f"{DIM}cible : {W}{TARGET['domain'] or TARGET['ip']}{RST}")
    print()

def cvss_of(cve):
    for metric in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        ms = cve.get("metrics", {}).get(metric, [])
        if ms:
            d = ms[0].get("cvssData", {})
            return d.get("baseScore"), d.get("baseSeverity"), d.get("vectorString", "")
    return None, None, ""

def fmt_cve(item, verbose=False):
    cve = item.get("cve", item)
    cid = cve.get("id", "?")
    score, sev, vec = cvss_of(cve)
    desc = ""
    for d in cve.get("descriptions", []):
        if d.get("lang") == "en": desc = d.get("value", "")[:220]; break
    date = cve.get("published", "")[:10]
    sev_c = R if (sev or "").upper() in ("CRITICAL", "HIGH") else Y if (sev or "").upper() == "MEDIUM" else G
    line = f"{B}{R}{cid:<16}{RST} {sev_c}{str(sev or '?'):<9}{RST} {str(score or '?'):<5} {DIM}{date}{RST}"
    if verbose:
        line += f"\n  {CY}{desc}{RST}\n  {DIM}CVSS: {vec}{RST}"
    return line, cid, desc, sev

def ask_target():
    t = input(f"\n{B}{C}CIBLE {RST}(IP ou domaine) {C}> {RST}").strip()
    if not t: return False
    TARGET["domain"] = t
    try: TARGET["ip"] = socket.gethostbyname(t)
    except Exception: TARGET["ip"] = t
    return True

# ─────────────────────────── LES TOOLS ───────────────────────────
def t_cve_search():
    banner_title("RECHERCHE CVE PAR MOT-CLÉ")
    kw = input(f"{B}{C}mot-clé{RST} (ex: wordpress, nginx, apache, openssh) {C}> {RST}").strip()
    if not kw: return
    try:
        d = http_get(f"{NVD}?keywordSearch={urllib.parse.quote(kw)}&resultsPerPage=15")
        vulns = d.get("vulnerabilities", [])
        print(f"\n{B}{len(vulns)} CVE(s) trouvée(s) pour '{kw}' :{RST}\n")
        for item in vulns:
            line, cid, desc, sev = fmt_cve(item, verbose=True)
            print(line)
        save_report("CVE SEARCH", "\n".join(i.get("cve", {}).get("id", "") for i in vulns))
    except Exception as e:
        print(f"{R}[!] NVD indisponible ({e.__class__.__name__}) — réessaie dans 30 s (rate limit){RST}")

def t_kev():
    banner_title("CISA KEV — FAILLES ACTIVEMENT EXPLOITÉES")
    try:
        d = http_get(KEV)
        vulns = d.get("vulnerabilities", [])
        vulns.sort(key=lambda v: v.get("dateAdded", ""), reverse=True)
        print(f"{B}{W}{len(vulns)} failles dans le catalogue KEV — les 20 plus récentes :{RST}\n")
        for v in vulns[:20]:
            rw = " 🔒 ransomware" if v.get("knownRansomwareUse") == "Known" else ""
            print(f"{B}{R}{v['cveID']:<16}{RST} {CY}{v.get('vendorProject','')}/{v.get('product','')[:28]:<28}{RST} "
                  f"{DIM}{v.get('dateAdded','')}{RST}{rw}")
            print(f"   {DIM}{v.get('shortDescription','')[:120]}{RST}")
        save_report("KEV", "\n".join(v.get("cveID", "") for v in vulns))
    except Exception as e:
        print(f"{R}[!] {e}{RST}")

def t_banner():
    banner_title("BANNER GRABBING — versions des services")
    if not TARGET["ip"]:
        print(f"{Y}[!] définis une cible (option c){RST}"); return
    ports = {21: None, 22: None, 25: None, 80: b"GET / HTTP/1.0\r\nHost: x\r\n\r\n",
             110: None, 143: None, 443: None, 3306: None, 8080: b"GET / HTTP/1.0\r\nHost: x\r\n\r\n"}
    banners = []
    for p, payload in ports.items():
        try:
            with socket.create_connection((TARGET["ip"], p), timeout=2.5) as s:
                s.settimeout(2.5)
                if payload: s.send(payload)
                data = s.recv(300).decode("latin1", "ignore").strip()
            if data:
                first = data.splitlines()[0][:100] if "\n" in data or "\r" in data else data[:100]
                print(f"  {C}{p:<6}{RST} {W}{first}{RST}")
                banners.append(f"{p}: {first}")
        except Exception:
            pass
    if not banners: print(f"{Y}aucun banner récupéré — ports fermés ou silencieux{RST}")
    save_report("BANNERS", "\n".join(banners))

def t_version_match():
    banner_title("BANNER → RECHERCHE CVE (match de version)")
    banner = input(f"{B}{C}banner/version{RST} (ex: 'OpenSSH_8.9p1', 'Apache/2.4.49', colle le banner) {C}> {RST}").strip()
    if not banner: return
    m = re.match(r"^\s*(\d+):\s*(.+)", banner)
    if m: banner = m.group(2)
    try:
        d = http_get(f"{NVD}?keywordSearch={urllib.parse.quote(banner)}&resultsPerPage=10")
        vulns = d.get("vulnerabilities", [])
        print(f"\n{B}{len(vulns)} CVE(s) pour '{banner}' :{RST}\n")
        for item in vulns:
            line, cid, desc, sev = fmt_cve(item, verbose=True)
            print(line)
        save_report("VERSION MATCH", banner)
    except Exception as e:
        print(f"{R}[!] {e.__class__.__name__} — rate limit NVD, attends 30 s{RST}")

def t_recent():
    banner_title("TOP CVEs RÉCENTES (triées par sévérité)")
    try:
        d = http_get(f"{NVD}?resultsPerPage=30")
        vulns = []
        for item in d.get("vulnerabilities", []):
            line, cid, desc, sev = fmt_cve(item)
            score = cvss_of(item.get("cve", {}))[0] or 0
            vulns.append((score or 0, line))
        vulns.sort(reverse=True)
        for _, line in vulns: print(line)
    except Exception as e:
        print(f"{R}[!] {e.__class__.__name__}{RST}")

def t_kev_prod():
    banner_title("KEV PAR PRODUIT")
    prod = input(f"{B}{C}produit{RST} (ex: apache, wordpress, exchange, chrome) {C}> {RST}").strip().lower()
    if not prod: return
    try:
        d = http_get(KEV)
        hits = [v for v in d.get("vulnerabilities", [])
                if prod in (v.get("product", "") + v.get("vendorProject", "")).lower()]
        print(f"\n{B}{len(hits)} faille(s) KEV pour '{prod}' :{RST}\n")
        for v in hits[:25]:
            print(f"{B}{R}{v['cveID']:<16}{RST} {CY}{v.get('product','')[:30]:<30}{RST} {DIM}{v.get('dateAdded','')}{RST}")
        save_report("KEV PRODUIT", f"{prod}: {len(hits)}")
    except Exception as e:
        print(f"{R}[!] {e}{RST}")

def t_cve_detail():
    banner_title("DÉTAIL D'UNE CVE")
    cid = input(f"{B}{C}CVE-ID{RST} (ex: CVE-2024-3400) {C}> {RST}").strip().upper()
    if not cid: return
    try:
        d = http_get(f"{NVD}?cveId={cid}")
        vulns = d.get("vulnerabilities", [])
        if not vulns: print(f"{Y}CVE inconnue{RST}"); return
        cve = vulns[0].get("cve", {})
        score, sev, vec = cvss_of(cve)
        print(f"\n{B}{R}{cve.get('id')}{RST}  {Y}CVSS {score} {sev}{RST}\n  {DIM}vecteur : {vec}{RST}")
        print(f"  publié  : {cve.get('published','')[:10]} · modifié : {cve.get('lastModified','')[:10]}")
        for d_ in cve.get("descriptions", []):
            if d_.get("lang") == "en":
                print(f"\n  {W}{d_.get('value')}{RST}")
        refs = [r.get("url") for r in cve.get("references", [])][:6]
        if refs:
            print(f"\n{B}RÉFÉRENCES :{RST}")
            for u in refs: print(f"  {CY}▸ {u}{RST}")
        cwe = cve.get("weaknesses", [])
        for w in cwe[:1]:
            descs = w.get("description", [])
            if descs: print(f"\n{DIM}CWE : {descs[0].get('value','')}{RST}")
        save_report("CVE DETAIL", f"{cid} CVSS {score} {sev}")
    except Exception as e:
        print(f"{R}[!] {e.__class__.__name__}{RST}")

def t_full():
    banner_title("SCAN COMPLET — banners → CVEs automatiquement")
    if not TARGET["ip"]:
        print(f"{Y}[!] définis une cible (option c){RST}"); return
    grab = []
    for p, payload in {80: b"GET / HTTP/1.0\r\nHost: x\r\n\r\n", 443: b"GET / HTTP/1.0\r\nHost: x\r\n\r\n"}.items():
        try:
            with socket.create_connection((TARGET["ip"], p), timeout=2.5) as s:
                s.settimeout(2.5); s.send(payload)
                grab.append(s.recv(500).decode("latin1", "ignore"))
        except Exception: pass
    hdr = ""
    for g in grab:
        m = re.search(r"(server|x-powered-by):\s*([^\r\n]+)", g, re.I)
        if m: hdr += m.group(2).strip() + " "
    print(f"{DIM}bannières détectées : {W}{hdr.strip() or 'aucune'}{RST}")
    terms = [t for t in re.findall(r"[\w/.-]+\d[\w.-]*", hdr) if t]
    for t in terms:
        try:
            d = http_get(f"{NVD}?keywordSearch={urllib.parse.quote(t)}&resultsPerPage=5")
            for item in d.get("vulnerabilities", [])[:3]:
                line, cid, desc, sev = fmt_cve(item)
                print(line)
        except Exception:
            print(f"{Y}[!] rate limit NVD — attends 30 s{RST}"); break
    save_report("SCAN COMPLET", f"{hdr.strip()}")

TOOLS = [
    ("1", "RECHERCHE CVE", t_cve_search, "par mot-clé produit/techno"),
    ("2", "CISA KEV", t_kev, "failles activement exploitées (top 20 récentes)"),
    ("3", "BANNER GRAB", t_banner, "versions des services sur les ports ouverts"),
    ("4", "VERSION → CVE", t_version_match, "colle un banner, reçois les CVEs"),
    ("5", "TOP CVEs RÉCENTES", t_recent, "30 dernières, triées par CVSS"),
    ("6", "KEV PAR PRODUIT", t_kev_prod, "ton produit dans la liste d'exploitation"),
    ("7", "DÉTAIL D'UNE CVE", t_cve_detail, "description, CVSS, vecteur, références"),
    ("8", "SCAN COMPLET", t_full, "cible → banners → CVEs automatiquement"),
]

def menu():
    print(CLEAR)
    for line in SKULL.splitlines():
        print(CD + line)
    print()
    print(f"{B}{C}  ╔═══════════════════════════════════════════════╗{RST}")
    print(f"{B}{C}  ║   V U L N   T O O L  —  hacker_tool           ║{RST}")
    print(f"{B}{C}  ╚═══════════════════════════════════════════════╝{RST}")
    print(f"{DIM}       powered by Maxime Leal · cibles autorisées uniquement{RST}\n")
    if TARGET["ip"] or TARGET["domain"]:
        print(f"  {B}CIBLE :{RST} {W}{TARGET['domain'] or TARGET['ip']}{RST}\n")
    else:
        print(f"  {Y}Aucune cible — entre 'c'{RST}\n")
    for n, name, _, desc in TOOLS:
        print(f"  {B}{C}{n}{RST}  {W}{name:<24}{RST} {DIM}{desc}{RST}")
    print(f"  {B}{C}c{RST}  {'CHANGER / DÉFINIR LA CIBLE':<24}{RST}")
    print(f"  {B}{C}r{RST}  {'VOIR LE RAPPORT':<24}{RST}")
    print(f"  {B}{C}q{RST}  {'QUITTER':<24}{RST}")
    print()

def show_report():
    t = TARGET["domain"] or TARGET["ip"]
    path = os.path.join(RAPPORTS, f"vuln_{t.replace('.', '_')}.txt") if t else None
    print(CY + open(path).read()[-3000:] if path and os.path.exists(path) else f"{Y}aucun rapport{RST}")

def main():
    splash()
    while True:
        try:
            menu()
            c = input(f"{B}{C}vuln>{RST} ").strip().lower()
            if c == "q": break
            elif c == "c": ask_target()
            elif c == "r": show_report()
            else:
                tool = next((t for t in TOOLS if t[0] == c), None)
                if tool:
                    tool[2]()
                elif c:
                    print(f"{Y}choix inconnu{RST}")
            input(f"{DIM}↩︎ Entrée pour continuer…{RST}")
        except KeyboardInterrupt:
            print()
    print(f"{C}Au revoir — rapports dans rapports/{RST}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
