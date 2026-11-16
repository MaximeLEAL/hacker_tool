#!/usr/bin/env python3
# language: Python 3, file: hash_tool.py, target: macOS
# ═══════════════════════════════════════════════════════════════════
#  HASH TOOL — la trousse crypto des CTFs · hacker_tool
#  powered by Maxime Leal
# ═══════════════════════════════════════════════════════════════════
import os, sys, hashlib, itertools, base64, time, threading, string, shutil, urllib.parse, codecs

ROOT = os.path.dirname(os.path.abspath(__file__))
RAPPORTS = os.path.join(ROOT, "rapports")
os.makedirs(RAPPORTS, exist_ok=True)

V   = "\033[38;2;155;48;255m"   # violet
VD  = "\033[38;2;95;28;160m"
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
      _______________
     /               \
    |  H A S H        |
    |  T O O L        |
    |    ___________  |
    |   | 🔮       |  |
     \  |___________| /
      \    ___________/
       \_/___________\
"""

def matrix_rain(seconds=3.2, fps=16):
    cols, rows = shutil.get_terminal_size((80, 24))
    charset = "0123456789abcdefABCDEF$#%&@=?/"
    drops = [random.randint(-rows, 0) for _ in range(cols)]
    frames = int(seconds * fps)
    for _ in range(frames):
        screen = [[" "] * cols for _ in range(rows)]
        for x in range(cols):
            y = drops[x]
            for dy in range(random.randint(4, 13)):
                yy = y - dy
                if 0 <= yy < rows: screen[yy][x] = random.choice(charset)
            drops[x] = y + 1 if y < rows + 12 else random.randint(-12, 0)
        sys.stdout.write(V + "\033[H" + "\n".join("".join(r) for r in screen)); sys.stdout.flush()
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
        print(V + line); time.sleep(.05)
    time.sleep(.4)
    type_line("        H A S H   T O O L", V, .03)
    type_line("   la trousse crypto des CTFs · hacker_tool", VD, .012)
    print()
    type_line("        ⚡ POWERED BY MAXIME LEAL ⚡", W, .02)
    time.sleep(.8)

def banner_title(txt):
    print(f"\n{B}{V}══════ {txt} ══════{RST}\n")

def save_report(name, content):
    path = os.path.join(RAPPORTS, "hash_tool.txt")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n[{time.strftime('%d/%m %H:%M')}] {name}\n{content}\n")
    print(f"{DIM}[+] rapport : {path}{RST}")

import random
# ─────────────────────────── 1. IDENTIFIER ───────────────────────────
def t_identify():
    banner_title("IDENTIFIER UN HASH")
    h = input(f"{B}{V}hash{RST} > ").strip()
    if not h: return
    n = len(h)
    hexa = all(c in "0123456789abcdefABCDEF" for c in h)
    cands = []
    if hexa:
        cands = {32: "MD5", 40: "SHA-1", 56: "SHA-224", 64: "SHA-256", 96: "SHA-384", 128: "SHA-512"}
        if n in cands: cands = [f"{cands[n]} (hex)"]
        else: cands = [f"hex inconnu ({n} chars)"]
    elif h.startswith("$2a$") or h.startswith("$2b$") or h.startswith("$2y$"):
        cands = ["bcrypt"]
    elif h.startswith("$6$"): cands = ["SHA-512 crypt (Unix)"]
    elif h.startswith("$5$"): cands = ["SHA-256 crypt (Unix)"]
    elif h.startswith("$1$"): cands = ["MD5 crypt (Unix)"]
    elif h.startswith("$argon2"): cands = ["Argon2"]
    elif h.startswith("$NT$"): cands = ["NTLM"]
    elif h.startswith("SHA(") or h.startswith("{SHA}"): cands = ["SHA (brut LDAP)"]
    elif all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567=" for c in h) and n >= 16:
        cands = ["Base32 ? (pas un hash standard)"]
    else:
        cands = ["format non reconnu"]
    print(f"\n  longueur : {W}{n}{RST}")
    for c in cands: print(f"  {B}{V}▸ {c}{RST}")
    if n in (32, 40, 64, 128):
        print(f"\n{DIM}pour casser : option 2 (dictionnaire) ou 3 (bruteforce){RST}")

# ─────────────────────────── 2-3. CASSER ───────────────────────────
WORDS = """password 123456 12345678 1234 qwerty 12345 dragon pussy baseball football
monkey letmein abc123 111111 mustang access shadow master michael superman
696969 batman trust me ipadmini love sunshine andrew tigger charlie
password1 password123 admin admin123 root toor flag ctf challenge
hacker hacker123 pwned pwn test test123 guest welcome welcome1
ninja azerty qwerty123 azerty123456 iloveyou princess sunshine daniel
starwars whatever hello hello123 freedom passw0rd secret secret1
 maximus 1q2w3e4r qwertyuiop 123qwe zxcvbnm 666666 google facebook
