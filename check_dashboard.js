const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: '/usr/bin/chromium' });
  const context = await browser.newContext({ userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" });
  const page = await context.newPage();

  await page.goto("https://www.screener.in/login/");
  await page.fill("input[name='username']", "ersakshamjain@gmail.com");
  await page.fill("input[name='password']", "SAPSAK2000");
  await Promise.all([page.waitForNavigation(), page.click("button[type='submit']")]);

  await page.goto("https://www.screener.in/");
  
  const links = await page.$$eval('a', as => as.map(a => ({ text: a.innerText.trim(), href: a.href })));
  const matches = links.filter(l => l.text.toLowerCase().includes('quick'));
  console.log("Dashboard matches:", matches);
  
  await browser.close();
})();
