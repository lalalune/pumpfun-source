import { expect, test, type Page } from "@playwright/test";

const symbols = ["RAT", "HEATSTREET", "CIRCLES", "PJAM", "STUCK", "Shibana"];
const firstMint = "7bS1mH6MXbw1GnEkKTU6w5YLTywPkQ1w3YVZXWFupump";

function monitor(page: Page, baseURL: string) {
  const errors: string[] = [];
  page.on("request", (request) => {
    if (
      new URL(request.url()).origin !== new URL(baseURL).origin ||
      !["GET", "HEAD"].includes(request.method())
    )
      errors.push(`${request.method()} ${request.url()}`);
  });
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  return errors;
}

async function ready(page: Page) {
  // Existing closed local-browser fixture, never an inference of original consent.
  await expect(page.locator("[data-clickwrap-overlay]")).toHaveCount(0);
  await expect(page.locator("[data-app-shell]")).not.toHaveAttribute("inert");
}

test("the captured six-record highlight workflow is mounted separately from the 42-card archive", async ({
  page,
  baseURL,
}) => {
  const errors = monitor(page, baseURL!);
  const response = await page.goto("/live");
  expect(response?.status()).toBe(200);
  await expect(
    page.getByText("42 exact archived cards", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Archived highlights", exact: true }),
  ).toBeVisible();
  const choices = page.getByTestId("archived-hero-choice");
  await expect(choices).toHaveCount(6);
  expect(await choices.locator("strong").allTextContents()).toEqual(symbols);
  await expect(choices.first()).toHaveAttribute("aria-current", "true");
  await expect(page.getByTestId("archived-hero-metadata")).toContainText(
    "$RAT - Exfil Rat",
  );
  await expect(page.getByText(/not six additional streams/)).toBeVisible();
  await expect(page.getByTestId("archived-stream-card")).toHaveCount(12);
  await expect(
    page.locator("main video, main audio, main iframe, main img"),
  ).toHaveCount(0);
  await expect(page.locator('main a[href^="/coin/"]')).toHaveCount(0);
  expect(await response!.text()).not.toMatch(
    /clips\.pump\.fun|pump\.mypinata\.cloud|playlistUrl|"marketCap"/u,
  );
  expect(errors).toEqual([]);
});

test("actual next/previous controls wrap the six captured identities without navigation", async ({
  page,
  baseURL,
}) => {
  const errors = monitor(page, baseURL!);
  await page.goto("/live");
  await ready(page);
  const choices = page.getByTestId("archived-hero-choice");
  const metadata = page.getByTestId("archived-hero-metadata");
  for (let index = 1; index <= 6; index += 1) {
    await page
      .getByRole("button", { name: "Next archived highlight", exact: true })
      .click();
    const selected = index % 6;
    await expect(choices.nth(selected)).toHaveAttribute("aria-current", "true");
    await expect(metadata.locator(".archived-hero-symbol")).toHaveText(
      symbols[selected],
    );
    await expect(metadata).toContainText(
      `Archived highlight ${selected + 1} of 6`,
    );
  }
  await page
    .getByRole("button", { name: "Previous archived highlight", exact: true })
    .click();
  await expect(choices.last()).toHaveAttribute("aria-current", "true");
  await expect(metadata.locator(".archived-hero-symbol")).toHaveText("Shibana");
  await expect(page).toHaveURL(/\/live$/u);
  expect(errors).toEqual([]);
});

test("direct selection and native keyboard controls work at mobile and desktop widths", async ({
  page,
  baseURL,
}) => {
  const errors = monitor(page, baseURL!);
  for (const width of [320, 1280]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/live");
    await ready(page);
    const choice = page.getByRole("button", {
      name: "Show archived highlight 4 of 6: PJAM",
      exact: true,
    });
    await choice.focus();
    await expect(choice).toBeFocused();
    await page.keyboard.press("Space");
    await expect(choice).toHaveAttribute("aria-current", "true");
    await expect(choice).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(choice).toHaveAttribute("aria-current", "true");
    const next = page.getByRole("button", {
      name: "Next archived highlight",
      exact: true,
    });
    await next.focus();
    await expect(next).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(
      page.getByRole("button", {
        name: "Show archived highlight 5 of 6: STUCK",
        exact: true,
      }),
    ).toHaveAttribute("aria-current", "true");
    await expect(next).toBeFocused();
    const metrics = await page.evaluate(() => ({
      width: document.documentElement.clientWidth,
      scroll: document.documentElement.scrollWidth,
    }));
    expect(metrics.scroll, `${width}px highlight`).toBeLessThanOrEqual(
      metrics.width,
    );
    await test.info().attach(`hero-${width}.png`, {
      body: await page.screenshot(),
      contentType: "image/png",
    });
    await expect(page).toHaveURL(/\/live$/u);
  }
  expect(errors).toEqual([]);
});

test("highlight state is separate from search, URL selection, Escape and reload", async ({
  page,
  baseURL,
}) => {
  const errors = monitor(page, baseURL!);
  await page.goto("/live");
  await ready(page);
  const choices = page.getByTestId("archived-hero-choice");
  const search = page.getByRole("searchbox", {
    name: "Search captured streams",
  });
  await search.fill("$mAjor");
  await search.press("Enter");
  await expect(page).toHaveURL(/\/live\?q=%24mAjor$/u);
  await choices.nth(4).click();
  await expect(choices.nth(4)).toHaveAttribute("aria-current", "true");
  await expect(page).toHaveURL(/\/live\?q=%24mAjor$/u);
  await expect(page.getByTestId("archived-stream-card")).toHaveCount(1);
  await page.reload();
  await expect(choices.first()).toHaveAttribute("aria-current", "true");
  await ready(page);
  await page.getByRole("button", { name: "Clear", exact: true }).click();
  await expect(page).toHaveURL(/\/live$/u);
  await page
    .getByRole("button", { name: "Inspect archived stream M $M", exact: true })
    .click();
  await expect(page).toHaveURL(new RegExp(`stream=${firstMint}$`));
  await expect(page.getByTestId("playback-unavailable")).toBeVisible();
  await choices.nth(4).click();
  await expect(
    page
      .getByTestId("playback-unavailable")
      .getByRole("heading", { name: "M", exact: true }),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page).toHaveURL(/\/live$/u);
  await expect(choices.nth(4)).toHaveAttribute("aria-current", "true");
  await expect(page.getByTestId("playback-unavailable")).toHaveCount(0);
  expect(errors).toEqual([]);
});