spotify instagram netflix amazon apple samsung taylor charliebrown""".split()

HASHES = {"1": ("MD5", hashlib.md5), "2": ("SHA-1", hashlib.sha1),
          "3": ("SHA-256", hashlib.sha256), "4": ("SHA-512", hashlib.sha512)}

def pick_hash():
    print(f"{DIM}1) MD5  2) SHA-1  3) SHA-256  4) SHA-512{RST}")
    t = input(f"{V}type{RST} > ").strip() or "1"
    return HASHES.get(t, HASHES["1"])

def t_dictionary():
    banner_title("ATTAQUE PAR DICTIONNAIRE")
    target = input(f"{B}{V}hash à casser{RST} > ").strip().lower()
    if not target: return
    algo, hfn = pick_hash()
    words = list(dict.fromkeys(WORDS))
    print(f"{DIM}{len(words)} candidats dans la wordlist intégrée…{RST}")
    t0 = time.time()
    for w in words:
        if hfn(w.encode()).hexdigest() == target:
            print(f"\n{B}{G}🎯 CASSÉ !{RST} {W}{w}{RST}  {DIM}({time.time()-t0:.2f}s){RST}")
            save_report("DICTIONNAIRE", f"{target} → {w}")
            return
    # variations leet + capitalisation
    def variations(w):
        yield w.capitalize()
        yield w + "1"; yield w + "123"; yield w + "!"
        yield w.replace("a", "4").replace("o", "0").replace("e", "3").replace("i", "1").replace("s", "$")
    for w in words:
        for v in variations(w):
            if hfn(v.encode()).hexdigest() == target:
                print(f"\n{B}{G}🎯 CASSÉ !{RST} {W}{v}{RST}  {DIM}(variation de '{w}'){RST}")
                save_report("DICTIONNAIRE", f"{target} → {v}")
                return
    print(f"\n{R}pas trouvé dans la wordlist — essaie un wordlist perso (option plus bas){RST}")
    wl = input(f"{DIM}chemin d'une wordlist perso (Entrée pour sauter){RST} > ").strip()
    if wl and os.path.exists(wl):
        n = 0
        with open(wl, "rb") as f:
            for line in f:
                w = line.strip()
                n += 1
                if n % 200000 == 0: print(f"{DIM}… {n} essayés{RST}")
                if hfn(w).hexdigest() == target:
                    print(f"\n{B}{G}🎯 CASSÉ !{RST} {W}{w.decode('utf-8', 'ignore')}{RST}")
                    save_report("DICTIONNAIRE", f"{target} → {w.decode('utf-8', 'ignore')}")
                    return
        print(f"{R}pas trouvé ({n} lignes testées){RST}")

def t_bruteforce():
    banner_title("BRUTEFORCE (hash courts — 6 chars max conseillé)")
    target = input(f"{B}{V}hash{RST} > ").strip().lower()
    if not target: return
    algo, hfn = pick_hash()
    cs = input(f"{DIM}charset [défaut: minuscules+digits]{RST} > ").strip() or (string.ascii_lowercase + string.digits)
    maxlen = int(input(f"{DIM}longueur max [4]{RST} > ") or 4)
    print(f"{DIM}espace : {len(cs)}^{maxlen} ≈ {len(cs)**maxlen:.0e} combinaisons{RST}")
    t0 = time.time(); count = 0; found = None
    for length in range(1, maxlen + 1):
        if found: break
        for combo in itertools.product(cs, repeat=length):
            w = "".join(combo); count += 1
            if hfn(w.encode()).hexdigest() == target:
                found = w; break
            if count % 2_000_000 == 0:
                print(f"{DIM}… {count:,} ({time.time()-t0:.0f}s){RST}")
    if found:
        print(f"\n{B}{G}🎯 CASSÉ !{RST} {W}{found}{RST}  {DIM}({count:,} essais, {time.time()-t0:.1f}s){RST}")
        save_report("BRUTEFORCE", f"{target} → {found}")
    else:
        print(f"\n{R}pas trouvé ({count:,} essais, {time.time()-t0:.1f}s) — augmente la wordlist plutôt{RST}")

# ─────────────────────────── 4. SOLVEUR POW ───────────────────────────
def t_pow():
    banner_title("SOLVEUR PROOF-OF-WORK (challenge CTF)")
    challenge = input(f"{B}{V}challenge/prefix du serveur{RST} > ").strip() or "ctf"
    bits = int(input(f"{DIM}difficulté : zéros hex au début [4]{RST} > ") or 4)
    prefix = "0" * bits
    print(f"{DIM}cible : sha256({challenge}+nonce) commence par '{prefix}'{RST}")
    found = threading.Event()
    t0 = time.time()
    def worker(tid):
        n = tid * 10_000_000
        enc = challenge.encode()
        while not found.is_set():
            h = hashlib.sha256(enc + str(n).encode()).hexdigest()
            if h.startswith(prefix):
                found.set()
                dt = time.time() - t0
                print(f"\n{B}{G}🎯 NONCE TROUVÉ !{RST} {W}{n}{RST}")
                print(f"{DIM}sha256('{challenge}{n}') = {h}  ({dt:.2f}s, {int(n/dt):,} H/s){RST}")
                save_report("POW", f"{challenge} bits={bits} → nonce {n} → {h}")
            n += 1
    threads = [threading.Thread(target=worker, args=(i,), daemon=True) for i in range(os.cpu_count() or 4)]
    for t in threads: t.start()
    for t in threads: t.join()

# ─────────────────────────── 5. DÉCODEUR ───────────────────────────
def try_all(s):
    out = []
    def add(name, val):
        if val: out.append((name, val))
    try: add("base64", base64.b64decode(s, validate=True).decode("utf-8", "replace"))
    except Exception: pass
    try: add("base32", base64.b32decode(s).decode("utf-8", "replace"))
    except Exception: pass
    if all(c in "0123456789abcdefABCDEF" for c in s) and len(s) % 2 == 0:
        try: add("hex", bytes.fromhex(s).decode("utf-8", "replace"))
        except Exception: pass
    if all(c in "01" for c in s) and len(s) % 8 == 0:
        try: add("binaire", "".join(chr(int(s[i:i+8], 2)) for i in range(0, len(s), 8)))
        except Exception: pass
    try: add("URL", urllib.parse.unquote(s))
    except Exception: pass
    try: add("rot13", codecs.decode(s, "rot13"))
    except Exception: pass
    if s.isdigit():
        add("décimal ASCII", "".join(chr(int(s[i:i+3])) for i in range(0, len(s), 3) if int(s[i:i+3]) < 128))
    try: add("base85", base64.b85decode(s).decode("utf-8", "replace"))
    except Exception: pass
    return out

def t_decode():
    banner_title("DÉCODEUR UNIVERSEL")
    s = input(f"{B}{V}chaîne à décoder{RST} > ").strip()
    if not s: return
    out = try_all(s)
    if not out: print(f"{R}aucun décodage reconnu{RST}"); return
    for name, val in out:
        print(f"\n{B}{V}{name}:{RST} {W}{val[:400]}{RST}")
    save_report("DÉCODEUR", f"{s[:60]} → {[o[0] for o in out]}")

# ─────────────────────────── 6. CLASSIQUES ───────────────────────────
def t_classic():
    banner_title("CHIFFREMENTS CLASSIQUES")
    s = input(f"{B}{V}texte{RST} > ").strip()
    if not s: return
    print(f"\n{B}CÉSAR — les 26 décalages :{RST}")
    for k in range(26):
        dec = "".join(chr((ord(c) - 97 + k) % 26 + 97) if c.islower()
                      else chr((ord(c) - 65 + k) % 26 + 65) if c.isupper() else c for c in s)
        print(f"  {DIM}{k:>2}{RST} {dec}")
    key = input(f"\n{DIM}VIGENÈRE — clé (Entrée pour sauter){RST} > ").strip()
    if key:
        ks = [ord(c) - 97 for c in key.lower() if c.isalpha()]
        dec = "".join(chr((ord(c) - 97 - ks[i % len(ks)]) % 26 + 97) if c.islower()
                      else chr((ord(c) - 65 - ks[i % len(ks)]) % 26 + 65) if c.isupper() else c
                      for i, c in enumerate(s))
        print(f"{V}vigenère décodé :{RST} {dec}")
    print(f"\n{B}MORSE :{RST} ", end="")
    MORSE = {"a": ".-", "b": "-...", "c": "-.-.", "d": "-..", "e": ".", "f": "..-.",
             "g": "--.", "h": "....", "i": "..", "j": ".---", "k": "-.-", "l": ".-..",
             "m": "--", "n": "-.", "o": "---", "p": ".--.", "q": "--.-", "r": ".-.",
             "s": "...", "t": "-", "u": "..-", "v": "...-", "w": ".--", "x": "-..-",
             "y": "-.--", "z": "--..", "0": "-----", "1": ".----", "2": "..---"}
    print(" ".join(MORSE.get(c, "") for c in s.lower() if c in MORSE) or "—")
    print(f"{B}BINAIRE :{RST} ", " ".join(format(ord(c), "08b") for c in s[:12]))

# ─────────────────────────── 7-8. XOR ───────────────────────────
def t_xor():
    banner_title("XOR CRACKER")
    s = input(f"{B}{V}chaîne hex à casser{RST} > ").strip()
    if not s: return
    try: data = bytes.fromhex(s)
    except Exception: print(f"{R}hex invalide{RST}"); return
    best = []
    for k in range(1, 256):
        dec = bytes(b ^ k for b in data)
        score = sum(1 for c in dec if chr(c) in string.ascii_letters + " ._") / len(dec)
        best.append((score, k, dec))
    best.sort(reverse=True)
    print(f"\n{B}TOP 5 clés mono-octet :{RST}")
    for score, k, dec in best[:5]:
        txt = "".join(chr(c) if 32 <= c < 127 else "." for c in dec)
        print(f"  {V}key 0x{k:02x}{RST} ({score:.0%})  {W}{txt[:80]}{RST}")
    key = input(f"\n{DIM}clé XOR multi-octets (texte, Entrée pour sauter){RST} > ").strip()
    if key:
        kb = key.encode()
        dec = bytes(b ^ kb[i % len(kb)] for i, b in enumerate(data))
        print(f"{V}décodé :{RST} {W}{dec.decode('utf-8', 'replace')[:200]}{RST}")
    save_report("XOR", f"{s[:40]} → top key 0x{best[0][1]:02x}")

def t_rainbow():
    banner_title("RAINBOW LOCAL (variations de mots courants)")
    target = input(f"{B}{V}hash (md5/sha1/sha256){RST} > ").strip().lower()
    if not target: return
    for name, hfn in (("md5", hashlib.md5), ("sha1", hashlib.sha1), ("sha256", hashlib.sha256)):
        if len(target) == hfn().hexdigest().__len__():
            print(f"{DIM}→ probablement {name}{RST}")
            hfn_used = (name, hfn); break
    else:
        hfn_used = ("md5", hashlib.md5)
    _, hfn = hfn_used
    t0 = time.time(); n = 0
    for w in WORDS:
        for v in (w, w.capitalize(), w + "1", w + "123", w + "!",
                  w.replace("a", "4").replace("o", "0").replace("e", "3").replace("i", "1").replace("s", "$"),
                  w[::-1]):
            n += 1
            if hfn(v.encode()).hexdigest() == target:
                print(f"\n{B}{G}🎯 TROUVÉ !{RST} {W}{v}{RST}  {DIM}({n} variations, {time.time()-t0:.2f}s){RST}")
                save_report("RAINBOW", f"{target} → {v}")
                return
    print(f"\n{R}pas trouvé ({n} variations) — c'est un hash non-courant{RST}")

TOOLS = [
    ("1", "IDENTIFIER UN HASH", t_identify, "md5? sha1? bcrypt? — détection par format"),
    ("2", "DICTIONNAIRE", t_dictionary, "wordlist intégrée + leet + wordlist perso"),
    ("3", "BRUTEFORCE", t_bruteforce, "charset et longueur configurables"),
    ("4", "SOLVEUR PoW", t_pow, "trouve le nonce — comme les vrais challenges CTF"),
    ("5", "DÉCODEUR UNIVERSEL", t_decode, "base64 · hex · binaire · URL · rot13 · base85"),
    ("6", "CHIFFREMENTS CLASSIQUES", t_classic, "césar ×26 · vigenère · morse · binaire"),
    ("7", "XOR CRACKER", t_xor, "mono-octet par fréquence + clé répétée"),
    ("8", "RAINBOW LOCAL", t_rainbow, "variations de mots courants, sans internet"),
]

def menu():
    print(CLEAR)
    for line in LOGO.splitlines():
        print(VD + line)
    print()
    print(f"{B}{V}  ╔═══════════════════════════════════════════════╗{RST}")
    print(f"{B}{V}  ║   H A S H   T O O L  —  hacker_tool           ║{RST}")
    print(f"{B}{V}  ╚═══════════════════════════════════════════════╝{RST}")
    print(f"{DIM}       powered by Maxime Leal · CTF crypto & forensics{RST}\n")
    for n, name, _, desc in TOOLS:
        print(f"  {B}{V}{n}{RST}  {W}{name:<26}{RST} {DIM}{desc}{RST}")
    print(f"  {B}{V}r{RST}  {'VOIR LE RAPPORT':<26}{RST}")
    print(f"  {B}{V}q{RST}  {'QUITTER':<26}{RST}")
    print()

def show_report():
    p = os.path.join(RAPPORTS, "hash_tool.txt")
    print(CY + open(p).read()[-2000:] if os.path.exists(p) else f"{Y}aucun rapport{RST}")

def main():
    splash()
    while True:
        try:
            menu()
            c = input(f"{B}{V}hash>{RST} ").strip().lower()
            if c == "q": break
            elif c == "r": show_report()
            else:
                tool = next((t for t in TOOLS if t[0] == c), None)
                if tool: tool[2]()
                elif c: print(f"{Y}choix inconnu{RST}")
            input(f"{DIM}↩︎ Entrée pour continuer…{RST}")
        except KeyboardInterrupt:
            print()
    print(f"{V}Au revoir — rapports dans rapports/{RST}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
