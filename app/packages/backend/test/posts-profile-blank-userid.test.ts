import test from 'node:test';
import assert from 'node:assert/strict';
import { PostStore, userToProfile, type RawPost } from '../src/posts-store.js';
import { UserStore, type User } from '../src/users-store.js';

const blankUser: User = {
  address: 'BlankWallet1111111111111111111111111111',
  userId: '',
  username: 'blank_id_user',
  profile_image: null,
  bio: null,
  followers: 3,
  following: 1,
  x_username: null,
};
const normalUser: User = {
  address: 'NormalWallet222222222222222222222222222',
  userId: 'user-normal',
  username: 'normal_user',
  profile_image: null,
  bio: null,
  followers: 3,
  following: 1,
  x_username: null,
};

test('profiles fall back to the wallet when the stored userId is blank', () => {
  const users = new UserStore([blankUser, normalUser], []);
  // UserStore treats a blank userId as absent: it is not indexed as an identity.
  assert.equal(users.getById(''), undefined);
  assert.equal(userToProfile(blankUser, false).userId, blankUser.address);
  assert.equal(userToProfile(normalUser, false).userId, 'user-normal');

  const post: RawPost = {
    postId: 'post-blank-1',
    authorId: blankUser.address,
    kind: 'root',
    content: 'hello',
    mediaUrl: null,
    createdAt: '2025-01-01T00:00:00.000Z',
    parentPostId: null,
    rootPostId: null,
    quotedPostId: null,
    repostedPostId: null,
    likeCount: 0,
    replyCount: 0,
    repostCount: 0,
    quoteCount: 0,
    mentions: [],
    deleted: false,
    likers: [blankUser.address],
    reposters: [blankUser.address],
  };
  const posts = new PostStore([post], users);
  assert.equal(posts.getLivePost('post-blank-1')?.author?.userId, blankUser.address);
  assert.equal(posts.getLikers('post-blank-1', {})?.likers[0]?.userId, blankUser.address);
  assert.equal(posts.getReposters('post-blank-1', {})?.reposters[0]?.userId, blankUser.address);
});
