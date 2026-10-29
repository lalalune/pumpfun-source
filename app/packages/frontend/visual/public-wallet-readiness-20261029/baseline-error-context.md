# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auth-first-open.spec.ts >> A single available Sign in activation opens the public-wallet chooser during client boot
- Location: tests/auth-first-open.spec.ts:5:5

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator:  getByTestId('auth-dialog')
Expected: visible
Received: hidden
Timeout:  5000ms

Call log:
  - Expect "toBeVisible" getByTestId('auth-dialog') with timeout 5000ms
  - waiting for getByTestId('auth-dialog')
    10 × locator resolved to <dialog role="dialog" aria-modal="true" data-auth-state="closed" data-testid="auth-dialog" aria-labelledby="_R_mb3lb_" aria-describedby="_R_mb3lbH1_" class="auth-dialog-module__J_wqWG__dialog">…</dialog>
       - unexpected value "hidden"

```

```yaml
- link "Skip to main content":
  - /url: "#main-content"
- complementary "Application navigation":
  - link "Pump reconstruction home":
    - /url: /
    - img "pump.fun logomark"
  - button "Toggle Sidebar"
  - navigation "Primary":
    - list:
      - listitem:
        - link "Home":
          - /url: /
      - listitem:
        - link "Explore":
          - /url: /explore
      - listitem:
        - button "Perps" [disabled]
      - listitem:
        - link "Leaderboard":
          - /url: /leaderboard
      - listitem:
        - link "Live":
          - /url: /live
    - list:
      - listitem:
        - link "GO":
          - /url: /go
      - listitem:
        - link "Mayhem":
          - /url: /mayhem
      - listitem:
        - link "Holder rewards":
          - /url: /holder-rewards
      - listitem:
        - button "$PUMP" [disabled]
      - listitem:
        - link "Portfolio":
          - /url: /portfolio
  - button "Create a coin":
    - img
  - list:
    - listitem:
      - button "Open settings"
    - listitem:
      - button "Support (Intercom) is outside this reconstruction" [disabled]
    - listitem:
      - button "Terminal" [disabled]
  - button "Toggle Sidebar"
- banner:
  - button "Go back"
  - search:
    - button "Search for coins and users": Search for coins and users... ⌘K
  - button "Create"
  - button "Sign in"
  - button "Info bar settings" [disabled]
  - radiogroup "Info bar content":
    - radio "Watchlist" [checked]
    - radio "Positions"
    - radio "Following"
    - radio "Recently viewed"
- main:
  - region "Explore":
    - paragraph: Historical evidence
    - heading "Explore" [level=1]
    - paragraph: Search one verified captured coin record. Results are historical, read-only and never refreshed from a production service.
    - text: Verified local snapshot
    - time: Oct 28, 2026, 10:48 AM UTC
    - search "Search the historical coin snapshot":
      - text: Search captured coins
      - searchbox "Search captured coins"
      - button "Search"
    - complementary "Snapshot limitations":
      - strong: "Local scope:"
      - text: this dataset contains exactly 1 historical record. A missing result says nothing about the current live Pump market.
    - paragraph: Captured record
    - heading "1 verified historical record" [level=2]
    - article:
      - text: MO
      - heading "MotoCross" [level=2]
      - paragraph: MotoCrose
      - term: Captured market cap (USD)
      - definition: $3,300.03
      - term: Protocol
      - definition: pump
      - text: Mint address
      - code: FwgY7679unGLV64cDpzYyfCtzocr7N2NNfbPnZhepump
      - button "Copy mint FwgY7679unGLV64cDpzYyfCtzocr7N2NNfbPnZhepump": Copy mint
      - paragraph: The captured external image is intentionally not loaded offline.
    - paragraph:
      - text: "Source: captured first-party"
      - code: /coins?offset=0&limit=1
      - text: response. SHA-256
      - code: b41a41c70fb4b2548dfc166e9c31e1b5b9dfd73d233cf94ee384a9c5d75e017d
      - text: .
    - paragraph: External images, token detail pages, wallet actions and trading are not enabled.
- contentinfo:
  - paragraph: © Pump.fun 2026
  - navigation "Footer":
    - link "Blog":
      - /url: https://medium.com/@pumpdotfun_
    - button "Resources"
    - button "Legal"
  - link "X":
    - /url: https://twitter.com/pumpfun
    - img
  - link "TikTok":
    - /url: https://www.tiktok.com/@pump.fun
    - img
  - link "YouTube":
    - /url: https://www.youtube.com/@pumpfunofficial
    - img
- alert
```

# Test source

```ts
  1  | import { expect, test } from "@playwright/test";
  2  | 
  3  | // Hold only this local app's client scripts, so the initial HTML remains usable
  4  | // for observation without relying on a short or a slow machine's timing.
  5  | test("A single available Sign in activation opens the public-wallet chooser during client boot", async ({
  6  |   page,
  7  | }, testInfo) => {
  8  |   let release!: () => void;
  9  |   const clientBoot = new Promise<void>((resolve) => {
  10 |     release = resolve;
  11 |   });
  12 |   const unexpected: string[] = [];
  13 |   page.on("request", (request) => {
  14 |     const url = new URL(request.url());
  15 |     if (
  16 |       !["127.0.0.1", "localhost"].includes(url.hostname) ||
  17 |       !["GET", "HEAD"].includes(request.method())
  18 |     )
  19 |       unexpected.push(request.url());
  20 |   });
  21 |   await page.route("**/_next/static/**/*.js*", async (route) => {
  22 |     await clientBoot;
  23 |     await route.continue().catch(() => {});
  24 |   });
  25 |   try {
  26 |     await page.goto("/explore", { waitUntil: "commit" });
  27 |     const trigger = page.getByTestId("sign-in-button");
  28 |     await expect(trigger).toBeVisible();
  29 |     await expect(page.getByTestId("auth-dialog")).toHaveCount(0);
  30 |     // Exercise the action if the page offers it; otherwise wait for the page
  31 |     // to offer it. A single accepted activation must not silently disappear.
  32 |     const initiallyEnabled = await trigger.isEnabled();
  33 |     await testInfo.attach("server-trigger-readiness", {
  34 |       body: JSON.stringify({ initiallyEnabled, clientScriptsHeld: true }),
  35 |       contentType: "application/json",
  36 |     });
  37 |     if (initiallyEnabled) await trigger.click();
  38 |     release();
  39 |     if (!initiallyEnabled) {
  40 |       await expect(trigger).toBeEnabled();
  41 |       await trigger.click();
  42 |     }
> 43 |     await expect(page.getByTestId("auth-dialog")).toBeVisible();
     |                                                   ^ Error: expect(locator).toBeVisible() failed
  44 |     await expect(page.getByTestId("auth-dialog")).toHaveAttribute(
  45 |       "data-auth-state",
  46 |       "ready",
  47 |     );
  48 |     await expect(
  49 |       page.getByRole("button", {
  50 |         name: "Connect a public wallet",
  51 |         exact: true,
  52 |       }),
  53 |     ).toBeVisible();
  54 |     await expect(page.getByTestId("auth-google-button")).toBeDisabled();
  55 |     await expect(page.locator("html")).toHaveAttribute("data-pf-auth", "out");
  56 |     expect(unexpected).toEqual([]);
  57 |   } finally {
  58 |     release();
  59 |   }
  60 | });
  61 | 
```