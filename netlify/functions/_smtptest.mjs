// TEMPORARY diagnostic: can we complete a full SMTP session from the Netlify runtime?
import tls from 'node:tls';
import net from 'node:net';

function readReply(sock) {
  return new Promise((resolve, reject) => {
    let buf = '';
    const onData = (d) => {
      buf += d.toString('utf8');
      // multiline: "250-EXT\r\n250 OK\r\n"
      if (/^\d{3} /.test(buf.split(/\r?\n/).filter(Boolean).slice(-1)[0] || '')) {
        sock.off('data', onData);
        resolve(buf);
      }
    };
    sock.on('data', onData);
    sock.on('error', reject);
    setTimeout(() => { sock.off('data', onData); resolve(buf); }, 6000);
  });
}

export const handler = async () => {
  const log = [];
  const say = (s) => { log.push(s); };
  try {
    const sock = tls.connect({ host: 'smtp.zoho.com', port: 465, servername: 'smtp.zoho.com', timeout: 8000 });
    await new Promise((res, rej) => { sock.once('secureConnect', res); sock.once('error', rej); sock.once('timeout', () => rej(new Error('tls timeout'))); });
    const b1 = await readReply(sock); say('TLS: ' + String(b1).split(/\r?\n/)[0]);

    sock.write('EHLO probe.netlify.app\r\n');
    const b2 = await readReply(sock); say('EHLO: ' + String(b2).split(/\r?\n/)[0]);

    sock.write('QUIT\r\n');
    sock.end();
    say('RESULT: TLS + EHLO succeeded on port 465 from the Netlify runtime');
  } catch (e) {
    say('FAILED: ' + (e.code || e.message));
  }
  return { statusCode: 200, headers: {'content-type':'text/plain'}, body: log.join('\n') };
};
