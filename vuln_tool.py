#!/usr/bin/env python3
# language: Python 3, file: vuln_tool.py, target: macOS
# ═══════════════════════════════════════════════════════════════════
#  VULN TOOL — radar de vulnérabilités · hacker_tool
#  powered by Maxime Leal
# ═══════════════════════════════════════════════════════════════════
#  Usage : python3 vuln_tool.py
import os, sys, subprocess, re, json, time, random, socket, shutil, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gt_lib

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
H   = "\033[97m"   # blanc H-option
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
    return gt_lib.http_get(url, timeout=timeout, as_json=True, retries=4)

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


# ─────────────────────── BOOST — les 12 nouveaux ───────────────────────
def t_kev_search():
    banner_title("KEV PAR MOT-CLÉ")
    kw = input(f"{B}{C}mot-clé (produit/vendeur){RST} > ").strip().lower()
    if not kw: return
    try:
        d = http_get(KEV)
        hits = [v for v in d.get("vulnerabilities", []) if kw in (v.get("product","")+v.get("vendorProject","")+v.get("shortDescription","")).lower()]
        print(f"\n{B}{len(hits)} faille(s) KEV pour '{kw}' :{RST}\n")
        for v in hits[:25]:
            rw = " 🔒" if v.get("knownRansomwareUse") == "Known" else ""
            print(f"{B}{R}{v['cveID']:<16}{RST} {CY}{v.get('product','')[:30]:<30}{RST} {DIM}{v.get('dateAdded','')}{RST}{rw}")
        save_report("KEV SEARCH", f"{kw}: {len(hits)}")
    except Exception as e:
        print(f"{R}[!] {e}{RST}")

def t_ransom_kev():
    banner_title("FAILLES KEV UTILISÉES PAR LES RANSOMWARES")
    try:
        d = http_get(KEV)
        rw = [v for v in d.get("vulnerabilities", []) if v.get("knownRansomwareUse") == "Known"]
        rw.sort(key=lambda v: v.get("dateAdded", ""), reverse=True)
        print(f"{B}{len(rw)} failles utilisées par des ransomwares :{RST}\n")
        for v in rw[:25]:
            print(f"{B}{R}{v['cveID']:<16}{RST} {CY}{v.get('vendorProject','')}/{v.get('product','')[:26]:<26}{RST} {DIM}{v.get('dateAdded','')}{RST}")
        save_report("RANSOM KEV", f"{len(rw)} failles")
    except Exception as e:
        print(f"{R}[!] {e}{RST}")

def t_cve_new30():
    banner_title("CVEs DES 30 DERNIERS JOURS (NVD)")
    import datetime
    end = datetime.datetime.now(datetime.timezone.utc)
    start = end - datetime.timedelta(days=30)
    fmt = "%Y-%m-%dT%H:%M:%S.000"
    try:
        d = http_get(f"{NVD}?pubStartDate={start.strftime(fmt)}&pubEndDate={end.strftime(fmt)}&resultsPerPage=30")
        vulns = []
        for item in d.get("vulnerabilities", []):
            line, cid, desc, sev = fmt_cve(item)
            vulns.append((cvss_of(item.get("cve", {}))[0] or 0, line))
        vulns.sort(reverse=True)
        for _, line in vulns: print(line)
    except Exception as e:
        print(f"{R}[!] {e.__class__.__name__}{RST}")

def t_cwe_top():
    banner_title("CWE LES PLUS FRÉQUENTES (failles récentes)")
    try:
        d = http_get(f"{NVD}?resultsPerPage=50")
        cwes = {}
        for item in d.get("vulnerabilities", []):
            for w in item.get("cve", {}).get("weaknesses", []):
                for x in w.get("description", []):
                    val = x.get("value", "")
                    if val.startswith("CWE"): cwes[val] = cwes.get(val, 0) + 1
        for val, n in sorted(cwes.items(), key=lambda x: -x[1])[:12]:
            print(f"  {C}{val:<14}{RST} ×{n}")
    except Exception as e:
        print(f"{R}[!] {e.__class__.__name__}{RST}")

