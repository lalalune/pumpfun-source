import { expect, test, type Locator, type Page } from '@playwright/test';

const ADDRESS = 'So11111111111111111111111111111111111111112';
type Trace = { type: string; trusted: boolean; target: string; x: number; y: number; open: boolean };
declare global {
  interface Window {
    authBackdropTrace?: Record<string, Trace[]>;
    authBackdropWalletCalls?: string[];
  }
}
async function observe(dialog: Locator, key: string) {
  await dialog.evaluate((node, key) => {
    if (!(node instanceof HTMLDialogElement)) throw Error('Native dialog required');
    window.authBackdropTrace ??= {};
    const records: Trace[] = [];
    window.authBackdropTrace[key] = records;
    for (const type of ['pointerdown', 'pointerup', 'pointercancel', 'click', 'close']) {
      window.addEventListener(type, (event) => {
        if (!(event.target instanceof Node) || !node.contains(event.target)) return;
        records.push({ type, trusted: event.isTrusted, target: event.target instanceof Element ? event.target.tagName : 'other', x: event instanceof MouseEvent ? event.clientX : 0, y: event instanceof MouseEvent ? event.clientY : 0, open: node.open });
      }, true);
    }
  }, key);
}
async function positions(dialog: Locator, address: Locator) {
  await address.scrollIntoViewIfNeeded();
  const d = await dialog.boundingBox(), a = await address.boundingBox();
  if (!d || !a || d.x <= 0) throw Error('Visible inset dialog/address required');
  return { inside: { x: a.x + Math.min(20, a.width / 2), y: a.y + a.height / 2 }, outside: { x: d.x / 2, y: d.y / 2 } };
}
async function drag(page: Page, p: Awaited<ReturnType<typeof positions>>) {
  await page.mouse.move(p.inside.x, p.inside.y);
  await page.mouse.down();
  await page.mouse.move(p.outside.x, p.outside.y, { steps: 12 });
  await page.mouse.up();
}
async function nativeReference(page: Page) {
  await page.evaluate((address) => {
    const d = document.createElement('dialog');
    d.setAttribute('aria-label', 'Native public address reference');
    d.setAttribute('closedby', 'any');
    d.style.cssText = 'width:min(356px,calc(100vw - 32px));height:200px;padding:20px;margin:auto';
    const code = document.createElement('button');
    code.type = 'button';
    code.onclick = () => { code.dataset.activations = String(Number(code.dataset.activations ?? '0') + 1); };
    code.textContent = address;
    code.style.cssText = 'display:block;padding:12px;max-width:100%';
    d.append(code); document.body.append(d); d.showModal();
  }, ADDRESS);
  const d = page.getByRole('dialog', { name: 'Native public address reference', includeHidden: true });
  const address = d.locator('button');
  await observe(d, 'native');
  const p = await positions(d, address);
  await drag(page, p);
  await expect(d).toBeVisible();
  await expect(address).toHaveText(ADDRESS);
  expect(await address.getAttribute('data-activations')).toBeNull();
  await page.mouse.click(p.outside.x, p.outside.y);
  await expect(d).not.toBeVisible(); // Native light-dismiss support control.
  await d.evaluate((node) => node.remove());
}
async function connect(page: Page) {
  await page.addInitScript((address) => {
    const accounts = [{ address, chains: ['solana:mainnet'] }];
    const calls: string[] = [];
    window.authBackdropWalletCalls = calls;
    window.addEventListener('wallet-standard:app-ready', ((event: CustomEvent) => {
      event.detail.register({ version: '1.0.0', name: 'Synthetic Address Selection Wallet', chains: ['solana:mainnet'], accounts,
        features: {
          'standard:connect': { version: '1.0.0', async connect() { calls.push('connect'); return { accounts }; } },
          'standard:events': { version: '1.0.0', on() { calls.push('on'); return () => calls.push('off'); } },
          get 'solana:signIn'(): never { throw Error('Sign-in forbidden'); },
          get 'solana:signMessage'(): never { throw Error('Signing forbidden'); },
          get 'solana:signTransaction'(): never { throw Error('Transactions forbidden'); },
        },
      });
    }) as EventListener);
  }, ADDRESS);
  await page.goto('/explore?marker=auth-address-selection#keep');
  await page.getByTestId('sign-in-button').click();
  const dialog = page.getByTestId('auth-dialog');
  await expect(dialog).toHaveAttribute('data-auth-state', 'ready');
  await dialog.getByRole('button', { name: 'Connect a public wallet', exact: true }).click();
  await dialog.getByRole('button', { name: 'Connect Synthetic Address Selection Wallet', exact: true }).click();
  const address = dialog.getByTestId('public-wallet-address');
  await expect(address).toHaveText(ADDRESS);
  await observe(dialog, 'auth');
  return { dialog, address };
}
test.afterEach(async ({ page }, info) => {
  await info.attach('trusted-auth-backdrop-events', { body: JSON.stringify(await page.evaluate(() => ({ url: location.href, events: window.authBackdropTrace, walletCalls: window.authBackdropWalletCalls, open: document.querySelector<HTMLDialogElement>('[data-testid="auth-dialog"]')?.open, focused: document.activeElement?.tagName }))), contentType: 'application/json' });
});
for (const viewport of [{ width: 1280, height: 900 }, { width: 390, height: 844 }]) {
  test(`aborted public disconnect-button press preserves chooser and connection at ${viewport.width}px`, async ({ page, context, baseURL }) => {
    await page.setViewportSize(viewport);
    const external: string[] = [];
    const errors: string[] = [];
    page.on('pageerror', (e) => errors.push(e.message));
    await context.route('**/*', (route) => {
      const req = route.request();
      if (new URL(req.url()).origin === new URL(baseURL!).origin && ['GET', 'HEAD'].includes(req.method())) return route.continue();
      external.push(req.method() + ' ' + req.url()); return route.abort();
    });
    const { dialog, address } = await connect(page);
    await nativeReference(page);
    await expect(dialog).toBeVisible();
    await expect(address).toHaveText(ADDRESS);
    const before = page.url();
    await drag(page, await positions(dialog, dialog.getByRole('button', { name: 'Disconnect and forget address', exact: true })));
    await expect(dialog).toBeVisible();
    await expect(address).toHaveText(ADDRESS);
    expect(page.url()).toBe(before);
    expect(await page.evaluate(() => window.authBackdropWalletCalls)).toEqual(['connect', 'on']);
    expect(external).toEqual([]); expect(errors).toEqual([]);
  });
}
