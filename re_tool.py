#!/usr/bin/env python3
# language: Python 3, file: re_tool.py, target: macOS
# ═══════════════════════════════════════════════════════════════════
#  RE TOOL — reverse engineering · hacker_tool
#  powered by Maxime Leal
# ═══════════════════════════════════════════════════════════════════
#  Analyse STATIQUE uniquement — radare2 embarque. Rien n'est exécuté.
import os, sys, subprocess, re, json, time, random, shutil, hashlib, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gt_lib

ROOT = os.path.dirname(os.path.abspath(__file__))
RAPPORTS = os.path.join(ROOT, "rapports")
os.makedirs(RAPPORTS, exist_ok=True)

C   = "\033[38;2;255;62;165m"   # magenta
CD  = "\033[38;2;130;25;95m"
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

SAMPLE = {"path": ""}

LOGO = r"""
    ____________________
   |  __________________|
  _|  |   RE  ENGINE
 |_   |   ______________
   |  |  /              /
   |  |  \_____________/
   |__|  RE TOOL · magenta
"""

def matrix_rain(seconds=3.2, fps=16):
    cols, rows = shutil.get_terminal_size((80, 24))
    charset = "MOV PUSH XOR JMP 0x1A2B3CRET CALL"
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
    type_line("        R E   T O O L", C, .03)
    type_line("   reverse engineering · radare2 embarqué · hacker_tool", CD, .012)
    print()
    type_line("        ⚡ POWERED BY MAXIME LEAL ⚡", W, .02)
    time.sleep(.8)

def banner_title(txt):
    print(f"\n{B}{C}══════ {txt} ══════{RST}")
    if SAMPLE["path"]:
        print(f"{DIM}échantillon : {W}{os.path.basename(SAMPLE['path'])}{RST}")
    print()

def save_report(name, content):
    p = SAMPLE["path"] or "session"
    path = os.path.join(RAPPORTS, f"re_{os.path.basename(p)}.txt")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*50}\n[{time.strftime('%d/%m/%Y %H:%M')}] {name}\n{'='*50}\n{content}\n")
    print(f"{DIM}[+] rapport : {path}{RST}")

def need_sample():
    if not SAMPLE["path"]:
        print(f"{Y}[!] charge d'abord un échantillon (option 0){RST}")
        return False
    return os.path.exists(SAMPLE["path"])

def r2(cmd):
    """passe une commande à radare2 — mode silencieux"""
    return subprocess.run(["r2", "-q", "-c", cmd, SAMPLE["path"]],
                          capture_output=True, text=True, timeout=60).stdout

def entropy(data):
    if not data: return 0.0
    freq = {}
    for b in data: freq[b] = freq.get(b, 0) + 1
    n = len(data)
    return -sum((c/n) * math.log2(c/n) for c in freq.values())

# ─────────────────────────── LES TOOLS ───────────────────────────
def t_load():
    banner_title("CHARGER UN ÉCHANTILLON")
    p = input(f"{B}{C}chemin du fichier{RST} > ").strip().strip('"').strip("'")
    p = os.path.expanduser(p)
    if not os.path.exists(p):
        print(f"{R}fichier introuvable{RST}"); return False
    SAMPLE["path"] = p
    size = os.path.getsize(p)
    print(f"{G}✓ chargé{RST} {os.path.basename(p)}  {DIM}({size:,} octets){RST}")
    return True

