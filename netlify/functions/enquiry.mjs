/**
 * Pliva River Lodge - enquiry email function.
 *
 * The guest fills in the form and presses "Send enquiry". This function
 * sends the enquiry as a real email from the server, so:
 *   - Milka receives it in her inbox
 *   - the collaborator is copied on it
 *   - the guest does nothing beyond pressing the button
 *
 * Netlify Functions cannot speak SMTP (no outbound port 25, no long-lived
 * process), so the mail is handed to a transactional email API. Resend is
 * used because it is the simplest to set up, but the API call below is
 * plain HTTP, so any provider can be swapped in.
 *
 * ENVIRONMENT VARIABLES - set these in Netlify, never in the repository:
 *   RESEND_API_KEY    the API key from your email provider
 *   MAIL_TO           who receives the enquiry (Milka)
 *   MAIL_CC           who is copied on it (the collaborator) - optional
 *   MAIL_FROM         the verified sender, e.g. "Pliva River Lodge" <bookings@yourdomain>
 *   MAIL_FROM_FALLBACK plain address to use if MAIL_FROM is not set
 *
 * If the API key is missing the function does not fail the form: it logs the
 * enquiry and returns a "not configured" status, and the browser falls back
 * to WhatsApp and the guest's own mail app. The enquiry is never lost.
 */

const RESEND_ENDPOINT = "https://api.resend.com/emails";

// Netlify injects these into process.env. They are read on every call
// rather than once at module load, so that changing an environment variable
// takes effect without a redeploy, and so that a missing key is handled as
// "not configured" rather than "failed".
function readConfig() {
  return {
    apiKey: process.env.RESEND_API_KEY,
    to: process.env.MAIL_TO || "milkasobic25@gmail.com",
    // The collaborator is copied by default. MAIL_CC overrides it.
    cc: process.env.MAIL_CC || "francesco.capuzzo@zoho.com",
    from:
      process.env.MAIL_FROM ||
      process.env.MAIL_FROM_FALLBACK ||
      "Pliva River Lodge <onboarding@resend.dev>",
  };
}

// The fields the form posts, in the order we want them in the email.
const FIELDS = [
  ["name", "Name"],
  ["email", "Email"],
  ["dates", "Preferred dates"],
  ["people", "How many people"],
  ["airport", "Arriving via"],
  ["message", "Message"],
];

function readField(body, name) {
  const value = body[name];
  return typeof value === "string" ? value.trim() : "";
}

/** Build the plain-text body of the email from the posted fields. */
function buildBody(body) {
  const lines = ["Website enquiry from guesthousesobic.netlify.app", ""];
  for (const [name, label] of FIELDS) {
    const value = readField(body, name);
    if (value) lines.push(`${label}: ${value}`);
  }
  lines.push("");
  lines.push(`Sent: ${body.page || "unknown page"}`);
  return lines.join("\n");
}

export default async (request, context) => {
  const config = readConfig();

  // Only POST is meaningful for this endpoint.
  if (request.method !== "POST") {
    return new Response("Method not allowed", {
      status: 405,
      headers: { Allow: "POST" },
    });
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return json(400, { ok: false, error: "Bad JSON" });
  }

  // The honeypot field must stay empty. A filled one means a bot.
  if (readField(body, "bot-field")) {
    return json(200, { ok: true, skipped: true });
  }

  const name = readField(body, "name");
  const email = readField(body, "email");

  // A real enquiry needs at least a name and a way to reply.
  if (!name || !email) {
    return json(400, { ok: false, error: "Name and email are required" });
  }

  const message = buildBody(body);
  const subject = `New enquiry — ${name}` +
    (readField(body, "dates") ? ` — ${readField(body, "dates")}` : "");

  // Reply-To is the guest, so pressing reply in Milka's inbox reaches them.
  const payload = {
    from: config.from,
    to: [config.to],
    subject,
    text: message,
    reply_to: email,
  };
  if (config.cc) payload.cc = [config.cc];

  if (!config.apiKey) {
    // Not configured. Do not fail the form - the browser has fallbacks.
    console.error(
      "[enquiry] RESEND_API_KEY is not set. Enquiry was:\n" + message
    );
    return json(503, {
      ok: false,
      configured: false,
      error: "Email service is not configured",
    });
  }

  try {
    const response = await fetch(RESEND_ENDPOINT, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${config.apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const result = await response.json().catch(() => ({}));

    if (!response.ok) {
      console.error("[enquiry] provider error:", response.status, result);
      return json(502, {
        ok: false,
        error: "The email service rejected the enquiry",
        detail: result,
      });
    }

    console.log("[enquiry] sent:", result.id || "no id returned");
    return json(200, { ok: true, id: result.id || null });
  } catch (err) {
    console.error("[enquiry] request failed:", err);
    return json(502, { ok: false, error: "Could not reach the email service" });
  }
};

function json(status, body) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}
