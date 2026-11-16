#!/usr/bin/env python3
# language: Python 3, file: snif_tool.py, target: macOS
# ═══════════════════════════════════════════════════════════════════
#  NET SNIFF — audit du réseau local · hacker_tool
#  powered by Maxime Leal
# ═══════════════════════════════════════════════════════════════════
import os, sys, subprocess, re, time, random, shutil, socket, threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gt_lib

ROOT = os.path.dirname(os.path.abspath(__file__))
RAPPORTS = os.path.join(ROOT, "rapports")
os.makedirs(RAPPORTS, exist_ok=True)

C   = "\033[38;2;230;230;235m"   # blanc
CD  = "\033[38;2;120;120;135m"
W   = "\033[97m"
G   = "\033[38;2;74;214;109m"
R   = "\033[38;2;255;70;70m"
Y   = "\033[93m"
CY  = "\033[96m"
DIM = "\033[2m"
B   = "\033[1m"
RST = "\033[0m"
CLEAR = "\033[2J\033[H"

LOGO = r"""
     ~ ~ ~ ~ ~ ~ ~ ~
    ~  N E T        ~
   ~      S N I F F  ~
    ~              ~
     ~ ~ ~ ~ ~ ~ ~ ~
"""

def matrix_rain(seconds=3.2, fps=16):
    cols, rows = shutil.get_terminal_size((80, 24))
    charset = "0123456789abcdef:.~, packetsYN"
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
    type_line("        N E T   S N I F F", C, .03)
    type_line("   audit du réseau local · hacker_tool", CD, .012)
    print()
    type_line("        ⚡ POWERED BY MAXIME LEAL ⚡", W, .02)
    time.sleep(.8)

def banner_title(txt):
    print(f"\n{B}{C}══════ {txt} ══════{RST}\n")

def save_report(name, content):
    path = os.path.join(RAPPORTS, "netsniff.txt")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*50}\n[{time.strftime('%d/%m/%Y %H:%M')}] {name}\n{'='*50}\n{content}\n")
    print(f"{DIM}[+] rapport : {path}{RST}")

def _pingable(ip):
    return ip if subprocess.run(["ping", "-c", "1", "-W", "1", ip], capture_output=True).returncode == 0 else None

def _base_ip():
    me = subprocess.run(["ipconfig", "getifaddr", "en0"], capture_output=True, text=True).stdout.strip() \
      or subprocess.run(["ipconfig", "getifaddr", "en1"], capture_output=True, text=True).stdout.strip()
    return me, ".".join(me.split(".")[:3]) if me else ""

def t_connections():
    banner_title("CONNEXIONS LIVE (diff toutes les 3 s — Ctrl+C pour stopper)")
    prev = set()
    first = True
    try:
        while True:
            out = subprocess.run(["lsof", "-i", "-n", "-P"], capture_output=True, text=True).stdout
            conns = set()
            for line in out.splitlines()[1:]:
                m = re.search(r"(\S+)\s+(\d+)\s+\S+\s+\S+\s+\S+\s+(?:IPv4|IPv6)\s+\S+TCP\s+([^>]+)>([^\s(]+)", line)
                if m:
                    proc, pid, src, dst = m.groups()
                    conns.add(f"{proc}({pid}) → {dst.strip()}")
            if first:
                print(f"{DIM}baseline : {len(conns)} connexions{RST}")
                prev = conns; first = False
            new = conns - prev
            if new:
                for n in sorted(new)[:12]:
                    print(f"  {R}▸ NOUVELLE{RST} {n}")
            gone = prev - conns
            if gone and not first:
                print(f"  {DIM}({len(gone)} connexions fermées){RST}")
            prev = conns
            time.sleep(3)
    except KeyboardInterrupt:
        print(f"\n{G}fin du live{RST}")

