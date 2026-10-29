# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: public-wallet.spec.ts >> connected public address reads mainnet only on explicit request without credentials or authentication
- Location: tests/public-wallet.spec.ts:196:5

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: getByTestId('public-wallet-balance-result')
Expected substring: "9007199.254740993 SOL"
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toContainText" getByTestId('public-wallet-balance-result') with timeout 5000ms
  - waiting for getByTestId('public-wallet-balance-result')

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
  - button "Sign in" [expanded]
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
- dialog "Welcome back":
  - banner:
    - heading "Welcome back" [level=2]
    - button "Close"
  - paragraph: Local reconstruction — sign-in is unavailable. No authenticated account or email is connected.
  - group "Continue with a social account":
    - button "Google" [disabled]
    - button "Apple" [disabled]
    - button "Continue with GitHub" [disabled]
  - text: Email address Unavailable or connect a wallet
  - button "Phantom Unavailable" [disabled]
  - button "Coinbase Wallet Unavailable" [disabled]
  - button "More wallets"
  - paragraph: Provider login, email codes and signing are disabled.
  - region "Public wallet connection":
    - heading "Public wallet connection" [level=3]
    - paragraph: Share a public Solana address with this page. This does not sign you in or request a signature. The address is forgotten when this dialog closes.
    - status: Connected public address — ownership unverified
    - code: So11111111111111111111111111111111111111112
    - button "Disconnect and forget address"
    - region "Public mainnet overview":
      - heading "Public mainnet overview" [level=4]
      - paragraph: Read public SOL holdings and token-account inventory for this address from the configured mainnet RPC. Your wallet may be using another network.
      - button "Read public mainnet overview"
      - alert: The public mainnet overview is unavailable. Try again.
