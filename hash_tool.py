#!/usr/bin/env python3
# language: Python 3, file: hash_tool.py, target: macOS
# ═══════════════════════════════════════════════════════════════════
#  HASH TOOL — la trousse crypto des CTFs · hacker_tool
#  powered by Maxime Leal
# ═══════════════════════════════════════════════════════════════════
import os, sys, hashlib, itertools, base64, time, threading, string, shutil, urllib.parse, codecs
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gt_lib

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
H   = "\033[97m"   # blanc H-option
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


# ─────────────────────── BOOST — les 12 nouveaux ───────────────────────
def t_wordlist100k():
    banner_title("DICTIONNAIRE 100K — wordlist SecLists (GitHub)")
    target = input(f"{B}{V}hash à casser{RST} > ").strip().lower()
    if not target: return
    algo, hfn = pick_hash()
    try:
        wl = gt_lib.lines("passwords-common.txt")
    except Exception as e:
        print(f"{R}[!] {e}{RST}"); return
    print(f"{DIM}{len(wl):,} mots — attaque en cours…{RST}")
    t0 = time.time()
    for i, w in enumerate(wl):
        if hfn(w.encode()).hexdigest() == target:
            print(f"\n{B}{G}🎯 CASSÉ !{RST} {W}{w}{RST}  {DIM}(position {i:,}, {time.time()-t0:.2f}s){RST}")
            save_report("100K", f"{target} → {w}")
            return
    print(f"\n{R}pas trouvé ({len(wl):,} mots, {time.time()-t0:.1f}s) — le mot de passe n'est pas courant{RST}")

def t_hashfile():
    banner_title("CRACKER UN FICHIER DE HASHES")
    algo, hfn = pick_hash()
    path = input(f"{DIM}fichier de hashes (un par ligne){RST} > ").strip()
    if not path or not os.path.exists(os.path.expanduser(path)):
        print(f"{R}fichier introuvable{RST}"); return
    hashes = [l.strip().lower() for l in open(os.path.expanduser(path)) if l.strip()]
    wl = list(WORDS)
    try:
        wl = gt_lib.lines("passwords-common.txt")[:100000]
    except Exception: pass
    print(f"{DIM}{len(hashes)} hashes × {len(wl):,} mots{RST}")
    found = {}
    for w in wl:
        h = hfn(w.encode()).hexdigest()
        if h in hashes: found[h] = w
    print(f"\n{B}{len(found)} cassé(s) sur {len(hashes)} :{RST}")
    for h, w in found.items(): print(f"  {G}{h[:16]}…{RST} → {W}{w}{RST}")
    if found: save_report("HASHFILE", "\n".join(f"{h} → {w}" for h, w in found.items()))

def t_unix_crypt():
    banner_title("CRACKER UN HASH UNIX ($6$ · $1$ · $5$)")
    target = input(f"{B}{V}hash complet (ex: $6$salt$hash...){RST} > ").strip()
    if not target.startswith("$"): print(f"{R}format crypt requis{RST}"); return
    import crypt
    algo_id = target.split("$")[1]
    salt = "$" + algo_id + "$" + target.split("$")[2]
    print(f"{DIM}algo crypt: {algo_id} · salt: {salt}{RST}")
    t0 = time.time()
    for w in WORDS:
        try:
            if crypt.crypt(w, salt) == target:
                print(f"\n{B}{G}🎯 CASSÉ !{RST} {W}{w}{RST}  {DIM}({time.time()-t0:.2f}s){RST}")
                save_report("UNIX CRYPT", f"{target[:30]} → {w}")
                return
        except Exception: break
    print(f"{R}pas trouvé dans la wordlist intégrée{RST}")

def t_morse_enc():
    banner_title("MORSE ENCODEUR")
    s = input(f"{B}{V}texte{RST} > ").strip()
    if not s: return
    MORSE = {"a": ".-", "b": "-...", "c": "-.-.", "d": "-..", "e": ".", "f": "..-.",
             "g": "--.", "h": "....", "i": "..", "j": ".---", "k": "-.-", "l": ".-..",
             "m": "--", "n": "-.", "o": "---", "p": ".--.", "q": "--.-", "r": ".-.",
             "s": "...", "t": "-", "u": "..-", "v": "...-", "w": ".--", "x": "-..-",
             "y": "-.--", "z": "--..", "0": "-----", "1": ".----", "2": "..---",
             "3": "...--", "4": "....-", "5": ".....", "6": "-....", "7": "--...",
             "8": "---..", "9": "----.", " ": "/"}
    out = " ".join(MORSE.get(c, "") for c in s.lower())
    print(f"\n{V}morse :{RST} {W}{out}{RST}")
    save_report("MORSE", out)

