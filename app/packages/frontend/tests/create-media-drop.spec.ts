import { test, expect, type Page } from "@playwright/test";

const PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
  "base64",
);
type LocalFile = { name: string; type: string; bytes: number[] };
const image = (name = "dropped.png"): LocalFile => ({
  name,
  type: "image/png",
  bytes: [...PNG],
});

async function drop(page: Page, files: LocalFile[], text?: string) {
  const data = await page.evaluateHandle(
    ({ files, text }) => {
      const transfer = new DataTransfer();
      for (const file of files)
        transfer.items.add(
          new File([new Uint8Array(file.bytes)], file.name, {
            type: file.type,
          }),
        );
      if (text) transfer.setData("text/uri-list", text);
      return transfer;
    },
    { files, text },
  );
  try {
    await page
      .getByRole("region", { name: "Drop local coin media" })
      .dispatchEvent("drop", { dataTransfer: data });
  } finally {
    await data.dispose();
  }
}

test.beforeEach(async ({ page }) => {
  await page.route("**/*", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    if (
      url.origin !== "http://127.0.0.1:3010" ||
      !["GET", "HEAD"].includes(request.method())
    ) {
      await route.abort();
      throw new Error(`Unexpected request: ${request.method()} ${url.origin}`);
    }
    await route.continue();
  });
});

test("dropped image is previewed; rejected multiple and URL drops retain it; file control still works", async ({
  page,
}) => {
  await page.goto("/create");
  const zone = page.getByRole("region", { name: "Drop local coin media" });
  await drop(page, [image()]);
  await expect(page.getByTestId("selected-image")).toContainText("dropped.png");
  await expect(page.locator(".preview-image")).toBeVisible();
  await drop(page, [image("one.png"), image("two.png")]);
  await expect(zone.getByRole("alert")).toContainText("exactly one");
  await drop(page, [], "https://example.invalid/not-a-local-file.png");
  await expect(zone.getByRole("alert")).toContainText("not text or a link");
  await expect(page.getByTestId("selected-image")).toContainText("dropped.png");
  await page
    .getByLabel(/^Coin image/)
    .setInputFiles({ name: "browsed.png", mimeType: "image/png", buffer: PNG });
  await expect(page.getByTestId("selected-image")).toContainText("browsed.png");
  await expect(zone.getByRole("alert")).toHaveCount(0);
  await page.getByRole("button", { name: "Reset draft", exact: true }).click();
  await expect(page.getByTestId("selected-image")).toHaveCount(0);
});

test("rejected and undecodable dropped video never replace a manually chosen image", async ({
  page,
}) => {
  await page.goto("/create");
  await drop(page, [image("manual.png")]);
  await drop(page, [{ name: "empty.mp4", type: "video/mp4", bytes: [] }]);
  await expect(
    page
      .getByRole("region", { name: "Drop local coin media" })
      .getByRole("alert"),
  ).toContainText("non-empty video");
  await drop(page, [
    {
      name: "invalid.webm",
      type: "video/webm",
      bytes: [...Buffer.from("synthetic, not video")],
    },
  ]);
  await expect(
    page.getByRole("group", { name: /^Video and cover/ }).getByRole("alert"),
  ).toContainText("could not decode");
  await expect(page.getByTestId("selected-image")).toContainText("manual.png");
  await expect(
    page.getByRole("button", {
      name: "Launch unavailable in local reconstruction",
    }),
  ).toBeDisabled();
});

test("manual drop and reset cancel a deliberately stalled dropped-video preparation", async ({
  page,
}) => {
  // Explicit lifecycle port, not a successful native-codec test.
  await page.addInitScript(() => {
    const src = Object.getOwnPropertyDescriptor(
      HTMLMediaElement.prototype,
      "src",
    )!;
    Object.defineProperty(HTMLVideoElement.prototype, "src", {
      ...src,
      set() {},
    });
    HTMLVideoElement.prototype.load = function () {};
  });
  await page.goto("/create");
  const field = page.getByRole("group", { name: /^Video and cover/ });
  const pending = {
    name: "pending.mp4",
    type: "video/mp4",
    bytes: [...Buffer.from("synthetic")],
  };
  await drop(page, [pending]);
  await expect(field.getByRole("status")).toContainText(
    "Preparing local video",
  );
  await drop(page, [image("replacement.png")]);
  await expect(field.getByRole("status")).toBeEmpty();
  await expect(page.getByTestId("selected-image")).toContainText(
    "replacement.png",
  );
  await drop(page, [pending]);
  await expect(field.getByRole("status")).toContainText(
    "Preparing local video",
  );
  await page.getByRole("button", { name: "Reset draft", exact: true }).click();
  await expect(field.getByRole("status")).toBeEmpty();
  await expect(page.getByTestId("selected-image")).toHaveCount(0);
});
