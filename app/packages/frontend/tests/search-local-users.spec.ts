import { expect, test } from "@playwright/test";
import { openShellSearch } from "./shell-controls";

test("searches the local user model and opens the exact profile", async ({
  page,
}) => {
  const unexpected: string[] = [];
  page.on("request", (request) => {
    if (
      new URL(request.url()).origin !== "http://127.0.0.1:3010" ||
      !["GET", "HEAD"].includes(request.method())
    )
      unexpected.push(request.url());
  });
  await page.goto("/");
  await openShellSearch(page);
  const dialog = page.getByRole("dialog", {
    name: "Search for coins and users",
  });
  await dialog.getByRole("searchbox").fill("alice");
  await expect(
    dialog.getByRole("link", { name: "alice_pump", exact: true }),
  ).toBeVisible();
  await expect(dialog).toContainText("Local synthetic profiles");
  await dialog.getByRole("link", { name: "alice_pump", exact: true }).click();
  await expect(page).toHaveURL(/\/profile\/user-001$/);
  await expect(dialog).not.toBeVisible();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "alice_pump",
  );
  expect(unexpected).toEqual([]);
});

test("honors two UTF-16 units and the captured 500ms debounce", async ({
  page,
}) => {
  const reads: string[] = [];
  page.on("request", (request) => {
    if (request.url().includes("/api/local-users/search?"))
      reads.push(request.url());
  });
  await page.goto("/");
  await openShellSearch(page);
  await page.clock.install({ time: new Date("2026-01-01T00:00:00Z") });
  await page.clock.pauseAt(new Date("2026-01-01T00:00:01Z"));
  const input = page.getByRole("dialog").getByRole("searchbox");
  await input.fill("a");
  await page.clock.runFor(600);
  expect(reads).toEqual([]);
  await input.fill(" alice ");
  await page.clock.runFor(499);
  expect(reads).toEqual([]);
  await page.clock.runFor(1);
  await expect.poll(() => reads.length).toBe(1);
  expect(new URL(reads[0]).searchParams.get("q")).toBe("alice");
  await expect(
    page.getByRole("dialog").getByRole("link", { name: "alice_pump" }),
  ).toBeVisible();
  await input.fill("😀");
  await page.clock.runFor(500);
  await expect.poll(() => reads.length).toBe(2);
  await expect(page.getByRole("dialog")).toContainText(
    "No matching local profiles.",
  );
});

test("clears obsolete rows immediately and ignores an old response that ignores abort", async ({
  page,
}) => {
  await page.addInitScript(() => {
    const original = window.fetch.bind(window);
    (window as any).__releaseOldSearch = null;
    window.fetch = (...args) => {
      const target = String(args[0]);
      if (
        target.includes("/api/local-users/search?") &&
        new URL(target, location.origin).searchParams.get("q") === "alice"
      ) {
        return new Promise<Response>((resolve) => {
          (window as any).__releaseOldSearch = () =>
            resolve(
              new Response(
                JSON.stringify([
                  {
                    address: "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
                    userId: "user-001",
                    wallet_label: "",
                    identifier: "user-001",
                    displayName: "alice_pump",
                    kind: "person",
                    banned: false,
                  },
                ]),
                {
                  status: 200,
                  headers: { "Content-Type": "application/json" },
                },
              ),
            );
        });
      }
      return original(...args);
    };
  });
  await page.goto("/");
  await openShellSearch(page);
  const dialog = page.getByRole("dialog", {
    name: "Search for coins and users",
  });
  const input = dialog.getByRole("searchbox");
  await input.fill("alice");
  await expect
    .poll(() => page.evaluate(() => typeof (window as any).__releaseOldSearch))
    .toBe("function");
  await input.fill("bob");
  await expect(dialog.getByRole("link", { name: "alice_pump" })).toHaveCount(0);
  await expect(dialog.getByRole("link", { name: "bob_degen" })).toBeVisible();
  await page.evaluate(async () => {
    (window as any).__releaseOldSearch();
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
  await expect(dialog.getByRole("link", { name: "alice_pump" })).toHaveCount(0);
  await expect(dialog.getByRole("link", { name: "bob_degen" })).toBeVisible();
  await input.fill("no-match");
  await expect(dialog.getByRole("link", { name: "bob_degen" })).toHaveCount(0);
  await expect(dialog).toContainText("No matching local profiles.");
});

test("closed dialogs cancel pending reads and preserve the existing Escape draft", async ({
  page,
}) => {
  const reads: string[] = [];
  page.on("request", (request) => {
    if (request.url().includes("/api/local-users/search?"))
      reads.push(request.url());
  });
  await page.goto("/");
  await openShellSearch(page);
  await page.clock.install({ time: new Date("2026-01-01T00:00:00Z") });
  await page.clock.pauseAt(new Date("2026-01-01T00:00:01Z"));
  const dialog = page.getByRole("dialog", {
    name: "Search for coins and users",
  });
  await dialog.getByRole("searchbox").fill("alice");
  await page.clock.runFor(250);
  await page.keyboard.press("Escape");
  await expect(dialog).not.toBeVisible();
  await page.clock.runFor(1000);
  expect(reads).toEqual([]);
  await openShellSearch(page);
  await expect(dialog.getByRole("searchbox")).toHaveValue("alice");
  await page.clock.runFor(500);
  await expect.poll(() => reads.length).toBe(1);
  await expect(dialog.getByRole("link", { name: "alice_pump" })).toBeVisible();
});

test("shows unavailable reads without remote fallback and keeps Enter on Explore", async ({
  page,
}) => {
  await page.route("**/api/local-users/search?**", (route) =>
    route.fulfill({ status: 503, json: { error: "LOCAL_USERS_UNAVAILABLE" } }),
  );
  await page.goto("/");
  await openShellSearch(page);
  const dialog = page.getByRole("dialog", {
    name: "Search for coins and users",
  });
  await dialog.getByRole("searchbox").fill("alice");
  await expect(dialog).toContainText("Local profiles are unavailable.");
  await expect(dialog.getByRole("link")).toHaveCount(0);
  await dialog.getByRole("searchbox").press("Enter");
  await expect(page).toHaveURL(/\/explore\?q=alice$/);
});
