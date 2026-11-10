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
 *   MAIL_BCC          who is blind-copied on it (the collaborator) - optional
 *   MAIL_FROM         the verified sender, e.g. "Pliva River Lodge" <bookings@yourdomain>
 *   MAIL_FROM_FALLBACK plain address to use if MAIL_FROM is not set
 *
 * If the API key is missing the function does not fail the form: it logs the
 * enquiry and returns a "not configured" status, and the browser falls back
 * to WhatsApp and the guest's own mail app. The enquiry is never lost.
 */

import { sendMail } from "./smtp.mjs";

const RESEND_ENDPOINT = "https://api.resend.com/emails";

// Netlify injects these into process.env. They are read on every call
// rather than once at module load, so that changing an environment variable
// takes effect without a redeploy, and so that a missing key is handled as
// "not configured" rather than "failed".
function readConfig() {
  const smtp = {
    host: process.env.SMTP_HOST,
    port: Number(process.env.SMTP_PORT || 465),
    user: process.env.SMTP_USER,
    password: process.env.SMTP_PASSWORD,
    fromEmail: process.env.SMTP_FROM_EMAIL,
    fromName: process.env.SMTP_FROM_NAME,
    secure: (process.env.SMTP_SECURE || "ssl").toLowerCase(),
  };
  // SMTP is configured when the host, the user and the password are all
  // present. Anything less and the transport is simply not available.
  smtp.configured = Boolean(smtp.host && smtp.user && smtp.password);

  return {
    apiKey: process.env.RESEND_API_KEY,
    smtp,
    to: process.env.MAIL_TO || "milkasobic25@gmail.com",
    // The collaborator is blind-copied by default, so Milka can forward the
    // enquiry on without exposing that address. MAIL_BCC overrides it.
    bcc: process.env.MAIL_BCC || "francesco.capuzzo@zoho.com",
    from:
      process.env.MAIL_FROM ||
      process.env.MAIL_FROM_FALLBACK ||
      // A domain the lodge owns. A *.netlify.app address cannot be used as
      // the sender: Netlify controls that DNS zone, so the provider can
      // never verify it. This address only works once the domain is
      // registered and verified with the email provider.
      "Pliva River Lodge <bookings@plivariverlodge.com>",
  };
}

// The fields the form posts, in the order we want them in the email.
const FIELDS = [
  ["name", "Name"],
  ["email", "Email"],
  ["dates", "Preferred dates"],
  ["airport", "Arriving via"],
  ["message", "Message"],
];

function readField(body, name) {
  const value = body[name];
  return typeof value === "string" ? value.trim() : "";
}

/**
 * The occupancy block.
 *
 * The form has two ways of saying how many people are coming:
 *   - "fishing" - the guest ticked Fly fishing, so "people" is the number
 *     of ANGLERS (1-4, or 5 or more, or a companion).
 *   - "booking" - the guest unticked it, so they picked a Booking.com-style
 *     occupancy: adults, children and rooms.
 *
 * Both are captured, so the email always says which kind of enquiry it is,
 * the total number of people, the category, and how many rooms.
 */
function occupancyLines(body) {
  const lines = [];
  const mode = readField(body, "people_mode");
  const label = readField(body, "people_label");
  const people = readField(body, "people");

  lines.push(mode === "fishing" ? "Trip type: Fly fishing" : "Trip type: General stay");

  if (mode === "booking") {
    const adults = readField(body, "adults");
    const children = readField(body, "children");
    const rooms = readField(body, "rooms");
    if (adults !== "") lines.push(`Adults: ${adults}`);
    if (children !== "") lines.push(`Children: ${children}`);
    if (rooms !== "") lines.push(`Rooms: ${rooms}`);
    const total = Number(adults || 0) + Number(children || 0);
    if (total > 0) lines.push(`Total people: ${total}`);
  } else if (people) {
    lines.push(`People: ${people}`);
  }

  if (label) lines.push(`Occupancy: ${label}`);
  return lines;
}