def t_arp():
    banner_title("TABLE ARP — qui est sur mon LAN")
    out = subprocess.run(["arp", "-a"], capture_output=True, text=True).stdout
    lines = [l for l in out.splitlines() if l.strip()]
    if not lines:
        print(f"{Y}table ARP vide (lance d'abord un ping sweep pour la remplir){RST}")
        me, base = _base_ip()
        if base:
            with threading.ThreadPoolExecutor(64) as ex:
                list(ex.map(_pingable, [f"{base}.{i}" for i in range(1, 255) if f"{base}.{i}" != me]))
            out = subprocess.run(["arp", "-a"], capture_output=True, text=True).stdout
            lines = [l for l in out.splitlines() if l.strip()]
    for l in lines: print(f"  {W}{l}{RST}")
    if lines: save_report("ARP", "\n".join(lines))

def t_traceroute():
    banner_title("TRACEROUTE")
    host = input(f"{B}{C}destination{RST} > ").strip()
    if not host: return
    out = subprocess.run(["traceroute", "-w", "1", "-q", "1", "-m", "20", host],
                         capture_output=True, text=True).stdout
    for l in out.splitlines():
        print(f"  {C}{l}{RST}")
    save_report("TRACEROUTE", out)

def t_listening():
    banner_title("PORTS EN ÉCOUTE + PROCESS")
    out = subprocess.run(["lsof", "-iTCP", "-sTCP:LISTEN", "-n", "-P"], capture_output=True, text=True).stdout
    seen = set()
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 9: continue
        proc, pid, port = parts[0], parts[1], parts[8]
        if port in seen: continue
        seen.add(port)
        risk = ""
        if re.search(r"python|nc|ncat", proc) and port not in ("*:8080", "*:9000"):
            risk = f"  {Y}← script ?{RST}"
        print(f"  {G}{proc:<18}{RST} PID {pid:<7} {CY}{port:<22}{RST}{risk}")
    save_report("LISTENING", "\n".join(sorted(seen)))

def t_sessions():
    banner_title("SESSIONS & UTILISATEURS")
    who = subprocess.run(["who"], capture_output=True, text=True).stdout
    print(f"{B}who :{RST}\n{who or '(vide)'}")
    last = subprocess.run(["last", "-10"], capture_output=True, text=True).stdout
    print(f"\n{B}10 dernières sessions :{RST}\n{last}")

def t_wifi():
    banner_title("WIFI — infos de la connexion")
    ssid = subprocess.run(["networksetup", "-getairportnetwork", "en0"],
                          capture_output=True, text=True).stdout
    print(f"{W}{ssid.strip()}{RST}")
    detail = subprocess.run(["networksetup", "-getinfo", "Wi-Fi"], capture_output=True, text=True).stdout
    print(detail)
    sec = subprocess.run(["ipconfig", "getsummary", "en0"], capture_output=True, text=True).stdout
    m = re.search(r"SSID\s*:\s*(\S+)", sec)
    if m: print(f"  SSID : {m.group(1)}")

def t_dnsconf():
    banner_title("CONFIGURATION DNS")
    out = subprocess.run(["scutil", "--dns"], capture_output=True, text=True).stdout
    servers = sorted(set(re.findall(r"nameserver\[0\]\s+: ([\d.]+)", out)))
    print(f"{B}serveurs DNS :{RST} {', '.join(servers)}")
    if servers and servers[0].startswith("127."):
        print(f"  {Y}⚠️ DNS local — VPN ou résolveur custom détecté{RST}")
    domains = sorted(set(re.findall(r"search domain\[0\]\s+: (\S+)", out)))
    print(f"{B}domaines de recherche :{RST} {', '.join(domains)}")
    save_report("DNS", f"servers: {servers}")


def t_lan_ports():
    banner_title("SCAN DE PORTS SUR LES HÔTES DU LAN")
    me, base = _base_ip()
    if not me: print(f"{R}[!] pas d'IP{RST}"); return
    with threading.ThreadPoolExecutor(64) as ex:
        alive = [x for x in ex.map(_pingable, [f"{base}.{i}" for i in range(1, 255) if f"{base}.{i}" != me]) if x]
    print(f"{DIM}{len(alive)} hôtes vivants{RST}")
    top = [21, 22, 80, 443, 445, 3306, 3389, 8080, 8443, 9000]
    for h in alive:
        open_p = []
        for p in top:
            try:
                with socket.create_connection((h, p), timeout=1): open_p.append(p)
            except Exception: continue
        print(f"  {C}{h:<16}{RST} {G}{', '.join(map(str, open_p)) or '—'}{RST}")
    save_report("LAN PORTS", f"{alive}")

