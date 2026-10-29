import test from "node:test";
import assert from "node:assert/strict";
import { VideoDraftSession } from "../packages/frontend/src/app/create-video-preview.ts";

// Synthetic preparation controls verify selection ownership, not codec support.
test("cancelPreparation preserves committed cover while aborting an older replacement", async () => {
  const jobs = [],
    selections = [];
  let state;
  const session = new VideoDraftSession(
    (next) => {
      state = next;
    },
    (selection) => selections.push(selection),
    () => {},
    (file, signal) =>
      new Promise((resolve) => jobs.push({ file, signal, resolve })),
  );
  const video = new File(["synthetic"], "first.mp4", { type: "video/mp4" });
  let released = 0;
  const first = {
    file: video,
    url: "blob:committed",
    covers: [
      {
        file: new File(["cover"], "cover.jpg", { type: "image/jpeg" }),
        url: "blob:cover",
        seconds: 1,
      },
    ],
    dispose() {
      released++;
    },
  };
  const initial = session.choose(video);
  jobs[0].resolve(first);
  await initial;
  const replacement = session.choose(video);
  session.cancelPreparation();
  assert.equal(jobs[1].signal.aborted, true);
  assert.equal(state.preview, first);
  assert.equal(state.selected, 0);
  assert.equal(state.pending, false);
  jobs[1].resolve({
    ...first,
    dispose() {
      released++;
    },
  });
  await replacement;
  assert.equal(selections.length, 1);
  assert.equal(state.preview, first);
  session.dispose();
  assert.equal(released, 2);
});

test("cancelPreparation without pending work does not detach an accepted cover", async () => {
  let state;
  const video = new File(["synthetic"], "first.mp4", { type: "video/mp4" });
  const preview = {
    file: video,
    url: "blob:video",
    covers: [
      { file: new File(["cover"], "cover.jpg"), url: "blob:cover", seconds: 1 },
    ],
    dispose() {},
  };
  const session = new VideoDraftSession(
    (next) => {
      state = next;
    },
    () => {},
    () => {},
    async () => preview,
  );
  await session.choose(video);
  session.cancelPreparation();
  assert.equal(state.selected, 0);
  assert.equal(state.preview, preview);
  session.dispose();
});
