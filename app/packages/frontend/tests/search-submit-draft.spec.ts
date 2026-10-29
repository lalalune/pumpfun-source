import { writeFile } from "node:fs/promises";
import { expect, test, type Page, type Route } from "@playwright/test";
import { openShellSearch } from "./shell-controls";

async function save(page: Page, observations: unknown) {
  await writeFile(
    test.info().outputPath("draft-observations.json"),
    JSON.stringify(
      {
        state: await page.evaluate(() => ({
          url: location.href,
          query:
            document.querySelector<HTMLInputElement>("#global-search")?.value,
          open: document.querySelector<HTMLDialogElement>(
            'dialog[aria-label="Search for coins and users"]',
          )?.open,
        })),
        observations,
      },
      null,
      2,
    ),
  );
  await page.screenshot({ path: test.info().outputPath("draft.png") });
}

async function prepare(page: Page) {
  const errors: string[] = [];
  const navigations: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  page.on("framenavigated", (frame) => {
    if (frame === page.mainFrame()) navigations.push(frame.url());
  });
  await page.goto("/explore?q=previous", { waitUntil: "networkidle" });
  const input = await openShellSearch(page);
  await expect(input).toHaveValue("previous");
  return { input, errors, navigations };
}

test("normal search submit follows its normalized committed query", async ({
  page,
}) => {
  const { input, errors, navigations } = await prepare(page);
  try {
    await input.fill("  submitted  ");
    await input.press("Enter");
    await expect(page).toHaveURL(/\/explore\?q=submitted$/);
    await openShellSearch(page);
    await expect(input).toHaveValue("submitted");
    expect(errors).toEqual([]);
  } finally {
    await save(page, { errors, navigations });
  }
});

for (const edit of [true, false]) {
  test(`pending submit ${edit ? "retains a newer reopened draft" : "still follows its URL without a new edit"}`, async ({
    page,
  }) => {
    const { input, errors, navigations } = await prepare(page);
    const dialog = page.getByRole("dialog", {
      name: "Search for coins and users",
    });
    const held: Route[] = [];
    let holding = true;
    const observations: unknown[] = [];
    page.on("response", (response) => {
      const url = new URL(response.url());
      if (
        url.searchParams.has("_rsc") &&
        url.searchParams.get("q") === "submitted"
      )
        observations.push({
          stage: "actual-rsc-response",
          url: url.href,
          status: response.status(),
          contentType: response.headers()["content-type"],
        });
    });
    await page.route("**/explore?**", async (route) => {
      const url = new URL(route.request().url());
      if (
        holding &&
        url.searchParams.has("_rsc") &&
        url.searchParams.get("q") === "submitted"
      ) {
        held.push(route);
        observations.push({ stage: "held-actual-rsc", url: url.href });
      } else await route.continue();
    });
    try {
      await input.fill("  submitted  ");
      await input.press("Enter");
      await expect(dialog).not.toBeVisible();
      await expect.poll(() => held.length).toBe(1);
      await openShellSearch(page);
      if (edit) await input.fill("new draft");
      observations.push({
        stage: "before-release",
        query: await input.inputValue(),
        url: page.url(),
      });
      holding = false;
      await Promise.all(held.map((route) => route.continue()));
      await expect(page).toHaveURL(/\/explore\?q=submitted$/);
      observations.push({
        stage: "after-commit",
        query: await input.inputValue(),
        url: page.url(),
      });
      await expect(input).toHaveValue(edit ? "new draft" : "submitted");
      await expect(dialog).toBeVisible();
      await page.goBack();
      await expect(page).toHaveURL(/\/explore\?q=previous$/);
      await expect(input).toHaveValue("previous");
      await page.goForward();
      await expect(page).toHaveURL(/\/explore\?q=submitted$/);
      await expect(input).toHaveValue("submitted");
      expect(errors).toEqual([]);
    } finally {
      holding = false;
      await page.unrouteAll({ behavior: "ignoreErrors" });
      await save(page, { errors, navigations, observations });
    }
  });
}