def t_process_conns():
    banner_title("CONNEXIONS PAR PROCESS (qui parle le plus)")
    out = subprocess.run(["lsof", "-i", "-n", "-P"], capture_output=True, text=True).stdout
    procs = {}
    for line in out.splitlines()[1:]:
        p = line.split()[0]
        procs[p] = procs.get(p, 0) + 1
    for p, n in sorted(procs.items(), key=lambda x: -x[1])[:15]:
        print(f"  {C}{p:<20}{RST} {n} connexion(s)")

def t_firewall():
    banner_title("STATUT DU FIREWALL macOS")
    fw = "/usr/libexec/ApplicationFirewall/socketfilterfw"
    for flag, label in (("--getglobalstate", "état global"),
                        ("--getblockall", "bloque tout"),
                        ("--getallowsigned", "apps signées autorisées"),
                        ("--getstealthmode", "mode furtif")):
        out = subprocess.run([fw, flag], capture_output=True, text=True).stdout.strip()
        col = G if "activated" in out.lower() or "enabled" in out.lower() else Y
        print(f"  {col}{label:<26}{RST} {out.replace('( ', '').replace(')', '')}")

def t_arpwatch():
    banner_title("ARP WATCH (diff des MAC toutes les 5 s — Ctrl+C pour stopper)")
    prev = set(); first = True
    try:
        while True:
            out = subprocess.run(["arp", "-a"], capture_output=True, text=True).stdout
            macs = set(re.findall(r"at\s+([\w:]+)", out))
            if first: print(f"{DIM}baseline : {len(macs)} appareils{RST}"); prev = macs; first = False
            new = macs - prev
            for m in new: print(f"  {R}▸ NOUVELLE MAC{RST} {m}")
            for m in prev - macs: print(f"  {DIM}▸ MAC disparue : {m}{RST}")
            prev = macs; time.sleep(5)
    except KeyboardInterrupt:
        print(f"{G}fin du watch{RST}")

def t_bandwidth():
    banner_title("DÉBIT — compteurs d'interface (échantillon 5 s)")
    itf = "en0"
    def counters():
        out = subprocess.run(["netstat", "-I", itf, "-b"], capture_output=True, text=True).stdout
        line = out.splitlines()[1].split()
        return int(line[6]), int(line[9])
    rx0, tx0 = counters(); t0 = time.time(); time.sleep(5)
    rx1, tx1 = counters()
    dt = time.time() - t0
    print(f"  {G}réception{RST} {max(0,(rx1-rx0))/dt/1024:.0f} Ko/s")
    print(f"  {G}envoi{RST}     {max(0,(tx1-tx0))/dt/1024:.0f} Ko/s")

def t_traceroute_lan():
    banner_title("TRACEROUTE LOCAL")
    me, base = _base_ip()
    router = subprocess.run(["netstat", "-rn"], capture_output=True, text=True).stdout
    m = re.search(r"^default\s+([\d.]+)", router, re.M)
    if m:
        out = subprocess.run(["traceroute", "-w", "1", "-q", "1", "-m", "5", m.group(1)],
                             capture_output=True, text=True).stdout
        for l in out.splitlines(): print(f"  {C}{l}{RST}")

def t_pingmon():
    banner_title("PING MONITOR — latence vers une destination (Ctrl+C pour stopper)")
    host = input(f"{B}{C}destination [1.1.1.1]{RST} > ").strip() or "1.1.1.1"
    print(f"{DIM}latences en direct :{RST}")
    try:
        subprocess.run(["ping", host])
    except KeyboardInterrupt:
        print(f"{G}fin{RST}")

