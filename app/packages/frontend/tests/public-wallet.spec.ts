import { expect, test, type Page } from "@playwright/test";
const ADDRESS = "So11111111111111111111111111111111111111112";
const OTHER_ADDRESS = "11111111111111111111111111111111";

type Probe = {
  calls: string[];
  reads: number;
  resolve(): void;
  reject(): void;
  change(address: string | null): void;
  unregister(): void;
};
async function installWallet(
  page: Page,
  mode: "success" | "pending" | "reject" | "without-disconnect" = "success",
) {
  await page.addInitScript(
    ({ address, mode }) => {
      let accounts = [{ address, chains: ["solana:mainnet"] }];
      let change: ((value: unknown) => void) | null = null;
      let unregister = () => {};
      const probe = {
        calls: [] as string[],
        reads: 0,
        resolve: () => {},
        reject: () => {},
        change(address: string | null) {
          accounts = address ? [{ address, chains: ["solana:mainnet"] }] : [];
          change?.({ accounts });
        },
        unregister: () => unregister(),
      };
      const wallet = {
        version: "1.0.0",
        name: "Browser Protocol Wallet",
        chains: ["solana:mainnet"],
        get accounts() {
          probe.reads++;
          return accounts;
        },
        get icon() {
          throw new Error("Wallet icon should not be read");
        },
        features: {
          "standard:connect": {
            version: "1.0.0",
            async connect(...args: unknown[]) {
              probe.calls.push(`connect:${args.length}`);
              if (mode === "reject")
                throw new Error("private-provider-payload");
              if (mode === "pending")
                await new Promise<void>((resolve, reject) => {
                  probe.resolve = resolve;
                  probe.reject = () =>
                    reject(new Error("private-provider-payload"));
                });
              return { accounts };
            },
          },
          "standard:events": {
            version: "1.0.0",
            on(event: string, callback: typeof change) {
              probe.calls.push(`on:${event}`);
              change = callback;
              return () => {
                probe.calls.push("off");
                change = null;
              };
            },
          },
          "standard:disconnect": {
            version: "1.0.0",
            async disconnect() {
              probe.calls.push("disconnect");
            },
          },
          get "solana:signMessage"() {
            throw new Error("Signing is forbidden");
          },
          get "solana:signTransaction"() {
            throw new Error("Signing is forbidden");
          },
          get "solana:signIn"() {
            throw new Error("Sign-in is forbidden");
          },
        },
      };
      if (mode === "without-disconnect")
        Reflect.deleteProperty(wallet.features, "standard:disconnect");
      window.addEventListener("wallet-standard:app-ready", ((
        event: CustomEvent,
      ) => {
        unregister = event.detail.register(wallet);
      }) as EventListener);
      Object.assign(window, { __publicWalletProbe: probe });
    },
    { address: ADDRESS, mode },
  );
}
const probe = (page: Page) =>
  page.evaluate(() => {
    const p = (window as unknown as { __publicWalletProbe: Probe })
      .__publicWalletProbe;
    return { calls: p.calls, reads: p.reads };
  });
const mutate = (page: Page, action: "resolve" | "unregister") =>
  page.evaluate((action) => {
    (window as unknown as { __publicWalletProbe: Probe }).__publicWalletProbe[
      action
    ]();
  }, action);
async function open(page: Page) {
  await page.goto("/explore");
  // The trigger is server-rendered; the portal confirms its client effect mounted.
  await expect(page.getByTestId("auth-dialog")).toBeAttached();
  await page.getByTestId("sign-in-button").click();
  await page
    .getByRole("button", { name: "Connect a public wallet", exact: true })
    .click();
}

async function connectPublicAddress(page: Page) {
  await installWallet(page);
  await open(page);
  await page
    .getByRole("button", {
      name: "Connect Browser Protocol Wallet",
      exact: true,
    })
    .click();
  await expect(page.getByTestId("public-wallet-address")).toHaveText(ADDRESS);
}

