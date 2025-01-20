import threading
import time
import sys
import json
from typing import List, Dict, Optional
from curl_cffi import requests
from colorama import Fore, Style, init
import os

# Initialize colorama for colored console output
init(autoreset=True)

# Lock for synchronized access to shared data
data_lock = threading.Lock()

# Lock for synchronized printing
print_lock = threading.Lock()

class Colors:
    SUCCESS = Fore.GREEN
    ERROR = Fore.RED
    INFO = Fore.CYAN
    WARNING = Fore.YELLOW
    RESULT = Fore.LIGHTMAGENTA_EX
    PING = Fore.GREEN
    POINTS = Fore.YELLOW
    STATUS = Fore.CYAN
    PROXY = Fore.BLACK
    NEXT_PING = Fore.GREEN
    RESET = Style.RESET_ALL

class Account:
    def __init__(self, index: int, email: str, password: str, token: str, proxy: str):
        self.index = index
        self.email = email
        self.password = password
        self.token = token
        self.proxy = proxy
        self.total_ping = 0
        self.points = {
            'activeStreak': 0,
            'points': 0,
            'registerpoints': 0,
            'signinpoints': 0,
            'twitter_x_id_points': 0,
            'discordid_points': 0,
            'telegramid_points': 0
        }
        self.total_points = 0  # New attribute for total points
        self.status = "Initializing"
        self.next_ping_time = time.time()  # Initialize next ping time to current time

def read_account_info(filename: str) -> List[Dict[str, str]]:
    """
    Reads the account_info.txt file and parses each line into a dictionary.
    Expected format per line: email|password|token
    """
    accounts = []
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
            for idx, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                parts = line.split('|')
                if len(parts) < 3:
                    with print_lock:
                        print(f"{Colors.WARNING}Warning: Invalid account line {idx}: {line}{Colors.RESET}")
                    continue
                email, password, token = parts[:3]
                accounts.append({'email': email, 'password': password, 'token': token})
    except FileNotFoundError:
        with print_lock:
            print(f"{Colors.ERROR}Error: '{filename}' not found.{Colors.RESET}")
        sys.exit(1)
    return accounts

def read_proxies(filename: str) -> List[str]:
    """
    Reads the proxy.txt file and returns a list of proxies.
    """
    proxies = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                proxy = line.strip()
                if proxy:
                    proxies.append(proxy)
    except FileNotFoundError:
        with print_lock:
            print(f"{Colors.ERROR}Error: '{filename}' not found.{Colors.RESET}")
        sys.exit(1)
    return proxies

def format_proxy(proxy: str) -> Dict[str, str]:
    """
    Formats the proxy string into a dictionary suitable for requests.
    Supports:
    - http://ip:port
    - http://user:pass@ip:port
    """
    return {
        'http': proxy,
        'https': proxy
    }

def clear_console():
    """
    Clears the console screen based on the operating system.
    """
    os.system('cls' if os.name == 'nt' else 'clear')

