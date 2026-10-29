import { test, expect } from "@playwright/test";

test("offline SDK instruction can be inspected, invalidated and cleared without network side effects", async ({
  page,
}) => {
  const external: string[] = [];
  page.on("request", (request) => {
    if (
      !request.url().startsWith("http://127.0.0.1:3010") &&
      !request.url().startsWith("blob:")
    )
      external.push(request.url());
  });
  await page.goto("/create");
  await page.getByLabel(/^Coin name/).fill("Offline example");
  await page.getByLabel(/^Ticker/).fill("EXAMPLE");
  await page
    .getByText("Inspect unsigned SDK create instruction", { exact: true })
    .click();
  await page.getByRole("button", { name: "Build unsigned preview" }).click();
  await expect(page.getByText(/mint: enter a canonical/)).toBeVisible();
  await page
    .getByLabel("Proposed mint public key")
    .fill("So11111111111111111111111111111111111111112");
  await page
    .getByLabel("Creator public key")
    .fill("11111111111111111111111111111111");
  await page
    .getByLabel("Payer public key")
    .fill("Vote111111111111111111111111111111111111111");
  await page
    .getByLabel("Existing metadata URI (not fetched)")
    .fill("https://example.invalid/metadata.json");
  await page.getByRole("button", { name: "Build unsigned preview" }).click();
  const output = page.getByTestId("create-instruction-json");
  await expect(output).toBeVisible();
  const result = JSON.parse((await output.textContent())!);
  expect(result.dataHex).toMatch(/^d6904cec5f8b31b4/);
  expect(result.accounts).toHaveLength(16);
  expect(
    result.accounts.filter((a: { isSigner: boolean }) => a.isSigner),
  ).toHaveLength(2);
  await page
    .getByLabel("Existing metadata URI (not fetched)")
    .fill("javascript:alert(1)");
  await expect(output).toHaveCount(0);
  await page.getByRole("button", { name: "Build unsigned preview" }).click();
  await expect(page.getByText(/Metadata URI: use HTTPS/)).toBeVisible();
  await page.getByRole("button", { name: "Clear instruction inputs" }).click();
  await expect(page.getByLabel("Proposed mint public key")).toHaveValue("");
  await expect(output).toHaveCount(0);
  await page
    .getByLabel("Proposed mint public key")
    .fill("So11111111111111111111111111111111111111112");
  await page.getByLabel(/^Coin name/).fill("Changed draft");
  await page
    .getByText("Inspect unsigned SDK create instruction", { exact: true })
    .click();
  await expect(page.getByLabel("Proposed mint public key")).toHaveValue("");
  await expect(
    page.getByRole("button", {
      name: "Launch unavailable in local reconstruction",
    }),
  ).toBeDisabled();
  expect(external).toEqual([]);
});
