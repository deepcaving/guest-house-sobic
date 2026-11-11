// Temporary probe: send a KNOWN-CLEAN body from inside Netlify, so the
// only variable between this and a successful local run is the runtime.
export default async () => {
  const CID = "1000.0PURR6879S646U70PHNCU98IK92W1J";
  const body =
    "grant_type=refresh_token&client_id=" + CID +
    "&client_secret=" + "a".repeat(42) +
    "&refresh_token=1000." + "b".repeat(65);
  const out = { body };
  try {
    const r = await fetch("https://accounts.zoho.com/oauth/v2/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    out.status = r.status;
    out.response = (await r.text()).slice(0, 150);
  } catch (e) {
    out.error = String(e && e.message);
  }
  return new Response(JSON.stringify(out), {
    headers: { "Content-Type": "application/json" },
  });
};
