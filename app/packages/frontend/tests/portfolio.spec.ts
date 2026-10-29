import { expect, test, type Page, type Route } from "@playwright/test";

const WALLET = "HN7cABqLq46Es1jh92dQQisAq662SmxELLLsHHe4YWrH";
const OTHER_WALLET = "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU";
const SPL_ACCOUNT = "69gGSxcFan4EoL63vdHsHeP8XNpXgVCEpcSu9P4fn6xa";
const TOKEN_2022_ACCOUNT = "B5PrYwGW7KqYBUoab2GsKftCW8tzPKcZy9MSNEbvU5DF";
const SPL_MINT = "Ht3cqPuEUR6jiNiFsF1n93TPokuq1jqiMKujAjDdxXCB";
const TOKEN_2022_MINT = "2NrDzgpDWQKKHmVJZqQVn3XjMt6WGhLdrr941RtzsQZG";

function tokenAccount({
  owner,
  tokenAccount,
  mint,
  program,
  programId,
  amount,
  decimals,
}: {
  owner: string;
  tokenAccount: string;
  mint: string;
  program: "spl-token" | "token-2022";
  programId: string;
  amount: string;
  decimals: number;
}) {
  return {
    tokenAccount,
    mint,
    owner,
    program,
    programId,
    rawAmount: amount,
    decimals,
    amount:
      decimals === 6
        ? `${amount.slice(0, -6) || "0"}.${amount.slice(-6).padStart(6, "0")}`
        : amount,
    state: "initialized" as const,
    isNative: false,
    extensions: program === "token-2022" ? ["immutableOwner"] : [],
  };
}

function portfolio(address = WALLET, empty = false) {
  const splAccount = tokenAccount({
    owner: address,
    tokenAccount: SPL_ACCOUNT,
    mint: SPL_MINT,
    program: "spl-token",
    programId: "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
    amount: "9007199254740993",
    decimals: 6,
  });
  const token2022Account = tokenAccount({
    owner: address,
    tokenAccount: TOKEN_2022_ACCOUNT,
    mint: TOKEN_2022_MINT,
    program: "token-2022",
    programId: "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",
    amount: "5000000",
    decimals: 6,
  });
  const group = (
    program: "spl-token" | "token-2022",
    programId: string,
    contextSlot: number,
    accounts: ReturnType<typeof tokenAccount>[],
  ) => ({
    program,
    programId,
    contextSlot,
    accounts,
    mints: accounts.map((account) => ({
      mint: account.mint,
      program,
      programId,
      rawAmount: account.rawAmount,
      decimals: account.decimals,
      amount: account.amount,
      accountCount: 1,
    })),
  });
  return {
    ok: true as const,
    address,
    cluster: "mainnet-beta" as const,
    genesisHash: "5eykt4UsFv8P8NJdTREpY1vzqKqZKvdpKuc147dw2N9d",
    commitment: "confirmed" as const,
    observedAt: "2026-10-28T18:30:00.000Z",
    endpointHost: "api.mainnet.solana.com",
    sol: {
      lamports: empty ? "0" : "10916321",
      amount: empty ? "0.000000000" : "0.010916321",
      contextSlot: 462_579_557,
    },
    splToken: group(
      "spl-token",
      "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
      462_579_558,
      empty ? [] : [splAccount],
    ),
    token2022: group(
      "token-2022",
      "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",
      462_579_559,
      empty ? [] : [token2022Account],
    ),
    snapshotAtomic: false as const,
  };
}

async function mockSuccess(page: Page, empty = false) {
  await page.route("**/api/portfolio?*", async (route) => {
    const address =
      new URL(route.request().url()).searchParams.get("address") ?? WALLET;
    await route.fulfill({ json: portfolio(address, empty) });
  });
}

