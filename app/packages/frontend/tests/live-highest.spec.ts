import { expect, test, type Page } from "@playwright/test";

const symbols = [
  "RAT",
  "HEATSTREET",
  "CIRCLES",
  "PJAM",
  "STUCK",
  "Shibana",
  "$J",
  "popcoin",
  "$R",
  "$O",
  "$mAjor",
  "$M",
  "NTRNDM",
  "PEPONK",
  "Wifoween",
  "YEET",
  "AUDACITY",
  "ASGARD",
  "CLAUDIA",
  "KATTBATT",
  "PillCrew",
  "CHERRY",
  "HOLD",
  "SPROUT",
];

function monitor(page: Page, baseURL: string) {
  const errors: string[] = [];
  page.on("request", (request) => {
    if (
      new URL(request.url()).origin !== new URL(baseURL).origin ||
      !["GET", "HEAD"].includes(request.method())
    ) {
      errors.push(`${request.method()} ${request.url()}`);
    }
  });
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  return errors;
}

test("the observed section route exposes all 24 cards in captured order and no playback", async ({
  page,
  baseURL,
}) => {
  const errors = monitor(page, baseURL!);
  const response = await page.goto("/live/highest-market-cap");
  expect(response?.status()).toBe(200);
  await expect(
    page.getByRole("heading", { level: 1, name: "Highest market cap" }),
  ).toBeVisible();
  const cards = page.getByTestId("highest-archived-card");
  await expect(cards).toHaveCount(24);
  expect(await cards.locator(".live-symbol").allTextContents()).toEqual(
    symbols,
  );
  await expect(
    page.getByText("24 exact archived cards", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("No current live status", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText(/They are not 24 additional streams/),
  ).toBeVisible();
  await expect(
    page.locator("main video, main audio, main iframe, main img"),
  ).toHaveCount(0);
  await expect(page.locator('main a[href^="/coin/"]')).toHaveCount(0);
  const html = await response!.text();
  expect(html).not.toMatch(
    /clips\.pump\.fun|pump\.mypinata\.cloud|playlistUrl|"marketCap"/u,
  );
  expect(errors).toEqual([]);
});

test("archived metadata has native keyboard disclosures at mobile and desktop widths", async ({
  page,
  baseURL,
}) => {
  const errors = monitor(page, baseURL!);
  for (const width of [320, 1280]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/live/highest-market-cap");
    const card = page.getByTestId("highest-archived-card").first();
    const summary = card.locator("summary");
    const details = card.locator("details");
    await expect(details).not.toHaveAttribute("open");
    await summary.focus();
    await page.keyboard.press("Enter");
    await expect(details).toHaveAttribute("open", "");
    await expect(summary).toBeFocused();
    await expect(
      card.getByText("GNpsFpSV82H16kmUvLF2hNn2trkPFsyWLqfJq5TSNiHN", {
        exact: true,
      }),
    ).toBeVisible();
    await expect(
      card.getByText("9FAjujeZsLW7C8jRLvcH1fS3dYCtLV6LYHKq822dpump", {
        exact: true,
      }),
    ).toBeVisible();
    const size = await page.evaluate(() => ({
      width: document.documentElement.clientWidth,
      scroll: document.documentElement.scrollWidth,
    }));
    expect(size.scroll, `${width}px open metadata`).toBeLessThanOrEqual(
      size.width,
    );
    await test.info().attach(`highest-${width}.png`, {
      body: await page.screenshot(),
      contentType: "image/png",
    });
    await page.keyboard.press("Space");
    await expect(details).not.toHaveAttribute("open");
    await page.reload();
    await expect(details).not.toHaveAttribute("open");
  }
  expect(errors).toEqual([]);
});

test("the sibling link and browser history preserve the separate Most viewers archive", async ({
  page,
  baseURL,
}) => {
  const errors = monitor(page, baseURL!);
  await page.goto("/live");
  await expect(page.getByTestId("archived-stream-card")).toHaveCount(12);
  await expect(
    page.getByText("42 exact archived cards", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("link", {
      name: "Highest market cap — 24 archived cards",
      exact: true,
    })
    .click();
  await expect(page).toHaveURL(/\/live\/highest-market-cap$/u);
  await expect(page.getByTestId("highest-archived-card")).toHaveCount(24);
  await page
    .getByRole("link", { name: "Return to captured Most viewers", exact: true })
    .click();
  await expect(page).toHaveURL(/\/live$/u);
  await expect(
    page.getByRole("tab", { name: "Most viewers", exact: true }),
  ).toHaveAttribute("aria-selected", "true");
  await page.getByRole("tab", { name: "Other sections", exact: true }).click();
  await expect(page.getByTestId("other-sections-unavailable")).toBeVisible();
  await page.goBack();
  await expect(page.getByTestId("archived-stream-card")).toHaveCount(12);
  expect(errors).toEqual([]);
});
