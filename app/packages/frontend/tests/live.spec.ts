import { expect, test, type Page, type Route } from "@playwright/test";

const FIRST_MINT = "7bS1mH6MXbw1GnEkKTU6w5YLTywPkQ1w3YVZXWFupump";

function monitorSafety(page: Page) {
  const unexpectedRequests: string[] = [];
  const consoleErrors: string[] = [];
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (
      url.origin !== "http://127.0.0.1:3010" ||
      !["GET", "HEAD"].includes(request.method())
    ) {
      unexpectedRequests.push(`${request.method()} ${request.url()}`);
    }
  });
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  return { unexpectedRequests, consoleErrors };
}

test("renders the authenticated archived discovery snapshot without fake current status", async ({
  page,
}) => {
  const safety = monitorSafety(page);
  const response = await page.goto("/live");
  expect(response?.status()).toBe(200);
  await expect(
    page.getByRole("heading", { level: 1, name: "Live discovery" }),
  ).toBeVisible();
  await expect(
    page.getByText("No current live status", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("42 exact archived cards", { exact: true }),
  ).toBeVisible();
  await expect(page.getByTestId("archived-stream-card")).toHaveCount(12);
  await expect(page.getByText("Captured snapshot — not current")).toHaveCount(
    12,
  );
  await expect(page.getByText("42", { exact: true })).toBeVisible();
  await expect(page.getByText(/No archived stream selected/)).toBeVisible();
  await expect(
    page.locator("main img, main video, main audio, main iframe"),
  ).toHaveCount(0);
  await expect(page.getByText(/^LIVE$/)).toHaveCount(0);
  expect(safety.unexpectedRequests).toEqual([]);
  expect(safety.consoleErrors).toEqual([]);
});

test("search and sorting are URL-backed, empty-safe and history-aware", async ({
  page,
}) => {
  await page.goto("/live");
  const search = page.getByRole("searchbox", {
    name: "Search captured streams",
  });
  await search.fill("$mAjor");
  await search.press("Enter");
  await expect(page).toHaveURL(/\/live\?q=%24mAjor$/);
  await expect(page.getByTestId("archived-stream-card")).toHaveCount(1);
  await expect(page.getByText("$mAjor", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "Clear", exact: true }).click();
  await expect(page).toHaveURL(/\/live$/);
  await expect(page.getByTestId("archived-stream-card")).toHaveCount(12);
  await page.getByLabel("Sort captured cards").selectOption("title");
  await expect(page).toHaveURL(/sort=title/);
  await expect(page.getByTestId("archived-stream-card").first()).toContainText(
    "$RAT - Exfil Rat",
  );

  await page.goBack();
  await expect(page).toHaveURL(/\/live$/);
  await expect(page.getByTestId("archived-stream-card").first()).toContainText(
    "$M",
  );
  await page.goBack();
  await expect(search).toHaveValue("$mAjor");
  await expect(page.getByTestId("archived-stream-card")).toHaveCount(1);
  await page.goForward();
  await expect(page.getByTestId("archived-stream-card")).toHaveCount(12);

  await search.fill("nothing in archive");
  await search.press("Enter");
  await expect(page.getByTestId("live-empty-results")).toContainText(
    "This says nothing about current broadcasts.",
  );
});

test("selection exposes only unavailable playback state and restores focus on Escape", async ({
  page,
}) => {
  await page.goto("/live");
  const inspect = page.getByRole("button", {
    name: "Inspect archived stream M $M",
  });
  await inspect.focus();
  await inspect.click();
  await expect(page).toHaveURL(new RegExp(`stream=${FIRST_MINT}$`));
  await expect(page.getByTestId("playback-unavailable")).toBeVisible();
  await expect(
    page.getByText("No media session was started", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText(/does not mean the broadcast is live now/),
  ).toBeVisible();
  await expect(page.locator("video, audio, iframe")).toHaveCount(0);

  await page.keyboard.press("Escape");
  await expect(page).toHaveURL(/\/live$/);
  await expect(inspect).toBeFocused();
  await expect(
    page.getByText("No archived stream selected", { exact: true }),
  ).toBeVisible();
});

test("invalid selections and unsupported captured sections fail honestly", async ({
  page,
}) => {
  await page.goto("/live?stream=not-in-the-archive");
  await expect(page.getByTestId("invalid-stream-selection")).toContainText(
    "Nothing was fetched from a production service.",
  );
  await page.getByRole("button", { name: "Close stream detail" }).click();
  await expect(page).toHaveURL(/\/live$/);

  const other = page.getByRole("tab", { name: "Other sections" });
  await other.click();
  await expect(page).toHaveURL(/section=other-sections/);
  await expect(page.getByTestId("other-sections-unavailable")).toContainText(
    "Other section payloads are not mapped",
  );
  await page.getByRole("button", { name: "Return to captured cards" }).click();
  await expect(page.getByTestId("archived-stream-card")).toHaveCount(12);
});

test("section navigation is keyboard operable", async ({ page }) => {
  await page.goto("/live");
  const mostViewers = page.getByRole("tab", { name: "Most viewers" });
  const other = page.getByRole("tab", { name: "Other sections" });
  await mostViewers.focus();
  await page.keyboard.press("ArrowRight");
  await expect(other).toBeFocused();
  await expect(other).toHaveAttribute("aria-selected", "true");
  await page.keyboard.press("Home");
  await expect(mostViewers).toBeFocused();
  await expect(mostViewers).toHaveAttribute("aria-selected", "true");
});

test("required viewports have usable controls and no horizontal overflow", async ({
  page,
}) => {
  for (const [width, height] of [
    [320, 640],
    [375, 812],
    [768, 1024],
    [1024, 768],
    [1280, 800],
    [1440, 900],
  ] as const) {
    await page.setViewportSize({ width, height });
    await page.goto("/live");
    await expect(
      page.getByRole("searchbox", { name: "Search captured streams" }),
    ).toBeVisible();
    await expect(
      page.getByTestId("archived-stream-card").first(),
    ).toBeVisible();
    const metrics = await page.evaluate(() => ({
      clientWidth: document.documentElement.clientWidth,
      scrollWidth: document.documentElement.scrollWidth,
      undersizedButtons: Array.from(
        document.querySelectorAll("main button"),
      ).filter((element) => {
        const box = element.getBoundingClientRect();
        return box.width > 0 && box.height > 0 && box.height < 36;
      }).length,
    }));
    expect(metrics.scrollWidth, `${width}px document`).toBeLessThanOrEqual(
      metrics.clientWidth,
    );
    expect(metrics.undersizedButtons, `${width}px controls`).toBe(0);
  }
});

test("interaction remains local and adjacent routes retain their boundaries", async ({
  page,
}) => {
  const safety = monitorSafety(page);
  await page.goto("/live");
  await page
    .getByRole("button", { name: "Inspect archived stream M $M" })
    .click();
  await page.getByRole("button", { name: "Close stream detail" }).click();
  await page.getByRole("link", { name: "Explore", exact: true }).click();
  await expect(
    page.getByRole("heading", { level: 1, name: "Explore" }),
  ).toBeVisible();
  await page.goto("/create");
  await expect(page.getByRole("form")).toBeVisible();
  await page.goto("/");
  await expect(page.getByRole("tab", { name: "For you" })).toBeVisible();
  expect(safety.unexpectedRequests).toEqual([]);
  expect(safety.consoleErrors).toEqual([]);
  for (const path of ["/coin/example", "/pump-token", "/profile/example"]) {
    const response = await page.goto(path);
    expect(response?.status(), path).toBe(404);
  }
});

test("all four local pages are reachable with stable history, reload and no duplicate records", async ({
  page,
}) => {
  const safety = monitorSafety(page);
  await page.goto("/live");
  const names: string[] = [];
  await expect(
    page.getByRole("button", { name: "Previous page" }),
  ).toBeDisabled();
  for (let current = 1; current <= 4; current += 1) {
    await expect(
      page.getByText(`Page ${current} of 4`, { exact: true }),
    ).toBeVisible();
    await expect(page.getByTestId("archived-stream-card")).toHaveCount(
      current === 4 ? 6 : 12,
    );
    names.push(
      ...(await page
        .getByTestId("archived-stream-card")
        .locator("h3")
        .allTextContents()),
    );
    if (current < 4) {
      await page.getByRole("button", { name: "Next page" }).click();
      await expect(page).toHaveURL(new RegExp(`page=${current + 1}$`));
    }
  }
  expect(names).toHaveLength(42);
  expect(new Set(names).size).toBe(42);
  expect(names[12]).toBe("CryptoCasinoWEB3");
  expect(names[41]).toBe("Be a U$Dolly visionary!");
  await expect(page.getByRole("button", { name: "Next page" })).toBeDisabled();
  await expect(
    page.getByText("Showing 37–42 of 42 captured records", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Previous page" }).click();
  await expect(page).toHaveURL(/page=3$/);
  await page.goBack();
  await expect(page).toHaveURL(/page=4$/);
  await page.reload();
  await expect(page.getByTestId("archived-stream-card")).toHaveCount(6);
  expect(safety.unexpectedRequests).toEqual([]);
  expect(safety.consoleErrors).toEqual([]);
});

test("search, sort and section changes reset pagination and dismiss selected metadata", async ({
  page,
}) => {
  await page.goto("/live?page=2");
  const search = page.getByRole("searchbox", {
    name: "Search captured streams",
  });
  await page
    .getByRole("button", {
      name: "Inspect archived stream CryptoCasinoWEB3 CHERRY",
    })
    .click();
  await expect(page.getByTestId("playback-unavailable")).toBeVisible();
  await search.fill("CryptoCasinoWEB3");
  await search.press("Enter");
  await expect(page).toHaveURL(/\/live\?q=CryptoCasinoWEB3$/);
  await expect(page.getByTestId("archived-stream-card")).toHaveCount(1);
  await expect(
    page.getByText("No archived stream selected", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Clear", exact: true }).click();
  await page.getByRole("button", { name: "Next page" }).click();
  await expect(page).toHaveURL(/page=2$/);
  await page.getByLabel("Sort captured cards").selectOption("viewers");
  await expect(page).toHaveURL(/\/live\?sort=viewers$/);
  await expect(page.getByTestId("archived-stream-card").nth(1)).toContainText(
    "CryptoCasinoWEB3",
  );
  await page.getByRole("button", { name: "Next page" }).click();
  await expect(page).toHaveURL(/page=2$/);
  await page.getByRole("tab", { name: "Other sections" }).click();
  await expect(page).not.toHaveURL(/page=/);
  await page.getByRole("button", { name: "Return to captured cards" }).click();
  await expect(page.getByText("Page 1 of 4", { exact: true })).toBeVisible();
});

test("malformed, duplicate and out-of-range pages fail closed without changing the URL", async ({
  page,
}) => {
  const safety = monitorSafety(page);
  for (const query of [
    "page=0",
    "page=5",
    "page=01",
    "page=1.5",
    "page=1&page=2",
    "page=1&page=1",
    "page=",
    "q=%24major&page=2",
    "q=absent-record&page=2",
  ]) {
    await page.goto(`/live?${query}`);
    await expect(page.getByTestId("live-invalid-page")).toBeVisible();
    await expect(page.getByTestId("archived-stream-card")).toHaveCount(0);
    expect(new URL(page.url()).search).toBe(`?${query}`);
    await page.getByRole("button", { name: "Return to first page" }).click();
    await expect(page).not.toHaveURL(/page=/);
    await expect(page.getByTestId("live-invalid-page")).toHaveCount(0);
  }
  await expect(page.getByTestId("live-empty-results")).toContainText(
    "42-record archive",
  );
  expect(safety.unexpectedRequests).toEqual([]);
  expect(safety.consoleErrors).toEqual([]);
});

test("selection dismisses on page changes and Escape has a visible fallback for off-page or blank selections", async ({
  page,
}) => {
  await page.goto("/live");
  await page
    .getByRole("button", { name: "Inspect archived stream M $M" })
    .click();
  await expect(page.getByTestId("playback-unavailable")).toBeVisible();
  await page.getByRole("button", { name: "Next page" }).click();
  await expect(page).toHaveURL(/\/live\?page=2$/);
  await expect(
    page.getByText("No archived stream selected", { exact: true }),
  ).toBeVisible();
  await page.goto(`/live?page=4&stream=${FIRST_MINT}`);
  await expect(page.getByTestId("playback-unavailable")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page).toHaveURL(/\/live\?page=4$/);
  await expect(
    page.getByRole("searchbox", { name: "Search captured streams" }),
  ).toBeFocused();
  await page.goto("/live?stream=");
  await expect(page.getByTestId("invalid-stream-selection")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page).toHaveURL(/\/live$/);
  await expect(
    page.getByRole("searchbox", { name: "Search captured streams" }),
  ).toBeFocused();
});

test("direct-visit details handle Escape as soon as they are exposed", async ({ page }) => {
  await page.addInitScript(() => {
    const probe = window as Window & {
      firstDetailEscape?: { prevented: boolean };
    };
    // This runs at the first DOM exposure, before a later passive effect could
    // make an otherwise-ready panel's missing keyboard handler pass by timing.
    const observer = new MutationObserver(() => {
      if (
        probe.firstDetailEscape ||
        !document.querySelector(
          '[data-testid="playback-unavailable"], [data-testid="invalid-stream-selection"]',
        )
      ) return;
      const event = new KeyboardEvent("keydown", {
        key: "Escape", bubbles: true, cancelable: true,
      });
      probe.firstDetailEscape = { prevented: false };
      window.dispatchEvent(event);
      probe.firstDetailEscape.prevented = event.defaultPrevented;
    });
    observer.observe(document, { childList: true, subtree: true });
  });

  for (const selection of [FIRST_MINT, ""]) {
    const response = await page.goto(`/live?page=4&stream=${selection}`);
    await expect(page).toHaveURL(/\/live\?page=4$/);
    expect(await response?.text()).toContain("Loading archived details…");
    expect(await page.evaluate(() => (window as Window & {
      firstDetailEscape?: { prevented: boolean };
    }).firstDetailEscape)).toEqual({ prevented: true });
    await expect(
      page.getByRole("searchbox", { name: "Search captured streams" }),
    ).toBeFocused();
  }
});

test("Escape belongs to an open modal before the underlying nonmodal stream detail", async ({
  page,
}) => {
  await page.goto(`/live?stream=${FIRST_MINT}`);
  await expect(page.getByTestId("playback-unavailable")).toBeVisible();
  // An isolated local dialog exercises ownership without requiring another
  // feature branch, external service or a captured runtime.
  await page.evaluate(() => {
    const dialog = document.createElement("dialog");
    dialog.id = "local-escape-owner";
    const button = document.createElement("button");
    button.textContent = "Local modal control";
    dialog.append(button);
    document.body.append(dialog);
    dialog.showModal();
    button.focus();
  });
  await page.keyboard.press("Escape");
  await expect(page.locator("#local-escape-owner")).not.toBeVisible();
  await expect(page).toHaveURL(new RegExp(`stream=${FIRST_MINT}$`));
  await expect(page.getByTestId("playback-unavailable")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page).toHaveURL(/\/live$/);
});

test("a prevented Escape does not dismiss stream detail", async ({ page }) => {
  await page.goto(`/live?stream=${FIRST_MINT}`);
  await expect(page.getByTestId("playback-unavailable")).toBeVisible();
  await page.evaluate(() => {
    window.addEventListener("keydown", (event) => event.preventDefault(), {
      capture: true,
      once: true,
    });
  });
  await page.keyboard.press("Escape");
  await expect(page).toHaveURL(new RegExp(`stream=${FIRST_MINT}$`));
  await expect(page.getByTestId("playback-unavailable")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page).toHaveURL(/\/live$/);
});

test("search preserves a sort change while its navigation is pending", async ({
  page,
}) => {
  await page.goto("/live");
  const search = page.getByRole("searchbox", {
    name: "Search captured streams",
  });
  await search.fill("$major");
  const held: Route[] = [];
  let holdNavigation = true;
  await page.route("**/live?**", async (route) => {
    if (
      holdNavigation &&
      new URL(route.request().url()).searchParams.has("_rsc")
    ) {
      held.push(route);
    } else {
      await route.continue();
    }
  });
  try {
    await page.getByLabel("Sort captured cards").selectOption("viewers");
    await expect.poll(() => held.length).toBe(1);
    await search.press("Enter");
    await expect.poll(() => held.length).toBe(2);
    holdNavigation = false;
    await Promise.all(held.map((route) => route.continue()));
    await expect(page).toHaveURL(/\/live\?sort=viewers&q=%24major$/);
    await expect(page.getByLabel("Sort captured cards")).toHaveValue("viewers");
    await expect(page.getByTestId("archived-stream-card")).toHaveCount(1);
    await expect(search).toHaveValue("$major");
  } finally {
    await page.unrouteAll({ behavior: "ignoreErrors" });
  }
});

test("delayed clear preserves the next archive search draft and URL history", async ({
  page,
}) => {
  await page.goto("/live?q=previous", { waitUntil: "networkidle" });
  const input = page.locator("#live-search");
  await expect(input).toHaveValue("previous");
  const held: Route[] = [];
  let hold = true;
  await page.route("**/live?**", async (route) => {
    if (hold && new URL(route.request().url()).searchParams.has("_rsc"))
      held.push(route);
    else await route.continue();
  });
  try {
    await page.getByRole("button", { name: "Clear", exact: true }).click();
    await expect.poll(() => held.length).toBeGreaterThan(0);
    await input.fill("new draft");
    hold = false;
    await Promise.all(held.map((route) => route.continue()));
    await expect(page).toHaveURL(/\/live$/);
    await expect(input).toHaveValue("new draft");
    await input.press("Enter");
    await expect(page).toHaveURL(/\/live\?q=new\+draft$/);
    await page.goBack();
    await expect(page).toHaveURL(/\/live$/);
    await expect(input).toHaveValue("");
    await page.goForward();
    await expect(input).toHaveValue("new draft");
  } finally {
    await page.unrouteAll({ behavior: "ignoreErrors" });
  }
});
