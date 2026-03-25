import requests
from bs4 import BeautifulSoup
import csv
import subprocess

def scrape_screener():
    session = requests.Session()
    
    # 1. Get login page to grab CSRF token
    login_url = "https://www.screener.in/login/"
    print("Fetching login page...")
    res = session.get(login_url)
    soup = BeautifulSoup(res.text, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']
    
    # 2. Login
    print("Logging in...")
    login_data = {
        'csrfmiddlewaretoken': csrf_token,
        'username': 'ersakshamjain@gmail.com',
        'password': 'Computer7@', # trying primary password
        'next': '/screens/'
    }
    
    res = session.post(login_url, data=login_data, headers={'Referer': login_url})
    
    if "Invalid username or password" in res.text:
        print("First password failed. Trying second...")
        login_data['password'] = 'SAPSAK2000'
        res = session.post(login_url, data=login_data, headers={'Referer': login_url})
        
    if "Log out" not in res.text and "ersakshamjain" not in res.text and "/login/" in res.url:
        print("Login failed entirely. Screener might have Cloudflare bot protection on the login endpoint.")
        return False
        
    print("Login successful! Navigating to Quick Formulae...")
    
    # The URL for "The Quick Formulae" is https://www.screener.in/screen/raw/?sort=&order=&source=&query=Market+Capitalization+%3E+0
    # Wait, the exact URL for the user's specific screen might vary. Let's find it.
    screens_page = session.get("https://www.screener.in/screens/")
    soup = BeautifulSoup(screens_page.text, 'html.parser')
    
    screen_link = None
    for a in soup.find_all('a'):
        if "The Quick Formulae" in a.text:
            screen_link = a['href']
            break
            
    if not screen_link:
        print("Could not find 'The Quick Formulae' on the screens page.")
        return False
        
    full_url = f"https://www.screener.in{screen_link}"
    print(f"Found screen URL: {full_url}")
    
    # 3. Scrape ALL pages
    all_data = []
    headers_saved = False
    
    page = 1
    while True:
        print(f"Scraping page {page}...")
        paged_url = f"{full_url}?page={page}"
        res = session.get(paged_url)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        table = soup.find('table')
        if not table:
            break
            
        rows = table.find_all('tr')
        if len(rows) <= 1 and page > 1:
            break # No more data
            
        for i, row in enumerate(rows):
            cols = row.find_all(['th', 'td'])
            row_data = [c.text.strip() for c in cols]
            
            if i == 0:
                if not headers_saved:
                    all_data.append(row_data)
                    headers_saved = True
            else:
                all_data.append(row_data)
                
        # Check if there is a 'next' page button
        pagination = soup.find('div', class_='flex-row flex-gap-16 flex-align-center')
        if not pagination or f"?page={page+1}" not in res.text:
            break
            
        page += 1
        time.sleep(1) # Be polite
        
    # 4. Save to CSV
    csv_file = "screener_quick_formulae.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(all_data)
        
    print(f"Saved {len(all_data)-1} entries to {csv_file}.")
    
    try:
        subprocess.run(['git', 'add', csv_file])
        subprocess.run(['git', 'commit', '-m', f'Add FULL {len(all_data)-1} entries of Screener Quick Formulae'])
        subprocess.run(['git', 'push', 'origin', 'master'])
        print("Pushed to GitHub!")
    except Exception as e:
        print(f"Git push failed: {e}")
        
    return True

scrape_screener()