/** Build the plain-text body of the email from the posted fields. */
function buildBody(body) {
  const lines = ["Website enquiry from guesthousesobic.netlify.app", ""];
  for (const [name, label] of FIELDS) {
    const value = readField(body, name);
    if (value) lines.push(`${label}: ${value}`);
  }
  lines.push("");
  lines.push(...occupancyLines(body));
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
  const peopleSummary =
    readField(body, "people_label") || readField(body, "people");
  const subject = `New enquiry — ${name}` +
    (readField(body, "dates") ? ` — ${readField(body, "dates")}` : "") +
    (peopleSummary ? ` — ${peopleSummary}` : "");

  // Reply-To is the guest, so pressing reply in Milka's inbox reaches them.
  const payload = {
    from: config.from,
    to: [config.to],
    subject,
    text: message,
    reply_to: email,
  };
  if (config.bcc) payload.bcc = [config.bcc];

  // 1. The SMTP transport. If Zoho is configured, use it - it is the
  //    mailbox the lodge actually owns, and it needs no domain verification.
  if (config.smtp.configured) {
    try {
      const result = await sendMail(config.smtp, {
        to: [config.to],
        bcc: config.bcc ? [config.bcc] : [],
        subject,
        text: message,
        replyTo: email,
      });
      console.log("[enquiry] sent over SMTP:", result.messageId || "no id");
      return json(200, {
        ok: true,
        id: result.messageId || null,
        transport: "smtp",
      });
    } catch (err) {
      // A failed SMTP send must not lose the enquiry. Log it and carry on
      // to the HTTP provider, which may still be configured.
      console.error("[enquiry] SMTP send failed:", err && err.message);
      // The password may be wrong, the mailbox may not be active, or Zoho
      // may be refusing the EHLO hostname. Say so precisely.
      if (/Authentication failed/i.test(String(err && err.message))) {
        return json(502, {
          ok: false,
          error: "The SMTP server rejected the login",
          detail: { hint: "SMTP_USER / SMTP_PASSWORD are wrong, or the mailbox has no Zoho account password yet." },
        });
      }
      if (!config.apiKey) {
        return json(502, {
          ok: false,
          error: "The email service could not be reached",
          detail: { message: String(err && err.message) },
        });
      }
      // Fall through to the HTTP provider.
    }
  }

  if (!config.apiKey) {
    // Not configured. Do not fail the form - the browser has fallbacks.
    //
    // This is almost always one of two Netlify settings problems:
    //   - the variable's scope does not include "Functions" (it was set for
    //     "Builds" only, so the function never sees it), or
    //   - it was given a value only for the "Production" deploy context,
    //     while this branch is running under the "Branch deploys" context.
    // The deploy context is reported so the cause is obvious in the logs.
    const context = process.env.CONTEXT || process.env.DEPLOY_CONTEXT || "unknown";
    console.error(
      `[enquiry] neither SMTP nor RESEND_API_KEY is configured ` +
        `(deploy context: ${context}). ` +
        "Check that the variable's scope includes Functions and that it has a " +
        "value for this deploy context.\nEnquiry was:\n" +
        message
    );
    return json(503, {
      ok: false,
      configured: false,
      error: "Email service is not configured",
      context,
      hint:
        "Set either SMTP_HOST + SMTP_USER + SMTP_PASSWORD, or RESEND_API_KEY, " +
        "with the Functions scope and a value for this deploy context " +
        "(Production, and Branch deploys for branch previews).",
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

      // The common case: the sending domain has not been verified at the
      // provider. Say so precisely, because "rejected the enquiry" hides the
      // fact that nothing is wrong with the enquiry itself.
      const message = String(result.message || "");
      if (/not verified|is not verified|domain.*verif/i.test(message)) {
        return json(502, {
          ok: false,
          error: "The sending domain is not verified yet",
          detail: result,
          hint:
            "Verify the sending domain with the email provider, then add the " +
            "DNS records it gives you. A *.netlify.app address cannot be " +
            "verified - Netlify controls that DNS zone - so use a domain you " +
            "own, then set MAIL_FROM to an address on it.",
        });
      }

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
