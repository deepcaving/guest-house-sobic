/**
 * Pliva River Lodge - Zoho Mail API transport.
 *
 * WHY THIS EXISTS
 *
 * The obvious way to send mail from this mailbox is SMTP. That works, and it
 * has been proven from the Netlify runtime: port 465 is open on Netlify's
 * Free plan (only port 25 is blocked, and that is an AWS Lambda restriction
 * on every plan, not a Netlify one). But SMTP needs the account password or
 * an app-specific password, and Zoho refuses the account password from an
 * unknown host until IMAP/SMTP is enabled and an app password is generated.
 *
 * Zoho's REST API sends the same mail over HTTPS, with no port restrictions
 * and no SMTP password at all. It authenticates with OAuth 2.0: a client id,
 * a client secret and a refresh token. The refresh token does not expire, so
 * the function can mint a fresh access token on every call and nothing needs
 * rotating.
 *
 * Because it is the real mailbox sending, the mail arrives from
 * `francesco.capuzzo@zoho.com` exactly as if Milka had sent it from Zoho
 * webmail. No domain verification is needed and no DKIM setup is needed -
 * which is the whole reason this transport exists.
 *
 * LIMIT (free Zoho Workplace mailbox): the Mail API cannot send to
 * EXTERNAL addresses. Zoho accepts the request and then answers 404 with
 * an empty body. Sending to another @zoho.com address works; sending to
 * gmail.com or any external domain does not. This is a plan restriction,
 * not a misconfiguration - see the SMTP transport for a path that works
 * on the free plan.
 *
 * SETUP (one time, in the Zoho API console)
 *
 *   1. https://api-console.zoho.com -> Add Client -> Server-based Application
 *      (or "Self Client", which is quicker and needs no redirect URI).
 *      Client Name: anything readable. Homepage URL: the site address.
 *      Authorized Redirect URI: http://localhost
 *   2. Authorise the scope ZohoMail.messages.CREATE (to send) plus
 *      ZohoMail.accounts.READ (to look up the account id). Both are needed:
 *      the send endpoint itself wants only CREATE, but the account id lookup
 *      wants READ, and the id is fetched at runtime when it is not set.
 *   3. Exchange the authorisation code for a refresh token:
 *        POST https://accounts.zoho.com/oauth/v2/token
 *        grant_type=authorization_code
 *        code=<the code Zoho gave you>
 *        client_id=<client id>
 *        client_secret=<client secret>
 *        redirect_uri=http://localhost
 *      The response contains a long-lived `refresh_token`.
 *   4. Find the account id: GET https://mail.zoho.com/api/accounts with the
 *      access token - the response lists each account with its `accountId`.
 *
 * ENVIRONMENT VARIABLES
 *
 *   ZOHO_CLIENT_ID       the client id from the API console
 *   ZOHO_CLIENT_SECRET   the client secret
 *   ZOHO_REFRESH_TOKEN    the long-lived refresh token
 *   ZOHO_ACCOUNT_ID      the numeric account id (optional - fetched at runtime)
 *   ZOHO_REGION          us (default) | eu | in | au | jp | ca | uk
 *   ZOHO_FROM_EMAIL      the From address (optional - defaults to the account)
 *   ZOHO_FROM_NAME       the display name on the From line (optional)
 *
 * The region matters: a European Zoho account lives on accounts.zoho.eu and
 * mail.zoho.eu. A token from the wrong region is rejected with an
 * `INVALID_CLIENT` error, so it is worth getting right.
 */

// The data centres Zoho runs, and the two hosts each one uses.
const REGIONS = {
  us: { accounts: "accounts.zoho.com", mail: "mail.zoho.com" },
  eu: { accounts: "accounts.zoho.eu", mail: "mail.zoho.eu" },
  in: { accounts: "accounts.zoho.in", mail: "mail.zoho.in" },
  au: { accounts: "accounts.zoho.com.au", mail: "mail.zoho.com.au" },
  jp: { accounts: "accounts.zoho.jp", mail: "mail.zoho.jp" },
  ca: { accounts: "accounts.zohocloud.ca", mail: "mail.zohocloud.ca" },
  uk: { accounts: "accounts.zoho.uk", mail: "mail.zoho.uk" },
};