def perform_keepalive(session: requests.Session, account: Account) -> Optional[Dict]:
    """
    Performs the Keepalive POST request.
    """
    url = 'https://www.aeropres.in/chromeapi/dawn/v1/userreward/keepalive'
    params = {'appid': '675459ef292ee78c04e714fe'}
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Authorization': f'Bearer {account.token}',  # Corrected 'Berear' to 'Bearer'
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json',
        'Origin': 'chrome-extension://fpdkjdnhkakefebpekbdhillbhonfjjp',
        'Pragma': 'no-cache',
        'Priority': 'u=1, i',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    }
    data = {
        "username": account.email,
        "extensionid": "fpdkjdnhkakefebpekbdhillbhonfjjp",
        "numberoftabs": 0,
        "_v": "1.1.2"
    }
    try:
        response = session.post(url, params=params, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            try:
                return response.json()
            except json.JSONDecodeError:
                with print_lock:
                    print(f"{account.index}. {account.email} | Keepalive Response is not valid JSON | Proxy: {account.proxy}")
                return None
        else:
            with print_lock:
                print(f"{account.index}. {account.email} | Keepalive HTTP Error: {response.status_code} | Proxy: {account.proxy}")
            return None
    except Exception as e:
        with print_lock:
            print(f"{account.index}. {account.email} | Keepalive Exception: {str(e)} | Proxy: {account.proxy}")
        return None

def perform_getpoint(session: requests.Session, account: Account) -> Optional[Dict]:
    """
    Performs the GetPoint GET request.
    """
    url = 'https://www.aeropres.in/api/atom/v1/userreferral/getpoint'
    params = {'appid': '675459ef292ee78c04e714fe'}
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Authorization': f'Bearer {account.token}',  # Corrected 'Berear' to 'Bearer'
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json',
        'Origin': 'chrome-extension://fpdkjdnhkakefebpekbdhillbhonfjjp',
        'Pragma': 'no-cache',
        'Priority': 'u=1, i',
        'Sec-Ch-Ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    }
    try:
        response = session.get(url, params=params, headers=headers, timeout=30)
        if response.status_code == 200:
            try:
                json_response = response.json()
                return json_response
            except json.JSONDecodeError:
                return None
        else:
            return None
    except Exception:
        return None

def update_points(account: Account, data: Dict):
    """
    Updates the account's points based on the GetPoint response and calculates total points.
    """
    referralPoint = data.get('referralPoint', {})
    rewardPoint = data.get('rewardPoint', {})
    account.points['activeStreak'] = rewardPoint.get('activeStreak', 0)
    account.points['points'] = rewardPoint.get('points', 0)
    account.points['registerpoints'] = rewardPoint.get('registerpoints', 0)
    account.points['signinpoints'] = rewardPoint.get('signinpoints', 0)
    account.points['twitter_x_id_points'] = rewardPoint.get('twitter_x_id_points', 0)
    account.points['discordid_points'] = rewardPoint.get('discordid_points', 0)
    account.points['telegramid_points'] = rewardPoint.get('telegramid_points', 0)
    
    # Calculate total points
    account.total_points = (
        account.points['points'] +
        account.points['registerpoints'] +
        account.points['signinpoints'] +
        account.points['twitter_x_id_points'] +
        account.points['discordid_points'] +
        account.points['telegramid_points']
    )

def account_worker(account: Account, status_dict: Dict):
    """
    The worker function for each account running in its own thread.
    """
    session = requests.Session()
    session.headers.update({
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Authorization': f'Bearer {account.token}',  # Corrected 'Berear' to 'Bearer'
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json',
        'Origin': 'chrome-extension://fpdkjdnhkakefebpekbdhillbhonfjjp',
        'Pragma': 'no-cache',
        'Priority': 'u=1, i',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    })
    session.proxies = format_proxy(account.proxy)

    # Define what statuses are considered as success
    success_statuses = {True, "true", "success", "Success"}

    while True:
        success = False
        # Attempt Keepalive and GetPoint
        while not success:
            keepalive_response = perform_keepalive(session, account)
            if keepalive_response and keepalive_response.get('success'):
                account.total_ping += 1
                getpoint_response = perform_getpoint(session, account)
                if getpoint_response and getpoint_response.get('status') in success_statuses:
                    data = getpoint_response.get('data', {})
                    if data:
                        update_points(account, data)
                        with print_lock:
                            print(f"{account.index}. {account.email} | Points Updated: {account.total_points} | Proxy: {account.proxy}")
                    else:
                        # Handle case where data is None but success is True
                        with print_lock:
                            print(f"{account.index}. {account.email} | Keep alive recorded but no data received | Proxy: {account.proxy}")
                    success = True
                    with data_lock:
                        status_dict[account.index] = {
                            'email': account.email,
                            'ping': account.total_ping,
                            'points': account.total_points,  # Use total_points here
                            'proxy': account.proxy,
                            'next_ping_time': time.time() + 120,  # **Changed from 300 to 120 seconds**
                            'status': "Ping Success"
                        }
                else:
                    message = getpoint_response.get('message', 'No message') if getpoint_response else 'No response'
                    with data_lock:
                        status_dict[account.index] = {
                            'email': account.email,
                            'ping': account.total_ping,
                            'points': account.total_points,
                            'proxy': account.proxy,
                            'next_ping_time': time.time() + 120,  # **Changed from 300 to 120 seconds**
                            'status': f"GetPoint Failed"
                        }
                    with print_lock:
                        print(f"{account.index}. {account.email} | GetPoint Failed: {message} | Proxy: {account.proxy}")
                    time.sleep(2)  # Wait before retrying
            else:
                message = keepalive_response.get('message', 'No message') if keepalive_response else 'No response'
                with data_lock:
                    status_dict[account.index] = {
                        'email': account.email,
                        'ping': account.total_ping,
                        'points': account.total_points,
                        'proxy': account.proxy,
                        'next_ping_time': time.time() + 120,  # **Changed from 300 to 120 seconds**
                        'status': f"Ping Failed"
                    }
                with print_lock:
                    print(f"{account.index}. {account.email} | Keepalive Failed: {message} | Proxy: {account.proxy}")
                time.sleep(2)  # Wait before retrying

        # Calculate sleep time until next ping
        sleep_duration = max(0, status_dict[account.index]['next_ping_time'] - time.time())
        if sleep_duration > 0:
            time.sleep(sleep_duration)

def display_status(status_dict: Dict):
    """
    Periodically clears the console and displays the status of all accounts.
    """
    while True:
        clear_console()
        print(f"{Colors.INFO}Account Status:{Colors.RESET}")
        print("-" * 100)
        with data_lock:
            for index in sorted(status_dict.keys()):
                status = status_dict[index]
                email = status['email']
                ping = status['ping']
                points = status['points']  # This will now reflect total_points
                proxy = status['proxy']
                next_ping_time = status['next_ping_time']
                status_message = status['status']
                next_ping_in = int(next_ping_time - time.time())
                if next_ping_in < 0:
                    next_ping_in = 0
                mins, secs = divmod(next_ping_in, 60)
                # Apply colors to each field
                colored_ping = f"{Colors.PING}Ping: {ping}{Colors.RESET}"
                colored_points = f"{Colors.POINTS}Points: {points}{Colors.RESET}"
                colored_status = f"{Colors.STATUS}{status_message}{Colors.RESET}"
                colored_proxy = f"{Colors.RESULT}Proxy: {proxy}{Colors.RESET}"
                colored_next_ping = f"{Colors.NEXT_PING}Next Ping in: {mins}m {secs}s{Colors.RESET}"
                print(f"{index}. {email} | {colored_ping} | {colored_points} | {colored_status} | {colored_proxy} | {colored_next_ping}")
        print("-" * 100)
        time.sleep(5)  # Update every 5 seconds

def main():
    """
    Main function to initialize accounts, proxies, and start worker and display threads.
    """
    # Read account_info.txt
    accounts_data = read_account_info('account_info.txt')
    if not accounts_data:
        with print_lock:
            print(f"{Colors.ERROR}No valid accounts found in 'account_info.txt'. Exiting.{Colors.RESET}")
        sys.exit(1)

    # Read proxy.txt
    proxies = read_proxies('proxy.txt')
    if not proxies:
        with print_lock:
            print(f"{Colors.ERROR}No proxies found in 'proxy.txt'. Exiting.{Colors.RESET}")
        sys.exit(1)

    if len(proxies) < len(accounts_data):
        with print_lock:
            print(f"{Colors.ERROR}Error: Not enough proxies for the number of accounts. Each account requires a unique proxy.{Colors.RESET}")
        sys.exit(1)

    # Assign proxies to accounts
    accounts = []
    status_dict = {}
    for idx, acc in enumerate(accounts_data, 1):
        proxy = proxies[idx - 1]
        # Ensure proxy has http scheme
        if not proxy.startswith(('http://', 'https://', 'socks4://', 'socks5://')):
            proxy = 'http://' + proxy
        account = Account(index=idx, email=acc['email'], password=acc['password'], token=acc['token'], proxy=proxy)
        accounts.append(account)
        # Initialize status
        status_dict[account.index] = {
            'email': account.email,
            'ping': account.total_ping,
            'points': account.points['points'],
            'proxy': account.proxy,
            'next_ping_time': account.next_ping_time,
            'status': "Initializing"
        }

    with print_lock:
        print(f"{Colors.SUCCESS}✓ Loaded {len(accounts)} accounts with proxies.{Colors.RESET}")

    # Start display thread
    display_thread = threading.Thread(target=display_status, args=(status_dict,), daemon=True)
    display_thread.start()

    # Start account threads
    for account in accounts:
        t = threading.Thread(target=account_worker, args=(account, status_dict), daemon=True)
        t.start()

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        with print_lock:
            print(f"\n{Colors.WARNING}Script terminated by user.{Colors.RESET}")
        sys.exit(0)

if __name__ == "__main__":
    main()
