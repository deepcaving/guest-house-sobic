// TEMPORARY diagnostic: which outbound ports can the Netlify runtime reach?
import net from 'node:net';

export const handler = async () => {
  const HOST = 'smtp.zoho.com';
  const out = [];
  for (const port of [25, 465, 587]) {
    const t0 = Date.now();
    try {
      await new Promise((resolve, reject) => {
        const s = net.connect({ host: HOST, port, timeout: 8000 });
        s.on('connect', () => { s.destroy(); resolve(); });
        s.on('timeout', () => { s.destroy(); reject(new Error('timeout')); });
        s.on('error', reject);
      });
      out.push({ port, open: true, ms: Date.now() - t0 });
    } catch (e) {
      out.push({ port, open: false, error: e.code || e.message, ms: Date.now() - t0 });
    }
  }
  return { statusCode: 200, headers: {'content-type':'application/json'}, body: JSON.stringify(out) };
};