function regionFor(name) {
  const key = String(name || "us").toLowerCase();
  return REGIONS[key] || REGIONS.us;
}

/**
 * Read the Zoho settings out of the environment.
 *
 * Everything is read on every call rather than once at module load, so that
 * changing an environment variable takes effect without a redeploy.
 */
export function readZohoConfig(env = process.env) {
  const region = regionFor(env.ZOHO_REGION);
  const config = {
    clientId: env.ZOHO_CLIENT_ID,
    clientSecret: env.ZOHO_CLIENT_SECRET,
    refreshToken: env.ZOHO_REFRESH_TOKEN,
    accountId: env.ZOHO_ACCOUNT_ID,
    fromEmail: env.ZOHO_FROM_EMAIL,
    fromName: env.ZOHO_FROM_NAME,
    region: String(env.ZOHO_REGION || "us").trim().toLowerCase() || "us",
    accountsUrl: region.accounts,
    mailUrl: region.mail,
    // The scheme is configurable so the transport can be pointed at a
    // staging host (or a local test double) without touching the code.
    scheme: env.ZOHO_SCHEME || "https",
  };
  // The three OAuth values are the minimum. The account id is fetched at
  // runtime if it is not set, so it is not part of the "configured" test.
  config.configured = Boolean(
    config.clientId && config.clientSecret && config.refreshToken
  );
  return config;
}

/**
 * Build an application/x-www-form-urlencoded body.
 *
 * Almost every value can be encoded normally - but NOT the percent sign.
 * Zoho client secrets contain a literal "%", and Zoho's token endpoint
 * rejects the percent-ENCODED form ("%25") with an HTTP 400 "Access
 * Denied" page instead of a normal OAuth error. The raw "%" has to go
 * through untouched.
 *
 * Everything else is still encoded, so a secret containing "&" or "+" or
 * a space cannot break the body apart.
 */
function formBody(params) {
  return Object.entries(params)
    .map(([key, value]) => {
      const raw = String(value == null ? "" : value);
      // Encode the characters that would otherwise break the body, but
      // leave "%" alone - Zoho wants it raw.
      const safe = raw
        .replace(/&/g, "%26")
        .replace(/\+/g, "%2B")
        .replace(/ /g, "%20")
        .replace(/=/g, "%3D");
      return `${key}=${safe}`;
    })
    .join("&");
}

/**
 * Exchange the refresh token for a fresh access token.
 *
 * The access token is short-lived, so this runs on every send. The refresh
 * token itself does not expire, which is why nothing here needs rotating.
 */
