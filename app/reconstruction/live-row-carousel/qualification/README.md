# Frozen row-carousel qualification

The initial source/method `c56bbf3d` was adjusted before any browser execution to count only the actual scroll-root listener, excluding React's unrelated root event listeners. `5e127c26` pins the six passing focused Node/source/SSR/portable cases and the first browser attempt: **six passing observations then a resize assertion failure**. `f8a263c8` pins the corrected method's **eight-observation PASS**. The first six observations are repeated controls, not14 unique successes. All three complete source snapshots and both exact method diffs are retained.

The initial assertion assumed the pre-resize scroll offset was the offset read by the source callback. The corrected method passively records callback-time offset/first-child width/gap, forwards the native callback unchanged, and checks its actual instant-scroll formula. In the corrected run the source read1632, width392+gap16, then issued1632. The initial failed run's callback-time operands were not measured. Native CSS adjustment is a plausible cause, not an established retroactive explanation. Product adapter, generator, provenance, README and Node tests stayed byte-identical between the two browser cohorts.

Both attempts retain inputs, full emitted bundle bytes (compressed), raw results, traces, cleanup and failure screenshot where applicable. All14 inputs per bundle and controller/proof hashes are bound. Only host HTML/bundle GETs occurred; no page errors. Both browsers disconnected and hosts stopped. The first phase exercises actual main Rows; the second is explicitly an authored genericCarousel selected/snap caller, since main Rows does not supply those props.

The source verifier, six unique focused Node cases, app698/npm/SDK, progress check/nine tests, required53Git/9capture/10tooling checks passed. Initial sparse-input progress failure, exact three-file Git hydration and successful check remain separate. No new source/runtime result is implied by later docs/packet additions.

The geometry CSS, Card and instrumentation are authored test infrastructure. Native observer/scroll implementations and React/compiler are real; no captured factory, original Card/CSS, media, navigation, provider, account or application executes. This is no mounted/native/visual/API/security acceptance.

Public replay commands are repository-relative in the parent README. Historical absolute log paths are observations, not required private inputs. To check this packet's current bytes from repository root:

```sh
python3 - <<'PY'
import pathlib,json,hashlib
q=pathlib.Path('app/reconstruction/live-row-carousel/qualification')
for r in json.loads((q/'MANIFEST.json').read_text())['files']:
 b=(q/r['path']).read_bytes()
 assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'],r['path']
print('qualification bytes PASS')
PY
```
