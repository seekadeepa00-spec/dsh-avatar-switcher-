// dsh-plugin-avatar-switcher — host half (v4)
// v4 = 图库：上传不再删旧图，state.json 记当前选中，支持列举 / 切换 / 单张删除。
import { createHash, randomBytes } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, readdirSync, renameSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';

export const name = 'dsh-plugin-avatar-switcher';
export const inject = ['webServer'];

const BASE = '/avatar-switcher';
const SIDES = ['user', 'ai'];
const MAX_BYTES = 8 * 1024 * 1024;
const QUOTA_BYTES = 64 * 1024 * 1024;
const LIBRARY_MAX = 60;
const ABI = 2;

const CAPABILITIES = {
  abi: ABI,
  layers: ['css', 'dom'],
  contentAddressed: true,
  health: true,
  library: true,
};

const MIME_OF_EXT = { png: 'image/png', jpg: 'image/jpeg', webp: 'image/webp' };
const NAME_RE = /^(user|ai)-[a-z0-9]{4,64}\.(png|jpg|webp)$/;

function rootDir() {
  const d = join(homedir(), '.dsh-avatar-switcher');
  if (!existsSync(d)) mkdirSync(d, { recursive: true });
  return d;
}

function avatarsDir() {
  const d = join(rootDir(), 'avatars');
  if (!existsSync(d)) mkdirSync(d, { recursive: true });
  return d;
}

function tokenPath() {
  return join(rootDir(), 'token');
}

function statePath() {
  return join(rootDir(), 'state.json');
}

function healthPath() {
  return join(rootDir(), 'health.json');
}

function readToken() {
  const p = tokenPath();
  if (existsSync(p)) {
    const t = readFileSync(p, 'utf8').trim();
    if (t.length >= 16) return t;
  }
  const t = randomBytes(16).toString('hex');
  writeFileSync(p, t, { mode: 0o600 });
  return t;
}

function sniff(buf) {
  if (buf.length >= 8 && buf[0] === 0x89 && buf[1] === 0x50 && buf[2] === 0x4e && buf[3] === 0x47) return 'png';
  if (buf.length >= 3 && buf[0] === 0xff && buf[1] === 0xd8 && buf[2] === 0xff) return 'jpg';
  if (buf.length >= 12 && buf.toString('ascii', 0, 4) === 'RIFF' && buf.toString('ascii', 8, 12) === 'WEBP') return 'webp';
  return null;
}

function readState() {
  const p = statePath();
  if (!existsSync(p)) return { user: null, ai: null };
  try {
    const o = JSON.parse(readFileSync(p, 'utf8'));
    const out = { user: null, ai: null };
    for (const s of SIDES) if (typeof o[s] === 'string' && NAME_RE.test(o[s])) out[s] = o[s];
    return out;
  } catch {
    return { user: null, ai: null };
  }
}

function writeState(next) {
  const p = statePath();
  const tmp = p + '.tmp-' + process.pid + '-' + Date.now();
  writeFileSync(tmp, JSON.stringify({ user: next.user || null, ai: next.ai || null, at: Date.now() }));
  renameSync(tmp, p);
}

// 全部条目，按 mtime 倒序；active 由 state.json 决定（state 缺失/失效时回落到最新一张）
function library() {
  const dir = avatarsDir();
  const st = readState();
  const items = [];
  for (const f of readdirSync(dir)) {
    if (!NAME_RE.test(f)) continue;
    let s;
    try { s = statSync(join(dir, f)); } catch { continue; }
    const side = f.slice(0, f.indexOf('-'));
    items.push({
      side,
      name: f,
      bytes: s.size,
      mtime: s.mtimeMs,
      sha: f.replace(/^(user|ai)-/, '').split('.')[0],
      active: st[side] === f,
    });
  }
  items.sort((a, b) => b.mtime - a.mtime);

  const live = { user: null, ai: null };
  for (const s of SIDES) {
    const hit = items.find((x) => x.side === s && x.active);
    if (hit) live[s] = hit.name;
    else {
      const newest = items.find((x) => x.side === s);
      live[s] = newest ? newest.name : null;
      if (newest) newest.active = true;
    }
  }
  return { items, live };
}

function fileOf(side) {
  const { live } = library();
  return live[side] || null;
}

function totalBytes() {
  const dir = avatarsDir();
  let n = 0;
  for (const f of readdirSync(dir)) {
    try { n += statSync(join(dir, f)).size; } catch { /* race */ }
  }
  return n;
}

function readHealth() {
  const p = healthPath();
  if (!existsSync(p)) return null;
  try { return JSON.parse(readFileSync(p, 'utf8')); } catch { return null; }
}

function json(res, code, obj, extra) {
  const body = Buffer.from(JSON.stringify(obj));
  res.writeHead(code, Object.assign({
    'content-type': 'application/json; charset=utf-8',
    'content-length': body.length,
    'cache-control': 'no-store',
    'x-content-type-options': 'nosniff',
  }, extra || {}));
  res.end(body);
}

