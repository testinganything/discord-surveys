import os
import random
import string
import requests
import time

# Configuration
BASE_URL = "https://discord.sjc1.qualtrics.com/jfe/form/SV_"
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
TESTED_LINKS_FILE = "tested_links.txt"
VALID_LINKS_FILE = "valid_links.txt"
NUM_ATTEMPTS = 100  # Number of URLs to try per run (adjust as needed)
REQUEST_DELAY = 1  # Seconds between requests to avoid rate-limiting

def load_links(filename):
    """Load links from a file."""
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_links(filename, links):
    """Save links to a file."""
    with open(filename, "w") as f:
        for link in sorted(links):
            f.write(f"{link}\n")

def generate_form_id():
    """Generate a random 15-character alphanumeric form ID."""
    characters = string.ascii_letters + string.digits  # a-z, A-Z, 0-9
    return "SV_" + "".join(random.choice(characters) for _ in range(15))

def is_valid_form(url):
    """Check if a Qualtrics form URL is valid."""
    try:
        # Send HEAD request to minimize data transfer
        response = requests.head(url, timeout=5, allow_redirects=True)
        if response.status_code == 200:
            # Verify it's a form page by checking for form content (optional GET request)
            response = requests.get(url, timeout=5)
            if "qualtrics" in response.text.lower() and "form" in response.text.lower():
                return True
        return False
    except requests.RequestException:
        return False

def send_to_discord(url):
    """Send a valid URL to the Discord webhook."""
    payload = {"content": f"New Qualtrics form found: {url}"}
    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        response.raise_for_status()
        print(f"Sent {url} to Discord")
    except requests.RequestException as e:
        print(f"Error sending {url} to Discord: {e}")

def main():
    # Load previously tested and valid links
    tested_links = load_links(TESTED_LINKS_FILE)
    valid_links = load_links(VALID_LINKS_FILE)

    new_valid_links = set()
    new_tested_links = set()

    # Generate and test URLs
    for _ in range(NUM_ATTEMPTS):
        form_id = generate_form_id()
        url = f"{BASE_URL}{form_id}"

        if url in tested_links or url in valid_links:
            continue

        print(f"Checking {url}")
        if is_valid_form(url):
            print(f"Valid form found: {url}")
            new_valid_links.add(url)
            send_to_discord(url)
        new_tested_links.add(url)

        # Delay to avoid rate-limiting
        time.sleep(REQUEST_DELAY)

    # Update link files
    if new_valid_links:
        valid_links.update(new_valid_links)
        save_links(VALID_LINKS_FILE, valid_links)
    if new_tested_links:
        tested_links.update(new_tested_links)
        save_links(TESTED_LINKS_FILE, tested_links)

    print(f"Checked {len(new_tested_links)} URLs, found {len(new_valid_links)} valid forms.")

if __name__ == "__main__":
    main()
