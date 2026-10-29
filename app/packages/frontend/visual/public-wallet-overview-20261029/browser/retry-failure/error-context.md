# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: public-wallet.spec.ts >> closing a connected dialog discards a late public balance response
- Location: tests/public-wallet.spec.ts:372:5

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.click: Test timeout of 30000ms exceeded.
Call log:
  - waiting for getByRole('button', { name: 'Connect a public wallet', exact: true })

```

# Page snapshot

```yaml
- generic [ref=e1]:
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
              - listitem [ref=e28]:
                - button "Perps" [disabled]
              - listitem [ref=e29]:
                - link "Leaderboard" [ref=e30] [cursor=pointer]:
                  - /url: /leaderboard
              - listitem [ref=e33]:
                - link "Live" [ref=e34] [cursor=pointer]:
                  - /url: /live
            - list [ref=e39]:
              - listitem [ref=e40]:
                - link "GO" [ref=e41] [cursor=pointer]:
                  - /url: /go
              - listitem [ref=e44]:
                - link "Mayhem" [ref=e45] [cursor=pointer]:
                  - /url: /mayhem
              - listitem [ref=e48]:
                - link "Holder rewards" [ref=e49] [cursor=pointer]:
                  - /url: /holder-rewards
              - listitem [ref=e56]:
                - button "$PUMP" [disabled]
              - listitem [ref=e57]:
                - link "Portfolio" [ref=e58] [cursor=pointer]:
                  - /url: /portfolio
          - button "Create a coin" [ref=e62] [cursor=pointer]
        - list [ref=e66]:
          - listitem [ref=e67]:
            - button "Open settings" [ref=e68] [cursor=pointer]
          - listitem [ref=e72]:
            - button "Support (Intercom) is outside this reconstruction" [disabled]
          - listitem [ref=e73]:
            - button "Terminal" [disabled]
        - button "Toggle Sidebar" [ref=e75]
    - generic [ref=e77]:
      - banner [ref=e78]:
        - generic [ref=e80]:
          - generic [ref=e82]:
            - button "Go back" [ref=e83] [cursor=pointer]
            - search [ref=e87]:
              - button "Search for coins and users" [ref=e88] [cursor=pointer]:
                - generic [ref=e89]: Search for coins and users...
                - generic: ⌘K
            - button [disabled] [aria-hidden] [ref=e90]
          - generic [ref=e93]:
            - button "Create" [ref=e95] [cursor=pointer]
            - button "Sign in" [active] [ref=e99] [cursor=pointer]
        - generic [ref=e101]:
          - button "Info bar settings" [disabled] [ref=e102]
          - radiogroup "Info bar content" [ref=e106]:
            - radio "Watchlist" [checked] [ref=e107] [cursor=pointer]
            - radio "Positions" [ref=e110] [cursor=pointer]
            - radio "Following" [ref=e113] [cursor=pointer]
            - radio "Recently viewed" [ref=e117] [cursor=pointer]
      - main [ref=e182]:
        - region [ref=e183]:
          - generic [ref=e184]:
            - generic [ref=e185]:
              - paragraph [ref=e186]: Historical evidence
              - heading "Explore" [level=1] [ref=e187]
              - paragraph [ref=e188]: Search one verified captured coin record. Results are historical, read-only and never refreshed from a production service.
            - generic [ref=e189]:
              - generic [ref=e190]: Verified local snapshot
              - time [ref=e191]: Oct 28, 2026, 10:48 AM UTC
          - search "Search the historical coin snapshot" [ref=e192]:
            - generic [ref=e193]: Search captured coins
            - generic [ref=e194]:
              - searchbox "Search captured coins" [ref=e195]
              - button "Search" [ref=e196] [cursor=pointer]
          - complementary "Snapshot limitations" [ref=e197]:
            - strong [ref=e198]: "Local scope:"
            - text: this dataset contains exactly 1 historical record. A missing result says nothing about the current live Pump market.
          - generic [ref=e200]:
            - paragraph [ref=e201]: Captured record
            - heading "1 verified historical record" [level=2] [ref=e202]
          - generic "Historical coin results" [ref=e203]:
            - article [ref=e204]:
              - generic [ref=e205]:
                - generic "Local image placeholder" [ref=e206]: MO
                - generic [ref=e207]:
                  - heading "MotoCross" [level=2] [ref=e208]
                  - paragraph [ref=e209]: MotoCrose
              - generic [ref=e210]:
                - generic [ref=e211]:
                  - term [ref=e212]: Captured market cap (USD)
                  - definition [ref=e213]: $3,300.03
                - generic [ref=e214]:
                  - term [ref=e215]: Protocol
                  - definition [ref=e216]: pump
              - generic [ref=e217]:
                - generic [ref=e218]: Mint address
                - code [ref=e219]: FwgY7679unGLV64cDpzYyfCtzocr7N2NNfbPnZhepump
                - button "Copy mint FwgY7679unGLV64cDpzYyfCtzocr7N2NNfbPnZhepump" [ref=e221] [cursor=pointer]: Copy mint
              - paragraph [ref=e222]: The captured external image is intentionally not loaded offline.
          - generic [ref=e223]:
            - paragraph [ref=e224]:
              - text: "Source: captured first-party"
              - code [ref=e225]: /coins?offset=0&limit=1
              - text: response. SHA-256
              - code [ref=e226]: b41a41c70fb4b2548dfc166e9c31e1b5b9dfd73d233cf94ee384a9c5d75e017d
              - text: .
            - paragraph [ref=e227]: External images, token detail pages, wallet actions and trading are not enabled.
      - contentinfo [ref=e228]:
        - generic [ref=e229]:
          - paragraph [ref=e230]: © Pump.fun 2026
          - navigation "Footer" [ref=e231]:
            - link "Blog" [ref=e232] [cursor=pointer]:
              - /url: https://medium.com/@pumpdotfun_
            - button "Resources" [ref=e233] [cursor=pointer]
            - button "Legal" [ref=e236] [cursor=pointer]
          - generic [ref=e239]:
            - link "X" [ref=e240] [cursor=pointer]:
              - /url: https://twitter.com/pumpfun
            - link "TikTok" [ref=e243] [cursor=pointer]:
              - /url: https://www.tiktok.com/@pump.fun
            - link "YouTube" [ref=e246] [cursor=pointer]:
              - /url: https://www.youtube.com/@pumpfunofficial
  - button "Open Next.js Dev Tools" [ref=e254] [cursor=pointer]
  - alert [ref=e258]
