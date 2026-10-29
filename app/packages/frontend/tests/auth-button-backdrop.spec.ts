import { expect, test, type Locator, type Page } from "@playwright/test";

const ADDRESS = "So11111111111111111111111111111111111111112";
type Trace = {
  type: string;
  trusted: boolean;
  target: string;
  x: number;
  y: number;
  open: boolean;
};
declare global {
  interface Window {
    authBackdropTrace?: Record<string, Trace[]>;
    authBackdropWalletCalls?: string[];
    authBackdropApprove?: () => void;
  }
}
async function observe(dialog: Locator, key: string) {
  await dialog.evaluate((node, key) => {
    if (!(node instanceof HTMLDialogElement))
      throw Error("Native dialog required");
    window.authBackdropTrace ??= {};
    const records: Trace[] = [];
    window.authBackdropTrace[key] = records;
    for (const type of [
      "pointerdown",
      "pointerup",
      "pointercancel",
      "click",
      "close",
    ]) {
      window.addEventListener(
        type,
        (event) => {
          if (!(event.target instanceof Node) || !node.contains(event.target))
            return;
          records.push({
            type,
            trusted: event.isTrusted,
            target:
              event.target instanceof Element ? event.target.tagName : "other",
            x: event instanceof MouseEvent ? event.clientX : 0,
            y: event instanceof MouseEvent ? event.clientY : 0,
            open: node.open,
          });
        },
        true,
      );
    }
  }, key);
}
async function positions(dialog: Locator, address: Locator) {
  await address.scrollIntoViewIfNeeded();
  const d = await dialog.boundingBox(),
    a = await address.boundingBox();
  if (!d || !a || d.x <= 0)
    throw Error("Visible inset dialog/address required");
  return {
    inside: { x: a.x + Math.min(20, a.width / 2), y: a.y + a.height / 2 },
    outside: { x: d.x / 2, y: d.y / 2 },
  };
}
async function drag(page: Page, p: Awaited<ReturnType<typeof positions>>) {
  await page.mouse.move(p.inside.x, p.inside.y);
  await page.mouse.down();
  await page.mouse.move(p.outside.x, p.outside.y, { steps: 12 });
  await page.mouse.up();
}
async function nativeReference(page: Page) {
  await page.evaluate((address) => {
    const d = document.createElement("dialog");
    d.setAttribute("aria-label", "Native public address reference");
    d.setAttribute("closedby", "any");
    d.style.cssText =
      "width:min(356px,calc(100vw - 32px));height:200px;padding:20px;margin:auto";
    const code = document.createElement("button");
    code.type = "button";
    code.onclick = () => {
      code.dataset.activations = String(
        Number(code.dataset.activations ?? "0") + 1,
      );
    };
    code.textContent = address;
    code.style.cssText = "display:block;padding:12px;max-width:100%";
    d.append(code);
    document.body.append(d);
    d.showModal();
  }, ADDRESS);
  const d = page.getByRole("dialog", {
    name: "Native public address reference",
    includeHidden: true,
  });
  const address = d.locator("button");
  await observe(d, "native");
  const p = await positions(d, address);
  await drag(page, p);
  await expect(d).toBeVisible();
  await expect(address).toHaveText(ADDRESS);
  expect(await address.getAttribute("data-activations")).toBeNull();
  await page.mouse.click(p.outside.x, p.outside.y);
  await expect(d).not.toBeVisible(); // Native light-dismiss support control.
  await d.evaluate((node) => node.remove());
}
async function connect(page: Page, pending = false) {
  await page.addInitScript(
    ({ address, pending }) => {
      const accounts = [{ address, chains: ["solana:mainnet"] }];
      const calls: string[] = [];
      window.authBackdropWalletCalls = calls;
      window.addEventListener("wallet-standard:app-ready", ((
        event: CustomEvent,
      ) => {
        event.detail.register({
          version: "1.0.0",
          name: "Synthetic Address Selection Wallet",
          chains: ["solana:mainnet"],
          accounts,
          features: {
            "standard:connect": {
              version: "1.0.0",
              async connect() {
                calls.push("connect");
                if (pending) {
                  await new Promise<void>((resolve) => {
                    window.authBackdropApprove = resolve;
                  });
                  calls.push("approved");
                }
                return { accounts };
              },
            },
            "standard:events": {
              version: "1.0.0",
              on() {
                calls.push("on");
                return () => calls.push("off");
              },
            },
            get "solana:signIn"(): never {
              throw Error("Sign-in forbidden");
            },
            get "solana:signMessage"(): never {
              throw Error("Signing forbidden");
            },
            get "solana:signTransaction"(): never {
              throw Error("Transactions forbidden");
            },
          },
        });
      }) as EventListener);
    },
    { address: ADDRESS, pending },
  );
  await page.goto("/explore?marker=auth-address-selection#keep");
  await page.getByTestId("sign-in-button").click();
  const dialog = page.getByTestId("auth-dialog");
  await expect(dialog).toHaveAttribute("data-auth-state", "ready");
  await dialog
    .getByRole("button", { name: "Connect a public wallet", exact: true })
    .click();
  await dialog
    .getByRole("button", {
      name: "Connect Synthetic Address Selection Wallet",
      exact: true,
    })
    .click();
  const address = dialog.getByTestId("public-wallet-address");
  if (pending)
    await expect(
      dialog.getByText("Waiting for wallet approval…", { exact: true }),
    ).toBeVisible();
  else await expect(address).toHaveText(ADDRESS);
  await observe(dialog, "auth");
  return { dialog, address };
}
test.afterEach(async ({ page }, info) => {
  await info.attach("trusted-auth-backdrop-events", {
    body: JSON.stringify(
      await page.evaluate(() => ({
        url: location.href,
        events: window.authBackdropTrace,
        walletCalls: window.authBackdropWalletCalls,
        open: document.querySelector<HTMLDialogElement>(
          '[data-testid="auth-dialog"]',
        )?.open,
        focused: document.activeElement?.tagName,
      })),
    ),
    contentType: "application/json",
  });
});
for (const viewport of [
  { width: 1280, height: 900 },
  { width: 390, height: 844 },
]) {
  test(`aborted public disconnect-button press preserves chooser and connection at ${viewport.width}px`, async ({
    page,
    context,
    baseURL,
  }) => {
    await page.setViewportSize(viewport);
    const external: string[] = [];
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await context.route("**/*", (route) => {
      const req = route.request();
      if (
        new URL(req.url()).origin === new URL(baseURL!).origin &&
        ["GET", "HEAD"].includes(req.method())
      )
        return route.continue();
      external.push(req.method() + " " + req.url());
      return route.abort();
    });
    const { dialog, address } = await connect(page);
    await nativeReference(page);
    await expect(dialog).toBeVisible();
    await expect(address).toHaveText(ADDRESS);
    const before = page.url();
    await drag(
      page,
      await positions(
        dialog,
        dialog.getByRole("button", {
          name: "Disconnect and forget address",
          exact: true,
        }),
      ),
    );
    await expect(dialog).toBeVisible();
    await expect(address).toHaveText(ADDRESS);
    expect(page.url()).toBe(before);
    expect(await page.evaluate(() => window.authBackdropWalletCalls)).toEqual([
      "connect",
      "on",
    ]);
    expect(external).toEqual([]);
    expect(errors).toEqual([]);
  });
}