def t_wifi_near():
    banner_title("RÉSEAUX WIFI AUTOUR (system_profiler — lent ~20 s)")
    out = subprocess.run(["system_profiler", "SPAirPortDataType"], capture_output=True, text=True).stdout
    nets = re.findall(r"(\S.*?):\n\s+PHY Mode: (\S+)", out)
    seen = set()
    for name, phy in nets[:30]:
        if name in seen: continue
        seen.add(name)
        print(f"  {C}{name[:44]:<44}{RST} {G}{phy}{RST}")
    if not nets: print(f"{Y}aucun réseau listé{RST}")
    save_report("WIFI NEAR", ", ".join(f"{n} ({p})" for n, p in nets[:20]))

def t_dns_test():
    banner_title("TEST DNS — résolveur local vs 1.1.1.1 (détection de hijack)")
    domains = ["google.com", "facebook.com", "amazon.com", "apple.com"]
    for d in domains:
        local = subprocess.run(["dig", "+short", d], capture_output=True, text=True).stdout.strip()
        cloud = subprocess.run(["dig", "+short", d, "@1.1.1.1"], capture_output=True, text=True).stdout.strip()
        same = local.split()[0] == cloud.split()[0] if local and cloud else True
        print(f"  {C}{d:<16}{RST} local: {local.split()[0] if local else '—':<16} 1.1.1.1: {cloud.split()[0] if cloud else '—'} {'✅' if same else R + '⚠️ DIFFÉRENT' + RST}")

def t_interfaces():
    banner_title("INTERFACES RÉSEAU (ifconfig)")
    out = subprocess.run(["ifconfig"], capture_output=True, text=True).stdout
    blocks = out.split("\n\n")
    for b in blocks:
        name = b.split(":")[0] if ":" in b else ""
        if "inet " in b and "127.0.0.1" not in b:
            ip = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", b)
            mac = re.search(r"ether (\S+)", b)
            print(f"  {B}{C}{name:<8}{RST} {W}{ip.group(1) if ip else '—':<16}{RST} {DIM}MAC {mac.group(1) if mac else '—'}{RST}")

def t_risk_ports():
    banner_title("PORTS OUVERTS À RISQUE")
    out = subprocess.run(["lsof", "-iTCP", "-sTCP:LISTEN", "-n", "-P"], capture_output=True, text=True).stdout
    risky = {23: "telnet — en clair", 445: "SMB — worms le ciblent", 3389: "RDP",
             5900: "VNC", 6379: "Redis — souvent sans auth", 27017: "MongoDB",
             11211: "Memcached", 1433: "MSSQL", 1883: "MQTT sans TLS"}
    found = 0
    for line in out.splitlines()[1:]:
        m = re.search(r":(\d+)\s+\(LISTEN\)", line)
        if m and int(m.group(1)) in risky:
            print(f"  {R}{m.group(1):<6}{RST} {Y}{risky[int(m.group(1))]}{RST}  {DIM}{line.split()[0]}{RST}")
            found += 1
    if not found: print(f"{G}✅ aucun port à risque exposé{RST}")

def t_geo_conns():
    banner_title("GÉOLOCALISATION DES CONNEXIONS SORTANTES")
    out = subprocess.run(["lsof", "-i", "-n", "-P"], capture_output=True, text=True).stdout
    ips = set()
    for line in out.splitlines()[1:]:
        m = re.search(r"->(\d+\.\d+\.\d+\.\d+)", line)
        if m and not m.group(1).startswith(("192.168.", "10.", "127.", "172.")):
            ips.add(m.group(1))
    print(f"{DIM}{len(ips)} IP(s) distante(s){RST}")
    import urllib.request as ur
    for ip in sorted(ips)[:12]:
        try:
            req = ur.Request(f"http://ip-api.com/json/{ip}?fields=country,city,isp", headers={"User-Agent": UA_})
            with ur.urlopen(req, timeout=6) as r:
                j = json.loads(r.read())
            print(f"  {G}{ip:<16}{RST} {W}{j.get('country','?'):<12}{RST} {DIM}{j.get('city','')}{RST} · {j.get('isp','')[:30]}")
        except Exception: continue

