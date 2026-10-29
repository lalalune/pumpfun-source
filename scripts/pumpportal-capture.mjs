#!/usr/bin/env node
/**
 * pumpportal-capture.mjs
 *
 * Connects to PumpPortal WebSocket Data API and captures real-time
 * pump.fun events into a structured evidence packet.
 *
 * Cascading mode: subscribes to new token creations, then automatically
 * subscribes to trades on each newly created token to capture early
 * trading activity.
 *
 * Usage:
 *   PUMPPORTAL_API_KEY=<key> node scripts/pumpportal-capture.mjs \
 *     [--duration 300] [--output research/pumpportal-live-capture-20261028]
 */

import { createHash } from "node:crypto";
import { writeFileSync, readdirSync, readFileSync, mkdirSync } from "node:fs";
import { join, resolve } from "node:path";

import { summariseCapture } from "./pumpportal-summary.mjs";

// --------------- CLI args ---------------

const args = process.argv.slice(2);
function argVal(name, fallback) {
  const idx = args.indexOf(`--${name}`);
  return idx >= 0 && args[idx + 1] ? args[idx + 1] : fallback;
}

const API_KEY = process.env.PUMPPORTAL_API_KEY;
if (!API_KEY) {
  console.error("Error: set PUMPPORTAL_API_KEY environment variable");
  process.exit(1);
}

const DURATION_S = parseInt(argVal("duration", "300"), 10);
const OUTPUT_DIR = resolve(argVal("output", "research/pumpportal-live-capture-20261028"));

mkdirSync(OUTPUT_DIR, { recursive: true });

// --------------- WebSocket capture ---------------

const WS_URL = `wss://pumpportal.fun/api/data?api-key=${API_KEY}`;
const events = [];
const trackedTokens = new Set();
const startUtc = new Date().toISOString();
let endUtc = null;

console.log(`[capture] connecting to PumpPortal WebSocket...`);
console.log(`[capture] duration: ${DURATION_S}s, output: ${OUTPUT_DIR}`);

const ws = new WebSocket(WS_URL);

const baseSubscriptions = [
  { method: "subscribeNewToken" },
  { method: "subscribeMigration" },
];

ws.addEventListener("open", () => {
  console.log(`[capture] connected, subscribing to base feeds...`);
  for (const sub of baseSubscriptions) {
    ws.send(JSON.stringify(sub));
    console.log(`[capture]   -> ${sub.method}`);
  }
});

ws.addEventListener("message", (evt) => {
  const receivedAt = new Date().toISOString();
  try {
    const data = JSON.parse(evt.data);
    events.push({ receivedAt, data });

    // Cascade: when a new token is created, subscribe to its trades
    if (data.txType === "create" && data.mint && !trackedTokens.has(data.mint)) {
      trackedTokens.add(data.mint);
      ws.send(
        JSON.stringify({
          method: "subscribeTokenTrade",
          keys: [data.mint],
        })
      );
      if (trackedTokens.size <= 20) {
        console.log(
          `[capture] +trade sub for ${data.mint.slice(0, 8)}... (tracking ${trackedTokens.size} tokens)`
        );
      }
    }

    if (events.length % 100 === 0) {
      const elapsed = ((Date.now() - new Date(startUtc).getTime()) / 1000) | 0;
      console.log(
        `[capture] ${events.length} events | ${trackedTokens.size} tokens tracked | ${elapsed}s elapsed`
      );
    }
  } catch {
    events.push({ receivedAt, raw: evt.data });
  }
});

ws.addEventListener("error", (err) => {
  console.error(`[capture] websocket error:`, err.message || err);
});

ws.addEventListener("close", (evt) => {
  console.log(`[capture] websocket closed (code=${evt.code})`);
  finalise();
});

// Graceful shutdown
const shutdownTimer = setTimeout(() => {
  console.log(`\n[capture] duration reached, closing...`);
  ws.close();
}, DURATION_S * 1000);

process.on("SIGINT", () => {
  clearTimeout(shutdownTimer);
  console.log(`\n[capture] interrupted, closing...`);
  ws.close();
});

// --------------- Finalise ---------------

function sha256(buf) {
  return createHash("sha256").update(buf).digest("hex");
}

function finalise() {
  clearTimeout(shutdownTimer);
  endUtc = new Date().toISOString();

  console.log(`[capture] finalising: ${events.length} events, ${trackedTokens.size} tokens`);

  // Aggregate event types and per-token summaries. Mint/type labels are
  // untrusted stream values, so the helpers use null-prototype maps.
  const { typeCounts, tokenIndex } = summariseCapture(events);

  // Write events.json
  const eventsPath = join(OUTPUT_DIR, "events.json");
  writeFileSync(eventsPath, JSON.stringify(events, null, 2));

  // Write token-index.json (per-token summaries)
  const tokenIndexPath = join(OUTPUT_DIR, "token-index.json");
  writeFileSync(
    tokenIndexPath,
    JSON.stringify(Object.values(tokenIndex), null, 2)
  );

  // Write summary.json
  const summary = {
    capture: "pumpportal-websocket-cascading",
    api_endpoint: "wss://pumpportal.fun/api/data",
    subscriptions: [
      ...baseSubscriptions.map((s) => s.method),
      `subscribeTokenTrade (dynamic, ${trackedTokens.size} tokens)`,
    ],
    start_utc: startUtc,
    end_utc: endUtc,
    duration_seconds: DURATION_S,
    total_events: events.length,
    event_types: typeCounts,
    unique_tokens: trackedTokens.size,
    tokens_with_trades: Object.values(tokenIndex).filter(
      (t) => t.buys + t.sells > 0
    ).length,
  };
  const summaryPath = join(OUTPUT_DIR, "summary.json");
  writeFileSync(summaryPath, JSON.stringify(summary, null, 2));

  // Write README.md
  const readme = `# PumpPortal Live Capture — ${startUtc.slice(0, 10)}

## Scope

Real-time cascading capture of pump.fun events via the PumpPortal WebSocket
Data API. The harness subscribes to new token creations, then automatically
subscribes to early trades on each newly created token.

## Subscriptions

**Base feeds:**
${baseSubscriptions.map((s) => `- \`${s.method}\``).join("\n")}

