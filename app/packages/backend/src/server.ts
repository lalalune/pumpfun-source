import { loadCalloutDiscussionsStore } from './callout-discussions-store.js';
import { buildApp, type Fixture } from './app.js';
import { readFileSync } from 'node:fs';
import { loadCalloutsStore } from './callouts-store.js';
import { loadPositionsStore } from './positions-store.js';
import { loadPayoutsStore } from './payouts-store.js';
import { loadUserTradesStore } from './user-trades-store.js';
import { startWithLocalMedia } from './local-media-runtime.js';
import { loadPortfolioBalancesStore } from './portfolio-balances-store.js';
import { loadHolderRewardsStore } from './holder-rewards-store.js';
// The sibling startup loaders (callouts, positions, portfolio balances) all
// reject malformed UTF-8 with a fatal decoder. Fixtures must fail the same
// way: a lossy "utf8" read would silently replace corrupted bytes with
// U+FFFD and start the server serving altered replay content.
const fixtures: Fixture[] = process.env.FIXTURES_FILE ? JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(readFileSync(process.env.FIXTURES_FILE))) : [];
const portfolioBalancesStore = process.env.PORTFOLIO_BALANCES_FILE ? loadPortfolioBalancesStore(process.env.PORTFOLIO_BALANCES_FILE) : undefined;
const calloutsStore = process.env.CALLOUTS_FILE ? loadCalloutsStore(process.env.CALLOUTS_FILE) : undefined;
if (process.env.CALLOUT_DISCUSSIONS_FILE && !calloutsStore) throw new Error('CALLOUT_DISCUSSIONS_FILE requires CALLOUTS_FILE');
const calloutDiscussionsStore = process.env.CALLOUT_DISCUSSIONS_FILE ? loadCalloutDiscussionsStore(process.env.CALLOUT_DISCUSSIONS_FILE, calloutsStore!) : undefined;
const positionsStore = process.env.POSITIONS_FILE ? loadPositionsStore(process.env.POSITIONS_FILE) : undefined;
const payoutsStore = loadPayoutsStore(process.env.PAYOUTS_FILE);
const userTradesStore = process.env.TRADES_FILE ? loadUserTradesStore(process.env.TRADES_FILE) : undefined;
const holderRewardsStore = loadHolderRewardsStore(process.env.HOLDER_REWARDS_FILE);
const app = await startWithLocalMedia(process.env, async (localMedia) => {
  const app = buildApp(fixtures, { calloutsStore, calloutDiscussionsStore, positionsStore, payoutsStore, userTradesStore, portfolioBalancesStore, holderRewardsStore, localMedia });
  try {
    await app.listen({ host: process.env.HOST ?? '127.0.0.1', port: Number(process.env.PORT ?? 3001) });
  } catch (startupError) {
    try { await app.close(); }
    catch (cleanupError) { throw new AggregateError([startupError, cleanupError], 'Server startup and cleanup both failed.'); }
    throw startupError;
  }
  return app;
});
for (const signal of ['SIGINT','SIGTERM']) process.on(signal, () => { void app.close(); });
