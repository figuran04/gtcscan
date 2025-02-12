import hashlib
import json
import time
import os

# Nama file
blockchain_file = "data/blockchain.json"
balances_file = "data/balances.json"
mempool_file = "data/mempool.json"
readme_file = "README.md"

initial_reward = 9.589  # Reward awal sebelum halving

# Fungsi hashing transaksi untuk mendapatkan txid
def generate_txid(tx):
    tx_string = f"{tx['from']}{tx['to']}{tx['amount']}{tx['timestamp']}"
    return hashlib.sha256(tx_string.encode()).hexdigest()

# Fungsi memuat blockchain dari file
def load_blockchain():
    if os.path.exists(blockchain_file):
        try:
            with open(blockchain_file, "r") as f:
                data = f.read().strip()
                if not data:
                    raise ValueError("File blockchain kosong")
                return json.loads(data)
        except (json.JSONDecodeError, ValueError):
            print("📛 File blockchain rusak atau kosong. Menginisialisasi ulang...")
    
    return initialize_blockchain()

# Fungsi menyimpan blockchain ke file
def save_blockchain(blockchain):
    with open(blockchain_file, "w") as f:
        json.dump(blockchain, f, indent=4)

# Fungsi memuat saldo dari file
def load_balances():
    if os.path.exists(balances_file):
        try:
            with open(balances_file, "r") as f:
                balances = json.load(f)
                # Pastikan github-action memiliki format baru
                if "github-action" not in balances or isinstance(balances["github-action"], (int, float)):
                    balances["github-action"] = {"balance": balances.get("github-action", 0), "last_transaction": None}
                return balances
        except json.JSONDecodeError:
            print("📛 File balances.json rusak, menginisialisasi ulang...")
    
    balances = {"github-action": {"balance": 0, "last_transaction": None}}
    save_balances(balances)
    return balances

# Fungsi menyimpan saldo ke file dengan urutan berdasarkan transaksi terbaru
def save_balances(balances):
    sorted_balances = dict(sorted(
        balances.items(),
        key=lambda item: item[1]["last_transaction"] or "1970-01-01T00:00:00Z",
        reverse=True
    ))

    with open(balances_file, "w") as f:
        json.dump(sorted_balances, f, indent=4)

