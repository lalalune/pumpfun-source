// Complete ordinary shared-search group readers and used schema/projection constructors. Required API/runtime capabilities only.
function schema0(ports) {
  const t = { contract: ports.contract };
  const r = { z: ports.z };
  let s = (e) => (e?.toLowerCase() === "group" ? "group" : "person");
  let o = r.z.string().nullish();
  let d = t.contract["GET /groups/search"].response.shape.results.element;
  let u = d
    .pick({ userId: !0 })
    .extend({
      username: d.shape.username.nullish(),
      bio: d.shape.bio.nullish(),
      profileImageUrl: d.shape.profileImageUrl.nullish(),
      headerImageUrl: d.shape.headerImageUrl.nullish(),
      followerCount: d.shape.followerCount.nullish(),
      followingCount: d.shape.followingCount.nullish(),
      createdAt: d.shape.createdAt.nullish(),
      updatedAt: d.shape.updatedAt.nullish(),
      walletAddress: d.shape.walletAddress.nullish(),
      isVerified: d.shape.isVerified.nullish(),
      verifiedBadgeVisible: d.shape.verifiedBadgeVisible.nullish(),
      resolvedAvatarDecoration: d.shape.resolvedAvatarDecoration.nullish(),
      memberCount: d.shape.memberCount.nullish(),
      kind: o,
    })
    .transform((e) => ({
      userId: e.userId,
      username: e.username ?? "",
      bio: e.bio || null,
      profileImage: e.profileImageUrl || null,
      headerImageUrl: e.headerImageUrl || null,
      walletAddress: e.walletAddress || null,
      followers: e.followerCount ?? 0,
      following: e.followingCount ?? 0,
      isVerified: e.isVerified ?? !1,
      verifiedBadgeVisible: !1 !== e.verifiedBadgeVisible,
      resolvedAvatarDecoration: e.resolvedAvatarDecoration ?? null,
      kind: s(e.kind),
      memberCount: e.memberCount ?? 0,
      createdAt: e.createdAt ?? null,
      updatedAt: e.updatedAt ?? null,
    }));
  let y = t.contract["GET /users/{id}"].response;
  let b = y.pick({}).extend({
    address: y.shape.address.nullish(),
    userId: y.shape.userId.nullish(),
    username: y.shape.username.nullish(),
    profile_image: y.shape.profile_image.nullish(),
    header_image_url: y.shape.header_image_url.nullish(),
    member_count: y.shape.member_count.nullish(),
    bio: y.shape.bio.nullish(),
    followers: y.shape.followers.nullish(),
    following: y.shape.following.nullish(),
    kind: o,
    active_competition_entry: y.shape.active_competition_entry,
  });
  let v = t.contract["GET /groups/search"].response.extend({
    results: u.array(),
  });
  return {
    D: u,
    Q: b,
    A: (e) => v.parse(e).results,
    h: (e) => ({
      groupId: e.userId,
      username: e.username || null,
      bio: e.bio,
      profileImage: e.profileImage,
      headerImageUrl: e.headerImageUrl,
      memberCount: e.memberCount,
      followers: e.followers,
      following: e.following,
      activeCompetitionEntry: null,
    }),
    t: ({ row: e, groupId: t }) => ({
      groupId: t,
      username: e.username ?? null,
      bio: e.bio ?? null,
      profileImage: e.profile_image ?? null,
      headerImageUrl: e.header_image_url ?? null,
      memberCount: e.member_count ?? 0,
      followers: e.followers ?? 0,
      following: e.following ?? 0,
      activeCompetitionEntry: e.active_competition_entry
        ? {
            competitionId: e.active_competition_entry.competition_id,
            competitionSlug: e.active_competition_entry.competition_slug,
            entryId: e.active_competition_entry.entry_id,
            phase: e.active_competition_entry.phase,
          }
        : null,
    }),
  };
}
function reader0(schema) {
  const u = schema;
  let m = async ({ api: e, groupId: t, signal: r }) => {
    let l = await e("GET /users/{id}", { params: { id: t }, signal: r });
    return (0, u.t)({ row: u.Q.parse(l), groupId: t });
  };
  let p = 20;
  let h = async ({
    api: e,
    searchTerm: t,
    offset: r,
    limit: l = p,
    signal: i,
  }) => {
    let a = await e("GET /groups/search", {
      query: { searchTerm: t, limit: l, offset: r },
      signal: i,
    });
    return (0, u.A)(a);
  };
  return { N: m, B: h };
}
function schema1(ports) {
  const t = { contract: ports.contract };
  const r = { z: ports.z };
  let s = (e) => (e?.toLowerCase() === "group" ? "group" : "person");
  let o = r.z.string().nullish();
  let d = t.contract["GET /groups/search"].response.shape.results.element;
  let u = d
    .pick({ userId: !0 })
    .extend({
      username: d.shape.username.nullish(),
      bio: d.shape.bio.nullish(),
      profileImageUrl: d.shape.profileImageUrl.nullish(),
      headerImageUrl: d.shape.headerImageUrl.nullish(),
      followerCount: d.shape.followerCount.nullish(),
      followingCount: d.shape.followingCount.nullish(),
      createdAt: d.shape.createdAt.nullish(),
      updatedAt: d.shape.updatedAt.nullish(),
      walletAddress: d.shape.walletAddress.nullish(),
      isVerified: d.shape.isVerified.nullish(),
      verifiedBadgeVisible: d.shape.verifiedBadgeVisible.nullish(),
      resolvedAvatarDecoration: d.shape.resolvedAvatarDecoration.nullish(),
      memberCount: d.shape.memberCount.nullish(),
      kind: o,
    })
    .transform((e) => ({
      userId: e.userId,
      username: e.username ?? "",
      bio: e.bio || null,
      profileImage: e.profileImageUrl || null,
      headerImageUrl: e.headerImageUrl || null,
      walletAddress: e.walletAddress || null,
      followers: e.followerCount ?? 0,
      following: e.followingCount ?? 0,
      isVerified: e.isVerified ?? !1,
      verifiedBadgeVisible: !1 !== e.verifiedBadgeVisible,
      resolvedAvatarDecoration: e.resolvedAvatarDecoration ?? null,
      kind: s(e.kind),
      memberCount: e.memberCount ?? 0,
      createdAt: e.createdAt ?? null,
      updatedAt: e.updatedAt ?? null,
    }));
  let b = t.contract["GET /users/{id}"].response;
  let y = b.pick({}).extend({
    address: b.shape.address.nullish(),
    userId: b.shape.userId.nullish(),
    username: b.shape.username.nullish(),
    profile_image: b.shape.profile_image.nullish(),
    header_image_url: b.shape.header_image_url.nullish(),
    member_count: b.shape.member_count.nullish(),
    bio: b.shape.bio.nullish(),
    followers: b.shape.followers.nullish(),
    following: b.shape.following.nullish(),
    kind: o,
    active_competition_entry: b.shape.active_competition_entry,
  });
  let v = t.contract["GET /groups/search"].response.extend({
    results: u.array(),
  });
  return {
    D: u,
    Q: y,
    A: (e) => v.parse(e).results,
    h: (e) => ({
      groupId: e.userId,
      username: e.username || null,
      bio: e.bio,
      profileImage: e.profileImage,
      headerImageUrl: e.headerImageUrl,
      memberCount: e.memberCount,
      followers: e.followers,
      following: e.following,
      activeCompetitionEntry: null,
    }),
    t: ({ row: e, groupId: t }) => ({
      groupId: t,
      username: e.username ?? null,
      bio: e.bio ?? null,
      profileImage: e.profile_image ?? null,
      headerImageUrl: e.header_image_url ?? null,
      memberCount: e.member_count ?? 0,
      followers: e.followers ?? 0,
      following: e.following ?? 0,
      activeCompetitionEntry: e.active_competition_entry
        ? {
            competitionId: e.active_competition_entry.competition_id,
            competitionSlug: e.active_competition_entry.competition_slug,
            entryId: e.active_competition_entry.entry_id,
            phase: e.active_competition_entry.phase,
          }
        : null,
    }),
  };
}
function reader1(schema) {
  const u = schema;
  let m = async ({ api: e, groupId: t, signal: r }) => {
    let a = await e("GET /users/{id}", { params: { id: t }, signal: r });
    return (0, u.t)({ row: u.Q.parse(a), groupId: t });
  };
  let p = 20;
  let h = async ({
    api: e,
    searchTerm: t,
    offset: r,
    limit: a = p,
    signal: i,
  }) => {
    let n = await e("GET /groups/search", {
      query: { searchTerm: t, limit: a, offset: r },
      signal: i,
    });
    return (0, u.A)(n);
  };
  return { N: m, B: h };
}
function schema2(ports) {
  const t = { contract: ports.contract };
  const a = { z: ports.z };
  let o = (e) => (e?.toLowerCase() === "group" ? "group" : "person");
  let s = a.z.string().nullish();
  let d = t.contract["GET /groups/search"].response.shape.results.element;
  let c = d
    .pick({ userId: !0 })
    .extend({
      username: d.shape.username.nullish(),
      bio: d.shape.bio.nullish(),
      profileImageUrl: d.shape.profileImageUrl.nullish(),
      headerImageUrl: d.shape.headerImageUrl.nullish(),
      followerCount: d.shape.followerCount.nullish(),
      followingCount: d.shape.followingCount.nullish(),
      createdAt: d.shape.createdAt.nullish(),
      updatedAt: d.shape.updatedAt.nullish(),
      walletAddress: d.shape.walletAddress.nullish(),
      isVerified: d.shape.isVerified.nullish(),
      verifiedBadgeVisible: d.shape.verifiedBadgeVisible.nullish(),
      resolvedAvatarDecoration: d.shape.resolvedAvatarDecoration.nullish(),
      memberCount: d.shape.memberCount.nullish(),
      kind: s,
    })
    .transform((e) => ({
      userId: e.userId,
      username: e.username ?? "",
      bio: e.bio || null,
      profileImage: e.profileImageUrl || null,
      headerImageUrl: e.headerImageUrl || null,
      walletAddress: e.walletAddress || null,
      followers: e.followerCount ?? 0,
      following: e.followingCount ?? 0,
      isVerified: e.isVerified ?? !1,
      verifiedBadgeVisible: !1 !== e.verifiedBadgeVisible,
      resolvedAvatarDecoration: e.resolvedAvatarDecoration ?? null,
      kind: o(e.kind),
      memberCount: e.memberCount ?? 0,
      createdAt: e.createdAt ?? null,
      updatedAt: e.updatedAt ?? null,
    }));
  let y = t.contract["GET /users/{id}"].response;
  let v = y.pick({}).extend({
    address: y.shape.address.nullish(),
    userId: y.shape.userId.nullish(),
    username: y.shape.username.nullish(),
    profile_image: y.shape.profile_image.nullish(),
    header_image_url: y.shape.header_image_url.nullish(),
    member_count: y.shape.member_count.nullish(),
    bio: y.shape.bio.nullish(),
    followers: y.shape.followers.nullish(),
    following: y.shape.following.nullish(),
    kind: s,
    active_competition_entry: y.shape.active_competition_entry,
  });
  let b = t.contract["GET /groups/search"].response.extend({
    results: c.array(),
  });
  return {
    D: c,
    Q: v,
    A: (e) => b.parse(e).results,
    h: (e) => ({
      groupId: e.userId,
      username: e.username || null,
      bio: e.bio,
      profileImage: e.profileImage,
      headerImageUrl: e.headerImageUrl,
      memberCount: e.memberCount,
      followers: e.followers,
      following: e.following,
      activeCompetitionEntry: null,
    }),
    t: ({ row: e, groupId: t }) => ({
      groupId: t,
      username: e.username ?? null,
      bio: e.bio ?? null,
      profileImage: e.profile_image ?? null,
      headerImageUrl: e.header_image_url ?? null,
      memberCount: e.member_count ?? 0,
      followers: e.followers ?? 0,
      following: e.following ?? 0,
      activeCompetitionEntry: e.active_competition_entry
        ? {
            competitionId: e.active_competition_entry.competition_id,
            competitionSlug: e.active_competition_entry.competition_slug,
            entryId: e.active_competition_entry.entry_id,
            phase: e.active_competition_entry.phase,
          }
        : null,
    }),
  };
}
function reader2(schema) {
  const c = schema;
  let m = async ({ api: e, groupId: t, signal: a }) => {
    let i = await e("GET /users/{id}", { params: { id: t }, signal: a });
    return (0, c.t)({ row: c.Q.parse(i), groupId: t });
  };
  let p = 20;
  let h = async ({
    api: e,
    searchTerm: t,
    offset: a,
    limit: i = p,
    signal: l,
  }) => {
    let r = await e("GET /groups/search", {
      query: { searchTerm: t, limit: i, offset: a },
      signal: l,
    });
    return (0, c.A)(r);
  };
  return { N: m, B: h };
}
function schema3(ports) {
  const r = { z: ports.z };
  const t = { contract: ports.contract };
  let n = (e) => (e?.toLowerCase() === "group" ? "group" : "person");
  let o = r.z.string().nullish();
  let u = t.contract["GET /groups/search"].response.shape.results.element;
  let c = u
    .pick({ userId: !0 })
    .extend({
      username: u.shape.username.nullish(),
      bio: u.shape.bio.nullish(),
      profileImageUrl: u.shape.profileImageUrl.nullish(),
      headerImageUrl: u.shape.headerImageUrl.nullish(),
      followerCount: u.shape.followerCount.nullish(),
      followingCount: u.shape.followingCount.nullish(),
      createdAt: u.shape.createdAt.nullish(),
      updatedAt: u.shape.updatedAt.nullish(),
      walletAddress: u.shape.walletAddress.nullish(),
      isVerified: u.shape.isVerified.nullish(),
      verifiedBadgeVisible: u.shape.verifiedBadgeVisible.nullish(),
      resolvedAvatarDecoration: u.shape.resolvedAvatarDecoration.nullish(),
      memberCount: u.shape.memberCount.nullish(),
      kind: o,
    })
    .transform((e) => ({
      userId: e.userId,
      username: e.username ?? "",
      bio: e.bio || null,
      profileImage: e.profileImageUrl || null,
      headerImageUrl: e.headerImageUrl || null,
      walletAddress: e.walletAddress || null,
      followers: e.followerCount ?? 0,
      following: e.followingCount ?? 0,
      isVerified: e.isVerified ?? !1,
      verifiedBadgeVisible: !1 !== e.verifiedBadgeVisible,
      resolvedAvatarDecoration: e.resolvedAvatarDecoration ?? null,
      kind: n(e.kind),
      memberCount: e.memberCount ?? 0,
      createdAt: e.createdAt ?? null,
      updatedAt: e.updatedAt ?? null,
    }));
  let x = t.contract["GET /users/{id}"].response;
  let b = x.pick({}).extend({
    address: x.shape.address.nullish(),
    userId: x.shape.userId.nullish(),
    username: x.shape.username.nullish(),
    profile_image: x.shape.profile_image.nullish(),
    header_image_url: x.shape.header_image_url.nullish(),
    member_count: x.shape.member_count.nullish(),
    bio: x.shape.bio.nullish(),
    followers: x.shape.followers.nullish(),
    following: x.shape.following.nullish(),
    kind: o,
    active_competition_entry: x.shape.active_competition_entry,
  });
  let w = t.contract["GET /groups/search"].response.extend({
    results: c.array(),
  });
  return {
    D: c,
    Q: b,
    A: (e) => w.parse(e).results,
    h: (e) => ({
      groupId: e.userId,
      username: e.username || null,
      bio: e.bio,
      profileImage: e.profileImage,
      headerImageUrl: e.headerImageUrl,
      memberCount: e.memberCount,
      followers: e.followers,
      following: e.following,
      activeCompetitionEntry: null,
    }),
    t: ({ row: e, groupId: t }) => ({
      groupId: t,
      username: e.username ?? null,
      bio: e.bio ?? null,
      profileImage: e.profile_image ?? null,
      headerImageUrl: e.header_image_url ?? null,
      memberCount: e.member_count ?? 0,
      followers: e.followers ?? 0,
      following: e.following ?? 0,
      activeCompetitionEntry: e.active_competition_entry
        ? {
            competitionId: e.active_competition_entry.competition_id,
            competitionSlug: e.active_competition_entry.competition_slug,
            entryId: e.active_competition_entry.entry_id,
            phase: e.active_competition_entry.phase,
          }
        : null,
    }),
  };
}
function reader3(schema) {
  const c = schema;
  let m = async ({ api: e, groupId: t, signal: r }) => {
    let l = await e("GET /users/{id}", { params: { id: t }, signal: r });
    return (0, c.t)({ row: c.Q.parse(l), groupId: t });
  };
  let f = 20;
  let p = async ({
    api: e,
    searchTerm: t,
    offset: r,
    limit: l = f,
    signal: a,
  }) => {
    let i = await e("GET /groups/search", {
      query: { searchTerm: t, limit: l, offset: r },
      signal: a,
    });
    return (0, c.A)(i);
  };
  return { N: m, B: p };
}
function schema4(ports) {
  const s = { z: ports.z };
  const r = { contract: ports.contract };
  let n = (e) => (e?.toLowerCase() === "group" ? "group" : "person");
  let o = s.z.string().nullish();
  let u = r.contract["GET /groups/search"].response.shape.results.element;
  let p = u
    .pick({ userId: !0 })
    .extend({
      username: u.shape.username.nullish(),
      bio: u.shape.bio.nullish(),
      profileImageUrl: u.shape.profileImageUrl.nullish(),
      headerImageUrl: u.shape.headerImageUrl.nullish(),
      followerCount: u.shape.followerCount.nullish(),
      followingCount: u.shape.followingCount.nullish(),
      createdAt: u.shape.createdAt.nullish(),
      updatedAt: u.shape.updatedAt.nullish(),
      walletAddress: u.shape.walletAddress.nullish(),
      isVerified: u.shape.isVerified.nullish(),
      verifiedBadgeVisible: u.shape.verifiedBadgeVisible.nullish(),
      resolvedAvatarDecoration: u.shape.resolvedAvatarDecoration.nullish(),
      memberCount: u.shape.memberCount.nullish(),
      kind: o,
    })
    .transform((e) => ({
      userId: e.userId,
      username: e.username ?? "",
      bio: e.bio || null,
      profileImage: e.profileImageUrl || null,
      headerImageUrl: e.headerImageUrl || null,
      walletAddress: e.walletAddress || null,
      followers: e.followerCount ?? 0,
      following: e.followingCount ?? 0,
      isVerified: e.isVerified ?? !1,
      verifiedBadgeVisible: !1 !== e.verifiedBadgeVisible,
      resolvedAvatarDecoration: e.resolvedAvatarDecoration ?? null,
      kind: n(e.kind),
      memberCount: e.memberCount ?? 0,
      createdAt: e.createdAt ?? null,
      updatedAt: e.updatedAt ?? null,
    }));
  let b = r.contract["GET /users/{id}"].response;
  let y = b.pick({}).extend({
    address: b.shape.address.nullish(),
    userId: b.shape.userId.nullish(),
    username: b.shape.username.nullish(),
    profile_image: b.shape.profile_image.nullish(),
    header_image_url: b.shape.header_image_url.nullish(),
    member_count: b.shape.member_count.nullish(),
    bio: b.shape.bio.nullish(),
    followers: b.shape.followers.nullish(),
    following: b.shape.following.nullish(),
    kind: o,
    active_competition_entry: b.shape.active_competition_entry,
  });
  let I = r.contract["GET /groups/search"].response.extend({
    results: p.array(),
  });
  return {
    D: p,
    Q: y,
    A: (e) => I.parse(e).results,
    h: (e) => ({
      groupId: e.userId,
      username: e.username || null,
      bio: e.bio,
      profileImage: e.profileImage,
      headerImageUrl: e.headerImageUrl,
      memberCount: e.memberCount,
      followers: e.followers,
      following: e.following,
      activeCompetitionEntry: null,
    }),
    t: ({ row: e, groupId: r }) => ({
      groupId: r,
      username: e.username ?? null,
      bio: e.bio ?? null,
      profileImage: e.profile_image ?? null,
      headerImageUrl: e.header_image_url ?? null,
      memberCount: e.member_count ?? 0,
      followers: e.followers ?? 0,
      following: e.following ?? 0,
      activeCompetitionEntry: e.active_competition_entry
        ? {
            competitionId: e.active_competition_entry.competition_id,
            competitionSlug: e.active_competition_entry.competition_slug,
            entryId: e.active_competition_entry.entry_id,
            phase: e.active_competition_entry.phase,
          }
        : null,
    }),
  };
}
function reader4(schema) {
  const p = schema;
  let m = async ({ api: e, groupId: r, signal: s }) => {
    let a = await e("GET /users/{id}", { params: { id: r }, signal: s });
    return (0, p.t)({ row: p.Q.parse(a), groupId: r });
  };
  let h = 20;
  let c = async ({
    api: e,
    searchTerm: r,
    offset: s,
    limit: a = h,
    signal: t,
  }) => {
    let i = await e("GET /groups/search", {
      query: { searchTerm: r, limit: a, offset: s },
      signal: t,
    });
    return (0, p.A)(i);
  };
  return { N: m, B: c };
}
const contexts = [
  "evidence/web/objects/c3601a995a6b7f37.js",
  "evidence/web/objects/ecf7ec803bfb3020.js",
  "evidence/web/objects/9535b69d76e2a69b.js",
  "evidence/web/objects/767cc801e3f88f8b.js",
  "evidence/web/objects/ea5d7a76f15713d7.js",
];
const schemas = [schema0, schema1, schema2, schema3, schema4],
  readers = [reader0, reader1, reader2, reader3, reader4];
export function createGroupSearchReadModel(ports) {
  if (
    !ports ||
    typeof ports.z?.string !== "function" ||
    !ports.contract?.["GET /groups/search"]?.response ||
    !ports.contract?.["GET /users/{id}"]?.response
  )
    throw new TypeError(
      "Explicit group schema runtime/contract responses required",
    );
  const i = contexts.indexOf(ports.context);
  if (i < 0)
    throw new TypeError("Explicit captured group source context required");
  const model = schemas[i](ports),
    request = readers[i](model);
  return {
    readGroup: request.N,
    searchGroups: request.B,
    projectSearchRow: model.h,
    projectProfile: model.t,
    groupRowSchema: model.D,
    profileSchema: model.Q,
    parseSearch: model.A,
  };
}
