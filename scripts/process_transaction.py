import hashlib
import os
import json
import time
import requests
import re
import random

REPO_OWNED = "figuran04"
REPO_NAME = "gtcscan"
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

MEMPOOL_FILE = "data/mempool.json"
BALANCES_FILE = "data/balances.json"
DEFAULT_BALANCES = {"github-action": {"balance": 0, "last_transaction": None}}


def load_json(file_path, default):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return default


def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)


def generate_txid(sender, recipient, amount, timestamp):
    return hashlib.sha256(f"{sender}{recipient}{amount}{timestamp}".encode()).hexdigest()


def add_transaction(sender, recipient, amount):
    balances = load_json(BALANCES_FILE, DEFAULT_BALANCES)
    if sender == recipient or sender not in balances or balances[sender]["balance"] < amount:
        return None
    
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    balances[sender]["balance"] -= amount
    balances[sender]["last_transaction"] = timestamp
    
    if recipient not in balances:
        balances[recipient] = {"balance": 0, "last_transaction": None}
    
    balances[recipient]["balance"] += amount
    balances[recipient]["last_transaction"] = timestamp
    
    txid = generate_txid(sender, recipient, amount, timestamp)
    
    mempool = load_json(MEMPOOL_FILE, [])
    mempool.append({"from": sender, "to": recipient, "amount": amount, "timestamp": timestamp, "txid": txid})
    
    save_json(MEMPOOL_FILE, mempool)
    save_json(BALANCES_FILE, balances)
    return txid


def process_issue():
    issues_url = f"https://api.github.com/repos/{GITHUB_REPO}/issues?state=open"
    response = requests.get(issues_url, headers=HEADERS)
    issues = response.json()
    
    for issue in issues:
        title, issue_number, username = issue["title"], issue["number"], issue["user"]["login"]
        txid = None
        
        if title.startswith("Terima dari @github-action"):
            balances = load_json(BALANCES_FILE, DEFAULT_BALANCES)
            max_amount = balances["github-action"]["balance"] / 3
            if max_amount > 0:
                random_amount = round(random.uniform(0.001, max_amount), 6)
                txid = add_transaction("github-action", username, random_amount)
        elif match := re.match(r"Kirim ([\d\.]+) GTC ke @([\w-]+)", title):
            amount, recipient = float(match.group(1)), match.group(2)
            txid = add_transaction(username, recipient, amount)
        
        comment_body = f"✅ Transaksi berhasil! TXID: [{txid}](https://{REPO_OWNED}.github.io/{REPO_NAME}/?q={txid})" if txid else "❌ Transaksi gagal!"
        requests.post(f"https://api.github.com/repos/{GITHUB_REPO}/issues/{issue_number}/comments", json={"body": comment_body}, headers=HEADERS)
        requests.patch(f"https://api.github.com/repos/{GITHUB_REPO}/issues/{issue_number}", json={"state": "closed"}, headers=HEADERS)


if __name__ == "__main__":
    process_issue()
