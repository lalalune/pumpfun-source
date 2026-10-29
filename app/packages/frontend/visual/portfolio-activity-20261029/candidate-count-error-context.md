# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: portfolio-activity-independent.spec.ts >> retrying holdings invalidates an activity snapshot without automatically reading it again
- Location: tests/portfolio-activity-independent.spec.ts:210:5

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: 2
Received: 3
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
            - button "Try again" [ref=e200] [cursor=pointer]
          - generic [ref=e201]:
            - paragraph [ref=e202]:
              - text: "Activity record wallet:"
              - code [ref=e203]: So11111111111111111111111111111111111111112
            - region [ref=e204]:
              - heading "Public Pump activity record" [level=2] [ref=e205]
              - paragraph [ref=e206]: Optionally inspect this wallet’s stored Pump program record. It is separate from wallet balances and does not establish current rewards, claim eligibility, ownership or profit.
              - button "Read public Pump record" [ref=e207] [cursor=pointer]
      - contentinfo [ref=e208]:
        - generic [ref=e209]:
          - paragraph [ref=e210]: © Pump.fun 2026
          - navigation "Footer" [ref=e211]:
            - link "Blog" [ref=e212] [cursor=pointer]:
              - /url: https://medium.com/@pumpdotfun_
            - button "Resources" [ref=e213] [cursor=pointer]
            - button "Legal" [ref=e216] [cursor=pointer]
          - generic [ref=e219]:
            - link "X" [ref=e220] [cursor=pointer]:
              - /url: https://twitter.com/pumpfun
            - link "TikTok" [ref=e223] [cursor=pointer]:
              - /url: https://www.tiktok.com/@pump.fun
            - link "YouTube" [ref=e226] [cursor=pointer]:
              - /url: https://www.youtube.com/@pumpfunofficial
  - button "Open Next.js Dev Tools" [ref=e234] [cursor=pointer]
  - alert [ref=e238]
```

# Test source

```ts
  133 |     await failedHoldings(page);
  134 |     await page.route("**/api/portfolio/pump-record?*", (route) => {
  135 |       requests++;
  136 |       return route.abort();
  137 |     });
  138 |     await page.goto(`/portfolio?${new URLSearchParams({ address })}`);
  139 |     await expect(
  140 |       page.getByLabel("Solana public-key address", { exact: true }),
  141 |     ).toHaveValue(address);
  142 |     await expect(page.getByTestId("portfolio-activity")).toHaveCount(0);
  143 |     expect(requests).toBe(0);
  144 |   });
  145 | }
  146 | 
  147 | test("editing a draft preserves the committed target; navigation clears the previous result", async ({
  148 |   page,
  149 | }) => {
  150 |   await failedHoldings(page);
  151 |   const requests: string[] = [];
  152 |   await page.route("**/api/portfolio/pump-record?*", (route) => {
  153 |     const address = new URL(route.request().url()).searchParams.get("address")!;
  154 |     requests.push(address);
  155 |     return route.fulfill({ json: record(address) });
  156 |   });
  157 |   await page.goto(`/portfolio?address=${ADDRESS}`);
  158 |   const input = page.getByLabel("Solana public-key address", { exact: true });
  159 |   await input.fill(OTHER);
  160 |   await expect(page.getByTestId("portfolio-activity")).toContainText(ADDRESS);
  161 |   await inspect(page).click();
  162 |   await expect(page.getByTestId("public-pump-record-result")).toBeVisible();
  163 |   expect(requests).toEqual([ADDRESS]);
  164 |   await page.getByRole("button", { name: "Load wallet", exact: true }).click();
  165 |   await expect(page).toHaveURL(new RegExp(`address=${OTHER}$`));
  166 |   await expect(page.getByTestId("portfolio-activity")).toContainText(OTHER);
  167 |   await expect(page.getByTestId("public-pump-record-result")).toHaveCount(0);
  168 |   expect(requests).toEqual([ADDRESS]);
  169 |   await inspect(page).click();
  170 |   await expect(page.getByTestId("public-pump-record-result")).toBeVisible();
  171 |   expect(requests).toEqual([ADDRESS, OTHER]);
  172 | });
  173 | 
  174 | test("navigation invalidates a pending activity result while both wallets have holdings errors", async ({
  175 |   page,
  176 | }) => {
  177 |   await failedHoldings(page);
  178 |   let release!: () => void, started!: () => void;
  179 |   const gate = new Promise<void>((resolve) => {
  180 |     release = resolve;
  181 |   });
  182 |   const pending = new Promise<void>((resolve) => {
  183 |     started = resolve;
  184 |   });
  185 |   await page.route("**/api/portfolio/pump-record?*", async (route) => {
  186 |     const address = new URL(route.request().url()).searchParams.get("address")!;
  187 |     if (address === ADDRESS) {
  188 |       started();
  189 |       await gate;
  190 |     }
  191 |     await route.fulfill({ json: record(address) }).catch(() => {});
  192 |   });
  193 |   await page.goto(`/portfolio?address=${ADDRESS}`);
  194 |   await inspect(page).click();
  195 |   await pending;
  196 |   await page
  197 |     .getByLabel("Solana public-key address", { exact: true })
  198 |     .fill(OTHER);
  199 |   await page.getByRole("button", { name: "Load wallet", exact: true }).click();
  200 |   await expect(page.getByTestId("portfolio-activity")).toContainText(OTHER);
  201 |   release();
  202 |   await expect(inspect(page)).toBeVisible();
  203 |   await expect(page.getByTestId("public-pump-record-result")).toHaveCount(0);
  204 |   await inspect(page).click();
  205 |   await expect(page.getByTestId("public-pump-record-result")).toContainText(
  206 |     record(OTHER).recordPda,
  207 |   );
  208 | });
  209 | 
  210 | test("retrying holdings invalidates an activity snapshot without automatically reading it again", async ({
  211 |   page,
  212 | }) => {
  213 |   let balanceRequests = 0,
  214 |     recordRequests = 0;
  215 |   await page.route("**/api/portfolio?*", (route) => {
  216 |     balanceRequests++;
  217 |     return route.fulfill({ status: 502, json: failure });
  218 |   });
  219 |   await page.route("**/api/portfolio/pump-record?*", (route) => {
  220 |     recordRequests++;
  221 |     return route.fulfill({ json: record() });
  222 |   });
  223 |   await page.goto(`/portfolio?address=${ADDRESS}`);
  224 |   await inspect(page).click();
  225 |   await expect(page.getByTestId("public-pump-record-result")).toBeVisible();
  226 |   await page
  227 |     .locator(".portfolio-error")
  228 |     .getByRole("button", { name: "Try again", exact: true })
  229 |     .click();
  230 |   await expect(inspect(page)).toBeVisible();
  231 |   await expect(page.getByTestId("public-pump-record-result")).toHaveCount(0);
  232 |   expect(recordRequests).toBe(1);
> 233 |   expect(balanceRequests).toBe(2);
      |                           ^ Error: expect(received).toBe(expected) // Object.is equality
  234 |   await inspect(page).click();
  235 |   await expect(page.getByTestId("public-pump-record-result")).toBeVisible();
  236 |   expect(recordRequests).toBe(2);
  237 | });
  238 | 
```