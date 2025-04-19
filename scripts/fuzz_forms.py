import os
import random
import string
import requests
import time

# Configuration
BASE_URL = "https://discord.sjc1.qualtrics.com/jfe/form/"
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
TESTED_LINKS_FILE = "tested_links.txt"
VALID_LINKS_FILE = "valid_links.txt"
NUM_ATTEMPTS = 100000
REQUEST_DELAY = 1

def load_links(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_links(filename, links):
    with open(filename, "w") as f:
        for link in sorted(links):
            f.write(f"{link}\n")

def generate_form_id():
    return "SV_" + "".join(random.choices(string.ascii_letters + string.digits, k=15))

def is_valid_form(url):
    """Check if the Qualtrics form exists and is usable."""
    try:
        response = requests.get(url, timeout=5)
        text = response.text.lower()
        print(f"GET {url}: Status {response.status_code}")

        if response.status_code == 200:
            if "survey not found" in text:
                print(f"Invalid form (Survey Not Found): {url}")
                return False
            if "qualtrics" in text and ("form" in text or "survey" in text):
                return True
        return False
    except requests.RequestException as e:
        print(f"Error accessing {url}: {e}")
        return False

def send_to_discord(url):
    """Notify Discord about a valid form."""
    payload = {"content": f"🚀 **New working Qualtrics form found:** {url}"}
    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        response.raise_for_status()
        print(f"Sent notification for {url}")
    except requests.RequestException as e:
        print(f"Failed to send Discord message: {e}")

def main():
    tested_links = load_links(TESTED_LINKS_FILE)
    valid_links = load_links(VALID_LINKS_FILE)

    new_valid_links = set()
    new_tested_links = set()

    for _ in range(NUM_ATTEMPTS):
        form_id = generate_form_id()
        url = f"{BASE_URL}{form_id}"

        if url in tested_links or url in valid_links:
            print(f"Skipping known URL: {url}")
            continue

        print(f"Testing URL: {url}")
        if is_valid_form(url):
            print(f"✅ Valid form: {url}")
            new_valid_links.add(url)
            send_to_discord(url)
        new_tested_links.add(url)

        time.sleep(REQUEST_DELAY)

    if new_valid_links:
        valid_links.update(new_valid_links)
        save_links(VALID_LINKS_FILE, valid_links)
    if new_tested_links:
        tested_links.update(new_tested_links)
        save_links(TESTED_LINKS_FILE, tested_links)

    print(f"\n🎯 Done: {len(new_tested_links)} URLs tested, {len(new_valid_links)} new valid forms found.")

if __name__ == "__main__":
    main()
