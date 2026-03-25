# Screener.in Multi-Page Scraping SOP

## Mission
Log into screener.in, navigate to "The Quick Formulae" screen, and scrape EVERY SINGLE PAGE of the data table (all 300+ entries, not just the first 25) into a single CSV file, then push it to GitHub.

## Execution Steps (Follow Exactly):
1. **Login:** Open `https://www.screener.in/login/`. Take a snapshot. Use `action="act"` to type `ersakshamjain@gmail.com` into the email field and `Computer7@` into the password field. Click the Login button.
2. **Navigate:** Go to `https://www.screener.in/screens/` and click "The Quick Formulae". Wait for the table to load.
3. **Initialize CSV:** Before scraping, run `exec` to create an empty file: `echo "" > screener_quick_formulae_full.csv`.
4. **Scraping Loop:** You must loop through ALL pages of the data table.
   a. Extract the current page's table data using `action="act"` with this exact JS evaluation:
      `request: {"kind": "evaluate", "fn": "() => { let csv = []; let rows = document.querySelectorAll('table tr'); for (let row of rows) { let cols = row.querySelectorAll('td, th'); let rowData = []; for (let col of cols) { rowData.push('\"' + col.innerText.replace(/\"/g, '\"\"').trim() + '\"'); } csv.push(rowData.join(',')); } return csv.join('\\n'); }"}`
   b. Use `exec` to append the extracted CSV string to `screener_quick_formulae_full.csv`.
   c. **Pagination:** Take a snapshot. Look for the "Next" button or the pagination numbers (e.g., page 2, 3, 4...) at the bottom of the table. Use `action="act"` with `kind="click"` to click the "Next" button or the next page number. 
   d. Wait a few seconds for the new page to load.
   e. Repeat steps (a) through (d) until the "Next" button is disabled or no longer exists (meaning you have reached the end of the 300+ entries).
5. **Deduplication & Cleanup (CRITICAL):** Because you appended the headers on every page, run this `exec` command to clean the file:
   `awk '!seen[$0]++' screener_quick_formulae_full.csv > screener_quick_formulae.csv`
6. **Push:** Run `git add screener_quick_formulae.csv && git commit -m "Add FULL 300+ entries of Screener.in Quick Formulae" && git push origin master`.
7. **Close:** Close the browser tab. Do not stop until all pages are scraped and pushed.