def t_analyze():
    banner_title("ANALYSE RAPIDE")
    if not need_sample(): return
    data = open(SAMPLE["path"], "rb").read()
    magic = data[:8].hex()
    ftype = ("PE Windows (exe/dll)" if data[:2] == b"MZ"
             else "ELF Linux" if data[:4] == b"\x7fELF"
             else "Mach-O macOS" if data[:4] in (b"\xcf\xfa\xed\xfe", b"\xca\xfe\xba\xbe")
             else "PDF" if data[:5] == b"%PDF-"
             else "ZIP/Office" if data[:4] == b"PK\x03\x04"
             else "Inconnu")
    ent = entropy(data[:2_000_000])
    print(f"  {G}type{RST}      : {W}{ftype}{RST}")
    print(f"  {G}taille{RST}    : {len(data):,} octets")
    print(f"  {G}entropie{RST}  : {ent:.2f} {'⚠️ packé/chiffré probable' if ent > 7.4 else ''}")
    print(f"  {G}md5{RST}       : {hashlib.md5(data).hexdigest()}")
    print(f"  {G}sha256{RST}    : {hashlib.sha256(data).hexdigest()}")
    if ftype.startswith("PE"):
        m = re.search(rb"(mb |Compiled|Rich)", data)
        # signature UPX
        if b"UPX!" in data: print(f"  {R}⚠️ UPX détecté — packé{RST}")
    print(f"\n{DIM}radare2 voit :{RST}")
    info = r2("iI~format,arch,bits,lang,compiler")
    print("  " + info.replace("\n", "\n  ")[:400] if info.strip() else "  (r2 n'a pas identifié)")
    save_report("ANALYSE", f"type={ftype} entropy={ent}")

def t_info():
    banner_title("INFOS RADARE2 (iI)")
    if not need_sample(): return
    print(r2("iI")[:3000])

def t_sections():
    banner_title("SECTIONS + ENTROPIE (iS)")
    if not need_sample(): return
    out = r2("iS~?,")
    data = open(SAMPLE["path"], "rb").read()
    for line in out.splitlines()[:25]:
        print(f"  {C}{line}{RST}")
    high = [s for s in out.splitlines() if re.search(r"upd,.*,\d", s)]
    save_report("SECTIONS", out[:1500])

def t_strings():
    banner_title("STRINGS FILTRÉES (les intéressantes)")
    if not need_sample(): return
    data = open(SAMPLE["path"], "rb").read()
    strings = re.findall(rb"[\x20-\x7e]{8,}", data[:3_000_000])
    strlist = [s.decode("latin1") for s in strings]
    cats = {
        "URLs": [s for s in strlist if re.search(r"https?://", s)],
        "IPs": [s for s in strlist if re.search(r"\b\d{1,3}(\.\d{1,3}){3}\b", s)],
        "Chemins Windows": [s for s in strlist if re.search(r"[A-Z]:\\\\|C:/|System32", s)],
        "Registre": [s for s in strlist if re.search(r"HKEY_|CurrentVersion", s)],
        "Suspices": [s for s in strlist if re.search(r"password|token|key|secret|hook|inject|persis|http", s, re.I)],
    }
    for cat, items in cats.items():
        uniq = list(dict.fromkeys(items))[:12]
        print(f"\n{B}{CY}{cat} ({len(items) if items else 0}) :{RST}")
        for s in uniq: print(f"  {G}▸ {RST}{s[:120]}")
    save_report("STRINGS", "\n".join(sum(cats.values(), [])[:60]))

def t_imports():
    banner_title("IMPORTS / LIBRAIRIES")
    if not need_sample(): return
    if sys.platform == "darwin":
        out = subprocess.run(["otool", "-L", SAMPLE["path"]], capture_output=True, text=True).stdout
        if "not an object file" not in out and out.strip():
            print(f"{W}{out[:2500]}{RST}")
            save_report("IMPORTS", out[:2500]); return
    # fallback radare2
    out = r2("ii")
    print(out[:3500] if out.strip() else f"{Y}imports non lisibles par r2/otool{RST}")
    save_report("IMPORTS", out[:3500])

def t_symbols():
    banner_title("SYMBOLES / FONCTIONS")
    if not need_sample(): return
    out = r2("is~sym")
    print(out[:3500] if out.strip() else f"{Y}pas de symboles (stripped) — normal pour un binaire de prod{RST}")
    save_report("SYMBOLS", out[:3500])

