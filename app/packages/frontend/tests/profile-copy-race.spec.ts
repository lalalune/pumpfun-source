import { expect, test } from "@playwright/test";

test("profile clipboard feedback follows the newest request and does not return after navigation", async ({
  page,
}) => {
  const unexpectedRequests: string[] = [];
  await page.route("**/*", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    if (
      url.origin !== "http://127.0.0.1:3010" ||
      !["GET", "HEAD"].includes(request.method())
    ) {
      unexpectedRequests.push(`${request.method()} ${request.url()}`);
      await route.abort();
      return;
    }
    await route.continue();
  });
  await page.addInitScript(() => {
    const pending: { resolve: () => void; reject: (error: Error) => void }[] =
      [];
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: {
        writeText: () =>
          new Promise<void>((resolve, reject) =>
            pending.push({ resolve, reject }),
          ),
      },
    });
    Object.assign(window, {
      settleProfileCopy: (index: number, ok: boolean) => {
        if (ok) pending[index].resolve();
        else pending[index].reject(new Error("Synthetic clipboard denial"));
      },
    });
  });
  await page.goto("/profile/user-001");
  const copy = page.getByRole("button", { name: "Copy wallet address" });
  const status = page.locator(".profile-copy-control [aria-live]");
  await copy.click();
  await copy.click();
  await page.evaluate(() =>
    (
      window as unknown as {
        settleProfileCopy: (i: number, ok: boolean) => void;
      }
    ).settleProfileCopy(1, true),
  );
  await expect(status).toHaveText("Wallet address copied");
  await page.evaluate(() =>
    (
      window as unknown as {
        settleProfileCopy: (i: number, ok: boolean) => void;
      }
    ).settleProfileCopy(0, false),
  );
  await expect(status).toHaveText("Wallet address copied");
  await copy.click();
  await expect(status).toHaveText("");
  await page.locator('a[href="/"]').first().click();
  await expect(page).toHaveURL("/");
  await page.evaluate(() =>
    (
      window as unknown as {
        settleProfileCopy: (i: number, ok: boolean) => void;
      }
    ).settleProfileCopy(2, true),
  );
  await expect(
    page.getByText("Wallet address copied", { exact: true }),
  ).toHaveCount(0);
  expect(unexpectedRequests).toEqual([]);
});
