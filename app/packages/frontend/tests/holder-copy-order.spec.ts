import { expect, test, type Page } from "@playwright/test";

const MINT = "So11111111111111111111111111111111111111112";
const OTHER = "11111111111111111111111111111111";

type ClipboardWrite = {
  value: string;
  resolve: () => void;
  reject: () => void;
};
declare global {
  interface Window {
    __delayedClipboardWrites: ClipboardWrite[];
  }
}

async function derive(page: Page) {
  await page.getByLabel("Solana mint address", { exact: true }).fill(MINT);
  await page.getByRole("button", { name: "Derive address", exact: true }).click();
  await expect(page.getByTestId("holder-rewards-result")).toBeVisible();
}

const feedback = (page: Page) =>
  page.getByTestId("holder-rewards-inspector").locator(':scope > p[role="status"]');

async function settle(page: Page, outcome: "resolve" | "reject") {
  await page.evaluate(async (outcome) => {
    window.__delayedClipboardWrites[0][outcome]();
    // Let the native Promise continuation and React's resulting render finish.
    await new Promise<void>((done) =>
      requestAnimationFrame(() => requestAnimationFrame(() => done())),
    );
  }, outcome);
}

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    window.__delayedClipboardWrites = [];
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: {
        writeText: (value: string) =>
          new Promise<void>((resolve, reject) => {
            window.__delayedClipboardWrites.push({
              value,
              resolve,
              reject: () => reject(new DOMException("Denied", "NotAllowedError")),
            });
          }),
      },
    });
  });
  await page.goto("/holder-rewards");
  await derive(page);
});

test("editing the mint discards an earlier copy success announcement", async ({ page }) => {
  await page.getByRole("button", { name: "Copy normalized mint", exact: true }).click();
  await expect.poll(() => page.evaluate(() => window.__delayedClipboardWrites.length)).toBe(1);
  expect(await page.evaluate(() => window.__delayedClipboardWrites[0].value)).toBe(MINT);
  await page.getByLabel("Solana mint address", { exact: true }).fill(OTHER);
  await expect(page.getByTestId("holder-rewards-no-result")).toBeVisible();
  await settle(page, "resolve");
  await expect(feedback(page)).toHaveText("");
  await expect(page.getByTestId("holder-rewards-inspector")).not.toContainText("Normalized mint copied.");
});

test("Clear keeps its current announcement when an earlier clipboard request rejects", async ({ page }) => {
  await page.getByRole("button", { name: "Copy holder-rewards pda", exact: true }).click();
  await expect.poll(() => page.evaluate(() => window.__delayedClipboardWrites.length)).toBe(1);
  await page.getByRole("button", { name: "Clear", exact: true }).click();
  await expect(feedback(page)).toHaveText("Inspector cleared.");
  await settle(page, "reject");
  await expect(feedback(page)).toHaveText("Inspector cleared.");
  await expect(page.getByTestId("holder-rewards-inspector")).not.toContainText("Could not copy");
});

test("a new derivation discards feedback from a copy started in the previous result", async ({ page }) => {
  await page.getByRole("button", { name: "Copy normalized mint", exact: true }).click();
  await expect.poll(() => page.evaluate(() => window.__delayedClipboardWrites.length)).toBe(1);
  await page.getByRole("button", { name: "Derive address", exact: true }).click();
  await expect(feedback(page)).toHaveText("");
  await settle(page, "resolve");
  await expect(feedback(page)).toHaveText("");
});
