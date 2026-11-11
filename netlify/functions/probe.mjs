// A minimal probe that sends the SAME body from inside Netlify, so the
// only variable is the runtime, not the payload.
const CID = "1000.0PURR6879S646U70PHNCU98IK92W1J";
const body = `grant_type=refresh_token&client_id=${CID}&client_secret=${"a".repeat(42)}&refresh_token=${"1000." + "b".repeat(65)}`;

export default async () => {
  const out = {};
  try {
    const r = await fetch("https://accounts.zoho.com/oauth/v2/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    const t = await r.text();
    out.status = r.status;
    out.body = t.slice(0, 120);
  } catch (e) {
    out.error = String(e && e.message);
  }
  return new Response(JSON.stringify(out), { headers: { "Content-Type": "application/json" } });
};
