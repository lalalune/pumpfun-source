import { expect, test } from "@playwright/test";

test("own search normalizes unchanged draft and genuine history restores URL text", async ({ page, context }) => {
  const forbidden: string[] = [];
  await context.route("**/*", (route) => {
    const request = route.request();
    if (new URL(request.url()).origin !== "http://127.0.0.1:3010" || !["GET", "HEAD"].includes(request.method())) {
      forbidden.push(`${request.method()} ${request.url()}`);
      return route.abort();
    }
    return route.continue();
  });
  await page.goto("/go?q=previous", { waitUntil: "networkidle" });
  const input = page.getByRole("searchbox", { name: "Search archived bounties" });
  await expect(input).toHaveValue("previous");
  await input.fill("  Follow  ");
  await input.press("Enter");
  await expect(page).toHaveURL(/\/go\?q=Follow$/);
  await expect(input).toHaveValue("Follow");
  await input.fill("unsent history draft");
  await page.goBack();
  await expect(page).toHaveURL(/\/go\?q=previous$/);
  await expect(input).toHaveValue("previous");
  await page.goForward();
  await expect(input).toHaveValue("Follow");
  await page.reload();
  await expect(input).toHaveValue("Follow");
  expect(forbidden).toEqual([]);
});