def t_functions():
    banner_title("ANALYSE DES FONCTIONS (aaa + afl)")
    if not need_sample(): return
    print(f"{DIM}r2 analyse… (peut prendre quelques secondes){RST}")
    out = r2("aaa; afl~?,")
    n = out.strip()
    out2 = r2("aaa; afl")
    lines = out2.splitlines()
    print(f"{B}{len(lines)} fonctions détectées{RST}\n")
    for l in lines[:30]: print(f"  {C}{l}{RST}")
    save_report("FUNCTIONS", "\n".join(lines[:60]))

def t_disasm():
    banner_title("DÉSASSEMBLAGE D'UNE FONCTION")
    if not need_sample(): return
    fn = input(f"{DIM}nom ou adresse (défaut: entry0) {RST}> ").strip() or "entry0"
    out = r2(f"aaa; pdf @ {fn}")
    if out.strip():
        print(f"{W}{out[:6000]}{RST}")
        save_report("DISASM", out[:6000])
    else:
        print(f"{Y}fonction introuvable — utilise l'option 6 pour lister{RST}")

def t_decompile():
    banner_title("PSEUDO-DÉCOMPILATION (pdc)")
    if not need_sample(): return
    fn = input(f"{DIM}fonction (défaut: entry0){RST} > ").strip() or "entry0"
    out = r2(f"aaa; pdc @ {fn}")
    if out.strip():
        print(f"{W}{out[:6000]}{RST}")
        save_report("PDC", out[:6000])
    else:
        print(f"{Y}pas de pseudo-code dispo pour cette fonction{RST}")

def t_console():
    banner_title("CONSOLE R2 LIBRE — tape tes commandes (exit pour sortir)")
    if not need_sample(): return
    print(f"{DIM}exemples : iI · iS · afl · pdf @ main · iz~http · is~imports · quit{RST}")
    while True:
        cmd = input(f"{B}{C}r2>{RST} ").strip()
        if cmd in ("quit", "q", "exit"): break
        if not cmd: continue
        try:
            out = r2(cmd)
            print(f"{W}{out[:5000]}{RST}")
        except Exception as e:
            print(f"{R}[!] {e}{RST}")

def t_packed():
    banner_title("DÉTECTION DE PACKING")
    if not need_sample(): return
    data = open(SAMPLE["path"], "rb").read()
    checks = []
    if b"UPX!" in data: checks.append(("UPX", R))
    for sig, name in ((b"UPX!", "UPX"), (b"PECompact", "PECompact"), (b"Themida", "Themida"),
                      (b"MPRESS", "MPRESS"), (b".aspack", "ASPack")):
        if sig in data: print(f"  {R}⚠️ signature {name} détectée{RST}")
    data_sample = data[:2_000_000]
    ent = entropy(data_sample)
    print(f"  {G}entropie globale{RST} : {ent:.2f}")
    if ent > 7.4: print(f"  {R}⚠️ entropie élevée — probablement packé ou chiffré{RST}")
    if not checks: print(f"  {G}pas de signature de packer connue{RST}")
    save_report("PACKING", f"entropy={ent}")


def t_overlays():
    banner_title("OVERLAY PE & FICHIERS INCRUSTÉS")
    if not need_sample(): return
    data = open(SAMPLE["path"], "rb").read()
    if data[:2] == b"MZ":
        import struct
        e_lfanew = struct.unpack("<I", data[0x3C:0x40])[0]
        coff = e_lfanew + 4
        nsec = struct.unpack("<H", data[coff+2:coff+4])[0]
        optsz = struct.unpack("<H", data[coff+16:coff+18])[0]
        maxend = 0
        for i in range(nsec):
            o = coff + 20 + optsz + i * 40
            rsz, roff = struct.unpack("<II", data[o+16:o+24])
            if roff and rsz: maxend = max(maxend, roff + rsz)
        overlay = len(data) - maxend
        print(f"  {G}fin des sections{RST} : {maxend:,} o")
        print(f"  {G}overlay{RST} : {overlay:,} o {'⚠️ données cachées après les sections ?' if overlay > 1024 else ''}")
    else:
        print(f"{DIM}overlay = PE uniquement{RST}")