test("loads exact SOL, SPL and Token-2022 balances with live provenance", async ({
  page,
}) => {
  const requests: string[] = [];
  await page.route("**/api/portfolio?*", async (route) => {
    requests.push(`${route.request().method()} ${route.request().url()}`);
    await route.fulfill({ json: portfolio() });
  });
  await page.goto("/portfolio");
  await expect(page.getByTestId("portfolio-idle")).toBeVisible();
  await page.getByLabel("Solana public-key address").fill(WALLET);
  await page.getByRole("button", { name: "Load wallet" }).click();
  await expect(page).toHaveURL(new RegExp(`/portfolio\\?address=${WALLET}$`));
  await expect(page.getByTestId("portfolio-result")).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Solana mainnet-beta" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "0.010916321 SOL" }),
  ).toBeVisible();
  await expect(
    page.getByText("9007199254.740993", { exact: true }).first(),
  ).toBeVisible();
  await expect(
    page.getByText("5.000000", { exact: true }).first(),
  ).toBeVisible();
  await expect(page.getByText("462,579,557", { exact: true })).toBeVisible();
  await expect(
    page.getByText("not an atomic account snapshot", { exact: false }),
  ).toBeVisible();
  const requestsBeforeRefresh = requests.length;
  expect(requestsBeforeRefresh).toBeGreaterThanOrEqual(1);
  expect(requests.every((request) => request.startsWith("GET "))).toBe(true);

  await page.getByRole("button", { name: "Refresh live balances" }).click();
  await expect
    .poll(() => requests.length)
    .toBeGreaterThan(requestsBeforeRefresh);
  expect(requests.every((request) => request.startsWith("GET "))).toBe(true);
});

test("preserves address URL history and ignores a stale wallet response", async ({
  page,
}) => {
  await page.route("**/api/portfolio?*", async (route) => {
    const address = new URL(route.request().url()).searchParams.get("address")!;
    if (address === WALLET)
      await new Promise((resolve) => setTimeout(resolve, 250));
    await route.fulfill({ json: portfolio(address) });
  });
  await page.goto(`/portfolio?address=${WALLET}`);
  await page.getByLabel("Solana public-key address").fill(OTHER_WALLET);
  await page.getByRole("button", { name: "Load wallet" }).click();
  await expect(page).toHaveURL(new RegExp(`address=${OTHER_WALLET}$`));
  await expect(page.getByTestId("portfolio-result")).toBeVisible();
  await expect(page.locator(`[title="${OTHER_WALLET}"]`)).toBeVisible();
  await page.goBack();
  await expect(page).toHaveURL(new RegExp(`address=${WALLET}$`));
  await expect(page.getByLabel("Solana public-key address")).toHaveValue(
    WALLET,
  );
  await page.goForward();
  await expect(page).toHaveURL(new RegExp(`address=${OTHER_WALLET}$`));
});

test("shows honest empty, rate-limit and refresh-failure states", async ({
  page,
}) => {
  await mockSuccess(page, true);
  await page.goto(`/portfolio?address=${WALLET}`);
  await expect(
    page.getByRole("heading", { name: "No on-chain holdings returned" }),
  ).toBeVisible();

  await page.unrouteAll({ behavior: "wait" });
  await page.route("**/api/portfolio?*", async (route: Route) => {
    await route.fulfill({
      status: 429,
      json: {
        ok: false,
        error: {
          code: "RPC_RATE_LIMITED",
          message: "The Solana RPC rate limit was reached. Try again later.",
          retryable: true,
        },
      },
    });
  });
  await page.getByRole("button", { name: "Refresh live balances" }).click();
  await expect(
    page.getByRole("heading", { name: "RPC rate limit reached" }),
  ).toBeVisible();
  await expect(
    page.getByText(
      "No cached, historical or synthetic holdings were substituted.",
    ),
  ).toBeVisible();
});

