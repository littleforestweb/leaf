/*
 Created on : 16 Jan 2023, 20:44:00
 Author     : xhico
 */


const puppeteer = require("puppeteer-core");
const mysql = require("mysql");
const fs = require("fs");
const path = require("path");

let siteId, configFile;
let dbCon, dbHost, dbPort, dbUser, dbPassword, dbName;
let PREVIEW_SERVER, WEBSERVER_FOLDER;
let browser, page;


async function exit() {
    console.log("-----------------------");
    console.log("Exiting");
    await browser.close();
    await dbCon.end();
    process.exit(1)
}

async function sleep(secs) {
    await new Promise(resolve => setTimeout(resolve, secs * 1000));
}

async function loadConfig() {
    let configJson = fs.readFileSync(configFile);
    configJson = JSON.parse(configJson);

    // Set Database config
    dbHost = configJson.DB_HOST;
    dbUser = configJson.DB_USER;
    dbPassword = configJson.DB_PASS;
    dbName = configJson.DB_NAME;
    dbCon = mysql.createConnection({
        host: dbHost, port: dbPort, user: dbUser, password: dbPassword, database: dbName
    });

    PREVIEW_SERVER = configJson.PREVIEW_SERVER;
    WEBSERVER_FOLDER = configJson.WEBSERVER_FOLDER;
}

async function initPuppeteer() {
    console.log("Initalyzing Puppeteer");

    // Set browser
    let args = ['--incognito', '--no-treekill', '--disable-gpu', '--no-sandbox', '--disable-setuid-sandbox', '--disable-infobars', '--window-position=0,0', '--ignore-certificate-errors', '--ignore-certificate-errors-spki-list'];
    browser = await puppeteer.launch({
        // executablePath: '/usr/bin/google-chrome',
        executablePath: "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        ignoreHTTPSErrors: true, headless: true, args: args, defaultViewport: {width: 1280, height: 720}
    });

    // Launch new page
    page = await browser.newPage();
}

async function getSitePages() {
    return new Promise((resolve, reject) => {
        let sql = "SELECT id, HTMLpath FROM site_meta WHERE site_id = " + siteId + " AND status = 200;";
        dbCon.query(sql, (error, results) => {
            return resolve(JSON.parse(JSON.stringify(results)));
        });
    });
}

async function main() {
    // Load Config
    await loadConfig();


    // Launch Puppeteer
    await initPuppeteer();

    // Get all 200 HTML Pages
    let pages = await getSitePages();

    // Open Pages on Puppeteer
    let counter = 1
    let pagesTotal = pages.length;
    for (const pageEntry of pages) {
        console.log("-----------------------");
        let progress = Math.round((counter / pagesTotal) * 100 * 100) / 100 + "%";
        let pageURL = PREVIEW_SERVER + pageEntry.HTMLpath;
        console.log(counter + ":" + pagesTotal + " (" + progress + ") - " + pageURL);

        let site_meta_screenshot_value;
        try {
            // Goto Page
            await page.goto(pageURL, {waitUntil: "domcontentloaded", timeout: 20000});

            // Screenshot the page
            let filename = pageEntry.id + ".jpg";
            let screenshotPath = path.join(WEBSERVER_FOLDER, "screenshots", filename);
            await page.screenshot({path: screenshotPath});

            site_meta_screenshot_value = path.join("screenshots", filename);
        } catch (e) {
            console.log("-----------------------");
            site_meta_screenshot_value = "NULL";
        }

        // Add screenshotPath to site_meta
        let sql = "UPDATE site_meta SET screenshotPath = '" + site_meta_screenshot_value + "' WHERE id = " + pageEntry.id + ";";
        await dbCon.query(sql);

        // Get random number between (max - min) + min -> Sleep
        // let sleepTime = Math.random() * (10 - 5) + 5;
        // await sleep(sleepTime);
        counter += 1;
    }
}

(async () => {
    // Get cmd args; Get only non system arguments
    process.argv.forEach(function (val, index) {
        if (index > 1 && val.startsWith("--")) {
            let argArray = val.split("=");
            if (argArray.length > 1) {
                let name = argArray[0];
                let value = argArray[1];
                if (name === "--siteId") {
                    siteId = value;
                } else if (name === "--configFile") {
                    configFile = value;
                }
            }
        }
    });

    try {
        await main();
    } catch (e) {
        console.log("-----------------------");
        console.log(e);
    } finally {
        await exit();
    }

})();