async function fetchAccessToken(config) {
  const body = formBody({
    grant_type: "refresh_token",
    client_id: config.clientId,
    client_secret: config.clientSecret,
    refresh_token: config.refreshToken,
  });

  const response = await fetch(`${config.scheme}://${config.accountsUrl}/oauth/v2/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: body,
  });

  const result = await response.json().catch(() => ({}));

  // Zoho's WAF answers some requests with an HTTP 400 "Access Denied"
  // HTML page instead of a JSON error. That is not an OAuth answer, so
  // the request is retried once with the standard percent-encoding - the
  // wall is sometimes a false positive on an unusual but legal body.
  if (response.status === 400 && !result.error) {
    console.warn(
      "[zoho] the token endpoint answered 400 with a wall page; retrying " +
        "with the standard encoding"
    );
    const retryBody = new URLSearchParams({
      grant_type: "refresh_token",
      client_id: config.clientId,
      client_secret: config.clientSecret,
      refresh_token: config.refreshToken,
    }).toString();
    const retry = await fetch(
      `${config.scheme}://${config.accountsUrl}/oauth/v2/token`,
      {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: retryBody,
      }
    );
    const retryResult = await retry.json().catch(() => ({}));
    if (retry.ok && retryResult.access_token) {
      return retryResult.access_token;
    }
    // Still a wall. Report the wall clearly, because it is a different
    // kind of failure from an OAuth error.
    throw new Error(
      `Zoho's server refused the token request (HTTP ${response.status}, ` +
        `an "Access Denied" page rather than an OAuth error). The account, ` +
        `client id or secret may have been blocked. Check the Zoho API ` +
        `console, and try again from a different network. ` +
        `[client_id=${config.clientId} region=${config.region} ` +
        `secret:${describeSecret(config.clientSecret)} ` +
        `token:${describeSecret(config.refreshToken)}]`
    );
  }

  if (!response.ok || !result.access_token) {
    // The most common cause by far: the token was minted in a different
    // region than the one configured. Say so, because the raw error
    // ("invalid_client") does not hint at it.
    const error = String(result.error || "unknown error");
    // What Zoho checks, and in what order, on the refresh_token grant:
    //   invalid_client        -> the CLIENT ID is not known here
    //   invalid_client_secret -> the client id is fine, the SECRET is wrong
    //   invalid_code          -> both are fine, the TOKEN is wrong/revoked
    // So the error names the first thing that is wrong. Say so, and show
    // the client id and region that were actually used - never the secret
    // or the token.
    let hint;
    if (/invalid_client_secret/i.test(error)) {
      hint = "The client id was accepted, so ZOHO_CLIENT_SECRET is wrong.";
    } else if (/invalid_client/i.test(error)) {
      hint =
        "ZOHO_CLIENT_ID was rejected - the client id in Netlify is not the " +
        "one this token was minted against. Check it for a stray " +
        "character, a different client, or an empty value.";
    } else if (/invalid_code/i.test(error)) {
      hint = "The client id and secret were accepted, so ZOHO_REFRESH_TOKEN " +
        "is wrong or revoked. Mint a new one.";
    } else {
      hint = "Check ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET and ZOHO_REFRESH_TOKEN.";
    }
    throw new Error(
      `Zoho token refresh failed (${response.status}): ${error} - ${hint} ` +
        `[client_id=${config.clientId} region=${config.region} ` +
        `secret:${describeSecret(config.clientSecret)} ` +
        `token:${describeSecret(config.refreshToken)}]`
    );
  }

  return result.access_token;
}

/**
 * Look up the account id when it was not configured.
 *
 * The account id is a number generated when the account was added to Zoho,
 * and it is needed in every send URL. It is fetched once per call here
 * rather than cached, because a function instance is short-lived anyway.
 */
async function fetchAccounts(config, accessToken) {
  const response = await fetch(`${config.scheme}://${config.mailUrl}/api/accounts`, {
    headers: {
      Authorization: `Zoho-oauthtoken ${accessToken}`,
      Accept: "application/json",
    },
  });

  const result = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      `Could not read the Zoho account id (${response.status}): ` +
        `${result.code || result.message || "unknown error"}`
    );
  }

  const accounts = Array.isArray(result.data) ? result.data : [];
  if (!accounts.length) {
    throw new Error(
      "Zoho returned no accounts. The token is probably not authorised for " +
        "this mailbox - check that the scope includes ZohoMail.accounts.READ."
    );
  }

  return accounts;
}

async function fetchAccountId(config, accessToken) {
  const accounts = await fetchAccounts(config, accessToken);
  return String(accounts[0].accountId);
}

/**
 * Send one email through the Zoho Mail API.
 *
 * @param {object} config   the settings from readZohoConfig()
 * @param {object} message
 * @param {string[]} message.to        the recipients
 * @param {string[]} [message.bcc]     blind copies - never visible to Milka
 * @param {string}   message.subject
 * @param {string}   message.text      the plain-text body
 * @param {string}   [message.replyTo] the guest, so Reply reaches them
 * @param {string}   [message.from]    the From address
 * @param {string}   [message.fromName] the display name
 * @returns {Promise<{id: string|null}>}
 */