def t_encoders():
    banner_title("ENCODEURS (cacher plutôt que décoder)")
    s = input(f"{B}{V}texte à encoder{RST} > ").strip()
    if not s: return
    b = s.encode()
    print(f"  {G}base64{RST}   {base64.b64encode(b).decode()}")
    print(f"  {G}hex{RST}       {b.hex()}")
    print(f"  {G}base32{RST}   {base64.b32encode(b).decode()}")
    print(f"  {G}base85{RST}   {base64.b85encode(b).decode()}")
    print(f"  {G}URL{RST}      {urllib.parse.quote(s)}")
    print(f"  {G}binaire{RST}  {' '.join(format(c, '08b') for c in b[:10])}…")
    print(f"  {G}rot13{RST}    {codecs.decode(s, 'rot13')}")
    save_report("ENCODEURS", s)

def t_rotn_auto():
    banner_title("ROT-N AUTO-CRACK (scoring anglais)")
    s = input(f"{B}{V}texte chiffré{RST} > ").strip()
    if not s: return
    common = "etaoinshrdlucmfwypvbgkjqxz"
    results = []
    for k in range(26):
        dec = "".join(chr((ord(c) - 97 + k) % 26 + 97) if c.islower()
                      else chr((ord(c) - 65 + k) % 26 + 65) if c.isupper() else c for c in s)
        freq = sum(common.index(c) for c in dec.lower() if c in common) / max(len(dec), 1)
        results.append((freq, k, dec))
    results.sort()
    print(f"{B}3 meilleurs décalages (par fréquence anglaise) :{RST}")
    for freq, k, dec in results[:3]:
        print(f"  {V}rot-{k:<3}{RST} {W}{dec[:100]}{RST}  {DIM}(score {freq:.0f}){RST}")

def t_vigenere_ioc():
    banner_title("VIGENÈRE — INDICE DE COÏNCIDENCE (longueur de clé)")
    s = input(f"{B}{V}texte chiffré{RST} > ").strip().lower()
    s = "".join(c for c in s if c.isalpha())
    if len(s) < 20: print(f"{R}trop court (20+ chars){RST}"); return
    print(f"{B}IoC par longueur de clé (≈0.066 = anglais mono-alphabétique) :{RST}")
    best = []
    for klen in range(1, 13):
        if klen > len(s) // 5: break
        ics = []
        for i in range(klen):
            sub = s[i::klen]
            n = len(sub)
            if n < 2: break
            freq = {}
            for c in sub: freq[c] = freq.get(c, 0) + 1
            ic = sum(c * (c - 1) for c in freq.values()) / (n * (n - 1)) if n > 1 else 0
            ics.append(ic)
        avg = sum(ics) / len(ics) if ics else 0
        best.append((avg, klen))
        print(f"  {V}clé {klen:<3}{RST} IoC {avg:.4f}  {'⭐ probable' if avg > 0.058 else ''}")
    best.sort(reverse=True)
    if best: print(f"\n{DIM}→ essaie une clé de {best[0][1]} caractères{RST}")

def t_freq():
    banner_title("ANALYSE DE FRÉQUENCE (substitution)")
    s = input(f"{B}{V}texte chiffré{RST} > ").strip().lower()
    s = "".join(c for c in s if c.isalpha())
    if not s: return
    freq = {}
    for c in s: freq[c] = freq.get(c, 0) + 1
    print(f"{B}fréquence du chiffré (triée) vs fréquence anglaise attendue :{RST}")
    english = "etaoinshrdlcumwfgypbvkjxqz"
    for c, n in sorted(freq.items(), key=lambda x: -x[1]):
        idx = english.index(c) if c in english else 26
        print(f"  {V}{c}{RST} ×{n:<3} {DIM}→ remplace probablement '{english[idx]}'{RST}")
    print(f"\n{DIM}casse le code en remplaçant dans cet ordre (option 9 du menu classique){RST}")

def t_conv():
    banner_title("CONVERTISSEUR INTERACTIF")
    s = input(f"{B}{V}texte{RST} > ").strip()
    if not s: return
    b = s.encode()
    print(f"  {G}hex{RST}       {b.hex()}")
    print(f"  {G}binaire{RST}  {' '.join(format(c, '08b') for c in b)}")
    print(f"  {G}base64{RST}   {base64.b64encode(b).decode()}")
    print(f"  {G}base32{RST}   {base64.b32encode(b).decode()}")
    print(f"  {G}URL{RST}      {urllib.parse.quote(s)}")
    print(f"  {G}decimal{RST}  {' '.join(str(c) for c in b)}")
    print(f"  {G}rot13{RST}    {codecs.decode(s, 'rot13')}")

def t_pwgen():
    banner_title("GÉNÉRATEUR SECURE (MDP + UUID)")
    import uuid
    length = int(input(f"{DIM}longueur [20]{RST} > ") or 20)
    cs = string.ascii_letters + string.digits + "!@#$%^&*-_+?"
    pw = "".join(random.SystemRandom().choice(cs) for _ in range(length))
    print(f"\n  {B}{W}{pw}{RST}")
    print(f"  {DIM}entropie ≈ {length * math.log2(len(cs)):.0f} bits{RST}")
    for _ in range(3):
        print(f"  {V}{str(uuid.uuid4())}{RST}")
    save_report("PWGEN", pw)

def t_hashfilemode(): pass  # réservé


