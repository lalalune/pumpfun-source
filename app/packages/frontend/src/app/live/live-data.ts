import { createHash } from "node:crypto";

export const LIVE_CAPTURE_URL = "https://pump.fun/live";
export const LIVE_CAPTURE_PATH = "evidence/web/objects/c45d40b52df03727";
export const LIVE_CAPTURE_SHA256 =
  "aeff704c15d99482fe6e6347a92db0170dffeceb940a70e61dcc10002b006355";
export const LIVE_CAPTURE_BYTES = 785_309;

export const LIVE_CAPTURED_AT = "2026-10-28T10:48:45.546100+00:00";
export const LIVE_ARCHIVED_STREAM_COUNT = 42;
export const LIVE_HIGHEST_MARKET_CAP_COUNT = 24;
export type LiveArchiveSection = "most-viewers" | "highest-market-cap";

const allowedCardFields = new Set([
  "id",
  "mint",
  "coinCreatedTimestamp",
  "title",
  "creator",
  "marketCap",
  "thumbnail",
  "ipfsThumbnail",
  "thumbnailUpdatedAt",
  "avatarUri",
  "isLive",
  "playlistUrl",
  "viewerCount",
  "linkUrl",
  "symbol",
  "coin",
]);

type UnknownRecord = Record<string, unknown>;

export type ArchivedStream = {
  id: string;
  mint: string;
  title: string;
  symbol: string;
  creatorAddress: string;
  viewerCountAtCapture: number;
  wasLiveAtCapture: true;
};

export type LiveSnapshot = {
  capturedAt: string;
  sourceUrl: string;
  sha256: string;
  streams: ArchivedStream[];
};

export class LiveEvidenceError extends Error {
  override name = "LiveEvidenceError";
}

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function safeString(
  record: UnknownRecord,
  field: string,
  context: string,
): string {
  const value = record[field];
  if (
    typeof value !== "string" ||
    value.length === 0 ||
    value.length > 160 ||
    /[\u0000-\u001f\u007f]/u.test(value)
  ) {
    throw new LiveEvidenceError(`${context} ${field} is invalid`);
  }
  return value;
}

// Read the single retained Flight push as JSON, never as executable script.
// Registry indexes 0 and 1 are Most viewers and Highest market cap. Keep their
// captured membership/order separate; neither includes the hero records.
function decodeArchivedSection(source: string, sectionIndex: 0 | 1): unknown[] {
  const pushes = [
    ...source.matchAll(
      /<script>self\.__next_f\.push\(([\s\S]*?)\)<\/script>/gu,
    ),
  ];
  if (pushes.length !== 1) {
    throw new LiveEvidenceError("Captured Live Flight payload is not unique");
  }
  let push: unknown;
  try {
    push = JSON.parse(pushes[0][1]);
  } catch {
    throw new LiveEvidenceError("Captured Live Flight payload is invalid JSON");
  }
  if (
    !Array.isArray(push) ||
    push.length !== 2 ||
    push[0] !== 1 ||
    typeof push[1] !== "string"
  ) {
    throw new LiveEvidenceError(
      "Captured Live Flight payload shape is invalid",
    );
  }
  const payload = push[1];
  const marker = '"initialSectionData":[';
  const markerStart = payload.indexOf(marker);
  if (
    markerStart < 0 ||
    payload.indexOf(marker, markerStart + marker.length) !== -1
  ) {
    throw new LiveEvidenceError(
      "Captured Live section is missing or ambiguous",
    );
  }
  let start = markerStart + marker.length;
  for (let index = 0; index <= sectionIndex; index += 1) {
    const end = sectionEnd(payload, start);
    if (index < sectionIndex) {
      // Skip only a complete preceding array and its single JSON separator.
      const separator = /^\s*,\s*/u.exec(payload.slice(end));
      if (!separator) {
        throw new LiveEvidenceError("Captured Live section is missing");
      }
      start = end + separator[0].length;
      continue;
    }
    let section: unknown;
    try {
      section = JSON.parse(payload.slice(start, end));
    } catch {
      throw new LiveEvidenceError("Captured Live section is invalid JSON");
    }
    const count =
      sectionIndex === 0
        ? LIVE_ARCHIVED_STREAM_COUNT
        : LIVE_HIGHEST_MARKET_CAP_COUNT;
    if (!Array.isArray(section) || section.length !== count) {
      throw new LiveEvidenceError(
        "Captured Live section record count does not match",
      );
    }
    return section;
  }
  throw new LiveEvidenceError("Captured Live section is missing");
}

function sectionEnd(payload: string, start: number): number {
  if (payload[start] !== "[") {
    throw new LiveEvidenceError("Captured Live section is not an array");
  }
  let depth = 0;
  let inString = false;
  let escaped = false;
  let end = -1;
  for (
    let index = start;
    index < Math.min(payload.length, start + 250_000);
    index += 1
  ) {
    const char = payload[index];
    if (inString) {
      if (escaped) escaped = false;
      else if (char === "\\") escaped = true;
      else if (char === '"') inString = false;
      continue;
    }
    if (char === '"') inString = true;
    else if (char === "[") depth += 1;
    else if (char === "]" && --depth === 0) {
      end = index + 1;
      break;
    }
  }
  if (end < 0) {
    throw new LiveEvidenceError("Captured Live section boundary is invalid");
  }
  return end;
}

