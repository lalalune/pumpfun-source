import "server-only";

import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import {
  type LiveArchiveSection,
  type LiveSnapshot,
  verifyLiveEvidence,
} from "./live-data";

const evidenceRoot = resolve(process.cwd(), "../../evidence");
const capturePath = resolve(evidenceRoot, "web/objects/c45d40b52df03727");
const manifestPath = resolve(evidenceRoot, "web/manifest.json");

export type LiveEvidenceResult =
  | { ok: true; snapshot: LiveSnapshot }
  | { ok: false; error: string };

export async function loadLiveEvidence(
  section: LiveArchiveSection = "most-viewers",
): Promise<LiveEvidenceResult> {
  try {
    const [bytes, manifestText] = await Promise.all([
      readFile(capturePath),
      readFile(manifestPath, "utf8"),
    ]);
    return {
      ok: true,
      snapshot: verifyLiveEvidence(bytes, JSON.parse(manifestText), section),
    };
  } catch (error) {
    return {
      ok: false,
      error:
        error instanceof Error
          ? error.message
          : "Unknown Live evidence validation failure",
    };
  }
}
