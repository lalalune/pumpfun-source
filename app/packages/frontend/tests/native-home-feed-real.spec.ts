import { expect, test, type Page } from "@playwright/test";

function collectBrowserSafety(page: Page) {
  const violations: string[] = [];
  const consoleErrors: string[] = [];
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (
      url.origin !== "http://127.0.0.1:3012" ||
      !["GET", "HEAD"].includes(request.method())
    ) {
      violations.push(`${request.method()} ${request.url()}`);
    }
  });
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  return { violations, consoleErrors };
}

test("renders and pages PR700 ranked callouts through the Next server", async ({
  page,
}) => {
  const safety = collectBrowserSafety(page);
  await page.goto("/");
  await expect(page.getByTestId("local-feed-item")).toHaveCount(6);
  await page.getByRole("tab", { name: "Local callouts" }).click();
  await expect(
    page.getByText("Local Example Alpha", { exact: true }),
  ).toBeVisible();
  await expect(page.getByTestId("native-callout-card")).toHaveCount(3);
  await page.getByRole("link", { name: "Next" }).click();
  await expect(page.getByText("Local page 2", { exact: true })).toBeVisible();
  await expect(page.getByTestId("native-callout-card")).toHaveCount(3);
  await page.getByRole("link", { name: "Next" }).click();
  await expect(page.getByText("Local page 3", { exact: true })).toBeVisible();
  await expect(page.getByTestId("native-callout-card")).toHaveCount(2);
  await expect(
    page.getByText("End of local list", { exact: true }),
  ).toBeVisible();
  expect(safety.violations).toEqual([]);
  expect(safety.consoleErrors).toEqual([]);
});

test("renders PR700 newest callouts and its pinned local count", async ({
  page,
}) => {
  const safety = collectBrowserSafety(page);
  await page.goto("/?tab=local-callouts&nativeView=newest");
  await expect(page.getByTestId("native-callout-card")).toHaveCount(3);
  await expect(page.getByTestId("native-feed-count")).toHaveText(
    "0 newer local callouts relative to this local snapshot.",
  );
  await page.getByRole("link", { name: "Next" }).click();
  await expect(page.getByText("Local page 2", { exact: true })).toBeVisible();
  await expect(page.getByTestId("native-feed-count")).toHaveCount(0);
  expect(safety.violations).toEqual([]);
  expect(safety.consoleErrors).toEqual([]);
});
