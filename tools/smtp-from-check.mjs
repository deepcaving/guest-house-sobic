#!/usr/bin/env node
/**
 * Check which From addresses the Zoho mailbox may send as.
 *
 * Zoho refuses to relay for an address the mailbox does not own:
 *
 *     550 5.7.1 Sender is not allowed to relay emails
 *
 * That is the same refusal whether the address is simply wrong or is an
 * alias that has not been created yet - so it is worth checking before
 * changing the site configuration.
 *
 * Usage:
 *   SMTP_USER=francesco.capuzzo@zoho.com \
 *   SMTP_PASSWORD=your-app-password \
 *   node tools/smtp-from-check.mjs your-alias@your-domain
 *
 * The password is read from the environment, never from the command line,
 * so it stays out of the shell history. The test mail goes to the mailbox
 * itself by default, so nothing lands in a guest's inbox.
 *
 * With no arguments it checks the addresses that matter for the lodge.
 */

import { readFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..");

// Load .env if it exists - it holds the same values Netlify is given.
const envPath = join(ROOT, ".env");
if (existsSync(envPath)) {
  for (const line of readFileSync(envPath, "utf8").split("\n")) {
    if (!line.includes("=")) continue;
    const i = line.indexOf("=");
    const key = line.slice(0, i).trim();
    if (!process.env[key]) process.env[key] = line.slice(i + 1).trim();
  }
}

const { sendMail } = await import(join(ROOT, "netlify/functions/smtp.mjs"));

const user = process.env.SMTP_USER;
const password = process.env.SMTP_PASSWORD;
const host = process.env.SMTP_HOST || "smtppro.zoho.com";
const port = Number(process.env.SMTP_PORT || 465);
const secure = (process.env.SMTP_SECURE || "ssl").toLowerCase();

if (!user || !password) {
  console.error("Set SMTP_USER and SMTP_PASSWORD (in the environment or in .env).");
  process.exit(1);
}

// The test mail goes to the mailbox itself, so nothing reaches a guest.
const recipient = process.env.SMTP_CHECK_TO || user;

const candidates = process.argv.slice(2);
const addresses = candidates.length
  ? candidates
  : [
      // The account itself, plus an address on another domain that Zoho
      // refuses. Pass your own alias as an argument to check it:
      //   node tools/smtp-from-check.mjs your-alias@your-domain
      user,
      "guesthouse@blink2ask.com",
    ];

console.log(`Logging in as ${user} via ${host}:${port}`);
console.log(`Test mail goes to ${recipient}\n`);

let allowed = 0;
for (const from of addresses) {
  try {
    const result = await sendMail(
      { host, port, user, password, fromEmail: from, fromName: "Pliva River Lodge", secure },
      {
        to: [recipient],
        bcc: [],
        subject: "Sender address check",
        text: "Checking whether this address may be used as the From address.",
        replyTo: "check@example.com",
      }
    );
    allowed += 1;
    console.log(`  ALLOWED  ${from}  (${result.messageId})`);
  } catch (err) {
    const message = String((err && err.message) || err);
    if (/not allowed to relay/i.test(message)) {
      console.log(`  REFUSED  ${from}  — not an address this mailbox owns.`);
      console.log(`           Add it as an EMAIL ALIAS on this account, then run this again.`);
    } else {
      console.log(`  FAILED   ${from}  — ${message.slice(0, 120)}`);
    }
  }
}

console.log(`\n${allowed} of ${addresses.length} may be used as the From address.`);
console.log("Set the ones you want in Netlify as SMTP_FROM_EMAIL.");
process.exit(allowed > 0 ? 0 : 1);
