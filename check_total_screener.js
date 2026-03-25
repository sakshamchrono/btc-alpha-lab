const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: '/usr/bin/chromium' });
  const context = await browser.newContext({ userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" });
  const page = await context.newPage();

  await page.goto("https://www.screener.in/login/");
  await page.fill("input[name='username']", "ersakshamjain@gmail.com");
  await page.fill("input[name='password']", "SAPSAK2000");
  await Promise.all([
    page.waitForNavigation(),
    page.click("button[type='submit']")
  ]);

  await page.goto("https://www.screener.in/screens/249580/the-quick-formulae/");
  
  // Get the total results text e.g., "1 to 50 of 320 results"
  const text = await page.innerText('.flex-row.flex-gap-16');
  console.log("Pagination Text:", text);
  
  await browser.close();
})();