/**
 * Describe a secret without revealing it.
 *
 * Only the shape is reported: the length, and which characters are
 * present. That is enough to spot a paste that carried a stray "%25",
 * a missing pair of quotes, or a truncated value - without printing the
 * credential itself.
 */
function describeSecret(value) {
  const raw = String(value == null ? "" : value);
  const flags = [];
  if (raw.includes("%")) flags.push("has%");
  if (raw.includes("%25")) flags.push("has%25");
  if (raw !== raw.trim()) flags.push("has-whitespace");
  if (raw.includes(" ")) flags.push("has-space");
  if (raw.includes("\n")) flags.push("has-newline");
  if (raw.includes("\r")) flags.push("has-cr");
  if (raw.includes("\t")) flags.push("has-tab");
  if (raw.includes('"')) flags.push("has-quote");
  if (raw.includes("'")) flags.push("has-apostrophe");
  if (raw.includes("&")) flags.push("has-amp");
  if (raw.includes("+")) flags.push("has-plus");
  if (raw.includes("=")) flags.push("has-equals");
  // The first and last few characters are safe to show when they are
  // ordinary letters or digits - enough to spot a copy-paste that
  // started in the wrong place, without revealing the credential.
  const edge = raw.slice(0, 4).replace(/[^A-Za-z0-9]/g, "") +
    ".." +
    raw.slice(-4).replace(/[^A-Za-z0-9]/g, "");
  // The full set of character codes. A secret is hex, so every code
  // should be in the 48-122 range and there should be nothing unusual
  // in it. This is the whole value's fingerprint without being the
  // value: a run of codes above 127 or a stray 0 shows a paste that
  // carried something invisible.
  const codes = Array.from(raw).map((c) => c.charCodeAt(0)).join(",");
  // Which characters are present at all, as a set of code points.
  const charset = Array.from(new Set(Array.from(raw).map((c) => c.charCodeAt(0))))
    .sort((a, b) => a - b)
    .join(",");
  return (
    `len=${raw.length} edge=${edge} charset=${charset}` +
    (flags.length ? " " + flags.join(" ") : "")
  );
}

/**
 * Compare two email addresses, ignoring case and any display name.
 */
function sameMailbox(a, b) {
  const bare = (value) =>
    String(value || "")
      .replace(/^[^<]*</, "")
      .replace(/>.*$/, "")
      .trim()
      .toLowerCase();
  const left = bare(a);
  const right = bare(b);
  return left !== "" && left === right;
}

/**
 * Read the account's primary mailbox address.
 *
 * Used as the From address when nothing is configured. The token is
 * scoped to this mailbox anyway, and Zoho only accepts a From address
 * the mailbox actually owns.
 */
async function fetchPrimaryMailbox(config, accessToken) {
  try {
    const response = await fetch(
      `${config.scheme}://${config.mailUrl}/api/accounts`,
      {
        headers: {
          Authorization: `Zoho-oauthtoken ${accessToken}`,
          Accept: "application/json",
        },
      }
    );
    const result = await response.json().catch(() => ({}));
    const accounts = Array.isArray(result.data) ? result.data : [];
    if (!accounts.length) return "";
    const account = accounts[0];
    // Zoho returns the address under different names depending on the
    // account type and the scope, so try each of them.
    const address =
      account.primaryEmailAddress ||
      account.emailAddress ||
      account.mailUrl ||
      "";
    // When nothing is found, say so in the log - an empty From is the
    // reason a send fails with a bare 404.
    if (!address) {
      console.warn(
        "[zoho] the account list has no primary address; keys:",
        Object.keys(account).join(",")
      );
    }
    return String(address);
  } catch (err) {
    console.warn("[zoho] could not read the account list:", err && err.message);
    return "";
  }
}

/**
 * Read the addresses the account owns: its primary mailbox plus every
 * confirmed alias.
 *
 * Zoho only accepts a From address the account actually owns, and an EMAIL
 * ALIAS of the account qualifies. The account list returns only the primary
 * address, so the detailed account record is fetched as well - it carries
 * the `emailAddress` array, where each entry says whether it is an alias
 * and whether it is confirmed.
 */