```

# Test source

```ts
  17  |   await page.addInitScript(
  18  |     ({ address, mode }) => {
  19  |       let accounts = [{ address, chains: ["solana:mainnet"] }];
  20  |       let change: ((value: unknown) => void) | null = null;
  21  |       let unregister = () => {};
  22  |       const probe = {
  23  |         calls: [] as string[],
  24  |         reads: 0,
  25  |         resolve: () => {},
  26  |         reject: () => {},
  27  |         change(address: string | null) {
  28  |           accounts = address ? [{ address, chains: ["solana:mainnet"] }] : [];
  29  |           change?.({ accounts });
  30  |         },
  31  |         unregister: () => unregister(),
  32  |       };
  33  |       const wallet = {
  34  |         version: "1.0.0",
  35  |         name: "Browser Protocol Wallet",
  36  |         chains: ["solana:mainnet"],
  37  |         get accounts() {
  38  |           probe.reads++;
  39  |           return accounts;
  40  |         },
  41  |         get icon() {
  42  |           throw new Error("Wallet icon should not be read");
  43  |         },
  44  |         features: {
  45  |           "standard:connect": {
  46  |             version: "1.0.0",
  47  |             async connect(...args: unknown[]) {
  48  |               probe.calls.push(`connect:${args.length}`);
  49  |               if (mode === "reject")
  50  |                 throw new Error("private-provider-payload");
  51  |               if (mode === "pending")
  52  |                 await new Promise<void>((resolve, reject) => {
  53  |                   probe.resolve = resolve;
  54  |                   probe.reject = () =>
  55  |                     reject(new Error("private-provider-payload"));
  56  |                 });
  57  |               return { accounts };
  58  |             },
  59  |           },
  60  |           "standard:events": {
  61  |             version: "1.0.0",
  62  |             on(event: string, callback: typeof change) {
  63  |               probe.calls.push(`on:${event}`);
  64  |               change = callback;
  65  |               return () => {
  66  |                 probe.calls.push("off");
  67  |                 change = null;
  68  |               };
  69  |             },
  70  |           },
  71  |           "standard:disconnect": {
  72  |             version: "1.0.0",
  73  |             async disconnect() {
  74  |               probe.calls.push("disconnect");
  75  |             },
  76  |           },
  77  |           get "solana:signMessage"() {
  78  |             throw new Error("Signing is forbidden");
  79  |           },
  80  |           get "solana:signTransaction"() {
  81  |             throw new Error("Signing is forbidden");
  82  |           },
  83  |           get "solana:signIn"() {
  84  |             throw new Error("Sign-in is forbidden");
  85  |           },
  86  |         },
  87  |       };
  88  |       if (mode === "without-disconnect")
  89  |         Reflect.deleteProperty(wallet.features, "standard:disconnect");
  90  |       window.addEventListener("wallet-standard:app-ready", ((
  91  |         event: CustomEvent,
  92  |       ) => {
  93  |         unregister = event.detail.register(wallet);
  94  |       }) as EventListener);
  95  |       Object.assign(window, { __publicWalletProbe: probe });
  96  |     },
  97  |     { address: ADDRESS, mode },
  98  |   );
  99  | }
  100 | const probe = (page: Page) =>
  101 |   page.evaluate(() => {
  102 |     const p = (window as unknown as { __publicWalletProbe: Probe })
  103 |       .__publicWalletProbe;
  104 |     return { calls: p.calls, reads: p.reads };
  105 |   });
  106 | const mutate = (page: Page, action: "resolve" | "unregister") =>
  107 |   page.evaluate((action) => {
  108 |     (window as unknown as { __publicWalletProbe: Probe }).__publicWalletProbe[
  109 |       action
  110 |     ]();
  111 |   }, action);
  112 | async function open(page: Page) {
  113 |   await page.goto("/explore");
  114 |   await page.getByTestId("sign-in-button").click();
  115 |   await page
  116 |     .getByRole("button", { name: "Connect a public wallet", exact: true })
> 117 |     .click();
      |      ^ Error: locator.click: Test timeout of 30000ms exceeded.
  118 | }
  119 | 
  120 | async function connectPublicAddress(page: Page) {
  121 |   await installWallet(page);
  122 |   await open(page);
  123 |   await page
  124 |     .getByRole("button", {
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
  144 |     amount: index ? "4.000000" : "3.000000",
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
  174 |           amount: "7.000000",
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
```