**Dynamic feeds:**
- \`subscribeTokenTrade\` — added for each new token as it appears (${trackedTokens.size} total)

## Results

| Metric | Value |
|--------|-------|
| Start | ${startUtc} |
| End | ${endUtc} |
| Duration | ${DURATION_S}s |
| Total events | ${events.length} |
| Unique tokens | ${trackedTokens.size} |
| Tokens with trades | ${summary.tokens_with_trades} |

### Event type breakdown

${Object.entries(typeCounts)
  .sort((a, b) => b[1] - a[1])
  .map(([t, c]) => `- \`${t}\`: ${c}`)
  .join("\n")}

## Files

| File | Description |
|------|-------------|
| events.json | All captured events with receive timestamps |
| token-index.json | Per-token summary (name, symbol, trade counts, volume) |
| summary.json | Capture metadata |
| manifest.json | SHA-256 integrity hashes |
| verify.py | Standalone verification script |

## Verification

\`\`\`bash
python3 verify.py
\`\`\`

## Notes

- Data commitment level: processed (per PumpPortal FAQ, <100ms behind gRPC)
- API key is NOT stored in this packet
- All event data is public on-chain information
- Cascading subscriptions increase volume by tracking early-stage trading
`;
  writeFileSync(join(OUTPUT_DIR, "README.md"), readme);

  // Write verify.py
  const verifyPy = `#!/usr/bin/env python3
"""Verify the integrity of this evidence packet."""
import hashlib, json, os, sys

PACKET_DIR = os.path.dirname(os.path.abspath(__file__))

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    manifest_path = os.path.join(PACKET_DIR, "manifest.json")
    if not os.path.exists(manifest_path):
        print("FAIL: manifest.json missing")
        return 1

    with open(manifest_path) as f:
        manifest = json.load(f)

    errors = 0
    for rel_path, expected_hash in manifest.items():
        full = os.path.join(PACKET_DIR, rel_path)
        if not os.path.exists(full):
            print(f"FAIL: {rel_path} missing")
            errors += 1
            continue
        actual = sha256_file(full)
        if actual != expected_hash:
            print(f"FAIL: {rel_path} hash mismatch")
            print(f"  expected: {expected_hash}")
            print(f"  actual:   {actual}")
            errors += 1
        else:
            print(f"  OK: {rel_path}")

    # Check summary consistency
    summary_path = os.path.join(PACKET_DIR, "summary.json")
    events_path = os.path.join(PACKET_DIR, "events.json")
    if os.path.exists(summary_path) and os.path.exists(events_path):
        with open(summary_path) as f:
            summary = json.load(f)
        with open(events_path) as f:
            events = json.load(f)
        if summary["total_events"] != len(events):
            print(f"FAIL: summary says {summary['total_events']} events but events.json has {len(events)}")
            errors += 1
        else:
            print(f"  OK: event count consistent ({len(events)})")

    # Check token-index consistency
    token_index_path = os.path.join(PACKET_DIR, "token-index.json")
    if os.path.exists(token_index_path) and os.path.exists(events_path):
        with open(token_index_path) as f:
            token_index = json.load(f)
        with open(events_path) as f:
            events = json.load(f)
        event_mints = set()
        for e in events:
            m = e.get("data", {}).get("mint")
            if m:
                event_mints.add(m)
        index_mints = set(t["mint"] for t in token_index)
        if not index_mints.issubset(event_mints):
            print(f"FAIL: token-index has mints not in events")
            errors += 1
        else:
            print(f"  OK: token-index mints consistent ({len(index_mints)} tokens)")

    if errors:
        print(f"\\n{errors} error(s)")
        return 1
    print("\\nAll checks passed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
`;
  writeFileSync(join(OUTPUT_DIR, "verify.py"), verifyPy);

  // Build manifest (hash of every file except manifest.json itself)
  const manifest = {};
  for (const name of readdirSync(OUTPUT_DIR).sort()) {
    if (name === "manifest.json") continue;
    const full = join(OUTPUT_DIR, name);
    manifest[name] = sha256(readFileSync(full));
  }
  writeFileSync(
    join(OUTPUT_DIR, "manifest.json"),
    JSON.stringify(manifest, null, 2)
  );

  console.log(`[capture] wrote ${Object.keys(manifest).length + 1} files to ${OUTPUT_DIR}`);
  console.log(`[capture] done.`);
  process.exit(0);
}
