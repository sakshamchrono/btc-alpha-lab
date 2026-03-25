const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: '/usr/bin/chromium' });
  const context = await browser.newContext({ userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" });
  const page = await context.newPage();

  console.log("Navigating to public URL without login...");
  await page.goto("https://www.screener.in/screens/249580/the-quick-formulae/");
  
  const text = await page.innerText('.flex-row.flex-gap-16');
  console.log("Pagination Text:", text);
  
  await browser.close();
})();
