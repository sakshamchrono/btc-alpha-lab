import csv

with open('us_professional_leads.csv', 'r') as f:
    reader = csv.reader(f)
    lines = list(reader)

with open('us_professional_leads_clean.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    for i, row in enumerate(lines):
        if i == 0:
            writer.writerow(row)
        else:
            # Clean URL
            url = row[3]
            if '&rut=' in url:
                url = url.split('&rut=')[0]
            
            # Clean Emails
            email = row[1]
            if "js-cookie" in email or "Your@email.com" in email:
                continue # Skip garbage
                
            writer.writerow([row[0], email, row[2], url, row[4], row[5]])
