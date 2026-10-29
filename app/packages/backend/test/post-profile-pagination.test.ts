import test from 'node:test';
import assert from 'node:assert/strict';
import {PostStore,SYNTHETIC_POSTS_SEED} from '../src/posts-store.js';
import {UserStore} from '../src/users-store.js';
test('dangling actor IDs cannot create empty pages with hasMore',()=>{
  const userStore=new UserStore();const users=userStore.list({}).slice(0,2);
  const raw=structuredClone(SYNTHETIC_POSTS_SEED[0]);
  raw.likers=['missing-a',users[0].address,'missing-b',users[1].address,'missing-c'];
  raw.reposters=[...raw.likers];
  const store=new PostStore([raw],userStore);
  for (const method of ['getLikers','getReposters'] as const) {
    const key=method==='getLikers'?'likers':'reposters';
    const first=store[method](raw.postId,{offset:0,limit:1})!;
    assert.equal((first as any)[key][0].walletAddress,users[0].canonical_svm_wallet ?? users[0].address);
    assert.equal(first.hasMore,true);
    const second=store[method](raw.postId,{offset:1,limit:1})!;
    assert.equal((second as any)[key].length,1);
    assert.equal(second.hasMore,false);
  }
});
