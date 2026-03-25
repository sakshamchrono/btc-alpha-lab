const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: '/usr/bin/chromium' });
  const context = await browser.newContext({ userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" });
  const page = await context.newPage();

  await page.goto("https://www.screener.in/login/");
  await page.fill("input[name='username']", "ersakshamjain@gmail.com");
  await page.fill("input[name='password']", "SAPSAK2000");
  await Promise.all([page.waitForNavigation(), page.click("button[type='submit']")]);

  for(let i=1; i<=4; i++) {
      await page.goto(`https://www.screener.in/screens/?page=${i}`);
      const links = await page.$$eval('a', as => as.map(a => ({ text: a.innerText.trim(), href: a.href })));
      const quick = links.filter(l => l.text.toLowerCase().includes('quick formula'));
      if(quick.length > 0) {
          console.log(`Found on page ${i}:`);
          console.log(quick);
      }
  }
  await browser.close();
})();
