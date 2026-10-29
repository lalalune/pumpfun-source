import { expect, test } from '@playwright/test';

test('settings search folds the case of compatibility-decomposed letters', async ({ page }) => {
  await page.goto('/?settings=privacy');
  const dialog = page.getByRole('dialog', { name: 'Settings', exact: true });
  await expect(dialog).toBeVisible();
  const search = dialog.getByRole('searchbox', { name: 'Search settings' });
  const result = dialog.locator('[data-setting-id="account.hidePersonalInfo"]');
  await search.fill('email');
  await expect(result).toBeVisible();
  for (const query of ['𝐄𝐌𝐀𝐈𝐋', '𝙀𝙈𝘼𝙄𝙇', 'ＥＭＡＩＬ', 'émail']) {
    await search.fill(query);
    await expect(result).toBeVisible();
  }
});