```

# Test source

```ts
  125 |       name: "Connect Browser Protocol Wallet",
  126 |       exact: true,
  127 |     })
  128 |     .click();
  129 |   await expect(page.getByTestId("public-wallet-address")).toHaveText(ADDRESS);
  130 | }
  131 | 
  132 | function publicOverview(address = ADDRESS) {
  133 |   const programId = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA";
  134 |   const accounts = ["3000000", "4000000"].map((rawAmount, index) => ({
  135 |     tokenAccount: index
  136 |       ? "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"
  137 |       : OTHER_ADDRESS,
  138 |     mint: ADDRESS,
  139 |     owner: address,
  140 |     program: "spl-token",
  141 |     programId,
  142 |     rawAmount,
  143 |     decimals: 6,
  144 |     amount: index ? "4" : "3",
  145 |     state: "initialized",
  146 |     isNative: false,
  147 |     extensions: [],
  148 |   }));
  149 |   return {
  150 |     ok: true,
  151 |     address,
  152 |     cluster: "mainnet-beta",
  153 |     genesisHash: "5eykt4UsFv8P8NJdTREpY1vzqKqZKvdpKuc147dw2N9d",
  154 |     commitment: "confirmed",
  155 |     observedAt: "2026-10-29T14:00:00.000Z",
  156 |     endpointHost: "public-rpc.example",
  157 |     snapshotAtomic: false,
  158 |     sol: {
  159 |       lamports: "9007199254740993",
  160 |       amount: "9007199.254740993",
  161 |       contextSlot: 321,
  162 |     },
  163 |     splToken: {
  164 |       program: "spl-token",
  165 |       programId,
  166 |       contextSlot: 322,
  167 |       accounts,
  168 |       mints: [
  169 |         {
  170 |           mint: ADDRESS,
  171 |           program: "spl-token",
  172 |           programId,
  173 |           rawAmount: "7000000",
  174 |           amount: "7",
  175 |           decimals: 6,
  176 |           accountCount: 2,
  177 |         },
  178 |       ],
  179 |     },
  180 |     token2022: {
  181 |       program: "token-2022",
  182 |       programId: "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",
  183 |       contextSlot: 323,
  184 |       accounts: [],
  185 |       mints: [],
  186 |     },
  187 |   };
  188 | }
  189 | 
  190 | const readOverview = (page: Page) =>
  191 |   page.getByRole("button", {
  192 |     name: "Read public mainnet overview",
  193 |     exact: true,
  194 |   });
  195 | 
  196 | test("connected public address reads mainnet only on explicit request without credentials or authentication", async ({
  197 |   page,
  198 |   context,
  199 | }) => {
  200 |   await context.addCookies([
  201 |     {
  202 |       name: "private_test_session",
  203 |       value: "not-forwarded",
  204 |       domain: "127.0.0.1",
  205 |       path: "/",
  206 |     },
  207 |   ]);
  208 |   const requests: {
  209 |     address: string | null;
  210 |     method: string;
  211 |     cookie: string | undefined;
  212 |   }[] = [];
  213 |   await page.route("**/api/portfolio?*", async (route) => {
  214 |     requests.push({
  215 |       address: new URL(route.request().url()).searchParams.get("address"),
  216 |       method: route.request().method(),
  217 |       cookie: route.request().headers().cookie,
  218 |     });
  219 |     await route.fulfill({ json: publicOverview() });
  220 |   });
  221 |   await connectPublicAddress(page);
  222 |   expect(requests).toEqual([]);
  223 |   await readOverview(page).click();
  224 |   const result = page.getByTestId("public-wallet-balance-result");
> 225 |   await expect(result).toContainText("9007199.254740993 SOL");
      |                        ^ Error: expect(locator).toContainText(expected) failed
  226 |   await expect(result).toContainText("2 accounts · 1 mint");
  227 |   await expect(result).toContainText("0 accounts · 0 mints");
  228 |   await expect(result).toContainText("SOL 321, SPL 322, Token-2022 323");
  229 |   await expect(result).toContainText("public-rpc.example");
  230 |   await expect(result).toContainText("not an atomic snapshot");
  231 |   await expect(result).toContainText("do not establish ownership");
  232 |   expect(requests).toEqual([
  233 |     { address: ADDRESS, method: "GET", cookie: undefined },
  234 |   ]);
  235 |   expect((await probe(page)).calls).toEqual(["connect:0", "on:change"]);
  236 |   await expect(page.locator("html")).toHaveAttribute("data-pf-auth", "out");
  237 |   await expect(page.getByTestId("auth-google-button")).toBeDisabled();
  238 | });
  239 | 
  240 | test("public overview refresh removes prior data on failure and can recover from rate limiting", async ({
  241 |   page,
  242 | }) => {
  243 |   let count = 0;
  244 |   await page.route("**/api/portfolio?*", (route) => {
  245 |     count++;
  246 |     return route.fulfill(
  247 |       count === 2
  248 |         ? {
  249 |             status: 429,
  250 |             json: {
  251 |               ok: false,
  252 |               error: {
  253 |                 code: "RPC_RATE_LIMITED",
  254 |                 retryable: true,
  255 |                 message: "private-provider-body",
  256 |               },
  257 |             },
  258 |           }
  259 |         : { json: publicOverview() },
  260 |     );
  261 |   });
  262 |   await connectPublicAddress(page);
  263 |   await readOverview(page).click();
  264 |   await expect(page.getByTestId("public-wallet-balance-result")).toBeVisible();
  265 |   await page
  266 |     .getByRole("button", {
  267 |       name: "Refresh public mainnet overview",
  268 |       exact: true,
  269 |     })
  270 |     .click();
  271 |   await expect(
  272 |     page.getByTestId("public-wallet-balance-overview").getByRole("alert"),
  273 |   ).toContainText("rate limited");
  274 |   await expect(page.getByTestId("public-wallet-balance-result")).toHaveCount(0);
  275 |   await expect(page.getByTestId("public-wallet-panel")).not.toContainText(
  276 |     "private-provider-body",
  277 |   );
  278 |   await expect(page.getByTestId("public-wallet-address")).toHaveText(ADDRESS);
  279 |   await readOverview(page).click();
  280 |   await expect(page.getByTestId("public-wallet-balance-result")).toBeVisible();
  281 |   expect(count).toBe(3);
  282 | });
  283 | 
  284 | test("public overview rejects a response belonging to another address", async ({
  285 |   page,
  286 | }) => {
  287 |   await page.route("**/api/portfolio?*", (route) =>
  288 |     route.fulfill({ json: publicOverview(OTHER_ADDRESS) }),
  289 |   );
  290 |   await connectPublicAddress(page);
  291 |   await readOverview(page).click();
  292 |   await expect(
  293 |     page.getByTestId("public-wallet-balance-overview").getByRole("alert"),
  294 |   ).toContainText("unavailable");
  295 |   await expect(page.getByTestId("public-wallet-balance-result")).toHaveCount(0);
  296 | });
  297 | 
  298 | test("an account change aborts the old overview and requires another explicit read", async ({
  299 |   page,
  300 | }) => {
  301 |   let release!: () => void, started!: () => void;
  302 |   const gate = new Promise<void>((resolve) => {
  303 |       release = resolve;
  304 |     }),
  305 |     pending = new Promise<void>((resolve) => {
  306 |       started = resolve;
  307 |     });
  308 |   const addresses: string[] = [];
  309 |   await page.route("**/api/portfolio?*", async (route) => {
  310 |     const address = new URL(route.request().url()).searchParams.get("address")!;
  311 |     addresses.push(address);
  312 |     if (address === ADDRESS) {
  313 |       started();
  314 |       await gate;
  315 |     }
  316 |     await route.fulfill({ json: publicOverview(address) }).catch(() => {});
  317 |   });
  318 |   await connectPublicAddress(page);
  319 |   await readOverview(page).click();
  320 |   await pending;
  321 |   await page.evaluate(
  322 |     (address) =>
  323 |       (
  324 |         window as unknown as { __publicWalletProbe: Probe }
  325 |       ).__publicWalletProbe.change(address),
```