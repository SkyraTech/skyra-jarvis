import { test, expect } from '@playwright/test';
test('Skyra branding, bundled typography and persistent light/dark appearance', async ({ page }) => {
  await page.goto('/?preview=1');
  const appearance = page.getByLabel('Appearance', { exact: true }).first();
  for (const theme of ['light', 'dark']) {
    await appearance.selectOption(theme);
    await expect(page.locator('html')).toHaveAttribute('data-theme', theme);
    await expect(page.locator('body')).toHaveCSS('background-color', theme === 'light' ? 'rgb(255, 255, 255)' : 'rgb(0, 0, 0)');
    await page.evaluate(() => document.fonts.ready);
    expect(await page.evaluate(() => document.fonts.check('14px "Inter Variable"'))).toBe(true);
    await page.screenshot({ path: '.results/appearance-'+theme+'.png', fullPage: true });
    await page.reload();
    await expect(appearance).toHaveValue(theme);
  }
  await page.evaluate(() => { localStorage.setItem('skyra.appearance.v1', 'light'); window.dispatchEvent(new StorageEvent('storage', {key:'skyra.appearance.v1',newValue:'light'})); });
  await expect(appearance).toHaveValue('light');
});
