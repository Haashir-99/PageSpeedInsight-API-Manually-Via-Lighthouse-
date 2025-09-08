import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import subprocess

import gspread
import schedule
import argparse
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

load_dotenv()

# [ GOOGLE SHEET SETUP]
# - explanation: We use the service account credentials to set up the Google Sheets API.
def setup_google_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(os.getenv("GOOGLE_CREDENTIALS"), scope)
    client = gspread.authorize(creds)
    sheet = client.open('PageSpeed Insights Data').sheet1 
    return sheet


# [ URL MANAGEMENT ]
URL_FILE = "urls.json" # File to store URLs
def load_urls():
    if os.path.exists(URL_FILE):
        try:
            with open(URL_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("⚠️ Error: test.json is corrupted. Creating backup and resetting.")
            os.rename(URL_FILE, URL_FILE + ".bak")  # Create backup
            return []
    return []
def save_urls(urls):
    with open(URL_FILE, "w") as f:
        json.dump(urls, f, indent=4)
def manage_urls(args):
    urls = load_urls()

    if args.action == "add":
        if not args.url:
            print("⚠️ Please provide a URL with --url")
            return
        if args.url in urls:
            print("⚠️ URL already exists.")
            return
        urls.append(args.url)
        save_urls(urls)
        print(f"✅ Added {args.url}")

    elif args.action == "remove":
        if not args.url:
            print("⚠️ Please provide a URL with --url")
            return
        if args.url not in urls:
            print("⚠️ URL not found.")
            return
        urls = [u for u in urls if u != args.url]
        save_urls(urls)
        print(f"❌ Removed {args.url}")

    elif args.action == "list":
        if urls:
            print("📂 Current URLs:")
            for u in urls:
                print(" -", u)
        else:
            print("⚠️ No URLs saved yet.")


# [ LIGHTHOUSE SETUP]
REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

# - Function to run Lighthouse and save report
# - Explanation: Since i could not access PageSpeed Insights API, I used Lighthouse CLI to generate reports.
def run_lighthouse(url, output_dir="reports"):
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, f"report_{int(time.time())}.json")

    cmd = f"lighthouse {url} --quiet --chrome-flags=--headless --output=json --output-path={report_path}"

    try:
        subprocess.run(cmd, check=True, shell=True)
    except subprocess.CalledProcessError:
        print(f"❌ Lighthouse failed for {url}")
        return None

    return report_path

# - Function to extract metrics from Lighthouse report
def extract_metrics(report_path, url, screen_type="desktop"):
    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    metrics = {
        "url": url,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "screen_type": screen_type,
        "CLS": data["audits"]["cumulative-layout-shift"]["numericValue"],
        "TBT": data["audits"]["total-blocking-time"]["numericValue"],
        "Speed Index": data["audits"]["speed-index"]["numericValue"],
        "LCP": data["audits"]["largest-contentful-paint"]["numericValue"],
        "FCP": data["audits"]["first-contentful-paint"]["numericValue"],
    }
    return metrics

# - Function to write metrics to Google Sheet
def write_to_sheet(sheet, metrics):
    sheet.append_row([
        metrics["url"],
        metrics["date"],
        metrics["CLS"],
        metrics["TBT"],
        metrics["Speed Index"],
        metrics["LCP"],
        metrics["FCP"],
        metrics["screen_type"]
    ])


# [ MAIN TESTING LOGIC ]
def process_url(url, sheet):
    print(f"Running Lighthouse for {url}...")
    report_path = run_lighthouse(url)
    if not report_path:
        return
    metrics = extract_metrics(report_path, url, screen_type="desktop")
    write_to_sheet(sheet, metrics)
    print(f"✅ Data saved for {url}")

def run_tests():
    urls = load_urls()
    if not urls:
        print("⚠️ No URLs to test. Add some with `python script.py manage add --url <URL>`")
        return
    sheet = setup_google_sheet()
    with ThreadPoolExecutor(max_workers=3) as executor: # Multi
        executor.map(lambda url: process_url(url, sheet), urls)
    print("✔️ All tests completed.")

def start_scheduler():
    schedule.every(4).hours.do(run_tests)
    # schedule.every(1).minutes.do(run_tests)  # For testing, runs every minute
    print("⏳ Scheduler started. Running every 4 hours. Press CTRL+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(60)


# [ CLI SETUP / ENTRY POINT ]
if __name__ == "__main__":
    # Here we set up the command line interface using argparse
    parser = argparse.ArgumentParser(description="PageSpeed Insights Tool")
    subparsers = parser.add_subparsers(dest="command")

    # CLI for managing URLs
    manage_parser = subparsers.add_parser("manage", help="Manage URLs")
    manage_parser.add_argument("action", choices=["add", "remove", "list"])
    manage_parser.add_argument("--url", help="URL to add/remove")

    # CLI for running tests once
    subparsers.add_parser("run", help="Run tests immediately")

    # CLI for starting scheduler
    subparsers.add_parser("schedule", help="Start scheduler (runs every 4 hours)")

    args = parser.parse_args()

    if args.command == "manage":
        manage_urls(args)
    elif args.command == "run":
        run_tests()
    elif args.command == "schedule":
        start_scheduler()
    else:
        parser.print_help()