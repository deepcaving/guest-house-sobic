#!/usr/bin/env node
/**
 * Pliva River Lodge - the small service behind the enquiry form.
 *
 * On Netlify the enquiry form is a serverless function. On our own
 * server it needs something to run on - this is that something, and it is
 * about a hundred lines.
 *
 * It hosts three things:
 *
 *   POST /.netlify/functions/enquiry        the enquiry, sent by email
 *   POST /.netlify/functions/whatsapp-click  a record of every WhatsApp click
 *   POST /                                  the backup copy of both forms
 *
 * The two functions in netlify/functions/ are UNCHANGED - they are written
 * against the standard Request/Response, so this file only has to hand
 * them what Netlify would have handed them: a Request, and a context with
 * the visitor's IP.
 *
 * The backup copy: Netlify keeps the forms in its own inbox. Here it is
 * written to a file, one JSON object per line, so nothing is ever lost
 * even if the mail server is down.
 *
 *   node deploy/server.mjs            listen on 127.0.0.1:8080
 *   PORT=3000 node deploy/server.mjs  listen on 127.0.0.1:3000
 */

import http from "node:http";
import { appendFile, mkdir } from "node:fs/promises";
import { dirname } from "node:path";

import enquiry from "../netlify/functions/enquiry.mjs";
import whatsappClick from "../netlify/functions/whatsapp-click.mjs";

const PORT = Number(process.env.PORT || 8080);
const HOST = process.env.HOST || "127.0.0.1";
const STORE = process.env.ENQUIRY_STORE || "/var/lib/pliva-site/enquiries.ndjson";

// The paths the page already knows. They keep their Netlify names on
// purpose: then form.js and the pages do not have to change.
const ROUTES = {
  "/.netlify/functions/enquiry": enquiry,
  "/.netlify/functions/whatsapp-click": whatsappClick,
};

function clientIp(req) {
  const fwd = req.headers["x-forwarded-for"];
  if (fwd) return String(fwd).split(",")[0].trim();
  return req.socket.remoteAddress || "";
}

/**
 * Netlify hands the function a context with the visitor's IP and their
 * approximate location. We have the IP. The location is NOT filled in:
 * working it out needs a third-party geo-IP service, and this site sends
 * nobody anywhere. The record keeps the IP, the device and the page.
 */
function contextFor(req) {
  return {
    ip: clientIp(req),
    geo: {},
    clientContext: {},
    deployContext: "own-server",
  };
}

async function readBody(req) {
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  return Buffer.concat(chunks);
}

async function store(fields) {
  const line = JSON.stringify({ at: new Date().toISOString(), ...fields }) + "\n";
  await mkdir(dirname(STORE), { recursive: true });
  await appendFile(STORE, line, "utf8");
}

/**
 * The backup copy of a form submission: the same fields Netlify would
 * have put in its forms inbox.
 */
async function storeForm(body) {
  const fields = {};
  for (const [k, v] of Object.entries(body)) {
    if (k === "form-name" || k === "bot-field") continue;
    fields[k] = Array.isArray(v) ? v[0] : v;
  }
  await store({ form: body["form-name"] || "unknown", ...fields });
}

function send(res, status, body, headers = {}) {
  res.writeHead(status, { "Content-Type": "text/plain; charset=utf-8", ...headers });
  res.end(body);
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || "localhost"}`);
  const raw = await readBody(req);

  try {
    // 1. the two functions, at the paths the page already uses
    const handler = ROUTES[url.pathname];
    if (handler) {
      const request = new Request(url.href, {
        method: req.method,
        headers: req.headers,
        body: req.method === "POST" ? raw : undefined,
      });
      const response = await handler(request, contextFor(req));
      const text = await response.text();
      res.writeHead(response.status, Object.fromEntries(response.headers));
      res.end(text);
      return;
    }

    // 2. the backup copy - a urlencoded POST to the site itself
    if (req.method === "POST") {
      const type = String(req.headers["content-type"] || "");
      if (type.includes("application/x-www-form-urlencoded")) {
        const body = Object.fromEntries(new URLSearchParams(raw.toString("utf8")));
        await storeForm(body);
        send(res, 200, "Thank you.");
        return;
      }
    }

    send(res, 404, "Not found");
  } catch (err) {
    console.error("[server]", err && err.stack ? err.stack : err);
    send(res, 500, "Server error");
  }
});

server.listen(PORT, HOST, () => {
  console.log(`[server] Pliva River Lodge service on http://${HOST}:${PORT}`);
  console.log(`[server] enquiries are backed up in ${STORE}`);
});
