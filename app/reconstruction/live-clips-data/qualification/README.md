# Frozen clips/VOD qualification

All measured source and method files are pinned to local `ffe68589ed24ea14b89cddeb2fc7da9ebccf3d35`. `MEASURED-SOURCE.json` and the source tar retain all seven files. Later README/qualification additions do not relabel those executions. The public commit/tree mapping is stated in the PR.

Source verification and 11 focused Node/real-React SSR cases passed. One real-React/compiler/DOM story passed eight observations, with zero page errors and only the host HTML/bundle GETs. Required 53-input/9-capture/10-tooling gates and app698/npm/SDK passed. Progress's initial sparse-input failure is preserved separately from exact-Git hydration and the successful check; its nine tests passed. The earlier draft generator-selector diagnostic is preserved, without pretending an unavailable draft snapshot exists.

`browser-INPUTS.json`, `browser-RESULT.json`, `RUNTIME-SOURCE-BINDING.json` and the full trace bind the controller, fixture, adapter, 12 bundle inputs and emitted bundle digest. The actual host was stopped and Chromium disconnected. The bundle was recomputed only for retention after the story and its full bytes match the original runtime digest exactly; `browser-BUNDLE-RETENTION.json` describes that operation. This is not a second runtime result.

The authored client/schema/query/coin/price/clock ports are synthetic. The real browser only executes the maintained adapter and React/DOM. There is no captured execution, provider request, original Zod/parser/query runtime result, media/playback, application mount, visual/native/API/financial claim or security acceptance. Source/evidence helpers and prior listing/coordinator work retain their attribution.

All paths for public replay are repository-relative in the parent README. Absolute paths in raw historical logs/records are observations, not required inputs. To authenticate current packet bytes without any browser or private workspace:

```sh
python3 - <<'PY'
import pathlib,json,hashlib
q=pathlib.Path('app/reconstruction/live-clips-data/qualification')
for row in json.loads((q/'MANIFEST.json').read_text())['files']:
 b=(q/row['path']).read_bytes()
 assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],row['path']
print('qualification bytes PASS')
PY
```