function serveImage(res, buf, ext, method) {
  res.writeHead(200, {
    'content-type': MIME_OF_EXT[ext] || 'application/octet-stream',
    'content-length': buf.length,
    'cache-control': 'private, max-age=31536000, immutable',
    'x-content-type-options': 'nosniff',
    'content-security-policy': "default-src 'none'; style-src 'unsafe-inline'",
  });
  res.end(method === 'HEAD' ? undefined : buf);
}

function browserWriteBlocked(req, token) {
  const origin = req.headers['origin'];
  const sfs = req.headers['sec-fetch-site'];
  if (!origin && !sfs) return false; // 本机 CLI / curl / 桌面 GUI
  const got = req.headers['x-avatar-token'];
  return got !== token;
}

function readBody(req, limit) {
  const cap = limit || MAX_BYTES + 1024;
  return new Promise((resolve, reject) => {
    const chunks = [];
    let size = 0;
    req.on('data', (c) => {
      size += c.length;
      if (size > cap) { reject(new Error('too-large')); req.destroy(); return; }
      chunks.push(c);
    });
    req.on('end', () => resolve(Buffer.concat(chunks)));
    req.on('error', reject);
  });
}

// 配额满了先淘汰最旧的、非当前选中的图，不动正在用的那张
function evictFor(needBytes) {
  const dir = avatarsDir();
  let guard = 0;
  while (totalBytes() + needBytes > QUOTA_BYTES && guard++ < 200) {
    const { items } = library();
    const victim = items.filter((x) => !x.active).pop() || null;
    if (!victim) return false;
    try { rmSync(join(dir, victim.name)); } catch { break; }
  }
  return totalBytes() + needBytes <= QUOTA_BYTES;
}