test.beforeEach(async ({ context, baseURL }) => {
  await context.route("**/*", (route) => {
    const req = route.request();
    return new URL(req.url()).origin === new URL(baseURL!).origin &&
      ["GET", "HEAD"].includes(req.method())
      ? route.continue()
      : route.abort();
  });
});

test("a complete backdrop click still closes and restores trigger focus without navigation", async ({
  page,
}) => {
  const { dialog } = await connect(page);
  const before = page.url();
  const p = await positions(
    dialog,
    dialog.getByRole("button", {
      name: "Disconnect and forget address",
      exact: true,
    }),
  );
  await page.mouse.click(p.outside.x, p.outside.y);
  await expect(dialog).not.toBeVisible();
  await expect(page.getByTestId("sign-in-button")).toBeFocused();
  expect(page.url()).toBe(before);
  expect(await page.evaluate(() => window.authBackdropWalletCalls)).toEqual([
    "connect",
    "on",
    "off",
  ]);
});

test("inside clicks and a reverse backdrop-to-panel drag preserve the public address", async ({
  page,
}) => {
  const { dialog, address } = await connect(page);
  const heading = dialog.getByRole("heading", {
    name: "Welcome back",
    exact: true,
  });
  await heading.click();
  await expect(dialog).toBeVisible();
  const p = await positions(dialog, heading);
  await page.mouse.move(p.outside.x, p.outside.y);
  await page.mouse.down();
  await page.mouse.move(p.inside.x, p.inside.y, { steps: 12 });
  await page.mouse.up();
  await expect(dialog).toBeVisible();
  await expect(address).toHaveText(ADDRESS);
  expect(await page.evaluate(() => window.authBackdropWalletCalls)).toEqual([
    "connect",
    "on",
  ]);
});

test("activating Cancel connection still cancels and rejects its later approval", async ({
  page,
}) => {
  const { dialog, address } = await connect(page, true);
  await dialog
    .getByRole("button", { name: "Cancel connection", exact: true })
    .click();
  await expect(dialog).toBeVisible();
  await expect(
    dialog.getByText("Waiting for wallet approval…", { exact: true }),
  ).toHaveCount(0);
  await expect(
    dialog.getByRole("button", {
      name: "Connect Synthetic Address Selection Wallet",
      exact: true,
    }),
  ).toBeEnabled();
  await page.evaluate(() => window.authBackdropApprove?.());
  await expect
    .poll(() => page.evaluate(() => window.authBackdropWalletCalls))
    .toEqual(["connect", "approved"]);
  await expect(address).toHaveCount(0);
});

test.describe("trusted touch cancellation", () => {
  test.use({ hasTouch: true });
  test("cancelled outside contact keeps the chooser open and a later click can dismiss", async ({
    page,
    context,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    const { dialog, address } = await connect(page);
    const p = await positions(
      dialog,
      dialog.getByRole("button", {
        name: "Disconnect and forget address",
        exact: true,
      }),
    );
    const cdp = await context.newCDPSession(page);
    await cdp.send("Input.dispatchTouchEvent", {
      type: "touchStart",
      touchPoints: [{ x: p.outside.x, y: p.outside.y, id: 1 }],
    });
    await cdp.send("Input.dispatchTouchEvent", {
      type: "touchCancel",
      touchPoints: [],
    });
    expect(
      await page.evaluate(() =>
        window.authBackdropTrace?.auth.some(
          (event) => event.type === "pointercancel" && event.trusted,
        ),
      ),
    ).toBe(true);
    await expect(dialog).toBeVisible();
    await expect(address).toHaveText(ADDRESS);
    await page.mouse.click(p.outside.x, p.outside.y);
    await expect(dialog).not.toBeVisible();
    await cdp.detach();
  });
});
