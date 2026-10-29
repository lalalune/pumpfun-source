# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: portfolio-activity-independent.spec.ts >> valid wallet activity remains explicitly inspectable when the holdings read fails
- Location: tests/portfolio-activity-independent.spec.ts:33:5

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: getByRole('alert')
Expected substring: "Token account response is unsupported."
Error: strict mode violation: getByRole('alert') resolved to 2 elements:
    1) <section role="alert" class="portfolio-error" data-error-code="RPC_RESPONSE_INVALID">…</section> aka getByText('Live portfolio unavailableToken account response is unsupported.No cached,')
    2) <div role="alert" aria-live="assertive" id="__next-route-announcer__"></div> aka locator('[id="__next-route-announcer__"]')

Call log:
  - Expect "toContainText" getByRole('alert') with timeout 5000ms
  - waiting for getByRole('alert')
    - locator resolved to <div role="alert" aria-live="assertive" id="__next-route-announcer__"></div>
    - unexpected value ""

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e2]:
    - link "Skip to main content" [ref=e3] [cursor=pointer]:
      - /url: "#main-content"
    - complementary "Application navigation" [ref=e4]:
      - generic [ref=e6]:
        - generic [ref=e7]:
          - link "Pump reconstruction home" [ref=e8] [cursor=pointer]:
            - /url: /
            - img "pump.fun logomark" [ref=e10]
          - button "Toggle Sidebar" [ref=e11] [cursor=pointer]
        - generic [ref=e14]:
          - navigation "Primary" [ref=e15]:
            - list [ref=e17]:
              - listitem [ref=e18]:
                - link "Home" [ref=e19] [cursor=pointer]:
                  - /url: /
              - listitem [ref=e23]:
                - link "Explore" [ref=e24] [cursor=pointer]:
                  - /url: /explore
              - listitem [ref=e27]:
                - button "Perps" [disabled]
              - listitem [ref=e28]:
                - link "Leaderboard" [ref=e29] [cursor=pointer]:
                  - /url: /leaderboard
              - listitem [ref=e32]:
                - link "Live" [ref=e33] [cursor=pointer]:
                  - /url: /live
            - list [ref=e38]:
              - listitem [ref=e39]:
                - link "GO" [ref=e40] [cursor=pointer]:
                  - /url: /go
              - listitem [ref=e43]:
                - link "Mayhem" [ref=e44] [cursor=pointer]:
                  - /url: /mayhem
              - listitem [ref=e47]:
                - link "Holder rewards" [ref=e48] [cursor=pointer]:
                  - /url: /holder-rewards
              - listitem [ref=e55]:
                - button "$PUMP" [disabled]
              - listitem [ref=e56]:
                - link "Portfolio" [ref=e57] [cursor=pointer]:
                  - /url: /portfolio
          - button "Create a coin" [ref=e61] [cursor=pointer]
        - list [ref=e65]:
          - listitem [ref=e66]:
            - button "Open settings" [ref=e67] [cursor=pointer]
          - listitem [ref=e71]:
            - button "Support (Intercom) is outside this reconstruction" [disabled]
          - listitem [ref=e72]:
            - button "Terminal" [disabled]
        - button "Toggle Sidebar" [ref=e74]
    - generic [ref=e76]:
      - banner [ref=e77]:
        - generic [ref=e79]:
          - generic [ref=e81]:
            - button "Go back" [ref=e82] [cursor=pointer]
            - search [ref=e86]:
              - button "Search for coins and users" [ref=e87] [cursor=pointer]:
                - generic [ref=e88]: Search for coins and users...
                - generic: ⌘K
            - button [disabled] [aria-hidden] [ref=e89]
          - generic [ref=e92]:
            - button "Create" [ref=e94] [cursor=pointer]
            - button "Sign in" [ref=e98] [cursor=pointer]
        - generic [ref=e100]:
          - button "Info bar settings" [disabled] [ref=e101]
          - radiogroup "Info bar content" [ref=e105]:
            - radio "Watchlist" [checked] [ref=e106] [cursor=pointer]
            - radio "Positions" [ref=e109] [cursor=pointer]
            - radio "Following" [ref=e112] [cursor=pointer]
            - radio "Recently viewed" [ref=e116] [cursor=pointer]
      - main [ref=e181]:
        - generic [ref=e182]:
          - generic [ref=e183]:
            - generic [ref=e184]:
              - paragraph [ref=e185]: Public mainnet read
              - heading "Solana portfolio" [level=1] [ref=e186]
              - paragraph [ref=e187]: Inspect SOL, SPL Token and Token-2022 accounts directly from a configured Solana mainnet RPC. No wallet connection or signing is required.
            - generic [ref=e188]: Read only
          - form "Load public Solana wallet" [ref=e189]:
            - generic [ref=e190]: Solana public-key address
            - generic [ref=e191]:
              - textbox "Solana public-key address" [ref=e192]:
                - /placeholder: Enter a public Solana address
                - text: So11111111111111111111111111111111111111112
              - button "Clear" [ref=e193] [cursor=pointer]
              - button "Load wallet" [ref=e194] [cursor=pointer]
            - paragraph [ref=e195]: Only public account data is read. Never enter a private key or seed phrase.
          - alert [ref=e196]:
            - heading "Live portfolio unavailable" [level=2] [ref=e197]
            - paragraph [ref=e198]: Token account response is unsupported.
            - generic [ref=e199]: No cached, historical or synthetic holdings were substituted.
      - contentinfo [ref=e200]:
        - generic [ref=e201]:
          - paragraph [ref=e202]: © Pump.fun 2026
          - navigation "Footer" [ref=e203]:
            - link "Blog" [ref=e204] [cursor=pointer]:
              - /url: https://medium.com/@pumpdotfun_
            - button "Resources" [ref=e205] [cursor=pointer]
            - button "Legal" [ref=e208] [cursor=pointer]
          - generic [ref=e211]:
            - link "X" [ref=e212] [cursor=pointer]:
              - /url: https://twitter.com/pumpfun
            - link "TikTok" [ref=e215] [cursor=pointer]:
              - /url: https://www.tiktok.com/@pump.fun
            - link "YouTube" [ref=e218] [cursor=pointer]:
              - /url: https://www.youtube.com/@pumpfunofficial
  - alert [ref=e221]
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
> 55 |   await expect(page.getByRole("alert")).toContainText(
     |                                         ^ Error: expect(locator).toContainText(expected) failed
  56 |     "Token account response is unsupported.",
  57 |   );
  58 |   expect(recordRequests).toBe(0);
  59 |   const inspect = page.getByRole("button", {
  60 |     name: "Read public Pump record",
  61 |     exact: true,
  62 |   });
  63 |   await expect(inspect).toBeVisible();
  64 |   await inspect.click();
  65 |   await expect(page.getByTestId("public-pump-record-result")).toContainText(
  66 |     "controlled-public.example",
  67 |   );
  68 |   expect(recordRequests).toBe(1);
  69 |   await expect(page.locator("html")).toHaveAttribute("data-pf-auth", "out");
  70 | });
  71 | 
```