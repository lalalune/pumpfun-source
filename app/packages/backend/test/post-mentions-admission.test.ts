import test from 'node:test';
import assert from 'node:assert/strict';
import seed from '../src/posts-seed.json' with {type:'json'};
import {PostStore, type RawPost} from '../src/posts-store.js';
import {buildApp} from '../src/app.js';

function post(mentions: unknown): RawPost {
  return {...structuredClone(seed[0]), mentions} as RawPost;
}
test('supplied mentions obey the closed array/item DTO before any post is served', () => {
  const valid = {userId:'user-002',username:'Bob',walletAddress:null};
  const sparse: unknown[] = [];
  sparse.length = 1;
  for (const mentions of [
    'wrong', 0, {},
    [null], [false], ['wrong'], [[]], sparse,
    [{...valid,userId:0}], [{...valid,username:null}], [{...valid,walletAddress:{}}],
    [{userId:'user-002',username:'Bob'}],
    [{...valid,extra:true}],
  ]) assert.throws(() => new PostStore([post(mentions)]), /Post mentions? must/);
});

test('real HTTP retains nullable/empty string mentions and existing absent-list fallback', async () => {
  for (const mentions of [[], null, undefined, [
    {userId:'',username:'',walletAddress:null},
    {userId:'unknown-user',username:'Unknown',walletAddress:''},
  ]]) {
    const raw=post(mentions);
    const store=new PostStore([raw]);
    const app=buildApp([], {postStore:store});
    try {
      const response=await app.inject({url:`/v1/posts/${raw.postId}`,headers:{authorization:`Bearer pf_live_${'A'.repeat(49)}`}});
      assert.equal(response.statusCode,200);
      assert.deepEqual(response.json().post.mentions,mentions??[]);
      if (Array.isArray(mentions) && mentions.length) {
        const before=store.getLivePost(raw.postId)!.mentions;
        (mentions[0] as {username:string}).username='mutated caller input';
        const result=store.getLivePost(raw.postId)!;
        result.mentions[0].username='mutated result';
        assert.deepEqual(store.getLivePost(raw.postId)!.mentions,before);
      }
    } finally {await app.close();}
  }
});
