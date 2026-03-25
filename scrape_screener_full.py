import asyncio
from playwright.async_api import async_playwright
import csv
import subprocess

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        page = await context.new_page()

        print("Navigating to login...")
        await page.goto("https://www.screener.in/login/")

        print("Filling credentials...")
        await page.fill("input[name='username']", "ersakshamjain@gmail.com")
        await page.fill("input[name='password']", "Computer7@")
        
        await page.click("button[type='submit']")
        await page.wait_for_load_state("networkidle")
        
        # Check if login was successful
        if "login" in page.url:
            print("First password failed. Trying second...")
            await page.fill("input[name='username']", "ersakshamjain@gmail.com")
            await page.fill("input[name='password']", "SAPSAK2000")
            await page.click("button[type='submit']")
            await page.wait_for_load_state("networkidle")

        print("Navigating to screens...")
        await page.goto("https://www.screener.in/screens/")
        await page.wait_for_load_state("networkidle")
        
        # Find "The Quick Formulae"
        link_element = await page.query_selector("text='The Quick Formulae'")
        if not link_element:
            link_element = await page.query_selector("text='Quick Formulae'")
            
        if link_element:
            href = await link_element.get_attribute("href")
            full_url = f"https://www.screener.in{href}"
            print(f"Found screen URL: {full_url}")
        else:
            print("Could not find the link on the screens page. Guessing public URL...")
            full_url = "https://www.screener.in/screens/249580/the-quick-formulae/"

        await page.goto(full_url)
        await page.wait_for_load_state("networkidle")

        all_data = []
        page_num = 1
        
        while True:
            print(f"Scraping page {page_num}...")
            
            # Extract table data
            table_data = await page.evaluate("""() => {
                let rows = document.querySelectorAll('table tr');
                let data = [];
                for (let row of rows) {
                    let cols = row.querySelectorAll('th, td');
                    let rowData = [];
                    for (let col of cols) {
                        rowData.push(col.innerText.trim());
                    }
                    data.push(rowData);
                }
                return data;
            }""")
            
            if page_num == 1:
                all_data.extend(table_data) # Include headers
            else:
                all_data.extend(table_data[1:]) # Skip headers on subsequent pages
                
            # Check for next button
            next_button = await page.query_selector("a:has-text('Next')")
            if next_button:
                print("Clicking Next...")
                await next_button.click()
                await page.wait_for_load_state("networkidle")
                page_num += 1
            else:
                print("No more pages.")
                break

        print(f"Extracted {len(all_data) - 1} total rows.")
        
        csv_file = "screener_quick_formulae_full.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(all_data)
            
        print("Data saved to CSV. Pushing to GitHub...")
        try:
            subprocess.run(['git', 'add', csv_file])
            subprocess.run(['git', 'commit', '-m', f'Add FULL {len(all_data)-1} entries of Screener Quick Formulae'])
            subprocess.run(['git', 'push', 'origin', 'master'])
            print("GitHub push successful!")
        except Exception as e:
            print(f"Git error: {e}")

        await browser.close()

asyncio.run(run())
