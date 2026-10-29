import "server-only";

import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import type { LiveEvidenceResult } from "./evidence";
import { verifyLiveHeroEvidence } from "./live-hero-data";

const evidenceRoot = resolve(process.cwd(), "../../evidence");

export async function loadLiveHeroEvidence(): Promise<LiveEvidenceResult> {
  try {
    const [bytes, manifest] = await Promise.all([
      readFile(resolve(evidenceRoot, "web/objects/c45d40b52df03727")),
      readFile(resolve(evidenceRoot, "web/manifest.json"), "utf8"),
    ]);
    return {
      ok: true,
      snapshot: verifyLiveHeroEvidence(bytes, JSON.parse(manifest)),
    };
  } catch (error) {
    return {
      ok: false,
      error:
        error instanceof Error
          ? error.message
          : "Unknown hero evidence failure",
    };
  }
}
