import assert from 'node:assert/strict';
import { test } from 'node:test';
import { buildApp } from '../src/app.js';
import { PositionsStore, type PositionsDataset } from '../src/positions-store.js';

function dataset(id: string): PositionsDataset {
  const now = '2026-10-28T00:00:00.000Z';
  return {
    schemaVersion: 1, dataSource: 'synthetic', observedAt: now,
    subjects: [{kind: 'person', id: 'person-a', aliases: [], positions: [{
      facts: {coinMint:'mint-a',chainId:101,isExited:false,walletAddress:'synthetic-wallet-a',amountHeld:1,pnlUsd:null,pnlPercentage:null,costBasisAmount:null,costBasisUsd:null,amountBoughtUsd:null,amountBought:null,tokenPriceUsd:null},
      calloutId: 'callout-a',
    }]}],
    coins: [],
    callouts: [{authorId:'person-a',updatesComplete:true,body:{
      calloutId:'callout-a',calledOutAtMcap:100,multiple:1,thesis:'Synthetic',mediaUrl:null,calloutTimestamp:now,likes:0,hasLiked:null,updates:[],updateCount:1,commentCount:0,replyCount:1,maxMultiplier:null,maxMultiplierAt:null,calloutPrice:1,repostCount:0,quoteCount:0,hasReposted:null,actingUserId:null,actingUser:null,quotedCallout:null,
    }}],
    updates: [{calloutId:'callout-a',authorId:'person-a',deleted:false,hidden:false,body:{id,content:'Synthetic update',createdAt:now,likeCount:0,mediaUrl:null,parentMessageId:'callout-a',repostCount:0}}],
  };
}
test('position update identities obey the existing nonempty control-free identity admission', () => {
  for (const id of ['', '\n', '\u0000', '\u007f']) {
    assert.throws(() => new PositionsStore(dataset(id)), /update.id must be nonempty text/, JSON.stringify(id));
  }
});
test('valid update identity is retained by the real position HTTP projection', async () => {
  const app = buildApp([], {positionsStore: new PositionsStore(dataset('update-1'))});
  try {
    const response = await app.inject({url:'/v1/user-positions/person-a?mints=mint-a&updatesLimit=1',headers:{authorization:`Bearer pf_live_${'A'.repeat(49)}`}});
    assert.equal(response.statusCode, 200);
    assert.equal(response.json().positions[0].callout.updates[0].id, 'update-1');
  } finally {await app.close();}
});
