import { expect, test } from "@playwright/test";
import { PublicKey } from "@solana/web3.js";
import { PUMP_PROGRAM_ID, userVolumeAccumulatorPda } from "@pump-fun/pump-sdk";
const ADDRESS = "So11111111111111111111111111111111111111112";
// Existing public-record DTO. No new service/API/SDK behavior is introduced.
function record() {
  return {
    ok: true,
    address: ADDRESS,
    programId: PUMP_PROGRAM_ID.toBase58(),
    recordPda: userVolumeAccumulatorPda(new PublicKey(ADDRESS)).toBase58(),
    cluster: "mainnet-beta",
    commitment: "confirmed",
    contextSlot: 321,
    endpointHost: "controlled-public.example",
    observedAt: "2026-10-29T05:00:00.000Z",
    dataBytes: 106,
    record: {
      user: ADDRESS,
      needsClaim: false,
      hasTotalClaimedTokens: false,
      totalUnclaimedTokens: "7",
      totalClaimedTokens: "0",
      currentSolVolume: "2",
      lastUpdateTimestamp: "0",
      cashbackEarned: "0",
      totalCashbackClaimed: "0",
      stableCashbackEarned: "0",
      totalStableCashbackClaimed: "0",
    },
  };
}
test("valid wallet activity remains explicitly inspectable when the holdings read fails", async ({
  page,
}) => {
  let recordRequests = 0;
  await page.route("**/api/portfolio?*", (route) =>
    route.fulfill({
      status: 502,
      json: {
        ok: false,
        error: {
          code: "RPC_RESPONSE_INVALID",
          message: "Token account response is unsupported.",
          retryable: false,
        },
      },
    }),
  );
  await page.route("**/api/portfolio/pump-record?*", (route) => {
    recordRequests++;
    return route.fulfill({ json: record() });
  });
  await page.goto(`/portfolio?address=${ADDRESS}`);
  await expect(page.getByRole("alert")).toContainText(
    "Token account response is unsupported.",
  );
  expect(recordRequests).toBe(0);
  const inspect = page.getByRole("button", {
    name: "Read public Pump record",
    exact: true,
  });
  await expect(inspect).toBeVisible();
  await inspect.click();
  await expect(page.getByTestId("public-pump-record-result")).toContainText(
    "controlled-public.example",
  );
  expect(recordRequests).toBe(1);
  await expect(page.locator("html")).toHaveAttribute("data-pf-auth", "out");
});