def t_exploit_links():
    banner_title("LIENS EXPLOIT POUR UNE CVE")
    cid = input(f"{B}{C}CVE-ID{RST} > ").strip().upper()
    if not cid: return
    num = cid.replace("CVE-", "")
    links = [
        ("NVD", f"https://nvd.nist.gov/vuln/detail/{cid}"),
        ("Exploit-DB", f"https://www.exploit-db.com/search?cve={num}"),
        ("Nuclei templates", f"https://github.com/search?q=repo%3Aprojectdiscovery%2Fnuclei-templates+{cid}&type=code"),
        ("Metasploit modules", f"https://github.com/search?q=repo%3Arapid7%2Fmetasploit-framework+{cid}&type=code"),
        ("GitHub PoCs", f"https://github.com/search?q={cid}+poc&type=repositories"),
        ("Google", f"https://www.google.com/search?q=%22{cid}%22+exploit"),
        ("Shodan (cibles publiques)", f"https://www.shodan.io/search?query=%22{cid}%22"),
    ]
    for name, url in links:
        print(f"  {G}▸ {name:<24}{RST} {CY}{url}{RST}")
    save_report("EXPLOIT LINKS", f"{cid}")

def t_lan_sweep():
    banner_title("BANNER SWEEP — versions sur tout le LAN")
    me = subprocess.run(["ipconfig", "getifaddr", "en0"], capture_output=True, text=True).stdout.strip() \
      or subprocess.run(["ipconfig", "getifaddr", "en1"], capture_output=True, text=True).stdout.strip()
    if not me: print(f"{R}[!] pas d'IP locale{RST}"); return
    base = ".".join(me.split(".")[:3])
    def alive(i):
        ip = f"{base}.{i}"
        return ip if subprocess.run(["ping", "-c", "1", "-W", "1", ip], capture_output=True).returncode == 0 else None
    with ThreadPoolExecutor(64) as ex:
        hosts = [x for x in ex.map(alive, range(1, 255)) if x]
    print(f"{DIM}{len(hosts)} hôtes vivants{RST}")
    for h in hosts:
        for p in (22, 80, 443, 8080):
            try:
                with socket.create_connection((h, p), timeout=1.5) as s:
                    s.settimeout(1.5)
                    if p in (80, 8080, 443): s.send(b"GET / HTTP/1.0\r\n\r\n")
                    b = s.recv(200).decode("latin1", "ignore").strip()
                if b:
                    print(f"  {C}{h:<16}{RST} {CY}{p:<6}{RST} {W}{b.splitlines()[0][:90] if chr(10) in b or chr(13) in b else b[:90]}{RST}")
            except Exception: continue

def t_ssl_scan():
    banner_title("SSL SCAN MULTI-PORTS")
    d = TARGET["domain"] or TARGET["ip"]
    if not d: print(f"{Y}[!] cible requise{RST}"); return
    for port in (443, 8443, 4443):
        try:
            out = subprocess.run(["openssl", "s_client", f"-connect", f"{d}:{port}", "-brief"],
                                 capture_output=True, text=True, input="", timeout=10)
            proto = re.search(r"Protocol version: (\S+)", out.stderr + out.stdout)
            cipher = re.search(r"Cipher\s*:\s*(\S+)", out.stderr + out.stdout)
            print(f"  {CY}:{port}{RST}  {G}{proto.group(1) if proto else 'TLS?'}{RST} / {W}{cipher.group(1) if cipher else '?'}{RST}")
            for v in ("tls1", "tls1_1"):
                r2_ = subprocess.run(["openssl", "s_client", f"-{v}", f"-connect", f"{d}:{port}", "-brief"],
                                     capture_output=True, text=True, input="", timeout=8)
                if "CONNECTION ESTABLISHED" in (r2_.stderr + r2_.stdout):
                    print(f"  {R}⚠️ {v} accepté sur :{port} — obsolète, risqué{RST}")
        except Exception:
            print(f"  {DIM}:{port} fermé/absent{RST}")

def t_hosts_audit():
    banner_title("AUDIT /etc/hosts")
    p = "/etc/hosts"
    if not os.path.exists(p): return
    sus = []
    for line in open(p).read().splitlines():
        line = line.strip()
        if not line or line.startswith("#"): continue
        parts = line.split()
        if parts[0] not in ("127.0.0.1", "::1", "255.255.255.255", "fe80::1%lo0"):
            sus.append(line)
    if sus:
        print(f"{B}{R}{len(sus)} entrée(s) NON-standards :{RST}")
        for l in sus: print(f"  {Y}{l}{RST}")
        print(f"{DIM}→ un domaine redirigé localement ? signature de redirection manuelle{RST}")
    else:
        print(f"{G}✅ /etc/hosts propre (que les entrées par défaut){RST}")
    save_report("HOSTS", "\n".join(sus) or "propre")