// React Flight stores a string that starts with "$" as "$$"; any other
// "$"-prefixed string is an unresolved Flight reference and is rejected.
function unescapeFlightStrings(value: unknown): unknown {
  if (typeof value === "string") {
    if (value.startsWith("$$")) return value.slice(1);
    if (value.startsWith("$")) {
      throw new LiveEvidenceError(
        "Archived stream contains an unresolved Flight reference",
      );
    }
    return value;
  }
  if (Array.isArray(value)) return value.map(unescapeFlightStrings);
  if (isRecord(value)) {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [
        key,
        unescapeFlightStrings(item),
      ]),
    );
  }
  return value;
}

export function validateArchivedStream(
  input: unknown,
  expectedMint?: string,
): ArchivedStream {
  if (!isRecord(input)) {
    throw new LiveEvidenceError("Archived stream must be an object");
  }
  const unexpected = Object.keys(input).filter(
    (field) => !allowedCardFields.has(field),
  );
  if (unexpected.length > 0) {
    throw new LiveEvidenceError(
      `Archived stream contains unexpected fields: ${unexpected.join(", ")}`,
    );
  }

  const mint = safeString(input, "mint", "Archived stream");
  const id = safeString(input, "id", "Archived stream");
  if (id !== mint || (expectedMint !== undefined && mint !== expectedMint)) {
    throw new LiveEvidenceError("Archived stream identity does not match");
  }
  if (input.isLive !== true) {
    throw new LiveEvidenceError(
      "Archived stream live-at-capture flag is invalid",
    );
  }
  if (
    typeof input.viewerCount !== "number" ||
    !Number.isSafeInteger(input.viewerCount) ||
    input.viewerCount < 0 ||
    input.viewerCount > 10_000_000
  ) {
    throw new LiveEvidenceError("Archived stream viewer count is invalid");
  }
  if (
    !isRecord(input.creator) ||
    Object.keys(input.creator).join() !== "address"
  ) {
    throw new LiveEvidenceError("Archived stream creator metadata is invalid");
  }
  if (!isRecord(input.coin)) {
    throw new LiveEvidenceError("Archived stream coin metadata is invalid");
  }
  if (input.coin.mint !== mint) {
    throw new LiveEvidenceError("Archived stream coin identity does not match");
  }

  return {
    id,
    mint,
    title: safeString(input, "title", "Archived stream"),
    symbol: safeString(input, "symbol", "Archived stream"),
    creatorAddress: safeString(
      input.creator,
      "address",
      "Archived stream creator",
    ),
    viewerCountAtCapture: input.viewerCount,
    wasLiveAtCapture: true,
  };
}

export function sha256(bytes: Uint8Array): string {
  return createHash("sha256").update(bytes).digest("hex");
}

export function parseLiveCapture(
  bytes: Uint8Array,
  expectedSha256 = LIVE_CAPTURE_SHA256,
): ArchivedStream[] {
  return parseCaptureSection(bytes, 0, expectedSha256);
}

export function parseHighestMarketCapCapture(
  bytes: Uint8Array,
  expectedSha256 = LIVE_CAPTURE_SHA256,
): ArchivedStream[] {
  return parseCaptureSection(bytes, 1, expectedSha256);
}

function parseCaptureSection(
  bytes: Uint8Array,
  sectionIndex: 0 | 1,
  expectedSha256: string,
): ArchivedStream[] {
  if (bytes.byteLength > 1_000_000) {
    throw new LiveEvidenceError("Captured Live page exceeds the size limit");
  }
  const actualSha256 = sha256(bytes);
  if (actualSha256 !== expectedSha256) {
    throw new LiveEvidenceError(
      `Captured Live page SHA-256 mismatch: expected ${expectedSha256}, received ${actualSha256}`,
    );
  }

  let source: string;
  try {
    source = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  } catch {
    throw new LiveEvidenceError("Captured Live page is not valid UTF-8");
  }

  const streams = decodeArchivedSection(source, sectionIndex).map((record) =>
    validateArchivedStream(unescapeFlightStrings(record)),
  );
  if (new Set(streams.map((stream) => stream.id)).size !== streams.length) {
    throw new LiveEvidenceError(
      "Captured Live section contains duplicate identities",
    );
  }
  // Preserve the authenticated section order. This is not a ranking formula.
  return streams;
}

export function verifyLiveEvidence(
  bytes: Uint8Array,
  manifest: unknown,
  section: LiveArchiveSection = "most-viewers",
): LiveSnapshot {
  if (!isRecord(manifest) || !Array.isArray(manifest.records)) {
    throw new LiveEvidenceError("Capture manifest records are missing");
  }
  const matches = manifest.records.filter(
    (record): record is UnknownRecord =>
      isRecord(record) && record.url === LIVE_CAPTURE_URL,
  );
  if (matches.length !== 1) {
    throw new LiveEvidenceError("Capture manifest Live record is not unique");
  }
  const record = matches[0];
  if (
    record.final_url !== LIVE_CAPTURE_URL ||
    record.status !== 200 ||
    record.path !== LIVE_CAPTURE_PATH ||
    record.bytes !== LIVE_CAPTURE_BYTES ||
    record.sha256 !== LIVE_CAPTURE_SHA256
  ) {
    throw new LiveEvidenceError(
      "Capture manifest Live provenance does not match",
    );
  }
  if (bytes.byteLength !== LIVE_CAPTURE_BYTES) {
    throw new LiveEvidenceError(
      "Captured Live page byte length does not match",
    );
  }
  if (manifest.captured_at !== LIVE_CAPTURED_AT) {
    throw new LiveEvidenceError("Capture manifest timestamp does not match");
  }

  return {
    capturedAt: manifest.captured_at,
    sourceUrl: LIVE_CAPTURE_URL,
    sha256: LIVE_CAPTURE_SHA256,
    streams:
      section === "highest-market-cap"
        ? parseHighestMarketCapCapture(bytes)
        : parseLiveCapture(bytes),
  };
}
