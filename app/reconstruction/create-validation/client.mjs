// Reconstructed selected nonmutating callbacks; authenticated inert AST, never whole captured modules.
// Explicit local capabilities and render snapshots only; no React, wallet, submit or upload execution.
export function createFieldValidator({
  utf8Bytes
}) {
  const eY = {
    W: utf8Bytes
  };
  const eX = {
    O: {
      IMAGE: 45e5,
      VIDEO: 1e7,
      BANNER: 45e5
    },
    f: {
      NAME_MAX_LENGTH: 32,
      TICKER_MAX_LENGTH: 10,
      DESCRIPTION_MAX_LENGTH: 2e3
    }
  };
  const X = {
    q: {
      telegram: /^(https?:\/\/)(t\.me|telegram\.me)\/[a-zA-Z0-9_]+$/,
      website: /^https:\/\/(www\.)?[-a-zA-Z0-9@:%._~#=]{1,256}\.[a-zA-Z]{2,20}\b([-a-zA-Z0-9()@:%_.~#?&/=]*)$/,
      twitter: /^(https?:\/\/)?(www\.)?(twitter\.com|x\.com)\/.+/i
    }
  };
  const e5 = eX.O.BANNER,
    e8 = e5 / 1e6;
  const ts = `Banner image too large: it must be under ${e8} MB`;
  return ({
    decodedJwt: e,
    name: t,
    ticker: r,
    description: a,
    image: i,
    video: s,
    banner: n,
    videoUploaded: o,
    previewStatus: l,
    selectedPreview: c,
    telegram: d,
    website: m,
    twitter: u
  }) => {
    if (!e) throw Error("Connect your wallet and sign in to create a coin");
    if (!t) throw Error("Coin needs a name");
    if ((0, eY.W)(t) > eX.f.NAME_MAX_LENGTH) throw Error("Name too long: it must be less than 32 characters");
    if (!r) throw Error("Coin needs a ticker");
    if ((0, eY.W)(r) > eX.f.TICKER_MAX_LENGTH) throw Error("Ticker cannot be more than 10 characters");
    if (a && a.length > eX.f.DESCRIPTION_MAX_LENGTH) throw Error("Description too long");
    if (i && i.size > eX.O.IMAGE) throw Error("Image too large: it must be less than 4.3 megabytes");
    if (s && s.size > eX.O.VIDEO) throw Error("Video too large: it must be less than 10 megabytes");
    if (n && n.size > e5) throw Error(ts);
    if (!i && !s) throw Error("Image or video required");
    if (s && !o) throw Error("Video not uploaded yet");
    if (o && 2 !== l && (!c || !c.length)) throw Error("Please select a thumbnail");
    if (d && !X.q.telegram.test(d)) throw Error("Invalid Telegram link format");
    if (m) {
      if (/^http:\/\//.test(m)) throw Error("Website must use HTTPS");
      if (!/^https?:\/\//.test(m)) throw Error("Website must include protocol (https://)");
      if (!X.q.website.test(m)) throw Error("Invalid Website link format");
    }
    if (u && !X.q.twitter.test(u)) throw Error("Invalid Twitter/X link format");
  };
}
export function createParentValidate(snapshot, {
  validateFields: tn,
  translate: e,
  toast: p
}) {
  const {
    decodedJwt: eD,
    name: e_,
    ticker: ey,
    description: ew,
    image: A,
    video: O,
    banner: X,
    videoUploaded: q,
    previewStatus: $,
    selectedPreview: V,
    telegram: eT,
    website: ek,
    twitter: ej
  } = snapshot;
  return () => {
    try {
      return tn({
        decodedJwt: eD,
        name: e_,
        ticker: ey,
        description: ew,
        image: A,
        video: O,
        banner: X,
        videoUploaded: q,
        previewStatus: $,
        selectedPreview: V,
        telegram: eT,
        website: ek,
        twitter: ej
      });
    } catch (t) {
      return p.c.error(e("web.create.validation_error"), {
        description: t instanceof Error ? t.message : String(t)
      }), !1;
    }
  };
}
export function createTextCallbacks({
  setName: eg,
  setTicker: ev,
  setDescription: eE
}) {
  return {
    name: e => {
      e.target.value.length <= 32 && eg(e.target.value);
    },
    ticker: e => {
      e.target.value.length <= 10 && ev(e.target.value);
    },
    description: e => eE(e.target.value)
  };
}
export function initialSocialErrors() {
  return {
    telegram: "",
    website: "",
    twitter: ""
  };
}
export function createSocialCallbacks({
  setTelegram: O,
  setWebsite: P,
  setTwitter: R,
  setErrors: M
}) {
  const X = {
    q: {
      telegram: /^(https?:\/\/)(t\.me|telegram\.me)\/[a-zA-Z0-9_]+$/,
      website: /^https:\/\/(www\.)?[-a-zA-Z0-9@:%._~#=]{1,256}\.[a-zA-Z]{2,20}\b([-a-zA-Z0-9()@:%_.~#?&/=]*)$/,
      twitter: /^(https?:\/\/)?(www\.)?(twitter\.com|x\.com)\/.+/i
    }
  };
  const D = (e, t) => {
    let r = e.target.value;
    "telegram" === t && O(r), "website" === t && P(r), "twitter" === t && R(r), M(e => ({
      ...e,
      [t]: ""
    }));
  };
  const F = (e, t) => {
    let r = e.target.value;
    M(e => ({
      ...e,
      [t]: function (e, t) {
        if ("" === t || void 0 === t) return "";
        let r = "";
        switch (e) {
          case "telegram":
            X.q.telegram.test(t) || (r = "Please enter a valid Telegram link (e.g. https://t.me/username)");
            break;
          case "website":
            /^http:\/\//.test(t) ? r = "Website link cannot use 'http'. Please use 'https'." : /^https:\/\//.test(t) ? X.q.website.test(t) || (r = "Please enter a valid website link (e.g. https://example.com)") : r = "Website must start with 'https://'.";
            break;
          case "twitter":
            X.q.twitter.test(t) || (r = "Please enter a valid Twitter/X username format");
        }
        return r;
      }(t, r)
    }));
  };
  return {
    website: {
      onChange: e => D(e, "website"),
      onBlur: e => F(e, "website")
    },
    twitter: {
      onChange: e => D(e, "twitter"),
      onBlur: e => F(e, "twitter")
    },
    telegram: {
      onChange: e => D(e, "telegram"),
      onBlur: e => F(e, "telegram")
    }
  };
}
export function createDialogCallbacks({
  walletAvailable: S,
  validate: _,
  setDialogOpen: T,
  setDialogError: A,
  requestWalletUI: O,
  telemetry: F,
  logger: console
}) {
  return {
    onClick: async () => {
      try {
        if (!S) {
          (0, F.Lw)({
            source: "create"
          }), O(!0);
          return;
        }
        _(), T(!0), A(void 0);
      } catch (e) {
        console.log(e), e instanceof Error ? A(e.message) : A("an unexpected error occurred");
      }
    },
    onOpenChange: T
  };
}
