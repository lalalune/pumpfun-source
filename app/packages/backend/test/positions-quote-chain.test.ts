import assert from 'node:assert/strict';
import { test } from 'node:test';
import { buildApp } from '../src/app.js';
import { PositionsStore, type PositionsDataset, type Callout } from '../src/positions-store.js';

function dataset(outer: string | undefined, inner: string | null | undefined): PositionsDataset {
  const now = '2026-10-28T00:00:00.000Z';
  const callout = (): Callout => ({
    calloutId:'callout-a',calledOutAtMcap:100,multiple:1,thesis:'Synthetic',mediaUrl:null,calloutTimestamp:now,likes:0,hasLiked:null,updates:[],updateCount:0,commentCount:0,replyCount:0,maxMultiplier:null,maxMultiplierAt:null,calloutPrice:1,repostCount:0,quoteCount:0,hasReposted:null,actingUserId:null,actingUser:null,quotedCallout:null,
  });
  const body = callout();
  body.chain = 'solana:mainnet';
  body.quotedCallout = {
    coinMint:'quoted-mint',walletAddress:null,userId:null,userName:null,profileImage:null,isVerified:false,verifiedBadgeVisible:false,accountKind:'person',xUsername:null,xFollowerCount:0,mediaUrl:null,
    ...(outer === undefined ? {} : {chain:outer}),
    callout:{...callout(),calloutId:'quoted-callout',...(inner === undefined ? {} : {chain:inner})},
  };
  return {
    schemaVersion:1,dataSource:'synthetic',observedAt:now,
    subjects:[{kind:'person',id:'person-a',aliases:[],positions:[{
      facts:{coinMint:'mint-a',chainId:101,chain:'solana:mainnet',isExited:false,walletAddress:'synthetic-wallet-a',amountHeld:1,pnlUsd:null,pnlPercentage:null,costBasisAmount:null,costBasisUsd:null,amountBoughtUsd:null,amountBought:null,tokenPriceUsd:null},
      calloutId:'callout-a',
    }]}],
    coins:[],callouts:[{authorId:'person-a',updatesComplete:true,body}],updates:[],
  };
}

test('the two chain identities of one nested quote must agree when both are known', () => {
  for (const [outer, inner] of [['eip155:8453','eip155:1'], ['solana:mainnet','eip155:8453']]) {
    assert.throws(() => new PositionsStore(dataset(outer, inner)), /quoted callout envelope\/body chain mismatch/);
  }
});

test('cross-chain quote targets and unknown quote-chain knowledge survive real HTTP reads', async () => {
  const pairs: Array<[string | undefined, string | null | undefined]> = [
    ['eip155:8453','eip155:8453'],
    ['eip155:8453',null],
    ['eip155:8453',undefined],
    [undefined,'eip155:8453'],
    [undefined,null],
  ];
  for (const [outer, inner] of pairs) {
    const app=buildApp([], {positionsStore:new PositionsStore(dataset(outer,inner))});
    try {
      for (const url of ['/v1/user-positions/person-a?mints=mint-a&updatesLimit=0', '/v1/user-portfolio/person-a']) {
        const response=await app.inject({url,headers:{authorization:`Bearer pf_live_${'A'.repeat(49)}`}});
        assert.equal(response.statusCode,200);
        const row=response.json().positions[0];
        assert.equal(row.chain,'solana:mainnet');
        assert.equal(row.callout.chain,'solana:mainnet');
        const quote=row.callout.quotedCallout;
        assert.equal(quote.chain,outer);
        assert.equal(quote.callout.chain,inner);
        assert.equal(Object.hasOwn(quote,'chain'),outer!==undefined);
        assert.equal(Object.hasOwn(quote.callout,'chain'),inner!==undefined);
      }
    } finally {await app.close();}
  }
});