def t_izz():
    banner_title("STRINGS + OFFSETS (izz)")
    if not need_sample(): return
    out = r2("izz~http")
    if out.strip():
        print(f"{B}URLs avec offsets :{RST}\n{out[:3000]}")
        save_report("IZZ", out[:3000])
    else:
        print(f"{Y}aucune URL{RST}")

def t_hexdump():
    banner_title("HEXDUMP (px)")
    if not need_sample(): return
    off = input(f"{DIM}offset (défaut 0x0){RST} > ").strip() or "0x0"
    print(f"{W}{r2('px 512 @ ' + off)[:3000]}{RST}")

def t_diffbin():
    banner_title("DIFF DE DEUX BINAIRES")
    if not need_sample(): return
    p2 = input(f"{DIM}2e fichier{RST} > ").strip().strip('"')
    if not os.path.exists(os.path.expanduser(p2)):
        print(f"{R}introuvable{RST}"); return
    def strs(p):
        data = open(p, "rb").read()
        return {x.decode('latin1') for x in re.findall(rb"[\x20-\x7e]{10,}", data[:3000000])}
    a, b = strs(SAMPLE["path"]), strs(os.path.expanduser(p2))
    print(f"\n{B}uniquement dans l'échantillon :{RST}")
    for x in sorted(a - b)[:12]: print(f"  {G}- {x[:110]}{RST}")
    print(f"\n{B}uniquement dans l'autre :{RST}")
    for x in sorted(b - a)[:12]: print(f"  {Y}+ {x[:110]}{RST}")

def t_macho():
    banner_title("INFOS MACH-O (macOS)")
    if not need_sample(): return
    out = subprocess.run(["otool", "-hv", SAMPLE["path"]], capture_output=True, text=True).stdout
    print(f"{W}{out[:1500]}{RST}")
    load = subprocess.run(["otool", "-l", SAMPLE["path"]], capture_output=True, text=True).stdout
    for tag in ("LC_SEGMENT_64", "LC_UUID", "LC_CODE_SIGNATURE"):
        print(f"  {G}{tag}{RST} ×{load.count(tag)}")

def t_cryptoconst():
    banner_title("CONSTANTES CRYPTO (AES S-box…)")
    if not need_sample(): return
    data = open(SAMPLE["path"], "rb").read()
    AES_SBOX = bytes([0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76])
    if AES_SBOX in data:
        print(f"  {R}⚠️ TABLE AES S-BOX à l'offset 0x{data.index(AES_SBOX):x} — chiffrement AES embarqué{RST}")
    else:
        print(f"  {G}pas de table AES S-box complète{RST}")
    for sig, name in ((b"-----BEGIN", "clé PEM embarquée"), (b"\x30\x82", "structure ASN.1")):
        try:
            if sig in data: print(f"  {Y}▸ {name}{RST}")
        except Exception: pass

def t_summary():
    banner_title("RÉSUMÉ RE — tout en un")
    for fn in (t_analyze, t_packed):
        try: fn()
        except Exception as e: print(f"{DIM}[{e}]{RST}")
    print(f"\n{DIM}rapport dans rapports/{RST}")

def t_memo():
    banner_title("MÉMO — commandes r2 utiles")
    print(f"""{W}  iI{RST} infos binaires   {W}iS{RST} sections      {W}ii{RST} imports    {W}iz{RST} strings data
{W}  izz{RST} strings bin     {W}is~sym{RST} symboles   {W}aaa{RST} analyse    {W}afl{RST} fonctions
{W}  pdf @ f{RST} décompile     {W}pdc @ f{RST} pseudo   {W}px 512{RST} hexdump    {W}agf{RST} graphe""")

