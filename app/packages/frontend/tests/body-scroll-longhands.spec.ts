import { expect, test } from '@playwright/test';

for (const css of [
  'overflow-x: clip',
  'overflow-y: scroll !important',
  'overflow-x: hidden !important; overflow-y: auto',
  'overflow-x: auto; overflow-y: scroll !important',
  'overflow: clip !important',
  '',
]) {
  test(`settings restores independent inline overflow declarations: ${css || 'unset'}`, async ({ page }) => {
    await page.goto('/explore');
    const trigger = page.getByRole('button', { name: 'Open settings', exact: true });
    await expect(trigger).toBeVisible();
    const dialog = page.getByRole('dialog', { name: 'Settings', exact: true });
    // Complete an interaction before changing body attributes after hydration.
    await trigger.click();
    await expect(dialog).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(dialog).not.toBeVisible();
    const before = await page.evaluate((css) => {
      document.body.style.cssText = `color: rgb(1, 2, 3); ${css}`;
      return ['overflow-x', 'overflow-y', 'color'].map((property) => [
        document.body.style.getPropertyValue(property),
        document.body.style.getPropertyPriority(property),
      ]);
    }, css);
    await trigger.click();
    await expect(dialog).toBeVisible();
    await expect.poll(() => page.evaluate(() => document.body.style.overflow)).toBe('hidden');
    await page.keyboard.press('Escape');
    await expect(dialog).not.toBeVisible();
    const after = await page.evaluate(() => ['overflow-x', 'overflow-y', 'color'].map((property) => [
      document.body.style.getPropertyValue(property),
      document.body.style.getPropertyPriority(property),
    ]));
    expect(after).toEqual(before);
  });
}
