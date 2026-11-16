#!/usr/bin/env python3
# language: Python 3, file: gt_lib.py, target: macOS
# GT_LIB — ressources GitHub partagées par tous les tools de hacker_tool
# télécharge une fois, met en cache, sert ensuite hors-ligne
import os, json, time, urllib.request

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
