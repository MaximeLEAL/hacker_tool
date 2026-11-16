# 🕶️ HACKER_TOOL — la famille d'outils du hacker

**La boîte à outils de reconnaissance · powered by Maxime Leal**

## Les tools
| Tool | Couleur | Fichier | Chaîne |
|---|---|---|---|
| 🕶️ RECON TOOL | vert | RECON.tool ✓ | qu'est-ce qui est exposé ? — 23 tools, wordlists SecLists |
| 🔴 VULN TOOL | rouge | VULN.tool ✓ | qu'est-ce qui est vulnérable ? (NVD + CISA KEV) |
| 🔮 HASH TOOL | violet | HASH.tool ✓ | la trousse crypto des CTFs : identifier/casser des hashes, PoW, décodeurs |
| 🟡 HUNT TOOL | or | HUNT.tool ✓ | bug bounty : subdomain takeover, secrets dans les JS |
| 🔵 OSINT DEEP | cyan | OSINT.tool ✓ | profiler une organisation — 482 plateformes sherlock |
| ⚪ NET SNIFF | blanc | SNIFF.tool ✓ | audit du réseau local |
| 🔍 RE TOOL | magenta | RE.tool ✓ | reverse engineering : radare2 embarqué (12 tools) — statique only |

Double-clique le .tool de ton choix.

## RE TOOL — reverse engineering (12 tools)
0. CHARGER UN ÉCHANTILLON · 1. ANALYSE RAPIDE · 2. INFOS RADARE2 · 3. SECTIONS · 4. STRINGS FILTRÉES
5. IMPORTS · 6. SYMBOLES · 7. FONCTIONS (aaa) · 8. DÉSASSEMBLAGE · 9. PSEUDO-DÉCOMPILATION (pdc)
a. CONSOLE R2 LIBRE · b. DÉTECTION PACKING — analyse STATIQUE uniquement, rien n'est exécuté

## OSINT DEEP (8 tools)
1. USERNAME 60+ PLATEFORMES · 2. GRAVATAR PAR EMAIL · 3. GITHUB OSINT (+emails des commits) · 4. ORG & INFRA
5. PAGES ÉQUIPE · 6. ASN & HÉBERGEMENT · 7. MAIGRET (300+ sites si installé) · 8. GITHUB DORKS (secrets/clés)

## HUNT TOOL — bug bounty (6 tools)
1. SUBDOMAIN TAKEOVER · 2. SECRETS DANS LES JS · 3. CORS · 4. PARAMÈTRES & FORMS · 5. WAYBACK · 6. MÉMO BOUNTY

## OSINT DEEP (6 tools)
1. USERNAME 20 PLATEFORMES · 2. GRAVATAR PAR EMAIL · 3. GITHUB OSINT (+emails des commits) · 4. ORG & INFRA · 5. PAGES ÉQUIPE · 6. ASN & HÉBERGEMENT

## NET SNIFF (7 tools)
1. CONNEXIONS LIVE · 2. TABLE ARP · 3. TRACEROUTE · 4. PORTS EN ÉCOUTE · 5. SESSIONS · 6. INFOS WIFI · 7. CONFIG DNS

## HASH TOOL — la trousse crypto (8 tools)
1. IDENTIFIER UN HASH · 2. DICTIONNAIRE (+leet) · 3. BRUTEFORCE · 4. SOLVEUR PoW
5. DÉCODEUR UNIVERSEL · 6. CLASSIQUES (césar/vigenère/morse) · 7. XOR CRACKER · 8. RAINBOW LOCAL

## BOOST GitHub (gt_lib.py) — les ressources publiques téléchargées et mises en cache
SecLists (subdomains 5000 · dirs · params · usernames · passwords) · base sherlock 482 plateformes

## RECON — la boîte à outils (23 tools)

## La boîte à outils (10 tools)
| # | Tool | Ce qu'il fait |
|---|---|---|
| 1 | WHOIS COMPLET | registre, registrar, dates, serveurs |
| 2 | ENUMÉRATION DNS | A · AAAA · MX · NS · TXT · SOA · CNAME |
| 3 | SOUS-DOMAINES | découverte par Certificate Transparency (crt.sh) |
| 4 | GÉOLOCALISATION IP | pays, ville, FAI, AS, carte |
| 5 | HEADERS + SÉCURITÉ | headers complets + audit des 6 security headers |
| 6 | FINGERPRINTING | technos, CMS, chemins exposés |
| 7 | SCAN DE PORTS | les 30 ports les plus utilisés |
| 8 | PING SWEEP LAN | appareils vivants sur le réseau local |
| 9 | ROBOTS & SITEMAP | ce que le site déclare aux crawlers |
| 0 | EMAILS & SOCIAUX | emails publics + réseaux sociaux liés |

Plus : animation matrix au lancement, logo mask, rapports sauvegardés
dans `rapports/` par cible.

⚠️ **Usage : uniquement sur des cibles que tu es autorisé à tester.**