function publicOverview(address = ADDRESS) {
  const programId = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA";
  const accounts = ["3000000", "4000000"].map((rawAmount, index) => ({
    tokenAccount: index
      ? "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"
      : OTHER_ADDRESS,
    mint: ADDRESS,
    owner: address,
    program: "spl-token",
    programId,
    rawAmount,
    decimals: 6,
    amount: index ? "4.000000" : "3.000000",
    state: "initialized",
    isNative: false,
    extensions: [],
  }));
  return {
    ok: true,
    address,
    cluster: "mainnet-beta",
    genesisHash: "5eykt4UsFv8P8NJdTREpY1vzqKqZKvdpKuc147dw2N9d",
    commitment: "confirmed",
    observedAt: "2026-10-29T14:00:00.000Z",
    endpointHost: "public-rpc.example",
    snapshotAtomic: false,
    sol: {
      lamports: "9007199254740993",
      amount: "9007199.254740993",
      contextSlot: 321,
    },
    splToken: {
      program: "spl-token",
      programId,
      contextSlot: 322,
      accounts,
      mints: [
        {
          mint: ADDRESS,
          program: "spl-token",
          programId,
          rawAmount: "7000000",
          amount: "7.000000",
          decimals: 6,
          accountCount: 2,
        },
      ],
    },
    token2022: {
      program: "token-2022",
      programId: "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",
      contextSlot: 323,
      accounts: [],
      mints: [],
    },
  };
}

const readOverview = (page: Page) =>
  page.getByRole("button", {
    name: "Read public mainnet overview",
    exact: true,
  });

test("connected public address reads mainnet only on explicit request without credentials or authentication", async ({
  page,
  context,
}) => {
  await context.addCookies([
    {
      name: "private_test_session",
      value: "not-forwarded",
      domain: "127.0.0.1",
      path: "/",
    },
  ]);
  const requests: {
    address: string | null;
    method: string;
    cookie: string | undefined;
  }[] = [];
  await page.route("**/api/portfolio?*", async (route) => {
    requests.push({
      address: new URL(route.request().url()).searchParams.get("address"),
      method: route.request().method(),
      cookie: route.request().headers().cookie,
    });
    await route.fulfill({ json: publicOverview() });
  });
  await connectPublicAddress(page);
  expect(requests).toEqual([]);
  await readOverview(page).click();
  const result = page.getByTestId("public-wallet-balance-result");
  await expect(result).toContainText("9007199.254740993 SOL");
  await expect(result).toContainText("2 accounts · 1 mint");
  await expect(result).toContainText("0 accounts · 0 mints");
  await expect(result).toContainText("SOL 321, SPL 322, Token-2022 323");
  await expect(result).toContainText("public-rpc.example");
  await expect(result).toContainText("not an atomic snapshot");
  await expect(result).toContainText("do not establish ownership");
  expect(requests).toEqual([
    { address: ADDRESS, method: "GET", cookie: undefined },
  ]);
  expect((await probe(page)).calls).toEqual(["connect:0", "on:change"]);
  await expect(page.locator("html")).toHaveAttribute("data-pf-auth", "out");
  await expect(page.getByTestId("auth-google-button")).toBeDisabled();
});