test("reports invalid addresses without rendering example balances", async ({
  page,
}) => {
  await page.route("**/api/portfolio?*", async (route) => {
    await route.fulfill({
      status: 400,
      json: {
        ok: false,
        error: {
          code: "INVALID_ADDRESS",
          message: "Enter a canonical Solana public-key address.",
          retryable: false,
        },
      },
    });
  });
  await page.goto("/portfolio");
  await page.getByLabel("Solana public-key address").fill("not-a-wallet");
  await page.getByRole("button", { name: "Load wallet" }).click();
  await expect(page.locator(".portfolio-error[role=alert]")).toContainText(
    "canonical Solana public-key",
  );
  await expect(page.getByTestId("portfolio-result")).toHaveCount(0);
});

test("remains accessible and contained at every required viewport", async ({
  page,
}) => {
  await mockSuccess(page);
  for (const [width, height] of [
    [320, 640],
    [375, 812],
    [390, 844],
    [768, 1024],
    [1280, 800],
    [1440, 900],
  ] as const) {
    await page.setViewportSize({ width, height });
    await page.goto(`/portfolio?address=${WALLET}`);
    await expect(page.getByTestId("portfolio-result")).toBeVisible();
    const dimensions = await page.evaluate(() => ({
      clientWidth: document.documentElement.clientWidth,
      scrollWidth: document.documentElement.scrollWidth,
    }));
    expect(dimensions.scrollWidth, `${width}x${height}`).toBeLessThanOrEqual(
      dimensions.clientWidth,
    );
    const input = page.getByLabel("Solana public-key address");
    await input.focus();
    await expect(input).toBeFocused();
    const refreshBox = await page
      .getByRole("button", { name: "Refresh live balances" })
      .boundingBox();
    expect(
      refreshBox?.height,
      `${width}px refresh target`,
    ).toBeGreaterThanOrEqual(44);
  }
});

test("performs no external browser request, mutation, signing or wallet action", async ({
  page,
}) => {
  const requests: Array<{ method: string; url: string }> = [];
  page.on("request", (request) =>
    requests.push({ method: request.method(), url: request.url() }),
  );
  await page.addInitScript(() => {
    const state = { discoveryRequests: 0 };
    Object.assign(window, { __portfolioWalletProbe: state });
    window.addEventListener("wallet-standard:app-ready", () => {
      state.discoveryRequests++;
    });
  });
  await mockSuccess(page);
  await page.goto(`/portfolio?address=${WALLET}`);
  await expect(page.getByTestId("portfolio-result")).toBeVisible();
  const assertReadOnlyRequests = () => {
    expect(
      requests.filter(({ url }) => {
        const parsed = new URL(url);
        return parsed.origin !== "http://127.0.0.1:3010";
      }),
    ).toEqual([]);
    expect(
      requests.some(({ method }) =>
        ["POST", "PUT", "PATCH", "DELETE"].includes(method),
      ),
    ).toBe(false);
  };
  assertReadOnlyRequests();
  await expect(
    page.getByText(
      "Only public account data is read. Never enter a private key or seed phrase.",
    ),
  ).toBeVisible();
  const capturedSignIn = page.getByRole("button", {
    name: /connect wallet|sign/i,
  });
  await expect(capturedSignIn).toHaveCount(1);
  await expect(capturedSignIn).toBeEnabled();
  await capturedSignIn.click();
  const chooser = page.getByTestId("auth-dialog");
  await expect(chooser).toBeVisible();
  await expect(chooser).toContainText("sign-in is unavailable");
  for (const provider of ["google", "apple", "github"])
    await expect(page.getByTestId(`auth-${provider}-button`)).toBeDisabled();
  await expect(chooser.locator("input, form, textarea")).toHaveCount(0);
  await expect(page.getByTestId("public-wallet-panel")).toHaveCount(0);
  expect(
    await page.evaluate(
      () =>
        (
          window as unknown as {
            __portfolioWalletProbe: { discoveryRequests: number };
          }
        ).__portfolioWalletProbe.discoveryRequests,
    ),
  ).toBe(0);
  await expect(page.locator("html")).toHaveAttribute("data-pf-auth", "out");
  await chooser.getByRole("button", { name: "Close", exact: true }).click();
  await expect(capturedSignIn).toBeFocused();
  assertReadOnlyRequests();
});