def t_snapshot():
    banner_title("SNAPSHOT COMPLET — tout en un rapport")
    for fn in (t_listening, t_arp, t_sessions, t_interfaces, t_dnsconf, t_firewall, t_risk_ports):
        try: fn()
        except Exception as e: print(f"{DIM}[{fn.__name__}: {e}]{RST}")

TOOLS = [
    ("1", "CONNEXIONS LIVE", t_connections, "nouvelles connexions sortantes en temps réel"),
    ("2", "TABLE ARP", t_arp, "les voisins du réseau avec leurs MAC"),
    ("3", "TRACEROUTE", t_traceroute, "le chemin jusqu'à une destination"),
    ("4", "PORTS EN ÉCOUTE", t_listening, "ports ouverts + process propriétaires"),
    ("5", "SESSIONS", t_sessions, "who + 10 dernières sessions"),
    ("6", "INFOS WIFI", t_wifi, "SSID, sécurité, configuration"),
    ("7", "CONFIG DNS", t_dnsconf, "résolveurs utilisés, domaines de recherche"),
    ("a", "PORTS DU LAN", t_lan_ports, "scan des top ports sur chaque hôte du wifi"),
    ("b", "CONNEXIONS/PROCESS", t_process_conns, "quelles apps parlent le plus"),
    ("c", "FIREWALL macOS", t_firewall, "global · furtif · apps signées"),
    ("d", "ARP WATCH", t_arpwatch, "nouvelles/disparues MAC en live"),
    ("e", "DÉBIT LIVE", t_bandwidth, "réception/envoi en Ko/s"),
    ("f", "TRACEROUTE LAN", t_traceroute_lan, "le chemin jusqu'au routeur"),
    ("g", "PING MONITOR", t_pingmon, "latence en continu"),
    ("h", "WIFI AUTOUR", t_wifi_near, "les réseaux voisins + sécurité"),
    ("i", "TEST DNS HIJACK", t_dns_test, "résolveur local vs 1.1.1.1"),
    ("j", "INTERFACES", t_interfaces, "IP et MAC de chaque interface"),
    ("k", "PORTS À RISQUE", t_risk_ports, "les exposés classiquement dangereux"),
    ("l", "GÉO CONNEXIONS", t_geo_conns, "pays des IP distantes"),
    ("m", "SNAPSHOT COMPLET", t_snapshot, "tout le dossier en un rapport"),
]

def menu():
    print(CLEAR)
    for line in LOGO.splitlines():
        print(CD + line)
    print()
    print(f"{B}{C}  ╔═══════════════════════════════════════════════╗{RST}")
    print(f"{B}{C}  ║   N E T   S N I F F  —  hacker_tool           ║{RST}")
    print(f"{B}{C}  ╚═══════════════════════════════════════════════╝{RST}")
    print(f"{DIM}       powered by Maxime Leal · audit de TON réseau{RST}\n")
    for n, name, _, desc in TOOLS:
        print(f"  {B}{C}{n}{RST}  {W}{name:<26}{RST} {DIM}{desc}{RST}")
    print(f"  {B}{C}r{RST}  {'VOIR LE RAPPORT':<26}{RST}")
    print(f"  {B}{H}{RST}  {'RAPPORT HTML → .html':<26}{RST}")
    print(f"  {B}{C}q{RST}  {'QUITTER':<26}{RST}")
    print()

def show_report():
    p = os.path.join(RAPPORTS, "netsniff.txt")
    print(CY + open(p).read()[-2000:] if os.path.exists(p) else f"{Y}aucun rapport{RST}")

def t_html():
    out = gt_lib.html_report(os.path.join(RAPPORTS, "netsniff.txt"), "NET SNIFF", os.path.join(RAPPORTS, "netsniff.html"), accent="#e8e8e8")
    print(f"{G}✓ rapport HTML : {out}{RST}" if out else f"{Y}aucun rapport à convertir{RST}")

def main():
    splash()
    while True:
        try:
            menu()
            c = input(f"{B}{C}sniff>{RST} ").strip().lower()
            if c == "q": break
            elif c == "r": show_report()
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
