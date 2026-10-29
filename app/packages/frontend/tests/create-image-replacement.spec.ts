import { expect, test } from "@playwright/test";

const PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
  "base64",
);

test("failed local image decode preserves the accepted draft image", async ({
  page,
}) => {
  const blocked: string[] = [];
  await page.route("**/*", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    if (
      url.origin !== "http://127.0.0.1:3010" ||
      !["GET", "HEAD"].includes(request.method())
    ) {
      blocked.push(`${request.method()} ${request.url()}`);
      await route.abort();
    } else await route.continue();
  });
  await page.goto("/create");
  const input = page.getByLabel(/^Coin image/);
  const preview = page.locator(".preview-image");
  await input.setInputFiles({
    name: "accepted.png",
    mimeType: "image/png",
    buffer: PNG,
  });
  await expect(page.getByTestId("selected-image")).toContainText(
    "accepted.png",
  );
  await expect
    .poll(() =>
      preview.evaluate((element) => {
        const image = element as HTMLImageElement;
        return image.complete && image.naturalWidth > 0;
      }),
    )
    .toBe(true);
  const acceptedUrl = await preview.getAttribute("src");
  await input.setInputFiles({
    name: "corrupt.png",
    mimeType: "image/png",
    buffer: Buffer.from("not PNG bytes"),
  });
  await expect(
    page.getByText("The browser could not decode this image file."),
  ).toBeVisible();
  await expect(page.getByTestId("selected-image")).toContainText(
    "accepted.png",
  );
  await expect(preview).toHaveAttribute("src", acceptedUrl!);
  await page.getByText("Inspect draft JSON").click();
  await expect(page.locator(".metadata-json pre")).toContainText(
    '"localFileName": "accepted.png"',
  );

  await input.setInputFiles({
    name: "replacement.png",
    mimeType: "image/png",
    buffer: PNG,
  });
  await expect(page.getByTestId("selected-image")).toContainText(
    "replacement.png",
  );
  await expect(page.locator("#image-error")).toHaveCount(0);
  await page.getByRole("button", { name: "Reset draft" }).click();
  await expect(page.getByTestId("selected-image")).toHaveCount(0);
  expect(blocked).toEqual([]);
});
