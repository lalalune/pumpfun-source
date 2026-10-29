import { symlink } from 'node:fs/promises';

/** Skip only a Windows fixture capability failure; keep rejection assertions intact. */
export async function createTestSymlink(t, target, path) {
  try {
    await symlink(target, path);
    return true;
  } catch (error) {
    if (process.platform !== 'win32' || error.code !== 'EPERM') throw error;
    t.skip('Windows symlink creation requires a capability unavailable to this test process');
    return false;
  }
}
