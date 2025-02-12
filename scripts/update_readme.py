import json
import os

BALANCES_FILE = "data/balances.json"
README_FILE = "README.md"
REPO_OWNED = "figuran04"
REPO_NAME = "gtcscan"

GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")

def load_balances():
    if not os.path.exists(BALANCES_FILE):
        return {}

    try:
        with open(BALANCES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def format_balance(value):
    return "{:.10f}".format(float(value)).rstrip('0').rstrip('.') if '.' in "{:.10f}".format(float(value)) else "{:.10f}".format(float(value))

def generate_user_table(balances):    
    if not balances:
        return "Tidak ada data user.\n"

    users = list(balances.items())[:10]

    table = "| Username | Balance | Kirim |\n"
    table += "|----------|---------|-------|\n"

    for user, data in users:
        balance = format_balance(data.get("balance", 0))
        send_link = f"[Kirim](https://github.com/{GITHUB_REPOSITORY}/issues/new?title=Kirim+1.23+GTC+ke+@{user}&body=Nominal+dapat+diganti+terlebih+dahulu+sebelum+mengirim+dan+menunggu+transaksi+divalidasi)"
        table += f"| [{user}](https://{REPO_OWNED}.github.io/{REPO_NAME}/?q={user}) | {balance} GTC | {send_link} |\n"

    return "**10 User Teratas:**\n\n" + table

def update_readme():
    balances = load_balances()

    user_table = generate_user_table(balances)

    info_text = (
        "Ingin mengirim GTC ke pengguna lain? Pastikan Anda memiliki saldo.\n"
        "Dapatkan koin gratis dari miner dengan klik "
        f"[di sini](https://github.com/{GITHUB_REPOSITORY}/issues/new?title=Terima+dari+@github-action&body=Cukup+kirim+dan+menunggu+transaksi+divalidasi).\n\n"
        f"> Cek transaksi Anda [di sini](https://{REPO_OWNED}.github.io/{REPO_NAME}).\n\n"
    )

    if os.path.exists(README_FILE):
        with open(README_FILE, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = ""

    if "<!--user:start-->" in content and "<!--user:end-->" in content:
        before = content.split("<!--user:start-->")[0]
        after = content.split("<!--user:end-->")[-1]
        new_content = f"{before}<!--user:start-->\n\n{info_text}{user_table}\n\n<!--user:end-->\n{after}"
    else:
        new_content = content + f"\n\n<!--user:start-->\n\n{info_text}{user_table}\n\n<!--user:end-->\n"

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("README.md berhasil diperbarui!")

if __name__ == "__main__":
    update_readme()