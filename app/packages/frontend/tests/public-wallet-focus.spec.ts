import { expect, test, type Page } from "@playwright/test";

// Private native-browser probe. Synthetic protocol only; never a real extension.
const origin = "http://127.0.0.1:3010";
const address = "So11111111111111111111111111111111111111112";
type Probe = {
  approve(): void;
  revoke(): void;
  unregister(): void;
  calls: string[];
};
const act = (page: Page, action: "approve" | "revoke" | "unregister") =>
  page.evaluate(
    (action) =>
      (window as unknown as { __focusWallet: Probe }).__focusWallet[action](),
    action,
  );
const focusedInside = (page: Page) =>
  page
    .getByTestId("auth-dialog")
    .evaluate((el) => el.contains(document.activeElement));
async function install(page: Page) {
  await page.addInitScript(
    ({ address }) => {
      let accounts = [{ address, chains: ["solana:mainnet"] }];
      let callback: ((change: unknown) => void) | null = null;
      let unregister = () => {};
      const probe: Probe = {
        calls: [],
        approve() {},
        revoke() {
          accounts = [];
          callback?.({ accounts });
        },
        unregister() {
          unregister();
        },
      };
      const wallet = {
        version: "1.0.0",
        name: "Synthetic Focus Wallet",
        chains: ["solana:mainnet"],
        get accounts() {
          return accounts;
        },
        get icon(): never {
          throw Error("Icons forbidden");
        },
        features: {
          "standard:connect": {
            version: "1.0.0",
            async connect() {
              probe.calls.push("connect");
              await new Promise<void>((resolve) => {
                probe.approve = resolve;
              });
              return { accounts };
            },
          },
          "standard:disconnect": {
            version: "1.0.0",
            async disconnect() {
              probe.calls.push("disconnect");
            },
          },
          "standard:events": {
            version: "1.0.0",
            on(_event: string, handler: typeof callback) {
              callback = handler;
              return () => {
                callback = null;
                probe.calls.push("off");
              };
            },
          },
          get "solana:signIn"(): never {
            throw Error("Authentication forbidden");
          },
          get "solana:signMessage"(): never {
            throw Error("Signing forbidden");
          },
          get "solana:signTransaction"(): never {
            throw Error("Transactions forbidden");
          },
        },
      };
      window.addEventListener("wallet-standard:app-ready", ((
        event: CustomEvent,
      ) => {
        unregister = event.detail.register(wallet);
      }) as EventListener);
      Object.assign(window, { __focusWallet: probe });
    },
    { address },
  );
}

for (const transition of [
  "discover",
  "connect",
  "approve",
  "cancel",
  "disconnect",
  "revoke",
  "unregister",
] as const) {
  test(`public wallet ${transition} keeps keyboard focus within its open dialog`, async ({
    page,
  }) => {
    const blocked: string[] = [],
      errors: string[] = [];
    await page.route("**/*", async (route) => {
      const req = route.request(),
        url = new URL(req.url());
      if (url.origin !== origin || !["GET", "HEAD"].includes(req.method())) {
        blocked.push(`${req.method()} ${url.href}`);
        await route.abort();
      } else await route.continue();
    });
    page.on("pageerror", (error) => errors.push(error.message));
    await install(page);
    await page.goto("/explore");
    await page.getByTestId("sign-in-button").click();
    const discovery = page.getByRole("button", {
      name: "Connect a public wallet",
      exact: true,
    });
    await discovery.focus();
    await discovery.click();
    if (transition !== "discover") {
      const connect = page.getByRole("button", {
        name: "Connect Synthetic Focus Wallet",
        exact: true,
      });
      await connect.focus();
      await connect.click();
      if (transition === "connect") {
        await expect(connect).toBeDisabled();
        await expect(page.getByTestId("public-wallet-panel")).toBeFocused();
        await expect(page.getByTestId("public-wallet-address")).toHaveCount(0);
      } else if (transition === "cancel") {
        const cancel = page.getByRole("button", {
          name: "Cancel connection",
          exact: true,
        });
        await cancel.focus();
        await cancel.click();
      } else {
        await act(page, "approve");
        await expect(page.getByTestId("public-wallet-address")).toHaveText(
          address,
        );
        if (transition !== "approve") {
          const disconnect = page.getByRole("button", {
            name: "Disconnect and forget address",
            exact: true,
          });
          await disconnect.focus();
          if (transition === "disconnect") await disconnect.click();
          else await act(page, transition);
          await expect(page.getByTestId("public-wallet-address")).toHaveCount(
            0,
          );
        }
      }
    }
    await expect.poll(() => focusedInside(page)).toBe(true);
    await expect(page.locator("html")).toHaveAttribute("data-pf-auth", "out");
    expect(errors).toEqual([]);
    expect(blocked).toEqual([]);
    await page
      .getByTestId("auth-dialog")
      .getByRole("button", { name: "Close", exact: true })
      .click();
    if (transition === "cancel" || transition === "connect")
      await act(page, "approve");
  });
}
