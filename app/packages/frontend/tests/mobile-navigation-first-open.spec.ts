import { writeFile } from "node:fs/promises";
import { expect, test, type Page, type Route } from "@playwright/test";
import { openShellSearch } from "./shell-controls";

async function observe(page: Page) {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  await page.addInitScript(() => {
    const trace: unknown[] = [];
    Reflect.set(window, "__firstMoreTrace", trace);
    const record = (stage: string, event?: Event) => {
      if (trace.length >= 60) return;
      const sidebar = document.getElementById("app-sidebar");
      const more = document.querySelector<HTMLButtonElement>(
        'button[aria-label="Open navigation"]',
      );
      trace.push({
        stage,
        time: performance.now(),
        trusted: event?.isTrusted,
        enabled: more ? !more.disabled : null,
        expanded: more?.getAttribute("aria-expanded"),
        drawer: document
          .querySelector("[data-app-shell]")
          ?.getAttribute("data-mobile-navigation"),
        responsiveVisibility: sidebar?.style.visibility,
        sidebarHidden: sidebar?.getAttribute("aria-hidden"),
      });
    };
    document.addEventListener(
      "click",
      (event) => {
        if (
          event.target instanceof Element &&
          event.target.closest('button[aria-label="Open navigation"]')
        )
          record("actual-more-click-capture", event);
      },
      true,
    );
    document.addEventListener("DOMContentLoaded", () =>
      record("DOMContentLoaded"),
    );
    let previous = "";
    new MutationObserver(() => {
      const sidebar = document.getElementById("app-sidebar");
      if (!sidebar) return;
      const fingerprint = [
        sidebar.style.visibility,
        sidebar.getAttribute("aria-hidden"),
        document
          .querySelector("[data-app-shell]")
          ?.getAttribute("data-mobile-navigation"),
      ].join("|");
      if (fingerprint !== previous) {
        previous = fingerprint;
        record("sidebar-state-change");
      }
    }).observe(document, { childList: true, subtree: true, attributes: true });
  });
  return errors;
}

async function save(
  page: Page,
  errors: string[],
  initialEnabled: boolean | null,
) {
  const result = await page.evaluate(() => ({
    trace: Reflect.get(window, "__firstMoreTrace"),
    drawer: document
      .querySelector("[data-app-shell]")
      ?.getAttribute("data-mobile-navigation"),
  }));
  await writeFile(
    test.info().outputPath("first-open-observations.json"),
    JSON.stringify({ errors, initialEnabled, ...result }, null, 2),
  );
  await page.screenshot({
    path: test.info().outputPath("first-open.png"),
    animations: "disabled",
  });
}

async function responsiveEffect(page: Page) {
  await page.waitForFunction(() =>
    ["hidden", "visible"].includes(
      document.getElementById("app-sidebar")?.style.visibility ?? "",
    ),
  );
}

test("a first offered More click before local boot opens the mobile drawer", async ({
  page,
}) => {
  await page.setViewportSize({ width: 767, height: 812 });
  const errors = await observe(page);
  const held: Route[] = [];
  let holding = true;
  let initialEnabled: boolean | null = null;
  const release = async () => {
    holding = false;
    await Promise.all(held.splice(0).map((route) => route.continue()));
  };
  await page.route("**/_next/static/**", async (route) => {
    if (holding && /\.js(?:\?|$)/.test(route.request().url())) held.push(route);
    else await route.continue();
  });
  try {
    await page.goto("/explore", { waitUntil: "commit" });
    const more = page.getByRole("button", {
      name: "Open navigation",
      exact: true,
    });
    await expect(more).toBeVisible();
    initialEnabled = await more.isEnabled();
    await page.screenshot({
      path: test.info().outputPath("offered-control.png"),
      animations: "disabled",
    });
    if (initialEnabled) await more.click();
    await release();
    await responsiveEffect(page);
    if (initialEnabled)
      await expect(page.locator("[data-app-shell]")).toHaveAttribute(
        "data-mobile-navigation",
        "open",
      );
    else {
      await expect(more).toBeEnabled();
      await more.click();
      await expect(page.locator("[data-app-shell]")).toHaveAttribute(
        "data-mobile-navigation",
        "open",
      );
    }
    expect(errors).toEqual([]);
  } finally {
    await release();
    await save(page, errors, initialEnabled);
  }
});

test("one normal first More click survives the initial responsive effects on a slow CPU", async ({
  page,
  context,
}) => {
  await page.setViewportSize({ width: 767, height: 812 });
  const cdp = await context.newCDPSession(page);
  await cdp.send("Emulation.setCPUThrottlingRate", { rate: 4 });
  const errors = await observe(page);
  let initialEnabled: boolean | null = null;
  try {
    await page.goto("/explore", { waitUntil: "domcontentloaded" });
    const more = page.getByRole("button", {
      name: "Open navigation",
      exact: true,
    });
    initialEnabled = await more.isEnabled();
    await more.click();
    await responsiveEffect(page);
    await expect(page.locator("[data-app-shell]")).toHaveAttribute(
      "data-mobile-navigation",
      "open",
    );
    expect(errors).toEqual([]);
  } finally {
    await save(page, errors, initialEnabled);
  }
});