# Fungsi memuat transaksi dari mempool
def load_mempool():
    if os.path.exists(mempool_file):
        try:
            with open(mempool_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("📛 File mempool.json rusak, mengosongkan...")
    
    return []  # Jika file tidak ada atau rusak, kembalikan list kosong

# Fungsi menyimpan transaksi ke mempool
def save_mempool(mempool):
    with open(mempool_file, "w") as f:
        json.dump(mempool, f, indent=4)


# Fungsi memperbarui README.md dengan informasi blockchain
def update_readme(blockchain, balances):
    total_blocks = len(blockchain["blocks"])
    last_block = blockchain["blocks"][-1]
    total_supply = sum(user["balance"] for user in balances.values())

    blockchain_info = f"""
**🛠 Blockchain Status**
- 📦 **Total Blok**: {total_blocks}
- 🔗 **Hash Blok Terakhir**: {last_block["hash"]}
- ⏳ **Waktu Blok Terakhir**: {last_block["timestamp"]}
- 💰 **Supply Beredar**: {total_supply} GTC
"""

    if os.path.exists(readme_file):
        with open(readme_file, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = ""

    start_tag = "<!--blockchain:start-->"
    end_tag = "<!--blockchain:end-->"

    if start_tag in content and end_tag in content:
        updated_content = content.split(start_tag)[0] + start_tag + "\n" + blockchain_info + "\n" + end_tag + content.split(end_tag)[1]
    else:
        updated_content = content + f"\n\n{start_tag}\n{blockchain_info}\n{end_tag}\n"

    with open(readme_file, "w", encoding="utf-8") as f:
        f.write(updated_content)

# Fungsi hashing blok
def generate_hash(index, timestamp, transactions, prev_hash):
    data = f"{index}{timestamp}{json.dumps(transactions, sort_keys=True)}{prev_hash}".encode()
    return hashlib.sha256(data).hexdigest()

# Fungsi pemberian hadiah blok dengan metode halving
def distribute_miner_reward(blockchain):
    halvings = len(blockchain["blocks"]) // 365  # Halving setiap 365 blok
    reward = initial_reward / (2 ** halvings)
    miner_reward = round(reward, 10)

    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    tx = {
        "from": "coinbase",
        "to": "github-action",
        "amount": miner_reward,
        "timestamp": timestamp
    }
    tx["txid"] = generate_txid(tx)

    return tx, timestamp

# Fungsi menambang blok baru
def mine_block():
    blockchain = load_blockchain()
    balances = load_balances()
    mempool = load_mempool()  # Ambil transaksi dari mempool

    prev_hash = blockchain["blocks"][-1]["hash"] if blockchain["blocks"] else "0000"

    # Tambahkan transaksi coinbase untuk hadiah miner
    coinbase_tx, timestamp = distribute_miner_reward(blockchain)
    all_transactions = [coinbase_tx] + mempool  # Gabungkan transaksi dari mempool dengan hadiah penambang

    # Perbarui saldo miner
    if "github-action" not in balances:
        balances["github-action"] = {"balance": 0, "last_transaction": None}

    balances["github-action"]["balance"] += coinbase_tx["amount"]
    balances["github-action"]["last_transaction"] = timestamp

    # Update saldo penerima dari transaksi di mempool
    # for tx in mempool:
    #     sender = tx["from"]
    #     recipient = tx["to"]
    #     amount = tx["amount"]

    #     # Kurangi saldo pengirim jika bukan "coinbase"
    #     if sender != "coinbase" and sender in balances:
    #         balances[sender]["balance"] -= amount

    #     # Tambahkan saldo penerima
    #     if recipient not in balances:
    #         balances[recipient] = {"balance": 0, "last_transaction": None}

    #     balances[recipient]["balance"] += amount
    #     balances[recipient]["last_transaction"] = timestamp

    # Buat blok baru
    index = len(blockchain["blocks"])
    hash_value = generate_hash(index, timestamp, all_transactions, prev_hash)

    block = {
        "index": index,
        "timestamp": timestamp,
        "transactions": all_transactions,
        "hash": hash_value,
        "prevHash": prev_hash
    }

    blockchain["blocks"].append(block)
    save_blockchain(blockchain)
    save_balances(balances)

    # Kosongkan mempool setelah transaksi masuk ke blockchain
    save_mempool([])

    # Perbarui README dengan status blockchain terbaru
    update_readme(blockchain, balances)

    print(f"✅ Blok #{index} berhasil ditambang! Miner mendapatkan {coinbase_tx['amount']} BTC.")
    print(f"📜 {len(mempool)} transaksi telah dikonfirmasi dalam blok ini.")

# Fungsi inisialisasi blockchain dengan blok genesis (dengan transaksi coinbase)
def initialize_blockchain():
    balances = load_balances()

    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    genesis_tx = {
        "from": "coinbase",
        "to": "github-action",
        "amount": initial_reward,
        "timestamp": timestamp
    }
    genesis_tx["txid"] = generate_txid(genesis_tx)

    if "github-action" not in balances:
        balances["github-action"] = {"balance": 0, "last_transaction": None}

    balances["github-action"]["balance"] = initial_reward
    balances["github-action"]["last_transaction"] = timestamp

    genesis_block = {
        "index": 0,
        "timestamp": timestamp,
        "transactions": [genesis_tx],
        "hash": "00000000000000000000000000000000",
        "prevHash": "None"
    }

    blockchain = {"blocks": [genesis_block]}
    save_blockchain(blockchain)
    save_balances(balances)

    return blockchain

# CLI untuk menambang blok
if __name__ == "__main__":
    mine_block()