test("public overview refresh removes prior data on failure and can recover from rate limiting", async ({
  page,
}) => {
  let count = 0;
  await page.route("**/api/portfolio?*", (route) => {
    count++;
    return route.fulfill(
      count === 2
        ? {
            status: 429,
            json: {
              ok: false,
              error: {
                code: "RPC_RATE_LIMITED",
                retryable: true,
                message: "private-provider-body",
              },
            },
          }
        : { json: publicOverview() },
    );
  });
  await connectPublicAddress(page);
  await readOverview(page).click();
  await expect(page.getByTestId("public-wallet-balance-result")).toBeVisible();
  await page
    .getByRole("button", {
      name: "Refresh public mainnet overview",
      exact: true,
    })
    .click();
  await expect(
    page.getByTestId("public-wallet-balance-overview").getByRole("alert"),
  ).toContainText("rate limited");
  await expect(page.getByTestId("public-wallet-balance-result")).toHaveCount(0);
  await expect(page.getByTestId("public-wallet-panel")).not.toContainText(
    "private-provider-body",
  );
  await expect(page.getByTestId("public-wallet-address")).toHaveText(ADDRESS);
  await readOverview(page).click();
  await expect(page.getByTestId("public-wallet-balance-result")).toBeVisible();
  expect(count).toBe(3);
});

test("public overview rejects a response belonging to another address", async ({
  page,
}) => {
  await page.route("**/api/portfolio?*", (route) =>
    route.fulfill({ json: publicOverview(OTHER_ADDRESS) }),
  );
  await connectPublicAddress(page);
  await readOverview(page).click();
  await expect(
    page.getByTestId("public-wallet-balance-overview").getByRole("alert"),
  ).toContainText("unavailable");
  await expect(page.getByTestId("public-wallet-balance-result")).toHaveCount(0);
});

test("an account change aborts the old overview and requires another explicit read", async ({
  page,
}) => {
  let release!: () => void, started!: () => void;
  const gate = new Promise<void>((resolve) => {
      release = resolve;
    }),
    pending = new Promise<void>((resolve) => {
      started = resolve;
    });
  const addresses: string[] = [];
  await page.route("**/api/portfolio?*", async (route) => {
    const address = new URL(route.request().url()).searchParams.get("address")!;
    addresses.push(address);
    if (address === ADDRESS) {
      started();
      await gate;
    }
    await route.fulfill({ json: publicOverview(address) }).catch(() => {});
  });
  await connectPublicAddress(page);
  await readOverview(page).click();
  await pending;
  await page.evaluate(
    (address) =>
      (
        window as unknown as { __publicWalletProbe: Probe }
      ).__publicWalletProbe.change(address),
    OTHER_ADDRESS,
  );
  await expect(page.getByTestId("public-wallet-address")).toHaveText(
    OTHER_ADDRESS,
  );
  await expect(readOverview(page)).toBeEnabled();
  release();
  await expect(page.getByTestId("public-wallet-balance-result")).toHaveCount(0);
  expect(addresses).toEqual([ADDRESS]);
  await readOverview(page).click();
  await expect(page.getByTestId("public-wallet-balance-result")).toBeVisible();
  expect(addresses).toEqual([ADDRESS, OTHER_ADDRESS]);
});

test("disconnect discards the pending public read", async ({ page }) => {
  let release!: () => void, started!: () => void;
  const pending = new Promise<void>((resolve) => {
      started = resolve;
    }),
    gate = new Promise<void>((resolve) => {
      release = resolve;
    });
  await page.route("**/api/portfolio?*", async (route) => {
    started();
    await gate;
    await route.fulfill({ json: publicOverview() }).catch(() => {});
  });
  await connectPublicAddress(page);
  await readOverview(page).click();
  await pending;
  await page
    .getByRole("button", { name: "Disconnect and forget address", exact: true })
    .click();
  release();
  await expect(page.getByTestId("public-wallet-balance-overview")).toHaveCount(
    0,
  );
  await page
    .getByTestId("auth-dialog")
    .getByRole("button", { name: "Close", exact: true })
    .click();
  await page.getByTestId("sign-in-button").click();
  await expect(page.getByTestId("public-wallet-address")).toHaveCount(0);
  await expect(page.getByTestId("public-wallet-balance-result")).toHaveCount(0);
});

