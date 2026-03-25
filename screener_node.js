const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');
const { execSync } = require('child_process');

const loginUrl = 'https://www.screener.in/login/';
const email = 'ersakshamjain@gmail.com';
const pw1 = 'Computer7@';
const pw2 = 'SAPSAK2000';

async function runScreener() {
    console.log("Fetching CSRF token...");
    
    // 1. Get Login Page & CSRF Token
    let res = await axios.get(loginUrl, { validateStatus: false });
    let cookie = res.headers['set-cookie'] || [];
    let cookieStr = cookie.map(c => c.split(';')[0]).join('; ');
    
    const $ = cheerio.load(res.data);
    const csrfToken = $('input[name="csrfmiddlewaretoken"]').val();
    
    // Update cookies
    const loginCookies = cookieStr + `; csrftoken=${csrfToken}`;
    
    console.log("Attempting Login 1...");
    const loginPayload = new URLSearchParams();
    loginPayload.append('csrfmiddlewaretoken', csrfToken);
    loginPayload.append('username', email);
    loginPayload.append('password', pw1);
    loginPayload.append('next', '/screens/');

    let loginRes = await axios.post(loginUrl, loginPayload, {
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': loginCookies,
            'Referer': loginUrl
        },
        maxRedirects: 0,
        validateStatus: false
    });
    
    // Check if successful (Status 302 means redirect to /screens/)
    if (loginRes.status !== 302) {
        console.log("Login 1 failed. Attempting Login 2...");
        loginPayload.set('password', pw2);
        loginRes = await axios.post(loginUrl, loginPayload, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Cookie': loginCookies,
                'Referer': loginUrl
            },
            maxRedirects: 0,
            validateStatus: false
        });
    }

    if (loginRes.status !== 302) {
        console.log("Login failed completely. Screener may require CAPTCHA or JS challenge.");
        return;
    }
    
    console.log("Login successful! Navigating to Screens...");
    
    // Combine session cookies
    let sessionCookies = loginRes.headers['set-cookie'] || [];
    let finalCookies = sessionCookies.map(c => c.split(';')[0]).join('; ') + '; ' + loginCookies;
    
    let screensRes = await axios.get('https://www.screener.in/screens/', {
        headers: { 'Cookie': finalCookies }
    });
    
    const $screens = cheerio.load(screensRes.data);
    let targetLink = null;
    $screens('a').each((i, el) => {
        if ($screens(el).text().includes("The Quick Formulae")) {
            targetLink = $screens(el).attr('href');
        }
    });
    
    if (!targetLink) {
        console.log("Could not find 'The Quick Formulae' link on /screens/");
        return;
    }
    
    console.log(`Found target screen URL: ${targetLink}`);
    
    let page = 1;
    let allData = [];
    let hasNextPage = true;
    
    while (hasNextPage) {
        console.log(`Scraping Page ${page}...`);
        let pageUrl = `https://www.screener.in${targetLink}?page=${page}`;
        let pageRes = await axios.get(pageUrl, {
            headers: { 'Cookie': finalCookies }
        });
        
        const $page = cheerio.load(pageRes.data);
        const rows = $page('table tr');
        
        if (rows.length === 0) break;
        
        rows.each((i, row) => {
            if (page > 1 && i === 0) return; // Skip headers on subsequent pages
            
            let rowData = [];
            $page(row).find('th, td').each((j, col) => {
                let text = $page(col).text().replace(/"/g, '""').trim();
                rowData.push(`"${text}"`);
            });
            allData.push(rowData.join(','));
        });
        
        // Check for 'Next' button or page links
        const paginationText = $page('.pagination').text() || $page('.flex-row').text();
        if (!paginationText.includes(`?page=${page+1}`) && !paginationText.includes("Next")) {
            hasNextPage = false;
        } else {
            page++;
            await new Promise(r => setTimeout(r, 1000));
        }
    }
    
    const csvContent = allData.join('\n');
    fs.writeFileSync('screener_quick_formulae.csv', csvContent);
    console.log(`Successfully scraped ${allData.length - 1} entries!`);
    
    // Git Push
    try {
        execSync('git add screener_quick_formulae.csv');
        execSync('git commit -m "Add full Screener.in Quick Formulae CSV via Node Scraper"');
        execSync('git push origin master');
        console.log("Pushed successfully to GitHub!");
    } catch(e) {
        console.log("Git push skipped or failed.", e.message);
    }
}

runScreener();