async function fetchAccountAddresses(config, accessToken, accountId) {
  const empty = { primary: "", aliases: [] };
  try {
    const response = await fetch(
      `${config.scheme}://${config.mailUrl}/api/accounts/${accountId}`,
      {
        headers: {
          Authorization: `Zoho-oauthtoken ${accessToken}`,
          Accept: "application/json",
        },
      }
    );
    const result = await response.json().catch(() => ({}));
    const account = (result && result.data) || {};
    if (!account || typeof account !== "object" || !Object.keys(account).length) {
      return empty;
    }

    const list = Array.isArray(account.emailAddress) ? account.emailAddress : [];
    const addresses = list
      .map((entry) => ({
        address: String(entry.mailId || entry.emailAddress || entry.address || ""),
        isAlias: entry.isAlias === true,
        isPrimary: entry.isPrimary === true,
        isConfirmed: entry.isConfirmed !== false,
      }))
      .filter((entry) => entry.address);

    const primary =
      account.primaryEmailAddress ||
      (addresses.find((e) => e.isPrimary) || addresses.find((e) => !e.isAlias) || {}).address ||
      "";

    const aliases = addresses
      .filter((entry) => entry.address && entry.isConfirmed && !entry.isPrimary)
      .map((entry) => entry.address);

    return { primary: String(primary), aliases };
  } catch (err) {
    console.warn("[zoho] could not read the account details:", err && err.message);
    return empty;
  }
}

export async function sendZohoMail(config, message) {
  const accessToken = await fetchAccessToken(config);

  // The account id is normally fetched at runtime. A configured
  // ZOHO_ACCOUNT_ID is used as-is, but if it turns out to be wrong the
  // send fails with a 404 and the reason is invisible - so fall back to
  // looking the real ones up rather than failing on a stale value.
  //
  // A Zoho user can have SEVERAL accounts, each with its own account id
  // (an external POP/IMAP account is one of them). Only the account that
  // owns the From address can send, so every account is tried until one
  // of them works.
  const allAccounts = await fetchAccounts(config, accessToken);
  const accountIds = [];
  if (config.accountId) accountIds.push(String(config.accountId));
  for (const account of allAccounts) {
    const id = String(account.accountId || "");
    if (id && !accountIds.includes(id)) accountIds.push(id);
  }
  // Report what the account list actually contains. A Zoho account can be
  // a personal mailbox, an organisation, or an external POP account, and
  // only some of them can send.
  const accountSummary = allAccounts.map((a) => ({
    accountId: a.accountId,
    primaryEmailAddress: a.primaryEmailAddress,
    accountName: a.accountName,
    accountType: a.accountType,
  }));
  console.warn("[zoho] accounts:", JSON.stringify(accountSummary));
  // Carried in the error, so the detail is visible without the logs.
  config.accountSummary = accountSummary;
  if (!accountIds.length) {
    throw new Error("Zoho returned no usable account id.");
  }
  let lastError = null;
  for (const accountId of accountIds) {
    try {
      return await sendWithAccount(config, message, accountId, accessToken);
    } catch (err) {
      lastError = err;
      if (!/404/.test(String(err && err.message))) throw err;
      // 404 = this account cannot send. Try the next one.
      console.warn("[zoho] account " + accountId + " cannot send; trying the next.");
    }
  }
  throw lastError;
}

/**
 * Send one message through one Zoho account.
 */
