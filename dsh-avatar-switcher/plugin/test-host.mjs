// 假 webServer 挂载 + 图库全链路冒烟。用法：node test-host.mjs
import { mkdirSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const HOME = mkdtempSync(join(tmpdir(), 'das-test-'));
process.env.USERPROFILE = HOME;
process.env.HOME = HOME;
mkdirSync(HOME, { recursive: true });

const mod = await import('./lib/index.js');

const PNG_A = Buffer.concat([Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]), Buffer.from('AAA-playload-1'.repeat(8))]);
const PNG_B = Buffer.concat([Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]), Buffer.from('BBB-payload-2'.repeat(8))]);

let route = null;
const ctx = {
  webServer: { register(opts) { route = opts; return () => { route = null; }; } },
  effect(fn) { fn(); return () => {}; },
};

const teardown = mod.apply(ctx, {});
console.log('name =', mod.name, '| inject =', JSON.stringify(mod.inject), '| route =', route && route.kind, route && route.path);

function call(method, path, body, headers) {
  return new Promise((resolve) => {
    const chunks = [];
    const req = {
      method,
      url: path,
      headers: Object.assign({}, headers || {}),
      on(ev, cb) {
        if (ev === 'data' && body) { chunks.push(body); cb(body); }
        if (ev === 'end') cb();
        return req;
      },
      destroy() {},
    };
    const res = {
      statusCode: 0,
      headers: {},
      body: Buffer.alloc(0),
      writeHead(code, h) { this.statusCode = code; this.headers = h || {}; },
      end(b) { this.body = b ? Buffer.from(b) : Buffer.alloc(0); resolve(this); },
    };
    route.handler(req, res);
  });
}

const show = (label, r) => {
  const txt = r.headers['content-type'] && String(r.headers['content-type']).includes('json')
    ? r.body.toString('utf8')
    : 'bytes=' + r.body.length + ' magic=' + r.body.slice(0, 8).toString('hex');
  console.log(label, '->', r.statusCode, txt.slice(0, 220));
  return r;
};

let r;

r = await call('GET', '/avatar-switcher/state');
show('GET /state', r);
const cap = JSON.parse(r.body.toString('utf8')).capabilities;
console.log('  abi =', cap.abi, '| library =', cap.library);

r = await call('POST', '/avatar-switcher/user', PNG_A, { 'content-type': 'image/png' });
show('POST /user A', r);
const nameA = JSON.parse(r.body.toString('utf8')).name;

r = await call('POST', '/avatar-switcher/user', PNG_B, { 'content-type': 'image/png' });
show('POST /user B', r);
const nameB = JSON.parse(r.body.toString('utf8')).name;
console.log('  A =', nameA, '| B =', nameB, '| kept both =', nameA !== nameB);

r = await call('GET', '/avatar-switcher/library');
show('GET /library', r);
console.log('  items =', JSON.parse(r.body.toString('utf8')).items.length);

r = await call('POST', '/avatar-switcher/library/apply', Buffer.from(JSON.stringify({ name: nameA })), { 'content-type': 'application/json' });
show('POST /library/apply -> A', r);

r = await call('GET', '/avatar-switcher/user');
show('GET /user (should be A)', r);
console.log('  is A =', r.body.equals(PNG_A));

r = await call('GET', '/avatar-switcher/library');
console.log('  active after apply =', JSON.parse(r.body.toString('utf8')).user);

r = await call('DELETE', '/avatar-switcher/library/item/' + encodeURIComponent(nameA), null, {});
show('DELETE /library/item A', r);

r = await call('GET', '/avatar-switcher/library');
const lib2 = JSON.parse(r.body.toString('utf8'));
console.log('  remaining =', lib2.items.map((x) => x.name).join(','), '| user now =', lib2.user);

r = await call('POST', '/avatar-switcher/ai', PNG_A, { 'content-type': 'image/png' });
show('POST /ai', r);

r = await call('DELETE', '/avatar-switcher/user', null, {});
show('DELETE /user (clear only)', r);

r = await call('POST', '/avatar-switcher/library/apply', Buffer.from(JSON.stringify({ name: '../evil.png' })), { 'content-type': 'application/json' });
show('POST /library/apply ../evil.png', r);

r = await call('POST', '/avatar-switcher/library/apply', Buffer.from(JSON.stringify({ name: 'user-000000000000.png' })), { 'content-type': 'application/json' });
show('POST /library/apply missing', r);

r = await call('POST', '/avatar-switcher/library/apply', Buffer.from(JSON.stringify({ name: nameB })), { 'content-type': 'application/json', origin: 'http://evil.example' });
show('POST /library/apply (browser, no token)', r);

r = await call('DELETE', '/avatar-switcher/library', null, {});
show('DELETE /library', r);

r = await call('GET', '/avatar-switcher/state');
show('GET /state (empty)', r);

teardown.dispose();
console.log('state dir =', join(HOME, '.dsh-avatar-switcher'));
rmSync(HOME, { recursive: true, force: true });
