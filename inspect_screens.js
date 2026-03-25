const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');

const loginUrl = 'https://www.screener.in/login/';
const email = 'ersakshamjain@gmail.com';
const pw2 = 'SAPSAK2000';

async function inspect() {
    let res = await axios.get(loginUrl, { validateStatus: false });
    let cookie = res.headers['set-cookie'] || [];
    let cookieStr = cookie.map(c => c.split(';')[0]).join('; ');
    
    const $ = cheerio.load(res.data);
    const csrfToken = $('input[name="csrfmiddlewaretoken"]').val();
    
    const loginCookies = cookieStr + `; csrftoken=${csrfToken}`;
    
    const loginPayload = new URLSearchParams();
    loginPayload.append('csrfmiddlewaretoken', csrfToken);
    loginPayload.append('username', email);
    loginPayload.append('password', pw2);
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
    
    let sessionCookies = loginRes.headers['set-cookie'] || [];
    let finalCookies = sessionCookies.map(c => c.split(';')[0]).join('; ') + '; ' + loginCookies;
    
    let screensRes = await axios.get('https://www.screener.in/screens/', {
        headers: { 'Cookie': finalCookies }
    });
    
    fs.writeFileSync('screens_html.txt', screensRes.data);
    console.log("Saved screens page HTML.");
}
inspect();
