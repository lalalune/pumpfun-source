import { expect, test, type Page } from "@playwright/test";
import { createHash } from "node:crypto";
import { resolve } from "node:path";

type Log = Array<Record<string, unknown>>;
const fixture = (name: string) =>
  resolve(process.cwd(), "tests/fixtures", name);

async function observe(page: Page, baseURL: string) {
  const errors: string[] = [];
  page.on("request", (request) => {
    if (
      /^https?:/u.test(request.url()) &&
      (new URL(request.url()).origin !== new URL(baseURL).origin ||
        !["GET", "HEAD"].includes(request.method()))
    )
      errors.push(`${request.method()} ${request.url()}`);
  });
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  page.on("pageerror", (error) => errors.push(error.message));
  await page.addInitScript(() => {
    const log: Array<Record<string, unknown>> = [];
    (window as unknown as { videoAudit: typeof log }).videoAudit = log;
    for (const type of ["input", "change"])
      document.addEventListener(
        type,
        (event) => {
          const target = event.target;
          if (
            target instanceof HTMLInputElement &&
            target.id === "create-video"
          )
            log.push({
              type,
              trusted: event.isTrusted,
              files: Array.from(target.files ?? []).map((file) => ({
                name: file.name,
                bytes: file.size,
                type: file.type,
              })),
              time: performance.now(),
            });
        },
        true,
      );
    const value = Object.getOwnPropertyDescriptor(
      HTMLInputElement.prototype,
      "value",
    )!;
    Object.defineProperty(HTMLInputElement.prototype, "value", {
      ...value,
      set(next: string) {
        if (this.id === "create-video")
          log.push({
            type: "value-set",
            value: next,
            files: this.files?.length,
            time: performance.now(),
          });
        value.set!.call(this, next);
      },
    });
    const create = URL.createObjectURL;
    URL.createObjectURL = function (blob) {
      const url = create.call(URL, blob);
      log.push({
        type: "object-url",
        url,
        mediaType: blob instanceof Blob ? blob.type : null,
        name: blob instanceof File ? blob.name : null,
        time: performance.now(),
      });
      return url;
    };
  });
  return errors;
}

async function snapshot(page: Page) {
  return page.evaluate(() => {
    const input = document.querySelector<HTMLInputElement>("#create-video");
    const preview = document.querySelector<HTMLVideoElement>(
      'video[aria-label="Local draft video preview"]',
    );
    return {
      log: (window as unknown as { videoAudit: Log }).videoAudit,
      files: Array.from(input?.files ?? []).map((file) => ({
        name: file.name,
        type: file.type,
        bytes: file.size,
      })),
      inputDisabled: input?.disabled,
      preview: preview
        ? {
            duration: preview.duration,
            width: preview.videoWidth,
            height: preview.videoHeight,
            readyState: preview.readyState,
            src: preview.currentSrc,
          }
        : null,
    };
  });
}

async function closedLocalShell(page: Page) {
  // Existing closed-browser fixture, not an inference of original/user consent.
  await expect(page.locator("[data-clickwrap-overlay]")).toHaveCount(0);
  await expect(page.locator("[data-app-shell]")).not.toHaveAttribute("inert");
}

async function pick(page: Page, name: string) {
  const chooser = page.waitForEvent("filechooser");
  await page.getByLabel("Local video", { exact: true }).click();
  await (await chooser).setFiles(fixture(name));
}

async function threeNativeCovers(page: Page) {
  await expect(
    page
      .getByRole("group", { name: "Video cover choices" })
      .getByRole("button"),
  ).toHaveCount(3, { timeout: 15000 });
  await expect(page.getByTestId("selected-image")).toContainText(
    "video-cover-1.jpg",
  );
  const state = await snapshot(page);
  expect(state.preview?.duration).toBe(2);
  expect(state.preview?.width).toBe(64);
  expect(state.preview?.height).toBe(64);
}

