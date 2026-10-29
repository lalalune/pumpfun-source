import { expect, test } from "@playwright/test";

for (const direction of ["ArrowRight", "ArrowLeft"] as const) {
  test(`two ${direction} presses compose while the first feed navigation is pending`, async ({
    page,
  }) => {
    let release!: () => void;
    const held = new Promise<void>((resolve) => {
      release = resolve;
    });
    let requested = false;
    await page.route("**/*", async (route) => {
      const request = route.request();
      if (
        new URL(request.url()).searchParams.get("tab") === "following" &&
        request.headers().rsc === "1"
      ) {
        requested = true;
        await held;
      }
      await route.continue();
    });
    await page.goto("/?settings=notifications");
    await expect(
      page.getByRole("dialog", { name: "Settings", exact: true }),
    ).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(
      page.getByRole("button", { name: "Open settings", exact: true }),
    ).toBeFocused();
    const tabs = page.getByRole("tablist", { name: "Feed views" });
    const first = tabs.getByRole("tab", { name: "For you", exact: true });
    await expect(first).toHaveAttribute("aria-selected", "true");
    try {
      await first.focus();
      await expect(first).toBeFocused();
      await page.keyboard.press(direction);
      await expect.poll(() => requested).toBe(true);
      await expect(first).toHaveAttribute("aria-selected", "true");
      await page.keyboard.press(direction);
    } finally {
      release();
    }
    await page.waitForLoadState("networkidle");
    await expect(first).toHaveAttribute("aria-selected", "true");
    await expect(page).not.toHaveURL(/tab=following/);
    await expect(
      tabs.getByRole("tab", { name: "Following", exact: true }),
    ).toHaveAttribute("aria-selected", "false");
    await first.press(direction);
    const following = tabs.getByRole("tab", { name: "Following", exact: true });
    await expect(following).toHaveAttribute("aria-selected", "true");
    await expect(following).toBeFocused();
    await first.click();
    await expect(first).toHaveAttribute("aria-selected", "true");
    await page.goBack();
    await expect(following).toHaveAttribute("aria-selected", "true");
    await following.press(direction);
    await expect(first).toHaveAttribute("aria-selected", "true");
    await expect(first).toBeFocused();
  });
}

test("Live section arrows compose before the first server navigation commits", async ({
  page,
}) => {
  let release!: () => void;
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  let requested = false;
  await page.route("**/*", async (route) => {
    const request = route.request();
    if (
      new URL(request.url()).searchParams.get("section") === "other-sections" &&
      request.headers().rsc === "1"
    ) {
      requested = true;
      await held;
    }
    await route.continue();
  });
  await page.goto("/live?settings=notifications");
  await expect(
    page.getByRole("dialog", { name: "Settings", exact: true }),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(
    page.getByRole("button", { name: "Open settings", exact: true }),
  ).toBeFocused();
  const tabs = page.getByRole("tablist", { name: "Captured Live sections" });
  const first = tabs.getByRole("tab", { name: "Most viewers", exact: true });
  const second = tabs.getByRole("tab", { name: "Other sections", exact: true });
  try {
    await first.focus();
    await first.press("ArrowRight");
    await expect.poll(() => requested).toBe(true);
    await expect(second).toBeFocused();
    await second.press("ArrowRight");
  } finally {
    release();
  }
  await page.waitForLoadState("networkidle");
  await expect(first).toHaveAttribute("aria-selected", "true");
  await expect(page).not.toHaveURL(/section=other-sections/);
  await expect(first).toBeFocused();
});