async function sendWithAccount(config, message, accountId, accessToken) {
  // Zoho wants the From as a bare address. The display name goes in
  // `fromDisplayName` instead of being folded into the address.
  //
  // The From must be an address the account actually owns, or one of its
  // aliases. A configured ZOHO_FROM_EMAIL that is neither is rejected by
  // Zoho with a bare 404, so it is checked against the account and
  // ignored when it does not belong.
  const accountMailbox = await fetchPrimaryMailbox(config, accessToken);
  // The account's own aliases are valid senders too - a Zoho email alias
  // is an address the account owns, so a lodge-style From address can be
  // used as long as the alias really exists on this account.
  const { aliases } = await fetchAccountAddresses(config, accessToken, accountId);
  const ownedAddresses = [accountMailbox, ...aliases].filter(Boolean);

  const configured = message.from || config.fromEmail || "";
  let fromAddress = "";
  if (configured) {
    const isOwned = ownedAddresses.some((address) => sameMailbox(configured, address));
    if (!accountMailbox || isOwned) {
      fromAddress = configured;
    } else {
      console.warn(
        "[zoho] the configured From address is not an address this account owns -",
        "using",
        accountMailbox,
        "instead of",
        configured,
        "| owned:",
        JSON.stringify(ownedAddresses)
      );
    }
  }
  if (!fromAddress) {
    fromAddress = accountMailbox;
  }
  if (!fromAddress) {
    throw new Error(
      "Zoho send: no From address. Set ZOHO_FROM_EMAIL to an address the " +
      "mailbox owns, or make sure the token can read the account list."
    );
  }

  const payload = {
    fromAddress,
    toAddress: message.to.join(","),
    subject: message.subject,
    content: message.text,
    encoding: "UTF-8",
    isScheduleSend: false,
  };

  if (message.fromName || config.fromName) {
    payload.fromDisplayName = message.fromName || config.fromName;
  }
  // The blind copy. Milka never sees this address, so she can forward the
  // enquiry to a guide or a supplier without exposing it.
  if (message.bcc && message.bcc.length) {
    payload.bccAddress = message.bcc.join(",");
  }
  // Reply-To is the guest, so pressing reply in Milka's inbox reaches them.
  if (message.replyTo) {
    payload.replyTo = message.replyTo;
  }

  const response = await fetch(
    `${config.scheme}://${config.mailUrl}/api/accounts/${accountId}/messages`,
    {
      method: "POST",
      headers: {
        Authorization: `Zoho-oauthtoken ${accessToken}`,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  const result = await response.json().catch(() => ({}));

  if (!response.ok) {
    const messageText = String(result.message || result.error || "");
    // A 404 means THIS account cannot send - the caller tries the next
    // account id. Anything else is a real error and stops here.
    if (response.status === 404) {
      // An empty 404 on this endpoint is what Zoho returns when the
      // mailbox is on a FREE Zoho Workplace plan and the recipient is
      // EXTERNAL. The request is accepted, then dropped. It also happens
      // when the account id belongs to an account that cannot send, so
      // the caller tries the next account id first.
      throw new Error(
        `Zoho rejected the message (404) for account ${accountId}: ` +
          `${messageText || "no detail"} [url=${config.mailUrl} ` +
          `accounts=${JSON.stringify(config.accountSummary || [])} ` +
          `hint=On a FREE Zoho Workplace mailbox the Mail API cannot send ` +
          `to external recipients - use the SMTP transport, or a Zoho ` +
          `account with a custom domain]`
      );
    }
    // The usual causes, named precisely so the logs are useful.
    let hint = "";
    if (/invalid.*sender|from.*address|not.*allowed/i.test(messageText)) {
      hint =
        " The From address is not an alias of this Zoho mailbox - set " +
        "ZOHO_FROM_EMAIL to an address the mailbox actually owns.";
    } else if (/quota|limit|exceed/i.test(messageText)) {
      hint = " The mailbox has hit its sending limit - Zoho applies a " +
        "rolling 1-hour limit on free accounts.";
    } else if (/invalid.*token|unauthor/i.test(messageText)) {
      hint = " The access token was rejected - check ZOHO_REGION matches the " +
        "data centre the token was created in.";
    }
    throw new Error(
      `Zoho rejected the message (${response.status}): ${messageText}${hint}` +
        ` [account_id=${accountId} from=${fromAddress} ` +
        `mailbox=${accountMailbox || "(not found)"}]`
    );
  }

  return { id: result.id || null };
}
