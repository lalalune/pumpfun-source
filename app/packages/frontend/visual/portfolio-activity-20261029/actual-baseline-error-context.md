# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: portfolio-activity-independent.spec.ts >> valid wallet activity remains explicitly inspectable when the holdings read fails
- Location: tests/portfolio-activity-independent.spec.ts:33:5

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByRole('button', { name: 'Read public Pump record', exact: true })
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByRole('button', { name: 'Read public Pump record', exact: true }) with timeout 5000ms
  - waiting for getByRole('button', { name: 'Read public Pump record', exact: true })

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
  - paragraph: Public mainnet read
  - heading "Solana portfolio" [level=1]
  - paragraph: Inspect SOL, SPL Token and Token-2022 accounts directly from a configured Solana mainnet RPC. No wallet connection or signing is required.
  - text: Read only
  - form "Load public Solana wallet":
    - text: Solana public-key address
    - textbox "Solana public-key address":
      - /placeholder: Enter a public Solana address
      - text: So11111111111111111111111111111111111111112
    - button "Clear"
    - button "Load wallet"
    - paragraph: Only public account data is read. Never enter a private key or seed phrase.
  - alert:
    - heading "Live portfolio unavailable" [level=2]
    - paragraph: Token account response is unsupported.
    - text: No cached, historical or synthetic holdings were substituted.
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
  2  | import { PublicKey } from "@solana/web3.js";
  3  | import { PUMP_PROGRAM_ID, userVolumeAccumulatorPda } from "@pump-fun/pump-sdk";
  4  | const ADDRESS = "So11111111111111111111111111111111111111112";
  5  | // Existing public-record DTO. No new service/API/SDK behavior is introduced.
  6  | function record() {
  7  |   return {
  8  |     ok: true,
  9  |     address: ADDRESS,
  10 |     programId: PUMP_PROGRAM_ID.toBase58(),
  11 |     recordPda: userVolumeAccumulatorPda(new PublicKey(ADDRESS)).toBase58(),
  12 |     cluster: "mainnet-beta",
  13 |     commitment: "confirmed",
  14 |     contextSlot: 321,
  15 |     endpointHost: "controlled-public.example",
  16 |     observedAt: "2026-10-29T05:00:00.000Z",
  17 |     dataBytes: 106,
  18 |     record: {
  19 |       user: ADDRESS,
  20 |       needsClaim: false,
  21 |       hasTotalClaimedTokens: false,
  22 |       totalUnclaimedTokens: "7",
  23 |       totalClaimedTokens: "0",
  24 |       currentSolVolume: "2",
  25 |       lastUpdateTimestamp: "0",
  26 |       cashbackEarned: "0",
  27 |       totalCashbackClaimed: "0",
  28 |       stableCashbackEarned: "0",
  29 |       totalStableCashbackClaimed: "0",
  30 |     },
  31 |   };
  32 | }
  33 | test("valid wallet activity remains explicitly inspectable when the holdings read fails", async ({
  34 |   page,
  35 | }) => {
  36 |   let recordRequests = 0;
  37 |   await page.route("**/api/portfolio?*", (route) =>
  38 |     route.fulfill({
  39 |       status: 502,
  40 |       json: {
  41 |         ok: false,
  42 |         error: {
  43 |           code: "RPC_RESPONSE_INVALID",
  44 |           message: "Token account response is unsupported.",
  45 |           retryable: false,
  46 |         },
  47 |       },
  48 |     }),
  49 |   );
  50 |   await page.route("**/api/portfolio/pump-record?*", (route) => {
  51 |     recordRequests++;
  52 |     return route.fulfill({ json: record() });
  53 |   });
  54 |   await page.goto(`/portfolio?address=${ADDRESS}`);
  55 |   await expect(page.locator(".portfolio-error")).toContainText(
  56 |     "Token account response is unsupported.",
  57 |   );
  58 |   expect(recordRequests).toBe(0);
  59 |   const inspect = page.getByRole("button", {
  60 |     name: "Read public Pump record",
  61 |     exact: true,
  62 |   });
> 63 |   await expect(inspect).toBeVisible();
     |                         ^ Error: expect(locator).toBeVisible() failed
  64 |   await inspect.click();
  65 |   await expect(page.getByTestId("public-pump-record-result")).toContainText(
  66 |     "controlled-public.example",
  67 |   );
  68 |   expect(recordRequests).toBe(1);
  69 |   await expect(page.locator("html")).toHaveAttribute("data-pf-auth", "out");
  70 | });
  71 | 
```