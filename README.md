<div align="center">

# 🕶️ HACKER_TOOL

**7 tools · 150+ outils · la trousse complète du hacker éthique**

*powered by Maxime Leal*

[![Tools](https://img.shields.io/badge/tools-150%2B-e63022?style=for-the-badge&labelColor=0c0e17)]()
[![Famille](https://img.shields.io/badge/famille-7_tools-ffd60a?style=for-the-badge&labelColor=0c0e17)]()
[![Python](https://img.shields.io/badge/Python-3-3776AB?style=for-the-badge&logo=python&logoColor=white)]()
[![Statique](https://img.shields.io/badge/analyse-statique_only-4ad66d?style=for-the-badge&labelColor=0c0e17)]()

</div>

---

## 🎨 La famille — chaque tool a sa couleur et son identité

| | Tool | Tools | La question à laquelle il répond |
|---|---|---|---|
| 🕶️ | **RECON** — vert | **23** | *qu'est-ce qui est exposé ?* |
| 🔴 | **VULN** — rouge | **20** | *qu'est-ce qui est vulnérable ?* |
| 🔮 | **HASH** — violet | **20** | *le flag CTF se casse comment ?* |
| 🟡 | **HUNT** — or | **20** | *qu'est-ce qui rapporte en bounty ?* |
| 🔵 | **OSINT DEEP** — cyan | **20** | *qui est derrière ?* |
| ⚪ | **NET SNIFF** — blanc | **20** | *qu'est-ce qui circule sur mon réseau ?* |
| 🔍 | **RE** — magenta | **20** | *comment ce binaire fonctionne ?* |

Chaque tool : **splash matrix plein écran** dans sa couleur + logo ASCII + menu numéroté + rapports sauvegardés dans `rapports/`.

## 🚀 Lancement

```bash
git clone https://github.com/MaximeLEAL/hacker_tool.git
cd hacker_tool
# double-clique le .tool de ton choix, ou :
python3 recon_tool.py
```

## 🕶️ RECON (23 tools) — la reconnaissance
whois · DNS (7 types) · subdomains (crt.sh) · geoloc IP · headers + audit sécurité ·
fingerprinting · 30 ports · ping sweep LAN · robots/sitemap · emails & sociaux ·
**DNS brute force 5000 wordlist** · **directory brute** · **TLS/certificat complet** ·
méthodes HTTP · cookies · WordPress enum · API docs (swagger/graphql) · endpoints JS ·
HTML comments · SPF/DKIM/DMARC · **zone transfer AXFR** · reverse DNS · ports custom

## 🔴 VULN (20 tools) — les vulnérabilités
recherche CVE (NVD) · **CISA KEV** (failles activement exploitées) · banner grabbing ·
version→CVE · top CVEs récentes · KEV par produit · détail CVE (CVSS, références) ·
scan complet auto · KEV par mot-clé · **failles ransomware** · CVEs des 30 derniers jours ·
CWE top · liens exploit (NVD/EDB/Nuclei/Metasploit) · banner sweep LAN · SSL scan ·
**audit /etc/hosts** · audit DNS · résumé exécutif · **KEV diff** (les nouvelles) · liens Shodan/Censys/VT

## 🔮 HASH (20 tools) — la crypto des CTFs
identifier un hash · dictionnaire (+leet) · bruteforce · **solveur PoW multi-thread** ·
décodeur universel · césar/vigenère/morse · XOR cracker · rainbow local ·
**dictionnaire 100k SecLists** · crack fichier de hashes · unix crypt · morse encoder ·
encodeurs · rot-N auto-crack · vigenère IoC · fréquence substitution · convertisseur ·
générateur secure · salted MD5 · double hash

## 🟡 HUNT (20 tools) — le bug bounty
subdomain takeover (15 services) · **secrets dans les JS** (AWS, Google, Stripe, JWT…) ·
CORS mal configuré · paramètres & formulaires · wayback · mémo bounty ·
directory brute · open redirect · subs→IP→hébergeur · wayback profond · Google dorks ·
headers par sub · stack par sub · métadonnées · mini-crawler · détection honeypot ·
XSS marqueur bénin · audit CSP · source maps exposées · résumé

## 🔵 OSINT DEEP (20 tools) — le profiling
username sur **482 plateformes** (base sherlock GitHub) · gravatar par email ·
GitHub OSINT (+emails des commits) · org & infrastructure · pages équipe · ASN ·
**maigret** (300+ sites) · GitHub dorks · dorks OSINT · téléphones & adresses ·
org via certificat TLS · technologies · âge du site · réseaux sociaux · DNS profond ·
emails probables · timeline wayback · moteurs personne · carte d'identité

## ⚪ NET SNIFF (20 tools) — ton réseau
connexions live · table ARP · traceroute · ports en écoute · sessions · infos wifi ·
config DNS · ports du LAN · connexions par process · **firewall macOS** · ARP watch ·
débit live · traceroute LAN · ping monitor · wifi autour · **test DNS hijack** ·
interfaces · ports à risque · géolocalisation des connexions · snapshot complet

## 🔍 RE (20 tools) — le reverse engineering (radare2 embarqué)
analyse rapide · infos r2 · sections · strings filtrées · imports · symboles ·
fonctions (aaa) · désassemblage (pdf) · pseudo-décompilation (pdc) · console R2 libre ·
détection packing · **overlay PE** · strings+offsets (izz) · hexdump · diff binaires ·
infos Mach-O · **constantes crypto** (AES S-box) · résumé · mémo r2

## 🧅 DARK TOOL — opérations Tor (20 tools)
1. STATUT · 2. INSTALL/DÉMARRER · 3. IP SORTIE · 4. FETCH VIA TOR · 5. SECUREDROP (officiel) · 6. MIROIRS · 7. CHECK .ONION
8. OPSEC · 9. VALIDER .ONION · a. CIRCUIT · b. NEWNYM · c. LOG · d. LATENCE · e. TEST DE FUITE · f. BATCH CHECK
g. PRESSE INTERNATIONALE · h. RECHERCHE AHMIA (moteur dark web filtré) · i. BRIDGES · j. DARK WEB EN CTF · k. STATS RÉSEAU
Services officiels uniquement — aucun annuaire de marketplaces. **+ logos ANSI-Shadow partout**

## ⚡ Le BOOST GitHub (gt_lib.py)

Tous les tools partagent un système de **ressources publiques téléchargées et mises en cache** :
- **SecLists** (danielmiessler) — 5000 subdomains, wordlists de directories/params/passwords (1M)
- **Sherlock** (sherlock-project) — la base de 482 plateformes d'OSINT
- **SecureDrop** (freedom of the press) — l'annuaire officiel des signalements journalistiques

## ⚖️ Usage

Ces outils sont conçus pour **l'apprentissage, les CTFs et les audits autorisés**.
Reconnaissance passive et analyse statique uniquement — rien n'est exécuté, rien
n'est intrusif. Utilise-les uniquement sur des cibles que tu es autorisé à tester.

---

<div align="center">

**HACKER_TOOL · 7 TOOLS · 150+ OUTILS · ANALYSE STATIQUE · 100% LOCAL**

*powered by Maxime Leal*

</div>
