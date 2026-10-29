import { expect, test } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
for (const width of [390, 1280])
  test(`mapped Settings identifier terms remain searchable at ${width}px`, async ({
    page,
    baseURL,
  }, testInfo) => {
    const errors: string[] = [],
      blocked: string[] = [],
      reads: Array<{ method: string; path: string; status: number }> = [];
    const observations: Array<{
      query: string;
      rows: (string | null)[];
      status: string | null;
    }> = [];
    page.on("pageerror", (error) => errors.push(error.message));
    page.on("response", (response) => {
      const request = response.request(),
        url = new URL(response.url());
      if (url.origin === new URL(baseURL!).origin)
        reads.push({
          method: request.method(),
          path: url.pathname + url.search,
          status: response.status(),
        });
    });
    await page.route("**/*", (route) => {
      const r = route.request();
      if (
        new URL(r.url()).origin !== new URL(baseURL!).origin ||
        !["GET", "HEAD"].includes(r.method())
      ) {
        blocked.push(r.method() + " " + r.url());
        return route.abort();
      }
      return route.continue();
    });
    await page.setViewportSize({ width, height: 844 });
    let overflow: number | undefined;
    const output = process.env.PUMP_SETTINGS_OUTPUT ?? testInfo.outputDir;
    try {
      const response = await page.goto("/?settings=privacy");
      expect(response?.status()).toBe(200);
      const dialog = page.getByRole("dialog", {
        name: "Settings",
        exact: true,
      });
      await expect(dialog).toBeVisible();
      const input = dialog.getByRole("searchbox", { name: "Search settings" });
      async function search(query: string) {
        await input.fill(query);
        await expect(input).toHaveValue(query);
        await page.evaluate(
          () =>
            new Promise<void>((resolve) =>
              requestAnimationFrame(() => resolve()),
            ),
        );
        const results = dialog.getByRole("region", {
          name: "Settings search results",
        });
        await expect(results).toBeVisible();
        const result = {
          query,
          rows: await results
            .locator("[data-setting-id]")
            .evaluateAll((nodes) =>
              nodes.map((node) => node.getAttribute("data-setting-id")),
            ),
          status: await results
            .locator(':scope > p[role="status"]')
            .textContent(),
        };
        observations.push(result);
        return result;
      }
      expect((await search("external links")).rows).toEqual([
        "privacy.confirmExternalLinks",
      ]);
      expect((await search("GróUP CHATS")).rows).toEqual([
        "chat.allowGroupNotifications",
      ]);
      expect((await search("not-mapped-setting")).rows).toEqual([]);
      // Original indexing replaces periods in the definition ID, not in the query.
      expect((await search("privacy.confirmExternalLinks")).rows).toEqual([]);
      const target = await search("privacy confirmExternalLinks");
      overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - innerWidth,
      );
      await mkdir(output, { recursive: true });
      await dialog.screenshot({
        path: path.join(output, `settings-id-${width}.png`),
      });
      expect(errors).toEqual([]);
      expect(blocked).toEqual([]);
      expect(overflow).toBeLessThanOrEqual(1);
      expect(target.rows).toEqual(["privacy.confirmExternalLinks"]);
      await expect(input).toBeFocused();
      await dialog.getByRole("button", { name: "Done", exact: true }).click();
      await expect(dialog).not.toBeVisible();
      expect(new URL(page.url()).searchParams.has("settings")).toBe(false);
    } finally {
      await mkdir(output, { recursive: true });
      await writeFile(
        path.join(output, `observations-${width}.json`),
        JSON.stringify(
          {
            width,
            observations,
            reads,
            errors,
            blocked,
            overflow,
            limits:
              "Actual Next Settings page, mapped static definitions only; fresh synthetic clickwrap state, no settings control activation or preference/account mutation. No fulfilled JSON or original provider/search parity.",
          },
          null,
          2,
        ) + "\n",
      );
    }
  });