test("closing a connected dialog discards a late public balance response", async ({
  page,
}) => {
  let release!: () => void, started!: () => void;
  const pending = new Promise<void>((resolve) => {
      started = resolve;
    }),
    gate = new Promise<void>((resolve) => {
      release = resolve;
    });
  await page.route("**/api/portfolio?*", async (route) => {
    started();
    await gate;
    await route.fulfill({ json: publicOverview() }).catch(() => {});
  });
  await connectPublicAddress(page);
  await readOverview(page).click();
  await pending;
  await page
    .getByTestId("auth-dialog")
    .getByRole("button", { name: "Close", exact: true })
    .click();
  release();
  await page.getByTestId("sign-in-button").click();
  await expect(page.getByTestId("public-wallet-address")).toHaveCount(0);
  await expect(page.getByTestId("public-wallet-balance-result")).toHaveCount(0);
});

test("a finite public overview deadline clears the spinner without losing disconnect control", async ({
  page,
}) => {
  await page.clock.install();
  let release!: () => void, started!: () => void;
  const pending = new Promise<void>((resolve) => {
      started = resolve;
    }),
    gate = new Promise<void>((resolve) => {
      release = resolve;
    });
  await page.route("**/api/portfolio?*", async (route) => {
    started();
    await gate;
    await route.fulfill({ json: publicOverview() }).catch(() => {});
  });
  await connectPublicAddress(page);
  await readOverview(page).click();
  await pending;
  await page.clock.fastForward(20_001);
  await expect(
    page.getByTestId("public-wallet-balance-overview").getByRole("alert"),
  ).toContainText("timed out");
  await expect(readOverview(page)).toBeEnabled();
  await expect(
    page.getByRole("button", {
      name: "Disconnect and forget address",
      exact: true,
    }),
  ).toBeEnabled();
  release();
  await expect(page.getByTestId("public-wallet-balance-result")).toHaveCount(0);
});

for (const width of [320, 1440])
  test(`connected public overview fits ${width}px without exposing signing or private auth`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: width === 320 ? 640 : 900 });
    await page.route("**/api/portfolio?*", (route) =>
      route.fulfill({ json: publicOverview() }),
    );
    await connectPublicAddress(page);
    await readOverview(page).click();
    const result = page.getByTestId("public-wallet-balance-result");
    await expect(result).toBeVisible();
    await result.scrollIntoViewIfNeeded();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    const box = await page.getByTestId("auth-dialog").boundingBox();
    expect(box).not.toBeNull();
    expect(box!.x).toBeGreaterThanOrEqual(0);
    expect(box!.width).toBeLessThanOrEqual(width);
    await page.screenshot({
      path: `../../artifacts/public-wallet-overview-${width}.png`,
    });
    await page.keyboard.press("Escape");
    await expect(page.getByTestId("auth-dialog")).not.toBeVisible();
    await page.getByTestId("sign-in-button").click();
    await expect(page.getByTestId("public-wallet-balance-result")).toHaveCount(
      0,
    );
  });

