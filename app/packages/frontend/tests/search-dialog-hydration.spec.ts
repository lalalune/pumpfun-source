import { writeFile } from "node:fs/promises";
import { expect, test, type Page } from "@playwright/test";
import { openShellSearch } from "./shell-controls";

async function observe(page: Page) {
  const errors: string[] = [];
  const observations: unknown[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
    if (
      message.type() === "debug" &&
      message.text().startsWith("__searchHydrationTrace:")
    )
      observations.push(
        JSON.parse(message.text().slice("__searchHydrationTrace:".length)),
      );
  });
  await page.addInitScript(() => {
    const trace: unknown[] = [];
    Reflect.set(window, "__searchHydrationTrace", trace);
    const record = (stage: string) => {
      const input = document.querySelector<HTMLInputElement>("#global-search");
      if (trace.length >= 80) return;
      const entry = {
        stage,
        time: performance.now(),
        url: location.href,
        mounted: Reflect.get(window, "__searchHydrationMounted") === true,
        inputValue: input?.value,
        serverValueAttribute: input?.getAttribute("value"),
        buttons: Array.from(input?.form?.querySelectorAll("button") ?? []).map(
          (button) => ({
            type: button.type,
            label: button.getAttribute("aria-label"),
            text: button.textContent,
          }),
        ),
      };
      trace.push(entry);
      console.debug("__searchHydrationTrace:" + JSON.stringify(entry));
    };
    const add = window.addEventListener;
    window.addEventListener = function (
      ...args: Parameters<typeof window.addEventListener>
    ) {
      const result = Reflect.apply(add, this, args);
      if (args[0] === "pump:open-search") {
        Reflect.set(window, "__searchHydrationMounted", true);
        record("actual-search-listener-mounted");
      }
      return result;
    };
    window.addEventListener("popstate", () => record("native-popstate"));
    document.addEventListener("DOMContentLoaded", () =>
      record("DOMContentLoaded"),
    );
    let previous = "";
    new MutationObserver(() => {
      const input = document.querySelector<HTMLInputElement>("#global-search");
      if (!input) return;
      const current = input.form?.innerHTML ?? "";
      if (current !== previous) {
        previous = current;
        record("search-markup-change");
      }
    }).observe(document, { childList: true, subtree: true, attributes: true });
  });
  return { errors, observations };
}

async function saveTrace(
  page: Page,
  errors: string[],
  observations: unknown[],
) {
  const latestDocument = await page.evaluate(() =>
    Reflect.get(window, "__searchHydrationTrace"),
  );
  await writeFile(
    test.info().outputPath("search-hydration-observations.json"),
    JSON.stringify({ errors, observations, latestDocument }, null, 2),
  );
  await page.screenshot({
    path: test.info().outputPath("search-dialog.png"),
    animations: "disabled",
  });
  await test.info().attach("search-hydration-observations", {
    body: JSON.stringify({ errors, observations, latestDocument }, null, 2),
    contentType: "application/json",
  });
}

test("query reload and browser history keep the shared search hydration consistent on a slow CPU", async ({
  page,
  context,
}) => {
  const { errors, observations } = await observe(page);
  const cdp = await context.newCDPSession(page);
  await cdp.send("Emulation.setCPUThrottlingRate", { rate: 4 });
  try {
    await page.goto("/go");
    const search = page.getByRole("searchbox", {
      name: "Search archived bounties",
    });
    await search.fill("alpha & beta=one");
    await search.press("Enter");
    await expect(page).toHaveURL(/\/go\?q=alpha\+%26\+beta%3Done$/);
    await expect(page.getByTestId("go-empty-results")).toBeVisible();
    await page.reload({ waitUntil: "domcontentloaded" });
    await expect(search).toHaveValue("alpha & beta=one");
    // Intentionally allow real history traversal before the hidden dialog mounts.
    await page.goBack();
    await expect(page).toHaveURL(/\/go$/);
    await expect(page.getByTestId("go-bounty-card")).toHaveCount(24);
    // Complete this native Back before moving Forward: otherwise the URL may
    // return to the server query before the shared boundary hydrates.
    await page.waitForFunction(
      () => Reflect.get(window, "__searchHydrationMounted") === true,
    );
    await page.goForward();
    await expect(search).toHaveValue("alpha & beta=one");
    await page.getByRole("button", { name: "Reset", exact: true }).click();
    await expect(page).toHaveURL(/\/go$/);
    await expect(search).toHaveValue("");
    await page.waitForFunction(
      () => Reflect.get(window, "__searchHydrationMounted") === true,
    );
    await expect(await openShellSearch(page)).toHaveValue("");
    expect(errors).toEqual([]);
  } finally {
    await saveTrace(page, errors, observations);
  }
});

test("a direct nonempty URL still initializes the dialog and follows later browser history", async ({
  page,
}) => {
  const { errors, observations } = await observe(page);
  await page.setViewportSize({ width: 390, height: 844 });
  try {
    await page.goto("/explore?q=retained");
    await page.waitForFunction(
      () => Reflect.get(window, "__searchHydrationMounted") === true,
    );
    const input = await openShellSearch(page);
    await expect(input).toHaveValue("retained");
    await input.fill("second");
    await input.press("Enter");
    await expect(page).toHaveURL(/\/explore\?q=second$/);
    await page.goBack();
    await expect(page).toHaveURL(/\/explore\?q=retained$/);
    await expect(await openShellSearch(page)).toHaveValue("retained");
    expect(errors).toEqual([]);
  } finally {
    await saveTrace(page, errors, observations);
  }
});
