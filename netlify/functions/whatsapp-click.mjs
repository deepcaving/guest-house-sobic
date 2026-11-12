/**
 * Record a WhatsApp click.
 *
 * A guest who opens WhatsApp from the page has not sent an enquiry, but
 * they are interested - and the lodge wants to know it happened, and
 * roughly where they are.
 *
 * The record is written as a Netlify Form submission, so it appears in the
 * Netlify dashboard next to the enquiries, with the details as ordinary
 * fields you can read at a glance:
 *
 *   page      where on the site the click happened
 *   link      which WhatsApp link was used
 *   trip      Fly fishing, or a general stay
 *   dates     the dates the guest was asking about, if they typed any
 *   people    how many people, if they said
 *   language  the language the page was in
 *   ip        the visitor's IP address
 *   city      the approximate location, from the Netlify request context
 *   region    ...the region, the country, the coordinates and the timezone
 *   device    a readable "iPhone · Safari" instead of the raw agent string
 *
 * The IP address and the location come from the Netlify request context -
 * `context.ip` and `context.geo` - which Netlify fills in for every
 * request. Nothing is stored in the visitor's browser: no cookie, no
 * identifier, no local storage. There is no name and no email either: the
 * guest did not send an enquiry, they only opened a chat.
 *
 * Nothing here may delay or break the click. The chat must open whether
 * this function is reachable or not, so every failure is swallowed.
 */

/* A short, readable description of the device, instead of the raw agent
 * string. "iPhone · Safari" tells the lodge more than "Mozilla/5.0 …". */
function deviceFromUserAgent(ua) {
  const s = String(ua || "");
  let device = "";
  if (/iPhone|iPod/i.test(s)) device = "iPhone";
  else if (/iPad/i.test(s)) device = "iPad";
  else if (/Android/i.test(s)) device = /Mobile/i.test(s) ? "Android phone" : "Android tablet";
  else if (/Windows Phone/i.test(s)) device = "Windows phone";
  else if (/Windows/i.test(s)) device = "Windows PC";
  else if (/Macintosh|Mac OS X/i.test(s)) device = "Mac";
  else if (/Linux/i.test(s)) device = "Linux";

  let browser = "";
  if (/Edg\//i.test(s)) browser = "Edge";
  else if (/OPR\/|Opera/i.test(s)) browser = "Opera";
  else if (/Chrome\//i.test(s)) browser = "Chrome";
  else if (/Firefox\//i.test(s)) browser = "Firefox";
  else if (/Safari\//i.test(s)) browser = "Safari";

  return [device, browser].filter(Boolean).join(" · ") || "unknown";
}

/* The approximate location, as flat fields. Netlify's context.geo is a
 * nested object, and a flat list of fields reads better in the dashboard. */
function geoFields(geo) {
  const g = geo || {};
  const country = g.country || {};
  const subdivision = g.subdivision || {};
  return {
    city: g.city || "",
    region: subdivision.name || subdivision.code || "",
    country: country.name || country.code || "",
    lat: g.latitude != null ? String(g.latitude) : "",
    lon: g.longitude != null ? String(g.longitude) : "",
    timezone: g.timezone || "",
  };
}

function readField(body, name) {
  const value = body && body[name];
  return typeof value === "string" ? value.trim().slice(0, 300) : "";
}

/**
 * Write the click into Netlify Forms.
 *
 * The browser posts to the site's own address with `form-name`, which is
 * the path Netlify's form handler watches. The function posts the same
 * way, so the record lands in the same list as the enquiries.
 */
async function saveToNetlifyForms(siteUrl, fields) {
  try {
    const response = await fetch(`${siteUrl}/`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams(fields).toString(),
    });
    const text = await response.text().catch(() => "");
    return { ok: response.ok, status: response.status, detail: text.slice(0, 200) };
  } catch (err) {
    return { ok: false, status: 0, detail: String((err && err.message) || err) };
  }
}

export default async (request, context) => {
  if (request.method !== "POST") {
    return new Response("Method not allowed", {
      status: 405,
      headers: { Allow: "POST" },
    });
  }

  let body = {};
  try {
    body = await request.json();
  } catch {
    body = {};
  }

  const ctx = context || {};
  const ip =
    ctx.ip ||
    request.headers.get("x-nf-client-connection-ip") ||
    (request.headers.get("x-forwarded-for") || "").split(",")[0].trim() ||
    "";
  const geo = geoFields(ctx.geo);
  const userAgent = request.headers.get("user-agent") || "";

  const fields = {
    "form-name": "whatsapp-click",
    "bot-field": "",
    page: readField(body, "page"),
    link: readField(body, "link"),
    trip: readField(body, "trip"),
    dates: readField(body, "dates"),
    people: readField(body, "people"),
    language: readField(body, "language"),
    ip,
    city: geo.city,
    region: geo.region,
    country: geo.country,
    lat: geo.lat,
    lon: geo.lon,
    timezone: geo.timezone,
    device: deviceFromUserAgent(userAgent),
  };

  const siteUrl = (process.env.URL || new URL(request.url).origin).replace(/\/+$/, "");
  const stored = await saveToNetlifyForms(siteUrl, fields);

  console.log(
    `[whatsapp-click] ${fields.link || fields.page} - ${ip} - ${fields.city || "?"}, ${fields.country || "?"} - stored: ${stored.ok}`
  );

  return new Response(
    JSON.stringify({ ok: true, stored: stored.ok, ip, ...geo, device: fields.device }),
    { status: 200, headers: { "Content-Type": "application/json" } }
  );
};