def t_dns_audit():
    banner_title("AUDIT DNS EXPRESS")
    d = TARGET["domain"]
    if not d: print(f"{Y}[!] domaine requis{RST}"); return
    spf = subprocess.run(["dig", "+short", "TXT", d], capture_output=True, text=True).stdout
    print(f"  {'✅' if 'v=spf1' in spf else '❌'} SPF")
    dm = subprocess.run(["dig", "+short", "TXT", f"_dmarc.{d}"], capture_output=True, text=True).stdout.strip()
    print(f"  {'✅' if dm else '❌'} DMARC {'· ' + dm[:60] if dm else ''}")
    dk = subprocess.run(["dig", "+short", "TXT", f"google._domainkey.{d}"], capture_output=True, text=True).stdout.strip()
    print(f"  {'✅' if dk else '❌'} DKIM (google)")
    dnssec = subprocess.run(["dig", "+short", "DNSKEY", d], capture_output=True, text=True).stdout.strip()
    print(f"  {'✅' if dnssec else '❌'} DNSSEC")
    for n in subprocess.run(["dig", "+short", "NS", d], capture_output=True, text=True).stdout.split()[:3]:
        r_ = subprocess.run(["dig", "AXFR", d, "@" + n], capture_output=True, text=True, timeout=10).stdout
        if "Transfer failed" not in r_ and len([l for l in r_.splitlines() if l.strip()]) > 2:
            print(f"  {R}⚠️ AXFR possible sur {n} !{RST}")
    save_report("DNS AUDIT", d)

def t_executive():
    banner_title("RÉSUMÉ EXÉCUTIF — tous les rapports de la cible")
    t = TARGET["domain"] or TARGET["ip"]
    if not t: print(f"{Y}[!] cible requise{RST}"); return
    path = os.path.join(RAPPORTS, f"vuln_{t.replace('.', '_')}.txt")
    if not os.path.exists(path): print(f"{Y}aucun rapport pour {t}{RST}"); return
    content = open(path).read()
    sections = content.count("=" * 50)
    cves = set(re.findall(r"CVE-\d{4}-\d{4,7}", content))
    print(f"{B}CIBLE :{RST} {t}")
    print(f"  {G}sections de scan{RST} : {sections}")
    print(f"  {G}CVEs uniques citées{RST} : {len(cves)}")
    if cves:
        for c in sorted(cves)[:20]: print(f"    {R}{c}{RST}")
    print(f"\n{DIM}{content[-800:]}{RST}")

def t_kev_diff():
    banner_title("KEV DIFF — les nouvelles depuis le dernier passage")
    sp = os.path.join(RAPPORTS, "kev_ids.json")
    try:
        d = http_get(KEV)
        ids = {v.get("cveID"): v for v in d.get("vulnerabilities", [])}
        old = set(json.load(open(sp))) if os.path.exists(sp) else None
        if old is None:
            print(f"{DIM}baseline établie : {len(ids)} failles (les prochaines exécutions montreront les nouvelles){RST}")
        else:
            new = [i for i in ids if i not in old]
            print(f"{B}{len(new)} NOUVELLE(S) faille(s) KEV :{RST}\n")
            for i in sorted(new)[:20]:
                v = ids[i]
                print(f"{B}{R}{i:<16}{RST} {CY}{v.get('product','')[:30]:<30}{RST} {DIM}{v.get('dateAdded','')}{RST}")
        json.dump(sorted(ids), open(sp, "w"))
        save_report("KEV DIFF", f"catalogue: {len(ids)}")
    except Exception as e:
        print(f"{R}[!] {e}{RST}")

def t_links():
    banner_title("LIENS UTILES POUR LA CIBLE")
    t = TARGET["domain"] or TARGET["ip"]
    if not t: print(f"{Y}[!] cible requise{RST}"); return
    links = [
        ("Shodan (exposés)", f"https://www.shodan.io/search?query=hostname%3A{t}"),
        ("Censys", f"https://search.censys.io/hosts?q={t}"),
        ("VirusTotal", f"https://www.virustotal.com/gui/domain/{t}"),
        ("Wayback", f"https://web.archive.org/web/*/{t}"),
        ("crt.sh (certs)", f"https://crt.sh/?q=%25.{t}"),
        ("Netcraft", f"https://sitedossier.com/site/{t}"),
        ("URLScan", f"https://urlscan.io/domain/{t}"),
        ("DNSDumpster", f"https://dnsdumpster.com/"),
    ]
    for name, url in links:
        print(f"  {G}▸ {name:<22}{RST} {CY}{url}{RST}")
    save_report("LINKS", f"{t}")

