import csv

valid_rows = []
with open('us_doctors_browser.csv', 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        if len(row) >= 4 and "Business Name" not in row[0] and "N/A" not in row[1]:
            valid_rows.append(row)

with open('us_doctors_browser_final.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["Business Name", "Email", "City/State", "WebsiteURL", "Reviews", "Rating"])
    writer.writerows(valid_rows)
    
print(f"Cleaned {len(valid_rows)} valid leads.")
