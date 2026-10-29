import { writeFile } from "node:fs/promises";
import { expect, test } from "@playwright/test";

test("GO local created dates hydrate across server and browser timezones", async ({
  page,
  context,
}, testInfo) => {
  const forbidden: string[] = [];
  const errors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  page.on("pageerror", (error) => errors.push(error.message));
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
  const response = await page.goto("/go", { waitUntil: "networkidle" });
  expect(response?.status()).toBe(200);
  const html = await response!.text();
  const server = await page.evaluate((source) => {
    const document = new DOMParser().parseFromString(source, "text/html");
    const element = document.querySelector('[data-testid="go-bounty-card"] time');
    return { datetime: element?.getAttribute("datetime"), label: element?.textContent };
  }, html);
  const first = page.getByTestId("go-bounty-card").first().locator("time").first();
  await expect(first).toHaveAttribute("datetime", server.datetime!);
  const expected = await first.evaluate((element) =>
    new Date(element.getAttribute("datetime")!).toLocaleDateString("en-US"),
  );
  await expect(first).toHaveText(expected);
  const observed = {
    server,
    client: { timezone: await page.evaluate(() => Intl.DateTimeFormat().resolvedOptions().timeZone), label: await first.textContent(), expected },
    errors,
    forbidden,
  };
  await writeFile(testInfo.outputPath("actual-date-hydration.json"), JSON.stringify(observed, null, 2));
  await page.screenshot({ path: testInfo.outputPath("created-dates.png"), fullPage: true });
  expect(errors.filter((message) => /hydration failed/i.test(message))).toEqual([]);
  expect(forbidden).toEqual([]);
});
