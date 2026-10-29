import test from 'node:test';
import assert from 'node:assert/strict';
import { UserStore, SYNTHETIC_SEED, type User } from '../src/users-store.js';

const row = SYNTHETIC_SEED[0];
for (const field of ['is_banned', 'is_pump_user'] as const) {
  test(`provided ${field} remains a boolean rather than a truthy seed value`, () => {
    for (const value of ['false', 0, 1, null]) {
      assert.throws(() => new UserStore([{ ...row, [field]: value } as unknown as User]), /User .* must be a boolean/);
    }
    for (const value of [true, false, undefined]) {
      const store = new UserStore([{ ...row, [field]: value }]);
      assert.equal(store.getById(row.address)![field], value);
    }
  });
}

test('a supplied account kind cannot be an unsupported classification', () => {
  for (const kind of ['robot', '', null, false]) {
    assert.throws(() => new UserStore([{ ...row, kind } as unknown as User]), /Invalid user kind/);
  }
  for (const kind of ['person', 'group', undefined] as const) {
    assert.equal(new UserStore([{ ...row, kind }]).getById(row.address)!.kind, kind);
  }
});

test('an explicit false ban remains false through the actual overview projection', () => {
  const store = new UserStore([{ ...row, is_banned: false }]);
  assert.equal(store.getOverview(row.address)!.banned, false);
  assert.equal(store.getOverview(row.address)!.profile!.is_banned, false);
});
