import { expect, test } from "@playwright/test";

// Hold only this local app's client scripts, so the initial HTML remains usable
// for observation without relying on a short or a slow machine's timing.
test("Sign in becomes actionable only when its client chooser can handle the first activation", async ({
  page,
}) => {
  let release!: () => void;
  const clientBoot = new Promise<void>((resolve) => {
    release = resolve;
  });
  const unexpected: string[] = [];
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (
      !["127.0.0.1", "localhost"].includes(url.hostname) ||
      !["GET", "HEAD"].includes(request.method())
    )
      unexpected.push(request.url());
  });
  await page.route("**/_next/static/**/*.js*", async (route) => {
    await clientBoot;
    await route.continue().catch(() => {});
  });
  try {
    await page.goto("/explore", { waitUntil: "commit" });
    const trigger = page.getByTestId("sign-in-button");
    await expect(trigger).toBeVisible();
    await expect(page.getByTestId("auth-dialog")).toHaveCount(0);
    // A server-rendered enabled button cannot open the client-only portal yet.
    await expect(trigger).toBeDisabled();
    release();
    await expect(trigger).toBeEnabled();
    await trigger.click();
    await expect(page.getByTestId("auth-dialog")).toBeVisible();
    await expect(page.getByTestId("auth-dialog")).toHaveAttribute(
      "data-auth-state",
      "ready",
    );
    await expect(
      page.getByRole("button", {
        name: "Connect a public wallet",
        exact: true,
      }),
    ).toBeVisible();
    await expect(page.getByTestId("auth-google-button")).toBeDisabled();
    await expect(page.locator("html")).toHaveAttribute("data-pf-auth", "out");
    expect(unexpected).toEqual([]);
  } finally {
    release();
  }
});
