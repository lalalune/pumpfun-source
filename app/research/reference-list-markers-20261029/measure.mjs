import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

const [repository, destination, stage] = process.argv.slice(2);
assert(repository && destination && ["baseline", "fixed"].includes(stage));
const frontend = resolve(repository, "app/packages/frontend");
const require = createRequire(resolve(frontend, "package.json"));
const { chromium } = require("@playwright/test");
const { acceptedClickwrapState } = await import(pathToFileURL(resolve(frontend, "tests/browser-state.ts")));
const origin = "http://127.0.0.1:3027";
await mkdir(destination, { recursive: true });
const browser = await chromium.launch();
const observations = [];
try {
  for (const width of [1280, 375]) {
    const context = await browser.newContext({ storageState: acceptedClickwrapState, viewport: { width, height: 850 } });
    try {
      const forbidden = [];
      await context.route("**/*", (route) => {
        const request = route.request();
        if (new URL(request.url()).origin !== origin || !["GET", "HEAD"].includes(request.method())) {
          forbidden.push(`${request.method()} ${request.url()}`);
          return route.abort();
        }
        return route.continue();
      });
      const page = await context.newPage();
      const errors = [];
      page.on("pageerror", (error) => errors.push(error.message));
      page.on("console", (message) => { if (message.type() === "error") errors.push(message.text()); });
      for (const [key, path, title, headings, tables, lists, items] of [
        ["fees", "/docs/fees", "Fees", 7, 7, 0, 0],
        ["privacy", "/docs/privacy-policy", "Privacy Notice", 16, 0, 4, 43],
        ["terms", "/docs/terms-and-conditions", "Terms Of Use", 36, 0, 4, 14],
      ]) {
        const response = await page.goto(origin + path, { waitUntil: "networkidle" });
        assert.equal(response.status(), 200);
        assert.equal(await page.locator("h1").textContent(), title);
        assert.equal(await page.getByTestId("reference-evidence-error").count(), 0);
        const document = page.getByTestId("reference-document");
        assert.equal(await document.locator("h2").count(), headings);
        assert.equal(await document.locator("table").count(), tables);
        assert.equal(await document.locator("ul").count(), lists);
        assert.equal(await document.locator("ul > li").count(), items);
        const styles = await document.locator("ul").evaluateAll((nodes) => nodes.map((list) => ({
          listStyleType: getComputedStyle(list).listStyleType,
          listStylePosition: getComputedStyle(list).listStylePosition,
          display: getComputedStyle(list).display,
          paddingLeft: getComputedStyle(list).paddingLeft,
          items: Array.from(list.children).filter((child) => child.tagName === "LI").length,
          firstItemText: list.querySelector("li")?.textContent,
          firstItemStyle: list.querySelector("li") ? getComputedStyle(list.querySelector("li")).listStyleType : null,
        })));
        const geometry = await page.evaluate(() => ({ viewportWidth: document.documentElement.clientWidth, documentWidth: document.documentElement.scrollWidth }));
        assert(geometry.documentWidth <= geometry.viewportWidth);
        if (lists) {
          await document.locator("ul > li").first().scrollIntoViewIfNeeded();
          await page.screenshot({ path: resolve(destination, `${key}-${width}.png`) });
        }
        observations.push({ stage, key, width, url: page.url(), status: response.status(), title, headings, tables, lists, items, styles, geometry });
      }
      assert.deepEqual(forbidden, []);
      assert.deepEqual(errors, []);
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
}
// This inspection records actual styles; it deliberately does not encode a
// replacement CSS rule as a maintained test assertion. Both healthy runs exit0.
await writeFile(resolve(destination, "observations.json"), JSON.stringify({ stage, observations }, null, 2) + "\n");
console.log(JSON.stringify({ stage, healthyPages: observations.length, observedListStyles: [...new Set(observations.flatMap((page) => page.styles.map((list) => list.listStyleType)))] }));
