/**
 * Minimal SMTP-over-TLS client (implicit TLS, port 465).
 *
 * Netlify Functions cannot use a normal SMTP library reliably - most of
 * them open a long-lived plain socket on port 25, which is blocked. This
 * speaks SMTP directly over a TLS socket, which works because the TLS
 * handshake and the SMTP session are the same connection.
 *
 * Used only as a fallback transport: if RESEND_API_KEY is configured the
 * enquiry goes through the Resend HTTP API, and only when that is missing
 * (or fails) does this client talk to Zoho.
 *
 * Environment variables:
 *   SMTP_HOST         e.g. smtp.zoho.com
 *   SMTP_PORT         465 for implicit TLS, 587 for STARTTLS
 *   SMTP_USER         the mailbox to authenticate as
 *   SMTP_PASSWORD     its password or app-specific password
 *   SMTP_FROM_EMAIL   the From address
 *   SMTP_FROM_NAME    the display name on the From line
 *   SMTP_SECURE       "ssl" (implicit TLS) or "starttls"
 */

import tls from "node:tls";
import net from "node:net";

/**
 * Read one complete SMTP reply.
 *
 * A reply can be several lines: "250-xxx" continues, "250 xxx" ends. The
 * end of a reply is therefore a line whose 4th character is a SPACE, not a
 * hyphen. The first line of the reply may also arrive on its own, so the
 * buffer has to be checked for the terminating pattern rather than assumed
 * to hold the whole reply.
 */
function makeReader(socket) {
  let buffer = "";
  const waiters = [];

  function tryDeliver() {
    // A complete reply ends with a line like "250 OK".
    const match = buffer.match(/(?:^|\r\n)(\d{3}) ([^\r\n]*)\r\n?$/);
    if (!match) return false;
    const lines = buffer.split(/\r\n/).filter(Boolean);
    const code = parseInt(match[1], 10);
    const consumed = buffer.length;
    buffer = "";
    const waiter = waiters.shift();
    if (waiter) waiter({ code, lines, text: lines.join("\n") });
    return true;
  }

  socket.on("data", (chunk) => {
    buffer += chunk.toString("utf8");
    // The reply may be split across chunks; keep reading until it is whole.
    while (waiters.length && tryDeliver()) { /* more replies may be queued */ }
  });

  socket.on("error", (err) => {
    const waiter = waiters.shift();
    if (waiter) waiter({ code: 0, lines: [], text: "", error: err });
  });

  return function read() {
    return new Promise((resolve, reject) => {
      waiters.push((reply) => {
        if (reply.error) reject(reply.error);
        else resolve(reply);
      });
      // The reply may already be in the buffer.
      tryDeliver();
    });
  };
}

/** Encode a header value that may contain non-ASCII (names with accents). */
function encodeHeader(value) {
  if (/^[\x20-\x7E]*$/.test(value)) return value;
  return `=?UTF-8?B?${Buffer.from(value, "utf8").toString("base64")}?=`;
}

/**
 * Send one email over SMTP.
 * Returns { ok: true, messageId } or throws with a useful message.
 */
