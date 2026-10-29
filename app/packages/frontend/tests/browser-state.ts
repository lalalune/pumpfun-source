/** Ordinary page cases start after the captured local welcome acknowledgement. */
export const acceptedClickwrapState = {
  cookies: [
    {
      name: "clickwrap_accepted",
      value: "true",
      domain: "127.0.0.1",
      path: "/",
      expires: -1,
      httpOnly: false,
      secure: false,
      sameSite: "Lax" as const,
    },
  ],
  origins: [],
};