TOOLS = [
    ("1", "RECHERCHE CVE", t_cve_search, "par mot-clé produit/techno"),
    ("2", "CISA KEV", t_kev, "failles activement exploitées (top 20 récentes)"),
    ("3", "BANNER GRAB", t_banner, "versions des services sur les ports ouverts"),
    ("4", "VERSION → CVE", t_version_match, "colle un banner, reçois les CVEs"),
    ("5", "TOP CVEs RÉCENTES", t_recent, "30 dernières, triées par CVSS"),
    ("6", "KEV PAR PRODUIT", t_kev_prod, "ton produit dans la liste d'exploitation"),
    ("7", "DÉTAIL D'UNE CVE", t_cve_detail, "description, CVSS, vecteur, références"),
    ("8", "SCAN COMPLET", t_full, "cible → banners → CVEs automatiquement"),
    ("a", "KEV PAR MOT-CLÉ", t_kev_search, "dans les failles activement exploitées"),
    ("b", "RANSOMWARE KEV", t_ransom_kev, "failles utilisées par les ransomwares"),
    ("c", "CVE 30 JOURS", t_cve_new30, "les nouvelles de ce mois, triées CVSS"),
    ("d", "CWE TOP", t_cwe_top, "les types de failles les plus fréquents"),
    ("e", "LIENS EXPLOIT", t_exploit_links, "NVD · Exploit-DB · Nuclei · Metasploit · PoCs"),
    ("f", "BANNER SWEEP LAN", t_lan_sweep, "versions de services sur tout ton réseau"),
    ("g", "SSL SCAN", t_ssl_scan, "443/8443/4443 + protocoles obsolètes"),
    ("h", "AUDIT /etc/hosts", t_hosts_audit, "redirections locales suspectes"),
    ("i", "AUDIT DNS", t_dns_audit, "SPF/DMARC/DKIM/DNSSEC/AXFR express"),
    ("j", "RÉSUMÉ EXÉCUTIF", t_executive, "compile tous tes rapports de la cible"),
    ("k", "KEV DIFF", t_kev_diff, "les NOUVELLES failles depuis le dernier passage"),
    ("l", "LIENS UTILES", t_links, "shodan · censys · virustotal · wayback · urlscan"),
]

def menu():
    print(CLEAR)
    for line in SKULL.splitlines():
        print(CD + line)
    print()
    print(gt_lib.bigtext("VULN", C))
    print(f"{DIM}       powered by Maxime Leal · cibles autorisées uniquement{RST}\n")
    if TARGET["ip"] or TARGET["domain"]:
        print(f"  {B}CIBLE :{RST} {W}{TARGET['domain'] or TARGET['ip']}{RST}\n")
    else:
        print(f"  {Y}Aucune cible — entre 'c'{RST}\n")
    for n, name, _, desc in TOOLS:
        print(f"  {B}{C}{n}{RST}  {W}{name:<24}{RST} {DIM}{desc}{RST}")
    print(f"  {B}{C}c{RST}  {'CHANGER / DÉFINIR LA CIBLE':<24}{RST}")
    print(f"  {B}{C}r{RST}  {'VOIR LE RAPPORT':<24}{RST}")
    print(f"  {B}{H}{RST}  {'RAPPORT HTML → .html':<24}{RST}")
    print(f"  {B}{C}q{RST}  {'QUITTER':<24}{RST}")
    print()

def show_report():
    t = TARGET["domain"] or TARGET["ip"]
    path = os.path.join(RAPPORTS, f"vuln_{t.replace('.', '_')}.txt") if t else None
    print(CY + open(path).read()[-3000:] if path and os.path.exists(path) else f"{Y}aucun rapport{RST}")

def t_html():
    t = TARGET["domain"] or TARGET["ip"]
    if not t: print(f"{Y}[!] cible requise{RST}"); return
    src = os.path.join(RAPPORTS, f"vuln_{t.replace('.', '_')}.txt")
    out = gt_lib.html_report(src, f"VULN — {t}", src.replace(".txt", ".html"), accent="#ff2a2a")
    print(f"{G}✓ rapport HTML : {out}{RST}")

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
