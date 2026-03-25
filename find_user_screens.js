const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: '/usr/bin/chromium' });
  const context = await browser.newContext({ userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" });
  const page = await context.newPage();

  console.log("Navigating to login...");
  await page.goto("https://www.screener.in/login/");

  console.log("Filling credentials...");
  await page.fill("input[name='username']", "ersakshamjain@gmail.com");
  await page.fill("input[name='password']", "SAPSAK2000");
  
  await Promise.all([
    page.waitForNavigation(),
    page.click("button[type='submit']")
  ]);

  console.log("Navigating to screens...");
  await page.goto("https://www.screener.in/screens/");
  
  // Print all anchor tags on the screens page to see where "The Quick Formulae" is hiding.
  const links = await page.$$eval('a', as => as.map(a => ({ text: a.innerText.trim(), href: a.href })));
  console.log(links.filter(l => l.href.includes('screen')));
  
  await browser.close();
})();