export function apply(ctx) {
  const token = readToken();
  const webServer = ctx.webServer;

  async function handle(req, res) {
    const url = new URL(req.url, 'http://x');
    const rest = url.pathname.slice(BASE.length).replace(/^\/+/, '').replace(/\/+$/, '');
    const method = req.method || 'GET';
    const write = method !== 'GET' && method !== 'HEAD';
    const blocked = write && browserWriteBlocked(req, token);
    const deny = () => json(res, 401, { error: 'token-required', tokenPath: tokenPath() });

    if (rest === '' || rest === 'state') {
      if (write) return json(res, 405, { error: 'method' });
      const { items, live } = library();
      return json(res, 200, {
        ok: true,
        user: live.user,
        ai: live.ai,
        dir: avatarsDir(),
        count: items.length,
        capabilities: CAPABILITIES,
        tokens: { requiredForBrowserWrites: true, path: tokenPath() },
        limits: { maxBytes: MAX_BYTES, quotaBytes: QUOTA_BYTES, usedBytes: totalBytes(), libraryMax: LIBRARY_MAX },
        health: readHealth(),
      });
    }

    if (rest === 'library') {
      if (method === 'DELETE') {
        if (blocked) return deny();
        const dir = avatarsDir();
        let removed = 0;
        for (const f of readdirSync(dir)) {
          if (!NAME_RE.test(f)) continue;
          try { rmSync(join(dir, f)); removed++; } catch { /* race */ }
        }
        writeState({ user: null, ai: null });
        return json(res, 200, { ok: true, removed });
      }
      if (write) return json(res, 405, { error: 'method' });
      const { items, live } = library();
      return json(res, 200, { ok: true, user: live.user, ai: live.ai, items, usedBytes: totalBytes(), quotaBytes: QUOTA_BYTES });
    }

    // POST /library/apply  {"side":"user","name":"user-abc123.png"}  —— 选中图库里已有的一张
    if (rest === 'library/apply') {
      if (method !== 'POST') return json(res, 405, { error: 'method' });
      if (blocked) return deny();
      let raw;
      try { raw = await readBody(req, 8192); } catch { return json(res, 413, { error: 'too-large' }); }
      let rep;
      try { rep = JSON.parse(raw.toString('utf8')); } catch { return json(res, 400, { error: 'bad-json' }); }
      const target = String(rep.name || '');
      if (!NAME_RE.test(target)) return json(res, 400, { error: 'bad-name', hint: 'user-<hex>.png | ai-<hex>.png' });
      const side = target.slice(0, target.indexOf('-'));
      if (!existsSync(join(avatarsDir(), target))) return json(res, 404, { error: 'not-found', name: target });
      const st = readState();
      st[side] = target;
      writeState(st);
      return json(res, 200, { ok: true, side, name: target, user: st.user, ai: st.ai });
    }

    // DELETE /library/item/<name> —— 删单张（若正被使用则同时清空选中）
    if (rest.startsWith('library/item/')) {
      if (method !== 'DELETE') return json(res, 405, { error: 'method' });
      if (blocked) return deny();
      const target = decodeURIComponent(rest.slice('library/item/'.length));
      if (!NAME_RE.test(target)) return json(res, 400, { error: 'bad-name' });
      const side = target.slice(0, target.indexOf('-'));
      const p = join(avatarsDir(), target);
      if (!existsSync(p)) return json(res, 404, { error: 'not-found', name: target });
      try { rmSync(p); } catch { return json(res, 500, { error: 'unlink-failed' }); }
      const st = readState();
      if (st[side] === target) { st[side] = null; writeState(st); }
      const { live } = library();
      return json(res, 200, { ok: true, removed: target, user: live.user, ai: live.ai });
    }

    if (rest === 'health') {
      if (!write) return json(res, 200, { ok: true, health: readHealth() });
      if (method !== 'POST') return json(res, 405, { error: 'method' });
      if (blocked) return deny();
      let raw;
      try { raw = await readBody(req, 65536); } catch { return json(res, 413, { error: 'too-large' }); }
      let rep;
      try { rep = JSON.parse(raw.toString('utf8')); } catch { return json(res, 400, { error: 'bad-json' }); }
      const rec = {
        layer: String(rep.layer || 'none').slice(0, 16),
        rows: Number(rep.rows) || 0,
        mountedAt: Number(rep.mountedAt) || Date.now(),
        abi: Number(rep.abi) || 0,
        at: Date.now(),
      };
      try { writeFileSync(healthPath(), JSON.stringify(rec)); } catch { /* read-only home */ }
      return json(res, 200, { ok: true, health: rec });
    }

    if (rest === 'all') {
      if (method !== 'DELETE') return json(res, 405, { error: 'method' });
      if (blocked) return deny();
      const dir = avatarsDir();
      let removed = 0;
      for (const f of readdirSync(dir)) {
        if (!NAME_RE.test(f)) continue;
        try { rmSync(join(dir, f)); removed++; } catch { /* race */ }
      }
      writeState({ user: null, ai: null });
      try { rmSync(healthPath(), { force: true }); } catch { /* race */ }
      return json(res, 200, { ok: true, removed });
    }

    const side = rest.split('/')[0];
    if (!SIDES.includes(side)) return json(res, 400, { error: 'bad-side', sides: SIDES });

    if (!write) {
      const f = fileOf(side);
      if (!f) return json(res, 404, { error: 'not-set', side });
      const buf = readFileSync(join(avatarsDir(), f));
      return serveImage(res, buf, f.split('.').pop(), method);
    }

    // DELETE /<side> —— 只取消选中，图留在库里
    if (method === 'DELETE') {
      if (blocked) return deny();
      const st = readState();
      const had = st[side];
      st[side] = null;
      writeState(st);
      const { live } = library();
      return json(res, 200, { ok: true, side, cleared: had, user: live.user, ai: live.ai });
    }

    if (method !== 'POST') return json(res, 405, { error: 'method' });
    if (blocked) return deny();

    let buf;
    try { buf = await readBody(req); } catch { return json(res, 413, { error: 'too-large' }); }
    if (!buf.length) return json(res, 400, { error: 'empty body' });
    const ext = sniff(buf);
    if (!ext) return json(res, 415, { error: 'not a real png/jpeg/webp' });

    const sha = createHash('sha256').update(buf).digest('hex').slice(0, 12);
    const fname = side + '-' + sha + '.' + ext;
    const dir = avatarsDir();
    const target = join(dir, fname);
    const already = existsSync(target);

    if (!already) {
      if (!evictFor(buf.length)) {
        return json(res, 507, { error: 'quota exceeded', usedBytes: totalBytes(), quotaBytes: QUOTA_BYTES });
      }
      const tmp = join(dir, '.tmp-' + process.pid + '-' + Date.now());
      writeFileSync(tmp, buf);
      renameSync(tmp, target);
    }

    const st = readState();
    st[side] = fname;
    writeState(st);

    const { items } = library();
    return json(res, 200, {
      ok: true,
      side,
      name: fname,
      bytes: buf.length,
      sha,
      deduped: already,
      count: items.length,
      user: st.user,
      ai: st.ai,
    });
  }

  let disposed = false;
  const teardown = () => {
    if (disposed) return;
    disposed = true;
  };

  const routes = [];
  const disposer = webServer.register({ kind: 'prefix', path: BASE, handler: (req, res) => {
    Promise.resolve(handle(req, res)).catch((err) => {
      try { json(res, 500, { error: 'internal', message: String((err && err.message) || err) }); } catch { /* headers sent */ }
    });
  } });
  if (typeof disposer === 'function') routes.push(disposer);

  const dispose = () => {
    teardown();
    for (const d of routes.splice(0)) { try { d(); } catch { /* already gone */ } }
  };

  if (typeof ctx.effect === 'function') ctx.effect(() => dispose, 'avatar-switcher: routes');

  teardown.dispose = dispose;
  return teardown;
}
