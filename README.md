# PageSpeed Insights Automation Tool

A Python-based CLI tool that automates running Google Lighthouse audits on a list of URLs, extracts key performance metrics, and saves the results into a Google Sheet.

## Features:  
📂 Manage URLs (add / remove / list) via CLI  
⚡ Run Lighthouse tests on demand  
⏳ Schedule automatic runs (default every 4 hours)  
📊 Export results directly into Google Sheets  
🔑 Secure configuration via .env file (no hard-coded values)  

## Prerequisites: 

Before running this project make sure you have installed:  
- [Python 3.10+]([url](https://www.python.org/downloads/))  
- [Node.js + npm]([url](https://nodejs.org/en/download/)) (needed for lighthouse)  
- Lighthouse installed globally:  

  ```bash
  npm install -g lighthouse
  ```

## Setup:

1. Clone the repository
   
   ```bash
    git clone <your-repo-url>
    cd <repo-folder>
    ```
2. Install Dependencies

   ```bash
   pip install -r requirements.txt
   ```
3. Create a .env file in the project root

   ```env
   GOOGLE_CREDENTIALS=C:\path\to\your\service_account.json
   ```
   ⚠️ Do not commit this file to GitHub
4. Share your google sheet
    - Create a Google Sheet named ```PageSpeed Insights Data```
    - Share it with the email inside your service account JSON
  
## Usage:

1. Manage URLs

   Add a URL:
   ```bash
   python script.py manage add --url https://example.com
   ```
   Remove a URL:
   ```bash
   python script.py manage remove --url https://example.com
   ```
   List all URLs:
   ```bash
   python script.py manage list
   ```
2. Run Tests Immediately
   ```bash
   python script.py run
   ```
3. Start Scheduler (runs every 4 hours)
   
   ```bash
   python script.py schedule
   ```

## Output
- Lighthouse JSON reports are saved in the reports/ folder.
- Extracted metrics are appended into the Google Sheet with columns:

  ```pgsql
  URL | Date | CLS | TBT | Speed Index | LCP | FCP | Screen Type
  ```
## License
MIT
