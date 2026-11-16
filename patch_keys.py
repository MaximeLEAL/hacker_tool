#!/usr/bin/env python3
# language: Python 3, file: patch_keys.py, target: macOS
# one-shot : ajoute keys.json + pwned_password à gt_lib
import json, os, sys

ROOT = os.path.dirname(os.path.abspath(__file__))

# 1. gt_lib : load_keys + pwned_password (k-anonymity)
s = open(os.path.join(ROOT, "gt_lib.py"), encoding="utf-8").read()
if "def load_keys" not in s:
    s += '''

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
'''
    open(os.path.join(ROOT, "gt_lib.py"), "w", encoding="utf-8").write(s)
    print("gt_lib : load_keys + pwned_password ajoutés")

# 2. keys.json template
kp = os.path.join(ROOT, "keys.json")
if not os.path.exists(kp):
    keys = {
        "_instructions": "CLÉS API GRATUITES — crée les comptes, colle les clés, sauvegarde :",
        "virustotal": "",
        "shodan": "",
        "urlscan": "",
        "censys": "",
        "_liens": {
            "virustotal": "https://www.virustotal.com → profil → API key (gratuit, 4 req/min)",
            "shodan": "https://account.shodan.io → API key (gratuit, résultats limités)",
            "urlscan": "https://urlscan.io → user settings → API (gratuit)",
            "censys": "https://search.censys.io → account → API (gratuit)"
        }
    }
    json.dump(keys, open(kp, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("keys.json créé (vide)")
