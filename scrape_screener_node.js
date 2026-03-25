const { chromium } = require('playwright');
const fs = require('fs');
const { execSync } = require('child_process');

(async () => {
  // Use the system chromium
  const browser = await chromium.launch({ headless: true, executablePath: '/usr/bin/chromium' });
  const context = await browser.newContext({ userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" });
  const page = await context.newPage();

  console.log("Navigating to login...");
  await page.goto("https://www.screener.in/login/");

  console.log("Filling credentials...");
  await page.fill("input[name='username']", "ersakshamjain@gmail.com");
  await page.fill("input[name='password']", "Computer7@");
  
  await Promise.all([
    page.waitForNavigation(),
    page.click("button[type='submit']")
  ]);
  
  // Check if login was successful
  if (page.url().includes('login')) {
      console.log("First password failed. Trying second...");
      await page.fill("input[name='username']", "ersakshamjain@gmail.com");
      await page.fill("input[name='password']", "SAPSAK2000");
      await Promise.all([
        page.waitForNavigation(),
        page.click("button[type='submit']")
      ]);
  }

  console.log("Navigating to screens...");
  await page.goto("https://www.screener.in/screens/");
  
  // Find "The Quick Formulae"
  console.log("Looking for 'The Quick Formulae' link...");
  const links = await page.$$('a');
  let targetUrl = null;
  
  for (let link of links) {
      const text = await link.innerText().catch(() => '');
      if (text.includes('The Quick Formulae') || text.includes('Quick Formulae')) {
          targetUrl = await link.getAttribute('href');
          break;
      }
  }

  if (targetUrl) {
      console.log(`Found screen URL: https://www.screener.in${targetUrl}`);
      await page.goto(`https://www.screener.in${targetUrl}`);
  } else {
      console.log("Could not find the link on the screens page. Guessing public URL...");
      await page.goto("https://www.screener.in/screens/249580/the-quick-formulae/");
  }

  let allData = [];
  let pageNum = 1;
  
  while (true) {
      console.log(`Scraping page ${pageNum}...`);
      
      // Extract table data
      const tableData = await page.evaluate(() => {
          let rows = document.querySelectorAll('table tr');
          let data = [];
          for (let row of rows) {
              let cols = row.querySelectorAll('th, td');
              let rowData = [];
              for (let col of cols) {
                  let text = col.innerText ? col.innerText.trim().replace(/"/g, '""') : '';
                  rowData.push('"' + text + '"');
              }
              if (rowData.length > 0) data.push(rowData.join(','));
          }
          return data;
      });
      
      if (pageNum === 1) {
          allData = allData.concat(tableData); // Include headers
      } else {
          allData = allData.concat(tableData.slice(1)); // Skip headers on subsequent pages
      }
          
      // Check for next button using pagination
      // Find all anchor tags that contain the text 'Next' or have an aria-label 'Next'
      const nextLinks = await page.$$('a');
      let nextButton = null;
      let isDisabled = false;
      
      for (let link of nextLinks) {
          const text = await link.innerText().catch(() => '');
          if (text.includes('Next') || text.includes('▶')) {
              nextButton = link;
              // Check if parent li has class 'disabled'
              const parentClass = await link.evaluate(el => el.parentElement ? el.parentElement.className : '');
              if (parentClass.includes('disabled')) {
                  isDisabled = true;
              }
              break;
          }
      }
      
      if (nextButton && !isDisabled) {
          console.log("Clicking Next...");
          await Promise.all([
              page.waitForNavigation(),
              nextButton.click()
          ]);
          pageNum++;
      } else {
          console.log("No more pages.");
          break;
      }
  }

  console.log(`Extracted ${allData.length - 1} total rows.`);
  
  const csvFile = "screener_quick_formulae_full.csv";
  fs.writeFileSync(csvFile, allData.join('\n'));
      
  console.log("Data saved to CSV. Pushing to GitHub...");
  try {
      execSync('git add ' + csvFile);
      execSync('git commit -m "Add FULL ' + (allData.length-1) + ' entries of Screener Quick Formulae"');
      execSync('git push origin master');
      console.log("GitHub push successful!");
  } catch (e) {
      console.log(`Git error: ${e.message}`);
  }

  await browser.close();
})();
