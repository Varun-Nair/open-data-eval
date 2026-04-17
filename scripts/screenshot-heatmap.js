const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1200, height: 800 });

  const htmlPath = path.resolve(__dirname, 'heatmap.html');
  await page.goto(`file://${htmlPath}`);
  await page.waitForTimeout(300);

  const outPath = path.resolve(__dirname, '../docs/assets/modality-heatmap.png');
  await page.screenshot({ path: outPath, clip: { x: 0, y: 0, width: 1200, height: 800 } });
  console.log('Saved:', outPath);
  await browser.close();
})();