async function earliestAdmittedSelection(
  page: Page,
  name: string,
  label: string,
  outcome: () => Promise<void>,
) {
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  const pattern = "**/_next/static/chunks/**";
  const held: Array<{ url: string; bytes: number; sha256: string }> = [];
  const handler = async (route: import("@playwright/test").Route) => {
    const response = await route.fetch();
    const bytes = await response.body();
    const text = bytes.toString("utf8");
    if (
      text.includes("create-video-input.tsx") &&
      text.includes("Local video")
    ) {
      held.push({
        url: route.request().url(),
        bytes: bytes.length,
        sha256: createHash("sha256").update(bytes).digest("hex"),
      });
      await gate;
    }
    // Standard transparent forwarding: no response or media bytes are changed.
    await route.fulfill({ response });
  };
  await page.route(pattern, handler);
  try {
    await page.goto("/create", { waitUntil: "commit" });
    await expect.poll(() => held.length).toBeGreaterThan(0);
    const input = page.getByLabel("Local video", { exact: true });
    const initiallyEnabled = await input.isEnabled();
    let chooserEvents = 0;
    const countChooser = () => {
      chooserEvents += 1;
    };
    page.on("filechooser", countChooser);
    if (initiallyEnabled) {
      // A currently enabled native control admits the user's first choice now.
      await pick(page, name);
    } else {
      // A not-ready control must actually block the native picker, then allow
      // exactly one choice after its real consumer becomes ready.
      await expect(input).toBeDisabled();
      await expect(
        page.getByText("Loading local video controls…", { exact: true }),
      ).toBeVisible();
      await input.scrollIntoViewIfNeeded();
      const box = await input.boundingBox();
      expect(box).not.toBeNull();
      await page.mouse.click(box!.x + box!.width / 2, box!.y + box!.height / 2);
      expect(chooserEvents).toBe(0);
    }
    const before = await snapshot(page);
    await test
      .info()
      .attach(`${label}-before.json`, {
        body: JSON.stringify(
          { held, initiallyEnabled, chooserEvents, before },
          null,
          2,
        ),
        contentType: "application/json",
      });
    expect(before.files).toHaveLength(initiallyEnabled ? 1 : 0);
    release();
    await closedLocalShell(page);
    // Prove that the actual form handler works after bootstrap, not just that
    // an unrelated shell hydrated while this chunk failed to execute.
    await page
      .getByRole("textbox", { name: "Coin name", exact: true })
      .fill("Video timing probe");
    await expect(page.locator(".metadata-json pre")).toContainText(
      '"name": "Video timing probe"',
    );
    await expect(input).toBeEnabled();
    if (!initiallyEnabled) await pick(page, name);
    try {
      await outcome();
    } finally {
      await test
        .info()
        .attach(`${label}-after.json`, {
          body: JSON.stringify(
            {
              held,
              initiallyEnabled,
              chooserEvents,
              after: await snapshot(page),
            },
            null,
            2,
          ),
          contentType: "application/json",
        });
      page.off("filechooser", countChooser);
    }
  } finally {
    release();
    if (!page.isClosed()) await page.unroute(pattern, handler);
  }
}

test("a ready native video choice genuinely decodes three JPEG covers", async ({
  page,
  baseURL,
}) => {
  const errors = await observe(page, baseURL!);
  await page.goto("/create");
  await closedLocalShell(page);
  await pick(page, "native-2s.webm");
  await threeNativeCovers(page);
  await expect(
    page.getByRole("button", {
      name: "Launch unavailable in local reconstruction",
    }),
  ).toBeDisabled();
  await test
    .info()
    .attach("ready-native.json", {
      body: JSON.stringify({ state: await snapshot(page), errors }, null, 2),
      contentType: "application/json",
    });
  expect(errors).toEqual([]);
});

test("the earliest admitted native choice works with delayed client code at both widths", async ({
  page,
  baseURL,
}) => {
  const errors = await observe(page, baseURL!);
  for (const width of [390, 1280]) {
    await page.setViewportSize({ width, height: 900 });
    await earliestAdmittedSelection(
      page,
      "native-2s.webm",
      `valid-${width}`,
      () => threeNativeCovers(page),
    );
    await test
      .info()
      .attach(`ready-${width}.png`, {
        body: await page.screenshot(),
        contentType: "image/png",
      });
  }
  expect(errors).toEqual([]);
});

test("earliest admission retains empty-video rejection without starting a decoder", async ({
  page,
  baseURL,
}) => {
  const errors = await observe(page, baseURL!);
  await earliestAdmittedSelection(page, "empty.webm", "empty", async () => {
    const field = page.getByRole("group", { name: /^Video and cover/ });
    await expect(field.getByRole("alert")).toContainText("non-empty video");
    await expect(
      page.getByLabel("Local video", { exact: true }),
    ).toHaveAttribute("aria-invalid", "true");
    await expect(
      page.getByRole("group", { name: "Video cover choices" }),
    ).toHaveCount(0);
    expect(
      (await snapshot(page)).log.filter((event) => event.type === "object-url"),
    ).toHaveLength(0);
  });
  expect(errors).toEqual([]);
});