test("opt-in public connection, change and disconnect preserve auth/privacy boundary", async ({
  page,
}) => {
  const unexpected: string[] = [],
    errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (
      !["127.0.0.1", "localhost"].includes(url.hostname) ||
      !["GET", "HEAD"].includes(request.method()) ||
      /\/auth\/|\/privy|wallet.*challenge/i.test(url.pathname)
    )
      unexpected.push(request.url());
  });
  await installWallet(page);
  await page.goto("/explore");
  const storage = await page.evaluate(() => ({
    local: { ...localStorage },
    session: { ...sessionStorage },
    cookies: document.cookie,
  }));
  await page.getByTestId("sign-in-button").click();
  expect(await probe(page)).toEqual({ calls: [], reads: 0 });
  await page
    .getByRole("button", { name: "Connect a public wallet", exact: true })
    .click();
  expect(await probe(page)).toEqual({ calls: [], reads: 0 });
  await page
    .getByRole("button", {
      name: "Connect Browser Protocol Wallet",
      exact: true,
    })
    .click();
  await expect(page.getByTestId("public-wallet-address")).toHaveText(ADDRESS);
  await expect(page.getByTestId("public-wallet-panel")).toContainText(
    "ownership unverified",
  );
  await expect(page.getByTestId("auth-google-button")).toBeDisabled();
  await expect(page.locator("html")).toHaveAttribute("data-pf-auth", "out");
  await page.evaluate(() =>
    (
      window as unknown as { __publicWalletProbe: Probe }
    ).__publicWalletProbe.change("11111111111111111111111111111111"),
  );
  await expect(page.getByTestId("public-wallet-address")).toHaveText(
    "11111111111111111111111111111111",
  );
  await page
    .getByRole("button", { name: "Disconnect and forget address" })
    .click();
  await expect(page.getByTestId("public-wallet-address")).toHaveCount(0);
  expect((await probe(page)).calls).toEqual([
    "connect:0",
    "on:change",
    "off",
    "disconnect",
  ]);
  expect(
    await page.evaluate(() => ({
      local: { ...localStorage },
      session: { ...sessionStorage },
      cookies: document.cookie,
    })),
  ).toEqual(storage);
  expect(unexpected).toEqual([]);
  expect(errors).toEqual([]);
});

test("declined wallet prompt shows no provider payload", async ({ page }) => {
  await installWallet(page, "reject");
  await open(page);
  await page
    .getByRole("button", {
      name: "Connect Browser Protocol Wallet",
      exact: true,
    })
    .click();
  await expect(
    page.getByTestId("public-wallet-panel").getByRole("alert"),
  ).toContainText("Unable to connect");
  await expect(page.getByTestId("public-wallet-panel")).not.toContainText(
    "private-provider-payload",
  );
  expect((await probe(page)).reads).toBe(0);
});

test("closing the dialog forgets connected address and rejects late pending approval", async ({
  page,
}) => {
  await installWallet(page, "pending");
  await open(page);
  await page
    .getByRole("button", {
      name: "Connect Browser Protocol Wallet",
      exact: true,
    })
    .click();
  await page
    .getByTestId("auth-dialog")
    .getByRole("button", { name: "Close", exact: true })
    .click();
  await mutate(page, "resolve");
  await page.getByTestId("sign-in-button").click();
  await expect(page.getByTestId("public-wallet-address")).toHaveCount(0);
  expect((await probe(page)).reads).toBe(0);
});

for (const width of [320, 1440])
  test(`public wallet chooser fits ${width}px and cleans up on revocation`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: width === 320 ? 640 : 900 });
    await installWallet(page);
    await open(page);
    await page
      .getByRole("button", {
        name: "Connect Browser Protocol Wallet",
        exact: true,
      })
      .click();
    await expect(page.getByTestId("public-wallet-address")).toHaveText(ADDRESS);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    const panel = page.getByTestId("public-wallet-panel");
    await panel.scrollIntoViewIfNeeded();
    await page.screenshot({
      path: `../../artifacts/public-wallet-${width}.png`,
    });
    await mutate(page, "unregister");
    await expect(page.getByTestId("public-wallet-address")).toHaveCount(0);
    await expect(panel).toContainText("Wallet is no longer available");
  });

test("wallet without disconnect support forgets locally and discloses remaining wallet authorization", async ({
  page,
}) => {
  await installWallet(page, "without-disconnect");
  await open(page);
  await page
    .getByRole("button", {
      name: "Connect Browser Protocol Wallet",
      exact: true,
    })
    .click();
  await expect(page.getByTestId("public-wallet-address")).toHaveText(ADDRESS);
  await page
    .getByRole("button", { name: "Disconnect and forget address" })
    .click();
  await expect(page.getByTestId("public-wallet-address")).toHaveCount(0);
  await expect(
    page.getByTestId("public-wallet-panel").getByRole("alert"),
  ).toContainText("wallet connection may remain active");
  expect((await probe(page)).calls).toEqual(["connect:0", "on:change", "off"]);
});
