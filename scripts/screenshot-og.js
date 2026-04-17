const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1200, height: 630 });

  const htmlPath = path.resolve(__dirname, 'og-image.html');
  await page.goto(`file://${htmlPath}`);
  await page.waitForTimeout(500); // let images render

  const outPath = path.resolve(__dirname, '../docs/scorecard/og-image.png');
  await page.screenshot({ path: outPath, clip: { x: 0, y: 0, width: 1200, height: 630 } });
  console.log('Saved:', outPath);
  await browser.close();
})();
