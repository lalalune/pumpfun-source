import { expect, test, type Route } from "@playwright/test";

const WALLET = "11111111111111111111111111111111";
const NEXT_WALLET = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA";

test("a delayed wallet clear preserves the next draft and browser history", async ({
  page,
}, testInfo) => {
  // The dedicated runner disables live RPC. This exercises the real local page,
  // router, request handler and form while the endpoint reports unavailable.
  await page.goto(`/portfolio?address=${WALLET}`, { waitUntil: "networkidle" });
  const input = page.getByLabel("Solana public-key address");
  await expect(input).toHaveValue(WALLET);
  const held: Route[] = [];
  let hold = true;
  await page.route("**/portfolio?**", async (route) => {
    const url = new URL(route.request().url());
    if (
      hold &&
      !url.searchParams.has("address") &&
      url.searchParams.has("_rsc")
    )
      held.push(route);
    else await route.continue();
  });
  try {
    await page.getByRole("button", { name: "Clear", exact: true }).click();
    await expect.poll(() => held.length).toBeGreaterThan(0);
    await input.fill(NEXT_WALLET);
    hold = false;
    await Promise.all(held.map((route) => route.continue()));
    await expect(page).toHaveURL(/\/portfolio$/);
    await expect(input).toHaveValue(NEXT_WALLET);
    await page.screenshot({ path: testInfo.outputPath("preserved-draft.png") });
    await input.press("Enter");
    await expect(page).toHaveURL(new RegExp(`address=${NEXT_WALLET}$`));
    await page.goBack();
    await expect(page).toHaveURL(/\/portfolio$/);
    await expect(input).toHaveValue("");
    await page.goBack();
    await expect(page).toHaveURL(new RegExp(`address=${WALLET}$`));
    await expect(input).toHaveValue(WALLET);
  } finally {
    await page.unrouteAll({ behavior: "ignoreErrors" });
  }
});

test("a delayed wallet submission preserves subsequent edits until history navigation", async ({
  page,
}) => {
  await page.goto(`/portfolio?address=${WALLET}`, { waitUntil: "networkidle" });
  const input = page.getByLabel("Solana public-key address");
  const held: Route[] = [];
  let hold = true;
  await page.route("**/portfolio?**", async (route) => {
    const url = new URL(route.request().url());
    if (
      hold &&
      url.searchParams.get("address") === NEXT_WALLET &&
      url.searchParams.has("_rsc")
    )
      held.push(route);
    else await route.continue();
  });
  try {
    await input.fill(NEXT_WALLET);
    await input.press("Enter");
    await expect.poll(() => held.length).toBeGreaterThan(0);
    await input.fill("draft after submission");
    hold = false;
    await Promise.all(held.map((route) => route.continue()));
    await expect(page).toHaveURL(new RegExp(`address=${NEXT_WALLET}$`));
    await expect(input).toHaveValue("draft after submission");
    await page.goBack();
    await expect(input).toHaveValue(WALLET);
    await page.goForward();
    await expect(input).toHaveValue(NEXT_WALLET);
  } finally {
    await page.unrouteAll({ behavior: "ignoreErrors" });
  }
});