def t_salted():
    banner_title("SALTED MD5 — md5(salt+pass) ou md5(pass+salt)")
    target = input(f"{B}{V}hash{RST} > ").strip().lower()
    salt = input(f"{B}{V}salt (connu du CTF){RST} > ").strip()
    if not target or not salt: return
    algo, hfn = pick_hash()
    t0 = time.time()
    for mode in ("salt+pass", "pass+salt"):
        for w in WORDS:
            v = (salt + w) if mode == "salt+pass" else (w + salt)
            if hfn(v.encode()).hexdigest() == target:
                print(f"\n{B}{G}🎯 CASSÉ !{RST} {W}{w}{RST}  {DIM}(mode {mode}, {time.time()-t0:.2f}s){RST}")
                save_report("SALTED", f"{target} → {w} ({mode})")
                return
    print(f"{R}pas trouvé{RST}")

def t_double():
    banner_title("DOUBLE HASH — md5(md5(pw)) · sha256(sha256(pw))")
    target = input(f"{B}{V}hash{RST} > ").strip().lower()
    if not target: return
    algo, hfn = pick_hash()
    t0 = time.time()
    for w in WORDS:
        h1 = hfn(w.encode()).hexdigest()
        if hfn(h1.encode()).hexdigest() == target:
            print(f"\n{B}{G}🎯 CASSÉ !{RST} {W}{w}{RST}  {DIM}(double {algo}, {time.time()-t0:.2f}s){RST}")
            save_report("DOUBLE", f"{target} → {w}")
            return
    print(f"{R}pas trouvé{RST}")

TOOLS = []  # placeholder (remplacé plus bas)

TOOLS = [
    ("1", "IDENTIFIER UN HASH", t_identify, "md5? sha1? bcrypt? — détection par format"),
    ("2", "DICTIONNAIRE", t_dictionary, "wordlist intégrée + leet + wordlist perso"),
    ("3", "BRUTEFORCE", t_bruteforce, "charset et longueur configurables"),
    ("4", "SOLVEUR PoW", t_pow, "trouve le nonce — comme les vrais challenges CTF"),
    ("5", "DÉCODEUR UNIVERSEL", t_decode, "base64 · hex · binaire · URL · rot13 · base85"),
    ("6", "CHIFFREMENTS CLASSIQUES", t_classic, "césar ×26 · vigenère · morse · binaire"),
    ("7", "XOR CRACKER", t_xor, "mono-octet par fréquence + clé répétée"),
    ("8", "RAINBOW LOCAL", t_rainbow, "variations de mots courants, sans internet"),
    ("a", "DICTIONNAIRE 100K", t_wordlist100k, "wordlist SecLists 100000 mots (GitHub)"),
    ("b", "CRACK FICHIER HASHES", t_hashfile, "un fichier de hashes → dictionnaire"),
    ("c", "UNIX CRYPT ($6$)", t_unix_crypt, "les hashes de /etc/shadow"),
    ("d", "MORSE ENCODEUR", t_morse_enc, "texte → morse"),
    ("e", "ENCODEURS", t_encoders, "base64 · hex · base32 · base85 · URL"),
    ("f", "ROT-N AUTO-CRACK", t_rotn_auto, "les 26 décalages scorés par anglais"),
    ("g", "VIGENÈRE IoC", t_vigenere_ioc, "trouve la longueur de clé"),
    ("h", "FRÉQUENCE SUBSTITUTION", t_freq, "aide au décodage par substitution"),
    ("i", "CONVERTISSEUR", t_conv, "hex · binaire · base64 · base32 · URL · décimal"),
    ("j", "GÉNÉRATEUR SECURE", t_pwgen, "mdp fort + UUID v4"),
    ("k", "SALTED MD5", t_salted, "md5(salt+pass) / md5(pass+salt)"),
    ("l", "DOUBLE HASH", t_double, "md5(md5(pw)) · sha256(sha256(pw))"),
]

def menu():
    print(CLEAR)
    for line in LOGO.splitlines():
        print(VD + line)
    print()
    print(gt_lib.bigtext("HASH", V))
    print(f"{DIM}       powered by Maxime Leal · CTF crypto & forensics{RST}\n")
    for n, name, _, desc in TOOLS:
        print(f"  {B}{V}{n}{RST}  {W}{name:<26}{RST} {DIM}{desc}{RST}")
    print(f"  {B}{V}r{RST}  {'VOIR LE RAPPORT':<26}{RST}")
    print(f"  {B}{H}{RST}  {'RAPPORT HTML → .html':<26}{RST}")
    print(f"  {B}{V}q{RST}  {'QUITTER':<26}{RST}")
    print()

def show_report():
    p = os.path.join(RAPPORTS, "hash_tool.txt")
    print(CY + open(p).read()[-2000:] if os.path.exists(p) else f"{Y}aucun rapport{RST}")

def t_html():
    out = gt_lib.html_report(os.path.join(RAPPORTS, "hash_tool.txt"), "HASH TOOL", os.path.join(RAPPORTS, "hash_tool.html"), accent="#9b30ff")
    print(f"{G}✓ rapport HTML : {out}{RST}" if out else f"{Y}aucun rapport à convertir{RST}")

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
