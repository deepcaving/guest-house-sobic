// TEMPORARY: prove the Zoho transport is reached and executed live.
import { readZohoConfig, sendZohoMail } from "./zoho.mjs";
export const handler = async () => {
  const c = readZohoConfig({
    ZOHO_CLIENT_ID: 'dummy', ZOHO_CLIENT_SECRET: 'dummy', ZOHO_REFRESH_TOKEN: 'dummy',
  });
  const out = { configured: c.configured, region: c.accountsUrl };
  try {
    await sendZohoMail(c, { to: ['x@y.z'], subject: 't', text: 'b' });
    out.result = 'sent (unexpected with dummy creds)';
  } catch (e) {
    out.error = String(e.message);
    out.reachedZoho = /invalid_client|Zoho token refresh failed/i.test(String(e.message));
  }
  return { statusCode: 200, headers: {'content-type':'application/json'}, body: JSON.stringify(out) };
};