for (const width of [320, 375, 767, 768, 1440]) {
  test(`More readiness agrees with actual CSS and navigation works at ${width}px`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 900 });
    const errors = await observe(page);
    let initialEnabled: boolean | null = null;
    try {
      await page.goto("/explore");
      if (width < 768) {
        await responsiveEffect(page);
      } else {
        // A completed existing shell interaction establishes mounted desktop
        // controls; this preservation case does not test their pre-boot state.
        const search = await openShellSearch(page);
        await search.press("Escape");
      }
      const more = page.locator('button[aria-label="Open navigation"]');
      const display = await page
        .getByRole("navigation", { name: "Mobile", includeHidden: true })
        .evaluate((nav) => getComputedStyle(nav.parentElement!).display);
      expect(display === "none").toBe(width >= 768);
      initialEnabled = await more.isEnabled();
      const sidebar = page.locator("#app-sidebar");
      if (width < 768) {
        await expect(more).toBeVisible();
        await expect(more).toBeEnabled();
        await expect(more).toHaveAttribute("title", "More");
        await more.click();
        await expect(more).toHaveAttribute("aria-expanded", "true");
        await expect(
          page.getByRole("button", { name: "Close navigation", exact: true }),
        ).toBeFocused();
        await page.keyboard.press("Escape");
        await expect(more).toHaveAttribute("aria-expanded", "false");
        await expect(more).toBeFocused();
      } else {
        await expect(more).not.toBeVisible();
        const toggle = page.locator("#app-sidebar-trigger");
        await expect(toggle).toBeVisible();
        await expect(sidebar).toHaveAttribute("data-state", "collapsed");
        await toggle.click();
        await expect(sidebar).toHaveAttribute("data-state", "expanded");
        await toggle.click();
        await expect(sidebar).toHaveAttribute("data-state", "collapsed");
      }
      await expect(page).toHaveURL(/\/explore$/);
      expect(errors).toEqual([]);
    } finally {
      await save(page, errors, initialEnabled);
    }
  });
}

test("native fractional iframe viewport has no visible-but-disabled More gap", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  const errors = await observe(page);
  await page.goto("/explore");
  // A same-origin native iframe supplies a fractional CSS viewport without
  // replacing matchMedia, app hooks, responses or the embedded app's CSS.
  await page.evaluate(() => {
    const host = document.createElement("iframe");
    host.id = "fractional-navigation-host";
    host.title = "Fractional navigation boundary fixture";
    host.src = "/explore";
    host.style.cssText =
      "position:fixed;inset:0 auto auto 0;width:767.5px;height:900px;border:0;z-index:9999";
    document.body.append(host);
  });
  const host = page.locator("#fractional-navigation-host");
  const frame = page.frameLocator("#fractional-navigation-host");
  await frame
    .getByRole("button", { name: "Search for coins and users", exact: true })
    .click();
  const searchDialog = frame.getByRole("dialog", {
    name: "Search for coins and users",
    exact: true,
  });
  await expect(searchDialog).toBeVisible();
  await searchDialog.getByRole("searchbox").press("Escape");
  const measurements = await frame.locator("html").evaluate(() => {
    const more = document.querySelector<HTMLButtonElement>(
      'button[aria-label="Open navigation"]',
    )!;
    return {
      cssMin768: matchMedia("(min-width: 768px)").matches,
      legacyMax767: matchMedia("(max-width: 767px)").matches,
      exactMobile: matchMedia("(width < 768px)").matches,
      innerWidth,
      mobileNavDisplay: getComputedStyle(
        document.querySelector('nav[aria-label="Mobile"]')!.parentElement!,
      ).display,
      moreDisabled: more.disabled,
    };
  });
  const embeddingWidth = await host.evaluate(
    (node) => node.getBoundingClientRect().width,
  );
  await writeFile(
    test.info().outputPath("fractional-boundary.json"),
    JSON.stringify({ embeddingWidth, measurements }, null, 2),
  );
  test.skip(
    !measurements.exactMobile ||
      measurements.legacyMax767 ||
      measurements.cssMin768,
    "Browser did not expose the fractional interval; see actual measurements, no fractional coverage claimed.",
  );
  expect(embeddingWidth).toBe(767.5);
  expect(measurements.mobileNavDisplay).not.toBe("none");
  expect(measurements.moreDisabled).toBe(false);
  const more = frame.getByRole("button", {
    name: "Open navigation",
    exact: true,
  });
  await more.click();
  await expect(frame.locator("[data-app-shell]")).toHaveAttribute(
    "data-mobile-navigation",
    "open",
  );
  const close = frame.getByRole("button", {
    name: "Close navigation",
    exact: true,
  });
  await expect(close).toBeFocused();
  await close.press("Escape");
  await expect(more).toBeFocused();
  await expect(frame.locator("[data-app-shell]")).toHaveAttribute(
    "data-mobile-navigation",
    "closed",
  );
  expect(errors).toEqual([]);
  await page.screenshot({
    path: test.info().outputPath("fractional-navigation.png"),
    animations: "disabled",
  });
});
