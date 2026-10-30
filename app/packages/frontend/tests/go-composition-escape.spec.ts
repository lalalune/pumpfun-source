import { expect, test } from "@playwright/test";

test("GO keeps an archived detail open while Escape cancels text composition", async ({
  page,
}) => {
  await page.goto("/go");
  const inspect = page
    .getByRole("button", { name: /^Inspect archived bounty / })
    .first();
  await inspect.click();
  const detail = page.getByTestId("go-bounty-detail");
  await expect(detail).toBeVisible();
  const selectedUrl = page.url();
  const search = page.getByRole("searchbox", {
    name: "Search archived bounties",
  });
  await search.focus();
  await search.dispatchEvent("compositionstart", { data: "" });
  await search.dispatchEvent("compositionupdate", { data: "任务" });
  const canceled = await search.evaluate(
    (input) =>
      !input.dispatchEvent(
        new KeyboardEvent("keydown", {
          key: "Escape",
          code: "Escape",
          isComposing: true,
          bubbles: true,
          cancelable: true,
        }),
      ),
  );
  expect(canceled).toBe(false);
  // A later browser task exposes an erroneous router transition before asserting.
  await page.evaluate(
    () =>
      new Promise<void>((resolve) =>
        requestAnimationFrame(() => requestAnimationFrame(() => resolve())),
      ),
  );
  await expect(page).toHaveURL(selectedUrl);
  await expect(detail).toBeVisible();
  await expect(search).toBeFocused();
  await search.dispatchEvent("compositionend", { data: "" });
  await search.press("Escape");
  await expect(page).not.toHaveURL(/task=/);
  await expect(detail).toHaveCount(0);
  await expect(inspect).toBeFocused();
});