export async function sendMail(config, mail) {
  const {
    host,
    port,
    user,
    password,
    fromEmail,
    fromName,
    secure = "ssl",
  } = config;

  const timeoutMs = 20000;

  const socket = secure === "starttls"
    ? net.connect({ host, port })
    : tls.connect({ host, port, servername: host, rejectUnauthorized: false });

  socket.setTimeout(timeoutMs, () => {
    socket.destroy(new Error(`SMTP timeout after ${timeoutMs}ms`));
  });

  await new Promise((resolve, reject) => {
    socket.once(secure === "starttls" ? "connect" : "secureConnect", resolve);
    socket.once("error", reject);
  });

  const read = makeReader(socket);
  const send = (line) => socket.write(`${line}\r\n`);

  try {
    const greeting = await read();
    if (greeting.code !== 220) {
      throw new Error(`SMTP greeting failed: ${greeting.text}`);
    }

    let hostname = "blink2ask.com";
    if (secure === "starttls") {
      send("EHLO " + hostname);
      const ehlo = await read();
      if (ehlo.code !== 250) throw new Error(`EHLO failed: ${ehlo.text}`);
      send("STARTTLS");
      const starttls = await read();
      if (starttls.code !== 220) throw new Error(`STARTTLS failed: ${starttls.text}`);
      socket.upgrade({ host, servername: host, rejectUnauthorized: false });
      await new Promise((resolve, reject) => {
        socket.once("secureConnect", resolve);
        socket.once("error", reject);
      });
    }

    send("EHLO " + hostname);
    const ehlo = await read();
    if (ehlo.code !== 250) throw new Error(`EHLO failed: ${ehlo.text}`);

    const capabilities = ehlo.lines.join("\n");
    if (!/AUTH/i.test(capabilities)) {
      throw new Error("The SMTP server offers no AUTH mechanism");
    }

    // Prefer PLAIN; fall back to LOGIN for servers that only offer it.
    if (/AUTH[^\n]*PLAIN/i.test(capabilities)) {
      const token = Buffer.from(`\0${user}\0${password}`, "utf8").toString("base64");
      send(`AUTH PLAIN ${token}`);
      const auth = await read();
      if (auth.code !== 235) throw new Error(`Authentication failed: ${auth.text}`);
    } else {
      send("AUTH LOGIN");
      await read();
      send(Buffer.from(user, "utf8").toString("base64"));
      await read();
      send(Buffer.from(password, "utf8").toString("base64"));
      const auth = await read();
      if (auth.code !== 235) throw new Error(`Authentication failed: ${auth.text}`);
    }

    const from = `<${fromEmail}>`;
    send(`MAIL FROM:${from}`);
    const mailFrom = await read();
    if (mailFrom.code !== 250) throw new Error(`MAIL FROM rejected: ${mailFrom.text}`);

    const recipients = [...(mail.to || []), ...(mail.bcc || [])];
    for (const rcpt of recipients) {
      send(`RCPT TO:<${rcpt}>`);
      const r = await read();
      if (r.code !== 250 && r.code !== 251) {
        throw new Error(`RCPT TO ${rcpt} rejected: ${r.text}`);
      }
    }

    send("DATA");
    const data = await read();
    if (data.code !== 354) throw new Error(`DATA rejected: ${data.text}`);

    const fromHeader = fromName
      ? `${encodeHeader(fromName)} <${fromEmail}>`
      : fromEmail;
    const headers = [
      `From: ${fromHeader}`,
      `To: ${(mail.to || []).join(", ")}`,
      ...(mail.bcc || []).length ? [`Bcc: ${mail.bcc.join(", ")}`] : [],
      `Subject: ${encodeHeader(mail.subject)}`,
      `Reply-To: ${mail.replyTo || fromEmail}`,
      `Date: ${new Date().toUTCString()}`,
      `Message-ID: <${Date.now()}.${Math.random().toString(36).slice(2)}@${hostname}>`,
      "MIME-Version: 1.0",
      'Content-Type: text/plain; charset=UTF-8',
      "Content-Transfer-Encoding: 8bit",
    ].filter(Boolean);

    const body = (mail.text || "").replace(/\r?\n/g, "\r\n");
    // Dot-stuffing: a line that is a single dot must become two dots.
    const safeBody = body
      .split("\r\n")
      .map((line) => (line === "." ? ".." : line))
      .join("\r\n");

    socket.write(`${headers.join("\r\n")}\r\n\r\n${safeBody}\r\n.\r\n`);

    const sent = await read();
    if (sent.code !== 250) throw new Error(`Message rejected: ${sent.text}`);

    send("QUIT");
    await read().catch(() => {});
    socket.end();

    const messageId = (headers.find((h) => h.startsWith("Message-ID:")) || "")
      .replace("Message-ID:", "")
      .trim();

    return { ok: true, messageId, transport: "smtp" };
  } finally {
    try { socket.destroy(); } catch { /* already closed */ }
  }
}
