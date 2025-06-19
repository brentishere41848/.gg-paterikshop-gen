# Python 3.11+, 3.12+, or 3.13+ required (install Python separately)
import random                 as rdm
import string                 # Use the standard name, not 'as str'
import requests               as rq
import os                     as x
import platform               as ptfm
import concurrent.futures     as cf
import threading              as td
import time                   as t
import shutil
import urllib.request
from datetime import datetime as dt
from tqdm import tqdm
from colorama import init, Fore, Style
import subprocess
import sys
import os  # Ensure os is imported for version check
import random  # Ensure random is imported for easter egg

init(autoreset=True)

# --- Auto-install requirements if missing ---
REQUIRED = ["requests", "colorama", "tqdm"]
for pkg in REQUIRED:
    try:
        __import__(pkg)
    except ImportError:
        print(f"[!] Installing missing package: {pkg}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

class DiscordGiftChecker:
    def __init__(s, token):
        s.base_url = "https://discord.com/api/v10/entitlements/gift-codes/"
        s.headers = {
            "authority": "discord.com",
            "method": "GET",
            "scheme": "https",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Authorization": token,
            "Pragma": "no-cache",
            "Priority": "u=0, i",
            "Sec-Ch-Ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        }
        s.username = x.getlogin()
        s.print_lock = None  # Wordt gezet door GiftCheckerApp

    def generate_code(s):
        return "".join(rdm.choices(string.digits + string.ascii_letters, k=16))

    def check_code(s, C):
        url = f"{s.base_url}{C}?with_application=false&with_subscription_plan=true"
        try:
            r = rq.get(url, headers=s.headers, timeout=10)
            msg = None
            if r.status_code in range(200, 204):
                msg = f"{Fore.GREEN}    [{dt.now().strftime('%H:%M')}] ╰──> [VALID]{Style.RESET_ALL} discord.gift/{C}"
                result = True
            else:
                msg = f"{Fore.RED}    [{dt.now().strftime('%H:%M')}] ╰──> [INVALID]{Style.RESET_ALL} discord.gift/{C}"
                result = False
            from tqdm import tqdm
            tqdm.write(msg)
            return C, result
        except Exception as e:
            from tqdm import tqdm
            tqdm.write(f"{Fore.YELLOW}    [{dt.now().strftime('%H:%M')}] ╰──> [ERROR]{Style.RESET_ALL} discord.gift/{C} | {type(e).__name__}: {e}")
            return C, False

class TerminalTitleSetter:
    @staticmethod
    def set_title(checked_count=None, elapsed_time=None):
        title = "By: .gg/paterikshop"
        if checked_count is not None:
            title += f" | Checked: {checked_count}"
        if elapsed_time:
            title += f" | Elapsed: {elapsed_time}"
        if ptfm.system() == "Windows":
            import ctypes as ct
            ct.windll.kernel32.SetConsoleTitleW(title)
        else:
            print(f"\033]0;{title}\007", end="", flush=True)

class FileHandler:
    @staticmethod
    def save(data, fn):
        with open(fn, "a") as f:
            f.write(data + "\n")

    @staticmethod
    def read(fn):
        codes = []
        if x.path.exists(fn):
            with open(fn, "r") as f:
                for line in f:
                    codes.append(line.strip())
        return codes

class CodeGenerator:
    @staticmethod
    def generate_amount(n):
        return ["".join(rdm.choices(string.digits + string.ascii_letters, k=16)) for _ in range(n)]

class GiftCheckerApp:
    def __init__(s, token, lang_dict):
        s.checker = DiscordGiftChecker(token)
        s.xdir = "data"
        s.vF = x.path.join(s.xdir, "valid.txt")
        s.invalid_file = x.path.join(s.xdir, "invalid.txt")
        s.codes_file = x.path.join(s.xdir, "codes.txt")
        s.checked_count = [0]
        s.checked_count_event = td.Event()
        s.start_time = t.time()
        s.print_lock = td.Lock()  # Toegevoegd voor thread-safe printen
        s.checker.print_lock = s.print_lock  # Geef lock door aan checker
        s.T = lang_dict

    def setup(s):
        if not x.path.exists(s.xdir):
            x.makedirs(s.xdir)
        # Ensure all data files exist
        for f in [s.vF, s.invalid_file, s.codes_file]:
            if not x.path.exists(f):
                with open(f, "w"): pass
        TerminalTitleSetter.set_title(checked_count=0, elapsed_time="0:00")
        print(f"{Fore.BLUE}{' '*7}╰──> Logged in as: {s.checker.username}{Style.RESET_ALL}\n")
        print(f"{Fore.CYAN}{' '*8}┌┐┌┬ ┬─┐ ┬┌─┐{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{' '*8}│││└┬┘┌┴┬┘│ │{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{' '*8}┘└┘ ┴ ┴ └─└─┘{Style.RESET_ALL}\n")

    def update_counter(s):
        while True:
            elapsed_time = int(t.time() - s.start_time)
            minutes = elapsed_time // 60
            seconds = elapsed_time % 60
            elapsed_time_str = f"{minutes}:{seconds:02d}"
            TerminalTitleSetter.set_title(checked_count=s.checked_count[0], elapsed_time=elapsed_time_str)
            t.sleep(1)

    def check_codes(s, CA):
        import sys
        from tqdm import tqdm
        import signal
        import os
        import time

        # Pause/Resume support
        paused = [False]
        def toggle_pause(signum=None, frame=None):
            paused[0] = not paused[0]
            if paused[0]:
                tqdm.write(f"{Fore.YELLOW}[PAUSED] Press 'p' again to resume...{Style.RESET_ALL}")
            else:
                tqdm.write(f"{Fore.GREEN}[RESUMED]{Style.RESET_ALL}")

        # Windows: use keyboard polling, Unix: use signal
        if os.name == 'nt':
            import msvcrt
            def check_pause():
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key in (b'p', b'P'):
                        toggle_pause()
        else:
            signal.signal(signal.SIGTSTP, toggle_pause)
            def check_pause():
                pass

        # Use a generator and submit new tasks as old ones finish to avoid memory overload
        def code_generator(n):
            for _ in range(n):
                yield s.checker.generate_code()

        td.Thread(target=s.update_counter, daemon=True).start()

        checked_codes = FileHandler.read(s.codes_file)
        vC = []
        iC = []

        def process_code(C):
            code, result = s.checker.check_code(C)
            return code, result

        max_workers = 10
        code_iter = code_generator(CA)
        with cf.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            # Submit initial batch
            for _ in range(max_workers):
                try:
                    C = next(code_iter)
                    futures.append(executor.submit(process_code, C))
                except StopIteration:
                    break
            pbar = tqdm(total=CA, desc="Checking codes", ncols=100, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{percentage:3.0f}%] | ETA: {remaining} | {postfix}')
            start_time = time.time()
            idx = 0
            # Helper to format ETA as days, hours, minutes, seconds
            def format_eta(seconds):
                days = int(seconds // 86400)
                hours = int((seconds % 86400) // 3600)
                minutes = int((seconds % 3600) // 60)
                secs = int(seconds % 60)
                parts = []
                if days > 0:
                    parts.append(f"{days}d")
                if hours > 0 or days > 0:
                    parts.append(f"{hours}h")
                if minutes > 0 or hours > 0 or days > 0:
                    parts.append(f"{minutes}m")
                parts.append(f"{secs}s")
                return " ".join(parts)
            while futures:
                # Pause/Resume logic
                while paused[0]:
                    time.sleep(0.2)
                    check_pause()
                check_pause()

                done, not_done = cf.wait(futures, return_when=cf.FIRST_COMPLETED)
                # Remove completed futures from the list
                futures = list(not_done)
                for future in done:
                    C, result = future.result()

                    if C in checked_codes:
                        print(f"{Fore.YELLOW}    [{dt.now().strftime('%H:%M')}] ╰──> [SKIPPED] {C} (Code already checked){Style.RESET_ALL}")
                        continue

                    s.checked_count[0] += 1
                    s.checked_count_event.set()

                    FileHandler.save(C, s.codes_file)

                    if result:
                        vC.append(C)
                        FileHandler.save(C, s.vF)
                    else:
                        iC.append(C)
                        FileHandler.save(C, s.invalid_file)

                    # ETA calculation
                    idx += 1
                    elapsed = time.time() - start_time
                    speed = idx / elapsed if elapsed > 0 else 0
                    remaining = CA - idx
                    eta = remaining / speed if speed > 0 else 0
                    percent = (idx / CA) * 100
                    pbar.update(1)
                    # One-line postfix with valid/invalid
                    pbar.set_postfix_str(f"Valid: {len(vC)} | Invalid: {len(iC)} | {percent:.1f}% | ETA: {format_eta(eta)}")
                    # Submit next code if available
                    try:
                        C = next(code_iter)
                        futures.append(executor.submit(process_code, C))
                    except StopIteration:
                        pass
            pbar.close()
        s.display_valid_codes(vC)
        # Summary report (multi-language)
        elapsed_total = time.time() - start_time
        avg_speed = idx / elapsed_total if elapsed_total > 0 else 0
        print("\n" + "="*40)
        print(f"{Fore.LIGHTCYAN_EX}{s.T['summary_title']}{Style.RESET_ALL}")
        print(f"{s.T['total_checked']} {idx}")
        print(f"{Fore.GREEN}{s.T['valid_codes']} {len(vC)}{Style.RESET_ALL}")
        print(f"{Fore.RED}{s.T['invalid_codes']} {len(iC)}{Style.RESET_ALL}")
        print(f"{s.T['skipped_codes']} {len(checked_codes)}")
        print(f"{s.T['elapsed_time']} {format_eta(elapsed_total)}")
        print(f"{s.T['avg_speed']} {avg_speed:.2f} codes/sec")
        print("="*40 + "\n")

    @staticmethod
    def display_valid_codes(vC, T=None):
        if T is None:
            T = LANGUAGES['en']
        print(f"\n{Fore.GREEN}{T['valid_codes_list']}{Style.RESET_ALL}")
        if vC:
            print(f"  ╰──> [Count: {len(vC)}]")
            for C in vC:
                print(C)
        else:
            print(T['none'])

def check_for_update(current_version):
    try:
        import sys
        import re
        import urllib.request
        possible_dirs = [
            os.path.dirname(os.path.abspath(__file__)),
            os.path.dirname(sys.executable),
            os.getcwd()
        ]
        version_file = None
        for d in possible_dirs:
            candidate = os.path.join(d, "version.md")
            if os.path.exists(candidate):
                version_file = candidate
                break
        latest = None
        if version_file:
            with open(version_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("**") and line.strip().endswith("**"):
                        match = re.search(r"\*\*(.*?)\*\*", line)
                        if match:
                            latest = match.group(1).strip()
                        else:
                            latest = line.strip().strip("*")
                        break
        if latest:
            if latest.strip() == current_version.strip():
                print(f"{Fore.GREEN}[Up to date]{Style.RESET_ALL} You are running the latest version: {current_version}")
            else:
                print(f"{Fore.YELLOW}[UPDATE AVAILABLE]{Style.RESET_ALL} New version {latest} is available! (You are running: {current_version}) See version.md for details.")
                # Self-update prompt
                update_url = "https://raw.githubusercontent.com/brentishere41848/.gg-paterikshop-gen/main/main.py"
                consent = input("Would you like to auto-update to the latest version? (y/n): ").strip().lower()
                if consent in ("y", "j", "o", "s", "e"):
                    try:
                        print("Downloading latest version...")
                        new_code = urllib.request.urlopen(update_url).read().decode("utf-8")
                        script_path = os.path.abspath(__file__)
                        with open(script_path, "w", encoding="utf-8") as f:
                            f.write(new_code)
                        print("Update complete! Please restart the script.")
                        input("Press Enter to exit...")
                        sys.exit(0)
                    except Exception as e:
                        print(f"[!] Update failed: {e}")
        else:
            print(f"{Fore.CYAN}[Info]{Style.RESET_ALL} Running version: {current_version} (version.md not found)")
    except Exception as e:
        print(f"{Fore.CYAN}[Info]{Style.RESET_ALL} Running version: {current_version} (Could not check for updates)")

# --- Language Support ---
LANGUAGES = {
    'en': {
        'welcome': "Do you like to print nitro gifts? (Press Enter to continue)",
        'tutorial_prompt': "Do you want to see a tutorial on how to find your Discord token? (y/n): ",
        'tutorial': [
            "How to find your Discord token:",
            "1. Open Discord in your web browser (preferably Chrome or Edge).",
            "2. Press F12 to open Developer Tools.",
            "3. Go to the 'Application' tab (in Chrome) or 'Storage' tab (in Edge/Firefox).",
            "4. In the left menu, expand 'Local Storage' and click on 'https://discord.com'.",
            "5. Look for an entry called 'token' in the key/value list.",
            "6. Copy the value of 'token' (it will look like a long string of letters, numbers, and dots).",
            "7. Paste this value into the script when prompted.",
            "Note: Never share your Discord token with others! It gives full access to your Discord account."
        ],
        'token_prompt': "Do you want to enter your Discord token now? (y/n): ",
        'token_input': "Paste your Discord token here (required): ",
        'token_required': "You must enter a token to continue!",
        'token_skip': "You chose not to enter a token. The checker will run without authentication, but you may be rate-limited or blocked by Discord.",
        'batch_prompt': "How many codes do you want to check in this batch? (default 10000): ",
        'batch_positive': "Please enter a positive integer.",
        'batch_valid': "Please enter a valid number.",
        'summary_title': "Summary Report",
        'total_checked': "Total checked:",
        'valid_codes': "Valid codes:",
        'invalid_codes': "Invalid codes:",
        'skipped_codes': "Skipped codes:",
        'elapsed_time': "Elapsed time:",
        'avg_speed': "Average speed:",
        'valid_codes_list': "  ╰──> Valid Codes:",
        'none': "  ╰──> [None]",
        'changelog': "Changelog",
        'made_by': "Made by: .gg/paterikshop.",
        'feedback': "\nWe value your feedback! Please let us know what you think or suggest improvements.\nType your feedback and press Enter (or just press Enter to skip):",
        'feedback_saved': "Thank you! Your feedback has been saved.",
        'feedback_file': "feedback.txt",
        'tutorial_userid_prompt': "Do you want to see a tutorial on how to find your Discord User ID? (y/n): ",
        'tutorial_userid': [
            "How to find your Discord User ID:",
            "1. Enable Developer Mode in Discord (User Settings > Advanced > Developer Mode).",
            "2. Right-click your profile in Discord and select 'Copy User ID'.",
            "3. Paste the User ID below when prompted."
        ],
        'user_id_prompt': "Enter your Discord User ID (or leave blank to skip): ",
    },
    'nl': {
        'welcome': "Wil je nitro gifts printen? (Druk op Enter om door te gaan)",
        'tutorial_prompt': "Wil je een tutorial zien over hoe je je Discord-token vindt? (j/n): ",
        'tutorial': [
            "Zo vind je je Discord-token:",
            "1. Open Discord in je webbrowser (bij voorkeur Chrome of Edge).",
            "2. Druk op F12 om de ontwikkelaarstools te openen.",
            "3. Ga naar het tabblad 'Application' (in Chrome) of 'Storage' (in Edge/Firefox).",
            "4. In het linkermenu, vouw 'Local Storage' uit en klik op 'https://discord.com'.",
            "5. Zoek naar een item genaamd 'token' in de lijst met sleutels/waarden.",
            "6. Kopieer de waarde van 'token' (dit is een lange reeks letters, cijfers en punten).",
            "7. Plak deze waarde in het script wanneer daarom wordt gevraagd.",
            "Let op: Deel je Discord-token nooit met anderen! Hiermee geef je volledige toegang tot je account."
        ],
        'token_prompt': "Wil je nu je Discord-token invoeren? (j/n): ",
        'token_input': "Plak hier je Discord-token (verplicht): ",
        'token_required': "Je moet een token invoeren om door te gaan!",
        'token_skip': "Je hebt ervoor gekozen geen token in te voeren. De checker draait zonder authenticatie, maar je kunt worden beperkt door Discord.",
        'batch_prompt': "Hoeveel codes wil je in deze batch controleren? (standaard 10000): ",
        'batch_positive': "Voer een positief geheel getal in.",
        'batch_valid': "Voer een geldig nummer in.",
        'summary_title': "Samenvatting",
        'total_checked': "Totaal gecontroleerd:",
        'valid_codes': "Geldige codes:",
        'invalid_codes': "Ongeldige codes:",
        'skipped_codes': "Overgeslagen codes:",
        'elapsed_time': "Verstreken tijd:",
        'avg_speed': "Gemiddelde snelheid:",
        'valid_codes_list': "  ╰──> Geldige codes:",
        'none': "  ╰──> [Geen]",
        'changelog': "Changelog",
        'made_by': "Gemaakt door: .gg/paterikshop.",
        'feedback': "\nWe waarderen je feedback! Laat ons weten wat je vindt of stel verbeteringen voor.\nTyp je feedback en druk op Enter (of druk op Enter om over te slaan):",
        'feedback_saved': "Bedankt! Je feedback is opgeslagen.",
        'feedback_file': "feedback.txt",
        'tutorial_userid_prompt': "Wil je een tutorial zien over hoe je je Discord User ID vindt? (j/n): ",
        'tutorial_userid': [
            "Zo vind je je Discord User ID:",
            "1. Zet Ontwikkelaarsmodus aan in Discord (Gebruikersinstellingen > Geavanceerd > Ontwikkelaarsmodus).",
            "2. Rechtsklik op je profiel in Discord en kies 'Kopieer gebruikers-ID'.",
            "3. Plak de gebruikers-ID hieronder wanneer daarom wordt gevraagd."
        ],
        'user_id_prompt': "Voer je Discord User ID in (of laat leeg om over te slaan): ",
    },
    'de': {
        'welcome': "Möchtest du Nitro-Geschenke generieren? (Drücke Enter zum Fortfahren)",
        'tutorial_prompt': "Möchtest du ein Tutorial sehen, wie du deinen Discord-Token findest? (j/n): ",
        'tutorial': [
            "So findest du deinen Discord-Token:",
            "1. Öffne Discord in deinem Webbrowser (am besten Chrome oder Edge).",
            "2. Drücke F12, um die Entwicklertools zu öffnen.",
            "3. Gehe zum Tab 'Application' (in Chrome) oder 'Storage' (in Edge/Firefox).",
            "4. Erweitere im linken Menü 'Local Storage' und klicke auf 'https://discord.com'.",
            "5. Suche nach einem Eintrag namens 'token' in der Schlüssel/Wert-Liste.",
            "6. Kopiere den Wert von 'token' (eine lange Zeichenkette).",
            "7. Füge diesen Wert in das Skript ein, wenn du dazu aufgefordert wirst.",
            "Achtung: Teile deinen Discord-Token niemals mit anderen!"
        ],
        'token_prompt': "Möchtest du jetzt deinen Discord-Token eingeben? (j/n): ",
        'token_input': "Füge hier deinen Discord-Token ein (erforderlich): ",
        'token_required': "Du musst einen Token eingeben, um fortzufahren!",
        'token_skip': "Du hast dich entschieden, keinen Token einzugeben. Der Checker läuft ohne Authentifizierung, aber du könntest von Discord eingeschränkt werden.",
        'batch_prompt': "Wie viele Codes möchtest du in diesem Durchgang prüfen? (Standard 10000): ",
        'batch_positive': "Bitte gib eine positive ganze Zahl ein.",
        'batch_valid': "Bitte gib eine gültige Zahl ein.",
        'summary_title': "Zusammenfassung",
        'total_checked': "Insgesamt geprüft:",
        'valid_codes': "Gültige Codes:",
        'invalid_codes': "Ungültige Codes:",
        'skipped_codes': "Übersprungene Codes:",
        'elapsed_time': "Verstrichene Zeit:",
        'avg_speed': "Durchschnittliche Geschwindigkeit:",
        'valid_codes_list': "  ╰──> Gültige Codes:",
        'none': "  ╰──> [Keine]",
        'changelog': "Änderungsprotokoll",
        'made_by': "Erstellt von: .gg/paterikshop.",
        'feedback': "\nWir schätzen dein Feedback! Teile uns deine Meinung oder Verbesserungsvorschläge mit.\nGib dein Feedback ein und drücke Enter (oder drücke Enter, um zu überspringen):",
        'feedback_saved': "Danke! Dein Feedback wurde gespeichert.",
        'feedback_file': "feedback.txt",
        'tutorial_userid_prompt': "Möchtest du ein Tutorial sehen, wie du deine Discord User ID findest? (j/n): ",
        'tutorial_userid': [
            "So findest du deine Discord User ID:",
            "1. Aktiviere den Entwicklermodus in Discord (Benutzereinstellungen > Erweitert > Entwicklermodus).",
            "2. Rechtsklicke auf dein Profil in Discord und wähle 'Benutzer-ID kopieren'.",
            "3. Füge die Benutzer-ID unten ein, wenn du dazu aufgefordert wirst."
        ],
        'user_id_prompt': "Gib deine Discord User ID ein (oder leer lassen zum Überspringen): ",
    },
    'fr': {
        'welcome': "Voulez-vous générer des cadeaux Nitro ? (Appuyez sur Entrée pour continuer)",
        'tutorial_prompt': "Voulez-vous voir un tutoriel pour trouver votre jeton Discord ? (o/n): ",
        'tutorial': [
            "Comment trouver votre jeton Discord:",
            "1. Ouvrez Discord dans votre navigateur (de préférence Chrome ou Edge).",
            "2. Appuyez sur F12 pour ouvrir les outils de développement.",
            "3. Allez dans l'onglet 'Application' (Chrome) ou 'Stockage' (Edge/Firefox).",
            "4. Dans le menu de gauche, développez 'Local Storage' et cliquez sur 'https://discord.com'.",
            "5. Recherchez une entrée appelée 'token' dans la liste des clés/valeurs.",
            "6. Copiez la valeur du 'token' (une longue chaîne de caractères).",
            "7. Collez cette valeur dans le script lorsque demandé.",
            "Attention : Ne partagez jamais votre jeton Discord !"
        ],
        'token_prompt': "Voulez-vous entrer votre jeton Discord maintenant ? (o/n): ",
        'token_input': "Collez ici votre jeton Discord (obligatoire): ",
        'token_required': "Vous devez entrer un jeton pour continuer !",
        'token_skip': "Vous avez choisi de ne pas entrer de jeton. Le vérificateur fonctionnera sans authentification, mais Discord peut vous limiter.",
        'batch_prompt': "Combien de codes voulez-vous vérifier dans ce lot ? (défaut 10000): ",
        'batch_positive': "Veuillez entrer un entier positif.",
        'batch_valid': "Veuillez entrer un nombre valide.",
        'summary_title': "Résumé",
        'total_checked': "Total vérifié:",
        'valid_codes': "Codes valides:",
        'invalid_codes': "Codes invalides:",
        'skipped_codes': "Codes ignorés:",
        'elapsed_time': "Temps écoulé:",
        'avg_speed': "Vitesse moyenne:",
        'valid_codes_list': "  ╰──> Codes valides:",
        'none': "  ╰──> [Aucun]",
        'changelog': "Journal des modifications",
        'made_by': "Créé par : .gg/paterikshop.",
        'feedback': "\nNous apprécions vos retours ! Faites-nous savoir ce que vous en pensez ou suggérez des améliorations.\nTapez votre retour et appuyez sur Entrée (ou appuyez sur Entrée pour passer):",
        'feedback_saved': "Merci ! Votre retour a été enregistré.",
        'feedback_file': "feedback.txt",
        'tutorial_userid_prompt': "Voulez-vous voir un tutoriel pour trouver votre identifiant Discord ? (o/n): ",
        'tutorial_userid': [
            "Comment trouver votre identifiant Discord:",
            "1. Activez le mode développeur dans Discord (Paramètres utilisateur > Avancé > Mode développeur).",
            "2. Faites un clic droit sur votre profil dans Discord et sélectionnez 'Copier l'identifiant'.",
            "3. Collez l'identifiant ci-dessous lorsque cela est demandé."
        ],
        'user_id_prompt': "Entrez votre identifiant Discord (ou laissez vide pour passer): ",
    },
    'es': {
        'welcome': "¿Quieres generar regalos de Nitro? (Presiona Enter para continuar)",
        'tutorial_prompt': "¿Quieres ver un tutorial sobre cómo encontrar tu token de Discord? (s/n): ",
        'tutorial': [
            "Cómo encontrar tu token de Discord:",
            "1. Abre Discord en tu navegador (preferiblemente Chrome o Edge).",
            "2. Presiona F12 para abrir las herramientas de desarrollador.",
            "3. Ve a la pestaña 'Application' (en Chrome) o 'Storage' (en Edge/Firefox).",
            "4. En el menú de la izquierda, expande 'Local Storage' y haz clic en 'https://discord.com'.",
            "5. Busca una entrada llamada 'token' en la lista de claves/valores.",
            "6. Copia el valor de 'token' (una cadena larga de caracteres).",
            "7. Pega este valor en el script cuando se te solicite.",
            "¡Atención! Nunca compartas tu token de Discord."
        ],
        'token_prompt': "¿Quieres ingresar tu token de Discord ahora? (s/n): ",
        'token_input': "Pega aquí tu token de Discord (obligatorio): ",
        'token_required': "¡Debes ingresar un token para continuar!",
        'token_skip': "Has elegido no ingresar un token. El verificador funcionará sin autenticación, pero Discord puede limitarte.",
        'batch_prompt': "¿Cuántos códigos quieres comprobar en este lote? (por defecto 10000): ",
        'batch_positive': "Por favor, introduce un número entero positivo.",
        'batch_valid': "Por favor, introduce un número válido.",
        'summary_title': "Resumen",
        'total_checked': "Total comprobado:",
        'valid_codes': "Códigos válidos:",
        'invalid_codes': "Códigos inválidos:",
        'skipped_codes': "Códigos omitidos:",
        'elapsed_time': "Tiempo transcurrido:",
        'avg_speed': "Velocidad media:",
        'valid_codes_list': "  ╰──> Códigos válidos:",
        'none': "  ╰──> [Ninguno]",
        'changelog': "Registro de cambios",
        'made_by': "Creado por: .gg/paterikshop.",
        'feedback': "\n¡Valoramos tus comentarios! Cuéntanos qué piensas o sugiere mejoras.\nEscribe tu comentario y presiona Enter (o solo presiona Enter para omitir):",
        'feedback_saved': "¡Gracias! Tu comentario ha sido guardado.",
        'feedback_file': "feedback.txt",
        'tutorial_userid_prompt': "¿Quieres ver un tutorial sobre cómo encontrar tu ID de usuario de Discord? (s/n): ",
        'tutorial_userid': [
            "Cómo encontrar tu ID de usuario de Discord:",
            "1. Activa el modo desarrollador en Discord (Ajustes de usuario > Avanzado > Modo desarrollador).",
            "2. Haz clic derecho en tu perfil de Discord y selecciona 'Copiar ID de usuario'.",
            "3. Pega el ID de usuario abajo cuando se te solicite."
        ],
        'user_id_prompt': "Introduce tu ID de usuario de Discord (o deja en blanco para omitir): ",
    },
    'it': {
        'welcome': "Vuoi generare regali Nitro? (Premi Invio per continuare)",
        'tutorial_prompt': "Vuoi vedere un tutorial su come trovare il tuo token Discord? (s/n): ",
        'tutorial': [
            "Come trovare il tuo token Discord:",
            "1. Apri Discord nel tuo browser (preferibilmente Chrome o Edge).",
            "2. Premi F12 per aprire gli strumenti per sviluppatori.",
            "3. Vai alla scheda 'Application' (in Chrome) o 'Storage' (in Edge/Firefox).",
            "4. Nel menu a sinistra, espandi 'Local Storage' e clicca su 'https://discord.com'.",
            "5. Cerca una voce chiamata 'token' nell'elenco delle chiavi/valori.",
            "6. Copia il valore di 'token' (una lunga stringa di caratteri).",
            "7. Incolla questo valore nello script quando richiesto.",
            "Attenzione: non condividere mai il tuo token Discord!"
        ],
        'token_prompt': "Vuoi inserire ora il tuo token Discord? (s/n): ",
        'token_input': "Incolla qui il tuo token Discord (obbligatorio): ",
        'token_required': "Devi inserire un token per continuare!",
        'token_skip': "Hai scelto di non inserire un token. Il checker funzionerà senza autenticazione, ma Discord potrebbe limitarti.",
        'batch_prompt': "Quanti codici vuoi controllare in questo batch? (predefinito 10000): ",
        'batch_positive': "Per favore, inserisci un numero intero positivo.",
        'batch_valid': "Per favore, inserisci un numero valido.",
        'summary_title': "Riepilogo",
        'total_checked': "Totale controllato:",
        'valid_codes': "Codici validi:",
        'invalid_codes': "Codici non validi:",
        'skipped_codes': "Codici saltati:",
        'elapsed_time': "Tempo trascorso:",
        'avg_speed': "Velocità media:",
        'valid_codes_list': "  ╰──> Codici validi:",
        'none': "  ╰──> [Nessuno]",
        'changelog': "Registro delle modifiche",
        'made_by': "Creato da: .gg/paterikshop.",
        'feedback': "\nApprezziamo il tuo feedback! Facci sapere cosa ne pensi o suggerisci miglioramenti.\nScrivi il tuo feedback e premi Invio (o premi Invio per saltare):",
        'feedback_saved': "Grazie! Il tuo feedback è stato salvato.",
        'feedback_file': "feedback.txt",
        'tutorial_userid_prompt': "Vuoi vedere un tutorial su come trovare il tuo ID utente Discord? (s/n): ",
        'tutorial_userid': [
            "Come trovare il tuo ID utente Discord:",
            "1. Abilita la modalità sviluppatore in Discord (Impostazioni utente > Avanzate > Modalità sviluppatore).",
            "2. Fai clic con il tasto destro sul tuo profilo Discord e seleziona 'Copia ID utente'.",
            "3. Incolla l'ID utente qui sotto quando richiesto."
        ],
        'user_id_prompt': "Inserisci il tuo ID utente Discord (o lascia vuoto per saltare): ",
    },
    'tr': {
        'welcome': "Nitro hediyeleri oluşturmak ister misiniz? (Devam etmek için Enter'a basın)",
        'tutorial_prompt': "Discord tokenınızı nasıl bulacağınızı gösteren bir eğitim görmek ister misiniz? (e/h): ",
        'tutorial': [
            "Discord tokenınızı nasıl bulursunuz:",
            "1. Discord'u web tarayıcınızda açın (tercihen Chrome veya Edge).",
            "2. Geliştirici Araçlarını açmak için F12'ye basın.",
            "3. 'Application' sekmesine (Chrome'da) veya 'Storage' sekmesine (Edge/Firefox'ta) gidin.",
            "4. Sol menüde 'Local Storage'ı genişletin ve 'https://discord.com'a tıklayın.",
            "5. Anahtar/değer listesinde 'token' adlı bir giriş arayın.",
            "6. 'token' değerini kopyalayın (uzun bir karakter dizisi olacaktır).",
            "7. Bu değeri istendiğinde script'e yapıştırın.",
            "Dikkat: Discord tokenınızı asla başkalarıyla paylaşmayın!"
        ],
        'token_prompt': "Discord tokenınızı şimdi girmek ister misiniz? (e/h): ",
        'token_input': "Discord tokenınızı buraya yapıştırın (zorunlu): ",
        'token_required': "Devam etmek için bir token girmelisiniz!",
        'token_skip': "Token girmemeyi seçtiniz. Kontrolcü kimlik doğrulama olmadan çalışacak, ancak Discord tarafından kısıtlanabilirsiniz.",
        'batch_prompt': "Bu partide kaç kod kontrol etmek istersiniz? (varsayılan 10000): ",
        'batch_positive': "Lütfen pozitif bir tam sayı girin.",
        'batch_valid': "Lütfen geçerli bir sayı girin.",
        'summary_title': "Özet Raporu",
        'total_checked': "Toplam kontrol edilen:",
        'valid_codes': "Geçerli kodlar:",
        'invalid_codes': "Geçersiz kodlar:",
        'skipped_codes': "Atlanan kodlar:",
        'elapsed_time': "Geçen süre:",
        'avg_speed': "Ortalama hız:",
        'valid_codes_list': "  ╰──> Geçerli Kodlar:",
        'none': "  ╰──> [Yok]",
        'changelog': "Değişiklik günlüğü",
        'made_by': ".gg/paterikshop tarafından yapıldı.",
        'feedback': "\nGeri bildiriminizi önemsiyoruz! Lütfen ne düşündüğünüzü veya geliştirme önerilerinizi bize bildirin.\nGeri bildiriminizi yazın ve Enter'a basın (veya atlamak için Enter'a basın):",
        'feedback_saved': "Teşekkürler! Geri bildiriminiz kaydedildi.",
        'feedback_file': "feedback.txt",
        'tutorial_userid_prompt': "Discord Kullanıcı Kimliğinizi nasıl bulacağınızı gösteren bir eğitim görmek ister misiniz? (e/h): ",
        'tutorial_userid': [
            "Discord Kullanıcı Kimliğinizi nasıl bulursunuz:",
            "1. Discord'da Geliştirici Modunu etkinleştirin (Kullanıcı Ayarları > Gelişmiş > Geliştirici Modu).",
            "2. Discord'da profilinize sağ tıklayın ve 'Kullanıcı Kimliğini Kopyala'yı seçin.",
            "3. İstendiğinde aşağıya Kullanıcı Kimliğinizi yapıştırın."
        ],
        'user_id_prompt': "Discord Kullanıcı Kimliğinizi girin (veya atlamak için boş bırakın): ",
    }
}

# --- Language Selection ---
def select_language():
    print("Select language / Kies taal / Sprache wählen / Choisir la langue / Selecciona idioma / Scegli la lingua / Dil seçin:")
    print("1. English (en)")
    print("2. Nederlands (nl)")
    print("3. Deutsch (de)")
    print("4. Français (fr)")
    print("5. Español (es)")
    print("6. Italiano (it)")
    print("7. Türkçe (tr)")
    choice = input("Enter 1-7: ").strip()
    return ['en', 'nl', 'de', 'fr', 'es', 'it', 'tr'][int(choice)-1] if choice in map(str, range(1,8)) else 'en'

if __name__ == "__main__":
    VERSION = "1.0.6"  # Update this version number as needed
    # Easter Egg: 1 in 50 chance to show a rare message/art
    if random.randint(1, 50) == 1:
        print(f"{Fore.MAGENTA}\n✨✨✨ RARE EASTER EGG! ✨✨✨\nYou found the secret Paterik Shop unicorn! 🦄\nJoin .gg/paterikshop and say 'unicorn' for a surprise!\n{Style.RESET_ALL}")
    check_for_update(VERSION)
    lang = select_language()
    T = LANGUAGES[lang]
    print(f"{Fore.LIGHTRED_EX}")
    print("")
    print("██████╗ ███████╗██╗  ██╗ ██████╗ ██████╗      ██████╗ ███████╗███╗   ██╗")
    print("██╔══██╗██╔════╝██║  ██║██╔═══██╗██╔══██╗    ██╔════╝ ██╔════╝████╗  ██║")
    print("██████╔╝███████╗███████║██║   ██║██████╔╝    ██║  ███╗█████╗  ██╔██╗ ██║")
    print("██╔═══╝ ╚════██║██╔══██║██║   ██║██╔═══╝     ██║   ██║██╔══╝  ██║╚██╗██║")
    print("██║     ███████║██║  ██║╚██████╔╝██║         ╚██████╔╝███████╗██║ ╚████║")
    print("╚═╝     ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝          ╚═════╝ ╚══════╝╚═╝  ╚═══╝")
    print("")
    # Info box (blue border, improved look)
    info_lines = [
        "Discord has removed the functionality for bots to create a server automatically.",
        "You will have to create a server manually and provide the server ID and the server you want to clone.",
        "Chance to randomly get a valid Nitro code: 1 / 4,767,240,170,682,353,345,026,333,081,600 (essentially zero)"
    ]
    max_info_len = max(len(line) for line in info_lines)
    box_width = max_info_len + 1
    print(f"{Fore.BLUE}┌{'─'*box_width}┐{Style.RESET_ALL}")
    for line in info_lines:
        print(f"{Fore.BLUE}│{Style.RESET_ALL} {line.ljust(max_info_len)} {Fore.BLUE}│{Style.RESET_ALL}")
    print(f"{Fore.BLUE}└{'─'*box_width}┘{Style.RESET_ALL}")
    print("")
    # Version box (purple border, improved look)
    version_text = f"Version: {VERSION}"
    version_box_width = len(version_text) + 4
    print(f"{Fore.MAGENTA}┌{'─'*version_box_width}┐{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}│{Style.RESET_ALL} {version_text} {Fore.MAGENTA}│{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}└{'─'*version_box_width}┘{Style.RESET_ALL}")
    print("")
    # Changelog panel (multi-language)
    print(f"{Fore.YELLOW}{'-'*60}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{T['changelog']}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{'-'*60}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}- Added multi-language support (English & Dutch) for all prompts.{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}- Added feedback prompt at the end of the script.{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}- Improved version check logic and user experience.{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}- Feedback embed now uses Paterik Shop logo as author and thumbnail, and background as footer icon.{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}- User ID ping and branding in Discord feedback improved.{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{'-'*60}{Style.RESET_ALL}")
    print("")
    print(f"{Fore.CYAN}{T['made_by']}{Style.RESET_ALL}")
    print("")
    print(T['welcome'])
    input()
    # Ask if user wants a tutorial on how to get their Discord User ID
    show_tutorial = input(T['tutorial_userid_prompt']).strip().lower()
    if show_tutorial in ("y", "j", "o", "s", "e"):  # Accept yes in all supported languages
        for line in T['tutorial_userid']:
            print(line)
        print("")
    # Prompt for Discord User ID after tutorial (or immediately if skipped)
    user_id = input(T['user_id_prompt']).strip()
    while True:
        try:
            batch_size = int(input(T['batch_prompt']) or "10000")
            if batch_size > 0:
                break
            else:
                print(T['batch_positive'])
        except ValueError:
            print(T['batch_valid'])
    CA = batch_size
    app = GiftCheckerApp('', T)  # Pass empty string for token
    app.setup()
    app.check_codes(CA)
    check_for_update(VERSION)
    # --- Feedback prompt ---
    send_feedback = input("Would you like to send feedback? (y/n): ").strip().lower()
    if send_feedback in ("y", "j"):
        feedback = input(T['feedback'])
        if feedback.strip():
            # Save to file
            with open(T['feedback_file'], "a", encoding="utf-8") as f:
                f.write(f"[{dt.now().strftime('%Y-%m-%d %H:%M:%S')}] {feedback}\n")
            # Send to Discord webhook as embed and ping if user_id was entered
            try:
                webhook_url = "https://discord.com/api/webhooks/1385343859353063514/ZXjlTF9Nwk9Cndn2y1TxAoWeScf6Zi0Wdzjor2x5V7bJJ2dRhCBkeFCWKg5yt_KARRiZ"
                import requests
                embed = {
                    "title": "🎁 New Feedback Received!",
                    "description": f"```{feedback}```",
                    "color": 0x5865F2,  # Discord blurple
                    "author": {
                        "name": "Nitro Gift Checker Feedback",
                        "icon_url": "https://cdn.discordapp.com/attachments/1372114224020459520/1385355029720076378/PATERIK_SHOP_cleaned-removebg-preview_1.png?ex=6855c3e9&is=68547269&hm=14dc02c3ca43ffd631d56b9d92bf9ce2e95a913743e096ba7305f5654aff0ad6&"
                    },
                    "fields": [
                        {"name": "Date", "value": dt.now().strftime('%Y-%m-%d %H:%M:%S'), "inline": True},
                        {"name": "Language", "value": lang, "inline": True},
                        {"name": "Version", "value": VERSION, "inline": True}
                    ],
                    "footer": {
                        "text": ".gg/paterikshop | Thank you for your feedback!",
                        "icon_url": "https://cdn.discordapp.com/attachments/1372114224020459520/1385355029720076378/PATERIK_SHOP_cleaned-removebg-preview_1.png?ex=6855c3e9&is=68547269&hm=14dc02c3ca43ffd631d56b9d92bf9ce2e95a913743e096ba7305f5654aff0ad6&"
                    },
                    "timestamp": dt.now().isoformat(),
                    "thumbnail": {
                        "url": ""
                    }
                }
                if user_id:
                    embed["fields"].append({"name": "User ID", "value": user_id, "inline": False})
                data = {"embeds": [embed]}
                if user_id:
                    data["content"] = f"<@{user_id}>"
                requests.post(webhook_url, json=data, timeout=5)
            except Exception as e:
                print(f"[!] Could not send feedback to Discord: {e}")
            print("Feedback sent, press enter to close")
            input()
        else:
            print("No feedback entered. Press enter to close.")
            input()
    else:
        print("Feedback cancelled, press enter to close.")
        input()

print("\n" + "="*50)
print("\033[95m" + "        Press Enter to close this window        " + "\033[0m")
input()