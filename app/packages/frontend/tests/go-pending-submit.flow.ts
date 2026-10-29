import { writeFile } from "node:fs/promises";
import { expect, test, type Route } from "@playwright/test";

for (const width of [1280, 375]) {
  test(`GO submitted search preserves the next unsent draft at ${width}px`, async ({
    page,
    context,
  }, testInfo) => {
    const forbidden: string[] = [];
    await context.route("**/*", (route) => {
      const request = route.request();
      if (
        new URL(request.url()).origin !== "http://127.0.0.1:3010" ||
        !["GET", "HEAD"].includes(request.method())
      ) {
        forbidden.push(`${request.method()} ${request.url()}`);
        return route.abort();
      }
      return route.continue();
    });
    await page.setViewportSize({ width, height: 850 });
    expect((await page.goto("/go", { waitUntil: "networkidle" }))?.status()).toBe(200);
    await expect(page.getByText("Authenticated local snapshot", { exact: true })).toBeVisible();
    const input = page.getByRole("searchbox", { name: "Search archived bounties" });
    const held: Route[] = [];
    let hold = true;
    await page.route("**/go?**", (route) => {
      const request = route.request(), url = new URL(request.url());
      if (url.origin !== "http://127.0.0.1:3010" || request.method() !== "GET")
        return route.abort();
      if (hold && url.searchParams.has("_rsc") && url.searchParams.get("q") === "Follow") {
        held.push(route);
        return;
      }
      return route.continue();
    });
    try {
      await input.fill("  Follow  ");
      await input.press("Enter");
      await expect.poll(() => held.length).toBe(1);
      await input.fill("next archive draft");
      await expect(input).toHaveValue("next archive draft");
      const pending = { url: page.url(), draft: await input.inputValue(), held: held.length };
      const apiResponse = page.waitForResponse((response) => {
        const url = new URL(response.url());
        return url.pathname === "/api/go-bounties" && url.searchParams.get("q") === "Follow";
      });
      hold = false;
      await Promise.all(held.map((route) => route.continue()));
      await expect(page).toHaveURL(/\/go\?q=Follow$/);
      const actual = await apiResponse;
      expect(actual.status()).toBe(200);
      // Observe after the actual archive read settles; no payload is replaced.
      await expect(page.locator(".go-workspace")).not.toHaveAttribute("aria-busy", "true");
      const after = { url: page.url(), draft: await input.inputValue(), archiveStatus: actual.status() };
      await writeFile(testInfo.outputPath("actual-draft-commit.json"), JSON.stringify({ width, pending, after, forbidden }, null, 2));
      await page.screenshot({ path: testInfo.outputPath("after-commit.png"), fullPage: true });
      expect(forbidden).toEqual([]);
      await expect(input).toHaveValue("next archive draft");
    } finally {
      await page.unrouteAll({ behavior: "ignoreErrors" });
    }
  });
}
