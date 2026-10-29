import { expect, test } from '@playwright/test';

declare global {
  interface Window { notificationViewportProbe?: Record<string, unknown>; }
}
for (const viewport of [{ width: 1280, height: 900 }, { width: 568, height: 320 }]) {
  test(`default notification reference Done activation at ${viewport.width}x${viewport.height}`, async ({ page, context, baseURL }, info) => {
    await page.setViewportSize(viewport);
    const errors: string[] = [], blocked: string[] = [];
    page.on('pageerror', (error) => errors.push(error.message));
    await context.route('**/*', (route) => {
      const request = route.request();
      if (new URL(request.url()).origin === new URL(baseURL!).origin && ['GET', 'HEAD'].includes(request.method())) return route.continue();
      blocked.push(request.method() + ' ' + request.url()); return route.abort();
    });
    const response = await page.goto('/explore?marker=notification-short&settings=notifications#keep');
    expect(response?.status()).toBe(200);
    const dialog = page.getByRole('dialog', { name: 'Settings', exact: true });
    await expect(dialog).toBeVisible();
    await expect(dialog.getByRole('tab', { name: 'Notifications', exact: true })).toHaveAttribute('aria-selected', 'true');
    await expect(dialog.locator('[data-setting-id]')).toHaveCount(13);
    await expect(dialog.getByRole('switch')).toHaveCount(0);
    const done = dialog.getByRole('button', { name: 'Done', exact: true });
    const observed = await done.evaluate((button) => {
      const rect = (node: Element) => { const b = node.getBoundingClientRect(); return { top: b.top, bottom: b.bottom, left: b.left, right: b.right, width: b.width, height: b.height }; };
      const bounds = rect(button);
      const clips = [{ top: 0, bottom: innerHeight, left: 0, right: innerWidth }];
      const ancestors = [];
      for (let node = button.parentElement; node; node = node.parentElement) {
        const style = getComputedStyle(node), b = rect(node);
        ancestors.push({ tag: node.tagName, bounds: b, overflowX: style.overflowX, overflowY: style.overflowY, display: style.display });
        if (style.overflowY !== 'visible') clips.push(b);
      }
      const intersection = { top: Math.max(bounds.top, ...clips.map(x => x.top)), bottom: Math.min(bounds.bottom, ...clips.map(x => x.bottom)) };
      const point = { x: bounds.left + bounds.width / 2, y: bounds.top + bounds.height / 2 };
      const hit = document.elementFromPoint(point.x, point.y);
      const result = { viewport: { width: innerWidth, height: innerHeight }, bounds, ancestors, visibleHeight: Math.max(0, intersection.bottom - intersection.top), point, centerHit: { tag: hit?.tagName ?? null, text: hit?.textContent?.slice(0, 100) ?? null }, beforeURL: location.href, events: [] as unknown[] };
      window.notificationViewportProbe = result;
      for (const kind of ['pointerdown', 'pointerup', 'click']) {
        window.addEventListener(kind, (event) => {
          if (!(event instanceof MouseEvent)) return;
          result.events.push({ kind, trusted: event.isTrusted, target: event.target instanceof Element ? event.target.tagName : null, text: event.target instanceof Element ? event.target.textContent?.slice(0, 100) : null, x: event.clientX, y: event.clientY, url: location.href });
        }, true);
      }
      return result;
    });
    // Raw trusted input deliberately avoids locator auto-scroll masking clipping.
    await page.screenshot({ path: info.outputPath("before-click.png") });
    await page.mouse.click(observed.point.x, observed.point.y);
    try {
      await expect(dialog).not.toBeVisible();
      const click = await page.evaluate(() => {
        const events = window.notificationViewportProbe?.events;
        if (!Array.isArray(events)) throw Error("Pointer observations required");
        return events.filter((event: { kind?: unknown }) => event.kind === "click").at(-1);
      });
      expect(click).toMatchObject({ kind: "click", trusted: true, target: "BUTTON", text: "Done" });
      expect(observed.centerHit).toEqual({ tag: "BUTTON", text: "Done" });
      expect(observed.visibleHeight).toBe(44);
      expect(new URL(page.url()).searchParams.has('settings')).toBe(false);
      expect(new URL(page.url()).searchParams.get('marker')).toBe('notification-short');
      expect(new URL(page.url()).hash).toBe('#keep');
      expect(errors).toEqual([]); expect(blocked).toEqual([]);
    } finally {
      await info.attach('notification-viewport-observation', { body: JSON.stringify(await page.evaluate(({ errors, blocked }) => ({ ...window.notificationViewportProbe, afterURL: location.href, errors, blocked }), { errors, blocked })), contentType: 'application/json' });
      await page.screenshot({ path: info.outputPath('viewport.png') });
    }
  });
}
