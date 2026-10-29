import {
  LIVE_CAPTURE_SHA256,
  LiveEvidenceError,
  type ArchivedStream,
  type LiveSnapshot,
  parseLiveCapture,
  unescapeFlightStrings,
  validateArchivedStream,
  verifyLiveEvidence,
} from "./live-data";

export const LIVE_ARCHIVED_HERO_COUNT = 6;

// Parse retained Flight JSON only. Hero DTOs have mint, but no id/linkUrl.
// A local metadata identity derives from that mint, as the original carousel's
// actual keyed consumer does. No media or nested coin data leaves this adapter.
export function parseLiveHeroCapture(
  bytes: Uint8Array,
  expectedSha256 = LIVE_CAPTURE_SHA256,
): ArchivedStream[] {
  // Reuse full capture/hash/UTF-8 admission and the known 42-card inventory.
  const mostViewers = parseLiveCapture(bytes, expectedSha256);
  const known = new Map(mostViewers.map((stream) => [stream.mint, stream]));
  const source = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  const pushMatch = source.match(
    /<script>self\.__next_f\.push\(([\s\S]*?)\)<\/script>/u,
  );
  if (!pushMatch)
    throw new LiveEvidenceError("Captured hero Flight push is missing");
  const push = JSON.parse(pushMatch[1]);
  const payload = push[1] as string;
  const marker = '"initialHeroData":';
  if (payload.indexOf(marker) !== payload.lastIndexOf(marker)) {
    throw new LiveEvidenceError("Captured hero Flight data is ambiguous");
  }
  const rows = payload.split("\n");
  const matching = rows.filter((row) => row.includes('"initialHeroData":'));
  if (matching.length !== 1) {
    throw new LiveEvidenceError(
      "Captured hero Flight row is missing or ambiguous",
    );
  }
  let data: unknown;
  try {
    const value = JSON.parse(matching[0].slice(matching[0].indexOf(":") + 1));
    if (value[1]?.[1] !== "$L116") throw new Error("Unknown hero consumer");
    data = value[1][3].initialHeroData;
  } catch {
    throw new LiveEvidenceError("Captured hero Flight row is invalid");
  }
  if (!Array.isArray(data) || data.length !== LIVE_ARCHIVED_HERO_COUNT) {
    throw new LiveEvidenceError("Captured hero record count does not match");
  }
  const streams = data.map((raw) => {
    const value = unescapeFlightStrings(raw);
    if (
      typeof value !== "object" ||
      value === null ||
      Array.isArray(value) ||
      "id" in value ||
      "linkUrl" in value
    ) {
      throw new LiveEvidenceError("Captured hero metadata shape is invalid");
    }
    const record = value as Record<string, unknown>;
    const projected = validateArchivedStream({ ...record, id: record.mint });
    const existing = known.get(projected.mint);
    if (
      !existing ||
      Object.keys(projected).some(
        (key) =>
          projected[key as keyof ArchivedStream] !==
          existing[key as keyof ArchivedStream],
      )
    ) {
      throw new LiveEvidenceError(
        "Captured hero metadata differs from its known archived identity",
      );
    }
    return projected;
  });
  if (new Set(streams.map((stream) => stream.mint)).size !== streams.length) {
    throw new LiveEvidenceError("Captured hero contains duplicate identities");
  }
  return streams;
}

export function verifyLiveHeroEvidence(
  bytes: Uint8Array,
  manifest: unknown,
): LiveSnapshot {
  const snapshot = verifyLiveEvidence(bytes, manifest);
  return { ...snapshot, streams: parseLiveHeroCapture(bytes) };
}
