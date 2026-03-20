const { chromium } = require('@playwright/test');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://en.wikipedia.org/wiki/Conan_the_Barbarian_(1982_film)');
  await page.waitForLoadState('domcontentloaded');

  const imageUrl = await page.evaluate(() => {
    const img = document.querySelector('.infobox img, .infobox-image img');
    return img ? (img.src.startsWith('//') ? 'https:' + img.src : img.src) : null;
  });

  if (!imageUrl) { console.log('Kein Bild gefunden.'); await browser.close(); return; }

  // Wikimedia Thumb-URL: Größe auf 2000px hochsetzen für mind. 1000px Höhe
  // Muster: /thumb/e/ed/file.jpg/250px-file.jpg → /thumb/e/ed/file.jpg/2000px-file.jpg
  const hiResUrl = imageUrl.replace(/\/(\d+)px-/, '/2000px-');
  console.log(`Downloading: ${hiResUrl}`);

  const response = await page.request.get(hiResUrl);
  const buffer = await response.body();
  fs.writeFileSync('conan.jpg', buffer);
  console.log(`Gespeichert: conan.jpg (${(buffer.length / 1024).toFixed(1)} KB)`);

  await browser.close();
})();
