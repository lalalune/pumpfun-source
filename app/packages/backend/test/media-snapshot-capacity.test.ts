import assert from 'node:assert/strict';
import { test } from 'node:test';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, dirname, resolve } from 'node:path';
import { LocalMediaStore } from '../src/local-media-store.js';

async function temporary() {
  const root = await mkdtemp(join(tmpdir(), 'pump-media-capacity-'));
  assert.equal(dirname(root), resolve(tmpdir()));
  assert.ok(root.startsWith(join(tmpdir(), 'pump-media-capacity-')));
  return root;
}
test('quota-admitted Unicode metadata can be reopened with the same limits', async () => {
  const root = await temporary(), limits = {maxBytes: 24, maxMetadata: 16};
  let store: LocalMediaStore | undefined;
  try {
    store = await LocalMediaStore.open(root, limits);
    const png = Buffer.from('89504e470d0a1a0a0000000d494844520000000100000001', 'hex');
    const image = await store.putImage(png, 'image/png');
    const make = (prefix: string) => prefix + '漢'.repeat(2048 - prefix.length);
    const ids: string[] = [];
    for (let index = 0; index < 16; index++) ids.push((await store.putMetadata({imageId: image.id, name: `Test${index}`, symbol: 'T', description: '漢'.repeat(2000), showName: true, twitter: make('https://x.com/'), telegram: make('https://t.me/'), website: make('https://example.com/')})).id);
    await assert.rejects(store.putMetadata({imageId:image.id,name:'excess',symbol:'T',description:'',showName:true}), /quota/i);
    await store.close(); store = undefined;
    store = await LocalMediaStore.open(root, limits);
    for (const id of ids) assert.equal(store.getMetadata(id).id, id);
    assert.equal(store.getImage(image.id).content.length, 24);
  } finally { await store?.close(); await rm(root, {recursive: true, force: true}); }
});
test('many quota-admitted small images retain serialized record overhead on restart', async () => {
  const root = await temporary(), limits = {maxBytes: 5000, maxImages: 1000, maxMetadata: 1};
  let store: LocalMediaStore | undefined;
  try {
    store = await LocalMediaStore.open(root, limits);
    const ids: string[] = [];
    for (let index = 0; index < 1000; index++) ids.push((await store.putImage(Buffer.from([255,216,255,index & 255,index >> 8]), 'image/jpeg')).id);
    await store.close(); store = undefined;
    store = await LocalMediaStore.open(root, limits);
    for (const id of ids) assert.equal(store.getImage(id).content.length, 5);
  } finally { await store?.close(); await rm(root, {recursive: true, force: true}); }
});
