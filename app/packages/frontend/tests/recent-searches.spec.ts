import { expect, test, type Page } from '@playwright/test';
import { openShellSearch } from './shell-controls';
const KEY = 'recently-searched-terms';
const modal = (page: Page) => page.getByRole('dialog', { name: 'Search for coins and users', exact: true });
const history = (page: Page) => modal(page).getByRole('region', { name: 'Recent searches', exact: true });

async function mounted(page: Page, url = '/explore') {
  await page.addInitScript(() => {
    const add = window.addEventListener;
    window.addEventListener = function (...args: Parameters<typeof window.addEventListener>) {
      const result = Reflect.apply(add, this, args);
      if (args[0] === 'pump:open-search') Reflect.set(window, '__searchHistoryMounted', true);
      return result;
    };
  });
  await page.goto(url);
  await page.waitForFunction(() => Reflect.get(window, '__searchHistoryMounted') === true);
}

test('real submissions survive reload and text-history navigation keeps its recorded order', async ({ page }) => {
  await mounted(page);
  for (const term of [' first & β ', 'second']) {
    const input = await openShellSearch(page);
    await input.fill(term); await input.press('Enter');
    await expect.poll(() => new URL(page.url()).searchParams.get('q')).toBe(term.trim());
  }
  await page.reload();
  await page.waitForFunction(() => Reflect.get(window, '__searchHistoryMounted') === true);
  const input = await openShellSearch(page); await input.fill('');
  await expect(history(page)).toBeVisible();
  await expect(history(page).getByRole('link')).toHaveText(['second', 'first & β']);
  await input.fill(' '); await expect(history(page)).not.toBeVisible();
  await input.fill('');
  const destination = history(page).getByRole('link', { name: 'first & β', exact: true });
  await expect(destination).toHaveAttribute('href', '/explore?q=first%20%26%20%CE%B2');
  await destination.click();
  await expect(modal(page)).not.toBeVisible();
  await expect.poll(() => new URL(page.url()).searchParams.get('q')).toBe('first & β');
  expect(await page.evaluate((key) => JSON.parse(localStorage.getItem(key)!), KEY)).toEqual(['second', 'first & β']);
});

test('strict duplicate promotion caps at twenty, collapsed display shows three, clear touches only its key', async ({ page }) => {
  await mounted(page);
  const initial = ['needle', 'Needle', ...Array.from({ length: 21 }, (_, index) => `term ${index}`)];
  await page.evaluate(({ key, initial }) => {
    localStorage.setItem(key, JSON.stringify(initial)); localStorage.setItem('unrelated-history-test', 'retained');
  }, { key: KEY, initial });
  await page.reload(); await page.waitForFunction(() => Reflect.get(window, '__searchHistoryMounted') === true);
  const input = await openShellSearch(page); await input.fill('needle'); await input.press('Enter');
  await expect.poll(() => new URL(page.url()).searchParams.get('q')).toBe('needle');
  const actual = await page.evaluate((key) => JSON.parse(localStorage.getItem(key)!), KEY);
  expect(actual).toEqual(['needle', ...initial.filter((term) => term !== 'needle').slice(0, 19)]);
  await openShellSearch(page); await modal(page).getByRole('searchbox').fill('');
  await expect(history(page).getByRole('link')).toHaveCount(3);
  await history(page).getByRole('button', { name: 'Clear recent searches', exact: true }).click();
  await expect(history(page).getByText('No recent searches yet.', { exact: true })).toBeVisible();
  expect(await page.evaluate((key) => localStorage.getItem(key), KEY)).toBe('[]');
  expect(await page.evaluate(() => localStorage.getItem('unrelated-history-test'))).toBe('retained');
});

test('malformed local data is explicit and can be cleared without inventing history', async ({ page }) => {
  await mounted(page);
  await page.evaluate((key) => localStorage.setItem(key, '{'), KEY);
  await page.reload(); await page.waitForFunction(() => Reflect.get(window, '__searchHistoryMounted') === true);
  await openShellSearch(page);
  await expect(history(page).getByRole('alert')).toHaveText('Recent searches are unavailable.');
  expect(await page.evaluate((key) => localStorage.getItem(key), KEY)).toBe('{');
  await history(page).getByRole('button', { name: 'Clear recent searches', exact: true }).click();
  await expect(history(page).getByText('No recent searches yet.', { exact: true })).toBeVisible();
  expect(await page.evaluate((key) => localStorage.getItem(key), KEY)).toBe('[]');
});

test('a failed history write does not block actual search navigation', async ({ page }) => {
  await mounted(page);
  await page.evaluate((key) => {
    const original = Storage.prototype.setItem;
    Storage.prototype.setItem = function (name, value) {
      if (name === key) throw new DOMException('Synthetic quota failure', 'QuotaExceededError');
      return original.call(this, name, value);
    };
  }, KEY);
  const input = await openShellSearch(page); await input.fill('still searchable'); await input.press('Enter');
  await expect.poll(() => new URL(page.url()).searchParams.get('q')).toBe('still searchable');
  expect(await page.evaluate((key) => localStorage.getItem(key), KEY)).toBeNull();
  await openShellSearch(page); await modal(page).getByRole('searchbox').fill('');
  await expect(history(page).getByRole('alert')).toHaveText('Recent searches are unavailable.');
});

test('real same-origin storage events keep another open page in sync', async ({ page, context }) => {
  await mounted(page);
  const other = await context.newPage();
  await mounted(other); await openShellSearch(other);
  const input = await openShellSearch(page); await input.fill('from first page'); await input.press('Enter');
  await expect(history(other).getByRole('link', { name: 'from first page', exact: true })).toBeVisible();
  await history(other).getByRole('button', { name: 'Clear recent searches', exact: true }).click();
  await openShellSearch(page); await modal(page).getByRole('searchbox').fill('');
  await expect(history(page).getByText('No recent searches yet.', { exact: true })).toBeVisible();
  await other.close();
});
