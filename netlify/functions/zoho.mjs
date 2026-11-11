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
 * `guesthousesobic@blink2ask.com` exactly as if Milka had sent it from
 * Zoho webmail. No domain verification is needed and no DKIM setup is
 * needed - which is the whole reason this transport exists.
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
 * Exchange the refresh token for a fresh access token.
 *
 * The access token is short-lived, so this runs on every send. The refresh
 * token itself does not expire, which is why nothing here needs rotating.
 */
async function fetchAccessToken(config) {
  const body = new URLSearchParams({
    grant_type: "refresh_token",
    client_id: config.clientId,
    client_secret: config.clientSecret,
    refresh_token: config.refreshToken,
  });

  const response = await fetch(`${config.scheme}://${config.accountsUrl}/oauth/v2/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: body.toString(),
  });

  const result = await response.json().catch(() => ({}));

  if (!response.ok || !result.access_token) {
    // The most common cause by far: the token was minted in a different
    // region than the one configured. Say so, because the raw error
    // ("invalid_client") does not hint at it.
    const hint = /invalid_client/i.test(String(result.error || ""))
      ? "That usually means ZOHO_REGION does not match the data centre the " +
        "account and token belong to. A European account is 'eu', not 'us'."
      : "Check ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET and ZOHO_REFRESH_TOKEN.";
    throw new Error(
      `Zoho token refresh failed (${response.status}): ` +
        `${result.error || "unknown error"} - ${hint}`
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
async function fetchAccountId(config, accessToken) {
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
export async function sendZohoMail(config, message) {
  const accessToken = await fetchAccessToken(config);

  const accountId = config.accountId
    ? String(config.accountId)
    : await fetchAccountId(config, accessToken);

  // Zoho wants the From as a bare address. The display name goes in
  // `fromDisplayName` instead of being folded into the address.
  const fromAddress = message.from || config.fromEmail || "";

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
      `Zoho rejected the message (${response.status}): ${messageText}${hint}`
    );
  }

  return { id: result.id || null };
}