TOOLS = [
    ("0", "CHARGER UN ÉCHANTILLON", t_load, "choisis le binaire/fichier à analyser"),
    ("1", "ANALYSE RAPIDE", t_analyze, "type, entropie, hashes, vue d'ensemble"),
    ("2", "INFOS RADARE2", t_info, "archi, bits, langage, compilateur"),
    ("3", "SECTIONS", t_sections, "les sections + leurs tailles"),
    ("4", "STRINGS FILTRÉES", t_strings, "URLs, IPs, registre, mots suspices"),
    ("5", "IMPORTS", t_imports, "librairies chargées"),
    ("6", "SYMBOLES", t_symbols, "fonctions nommées si présentes"),
    ("7", "FONCTIONS (aaa)", t_functions, "analyse complète radare2 + liste"),
    ("8", "DÉSASSEMBLAGE", t_disasm, "pdf d'une fonction au choix"),
    ("9", "PSEUDO-DÉCOMPILATION", t_decompile, "pdc — pseudo-code lisible"),
    ("a", "CONSOLE R2 LIBRE", t_console, "toutes les commandes radare2 en direct"),
    ("b", "DÉTECTION PACKING", t_packed, "UPX, Themida, entropie"),
    ("c", "OVERLAY PE", t_overlays, "données cachées après les sections"),
    ("d", "STRINGS + OFFSETS", t_izz, "radare2 izz — les URLs localisées"),
    ("e", "HEXDUMP", t_hexdump, "vue hexa à l'offset voulu"),
    ("f", "DIFF BINAIRES", t_diffbin, "strings uniques de deux échantillons"),
    ("g", "INFOS MACH-O", t_macho, "otool : segments, UUID, signature"),
    ("h", "CONSTANTES CRYPTO", t_cryptoconst, "AES S-box, PEM, ASN.1"),
    ("i", "RÉSUMÉ RE", t_summary, "analyse + packing + overlay en un coup"),
    ("x", "MÉMO R2", t_memo, "les commandes radare2 utiles"),
]

def menu():
    print(CLEAR)
    for line in LOGO.splitlines():
        print(CD + line)
    print()
    print(gt_lib.bigtext("RE", C))
    print(f"{DIM}       powered by Maxime Leal · analyse statique · radare2 6.x{RST}\n")
    if SAMPLE["path"]:
        print(f"  {B}ÉCHANTILLON :{RST} {W}{os.path.basename(SAMPLE['path'])}{RST}\n")
    else:
        print(f"  {Y}Aucun échantillon — entre '0' pour charger{RST}\n")
    for n, name, _, desc in TOOLS:
        print(f"  {B}{C}{n}{RST}  {W}{name:<26}{RST} {DIM}{desc}{RST}")
    print(f"  {B}{C}r{RST}  {'VOIR LE RAPPORT':<26}{RST}")
    print(f"  {B}{H}{RST}  {'RAPPORT HTML → .html':<26}{RST}")
    print(f"  {B}{C}q{RST}  {'QUITTER':<26}{RST}")
    print()

def show_report():
    p = SAMPLE["path"] or "session"
    path = os.path.join(RAPPORTS, f"re_{os.path.basename(p)}.txt")
    print(CY + open(path).read()[-3000:] if os.path.exists(path) else f"{Y}aucun rapport{RST}")

def t_html():
    p = SAMPLE["path"] or "session"
    src = os.path.join(RAPPORTS, f"re_{os.path.basename(p)}.txt")
    out = gt_lib.html_report(src, f"RE — {os.path.basename(p)}", src.replace(".txt", ".html"), accent="#ff3ea5")
    print(f"{G}✓ rapport HTML : {out}{RST}" if out else f"{Y}aucun rapport à convertir{RST}")

def main():
    splash()
    while True:
        try:
            menu()
            c = input(f"{B}{C}re>{RST} ").strip().lower()
            if c == "q": break
            elif c == "r": show_report()
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
