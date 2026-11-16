#!/usr/bin/env python3
# language: Python 3, file: snif_tool.py, target: macOS
# ═══════════════════════════════════════════════════════════════════
#  NET SNIFF — audit du réseau local · hacker_tool
#  powered by Maxime Leal
# ═══════════════════════════════════════════════════════════════════
import os, sys, subprocess, re, time, random, shutil, socket, threading

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

TOOLS = [
    ("1", "CONNEXIONS LIVE", t_connections, "nouvelles connexions sortantes en temps réel"),
    ("2", "TABLE ARP", t_arp, "les voisins du réseau avec leurs MAC"),
    ("3", "TRACEROUTE", t_traceroute, "le chemin jusqu'à une destination"),
    ("4", "PORTS EN ÉCOUTE", t_listening, "ports ouverts + process propriétaires"),
    ("5", "SESSIONS", t_sessions, "who + 10 dernières sessions"),
    ("6", "INFOS WIFI", t_wifi, "SSID, sécurité, configuration"),
    ("7", "CONFIG DNS", t_dnsconf, "résolveurs utilisés, domaines de recherche"),
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
    print(f"  {B}{C}q{RST}  {'QUITTER':<26}{RST}")
    print()

def show_report():
    p = os.path.join(RAPPORTS, "netsniff.txt")
    print(CY + open(p).read()[-2000:] if os.path.exists(p) else f"{Y}aucun rapport{RST}")

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
