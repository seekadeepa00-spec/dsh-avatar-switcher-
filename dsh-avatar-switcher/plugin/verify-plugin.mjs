// verify-plugin.mjs — DSH 插件契约静态校验，装进 bundle 前先跑这一条
// 用法: node verify-plugin.mjs <插件包目录>
// 退出码: 0 = 合规可装载, 1 = 有致命问题
import { readFileSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const dir = resolve(process.argv[2] || '.');
const errs = [];
const warns = [];
const ok = (m) => console.log('  OK   ' + m);
const bad = (m) => { errs.push(m); console.log('  FAIL ' + m); };
const warn = (m) => { warns.push(m); console.log('  WARN ' + m); };

console.log('plugin: ' + dir);

// --- 1. package.json 清单
const pkgPath = join(dir, 'package.json');
if (!existsSync(pkgPath)) { bad('package.json 缺失'); }
else {
  const pkg = JSON.parse(readFileSync(pkgPath, 'utf8'));
  pkg.name ? ok('name = ' + pkg.name) : bad('package.json 缺 name');
  pkg.type === 'module' ? ok('type = module') : warn('type 不是 module');
  const dsh = pkg.dsh || {};
  dsh.id ? ok('dsh.id = ' + dsh.id) : bad('dsh.id 缺失（bundle 安装必需）');
  dsh.bundle && dsh.bundle.patch ? ok('dsh.bundle.patch = ' + dsh.bundle.patch) : bad('dsh.bundle.patch 缺失');
  dsh.client && dsh.client.platform === 'web' ? ok('dsh.client.platform = web') : warn('dsh.client 未声明 web');
  if (dsh.client && Array.isArray(dsh.client.inject)) ok('dsh.client.inject = ' + JSON.stringify(dsh.client.inject));
  else warn('dsh.client.inject 不是数组');
  const exp = pkg.exports || {};
  exp['.'] ? ok('exports["."] = ' + exp['.']) : bad('exports["."] 缺失');
  exp['./client'] ? ok('exports["./client"] = ' + exp['./client']) : warn('exports["./client"] 缺失（浏览器半边不会加载）');
  const patchRel = (dsh.bundle && dsh.bundle.patch) || './cordis.patch.yml';
  existsSync(join(dir, patchRel)) ? ok('patch 文件存在 ' + patchRel) : bad('patch 文件缺失 ' + patchRel);
}

// --- 2. 宿主半边：ESM 动态导入，校验 name/inject/apply
const hostRel = (() => {
  try { return JSON.parse(readFileSync(pkgPath, 'utf8')).exports?.['.'] || './lib/index.js'; } catch { return './lib/index.js'; }
})();
const hostPath = join(dir, hostRel);
if (!existsSync(hostPath)) bad('宿主入口缺失 ' + hostRel);
else {
  try {
    const host = await import(pathToFileURL(hostPath).href + '?t=' + Date.now());
    typeof host.name === 'string' && host.name ? ok('host.name = ' + host.name) : bad('host 未导出 name');
    Array.isArray(host.inject) ? ok('host.inject = ' + JSON.stringify(host.inject)) : bad('host 未导出 inject 数组');
    typeof host.apply === 'function' ? ok('host.apply 是函数') : bad('host 未导出 apply（cordis 会抛 invalid plugin）');
  } catch (e) {
    bad('宿主入口导入抛异常: ' + e.message);
  }
}

// --- 3. 浏览器半边：桩一个 __ModuleLoader__，抓 exports 再断言契约
const clientPath = join(dir, 'lib', 'client.js');
if (!existsSync(clientPath)) warn('lib/client.js 不存在，跳过浏览器半边校验');
else {
  let captured = null;
  globalThis.window = {
    __ModuleLoader__: { load: (spec) => { captured = spec && spec.factory ? spec.factory(() => ({})) : null; } },
    addEventListener() {}, removeEventListener() {}, matchMedia: () => ({ matches: false, addEventListener() {} }),
    localStorage: { getItem: () => null, setItem() {} },
    location: { href: 'http://127.0.0.1/', origin: 'http://127.0.0.1' },
  };
  const stubEl = () => ({
    style: {}, dataset: {}, classList: { add() {}, remove() {}, contains: () => false, toggle() {} },
    appendChild(c) { return c; }, insertBefore(c) { return c; }, removeChild(c) { return c; }, remove() {},
    setAttribute() {}, getAttribute: () => null, removeAttribute() {}, hasAttribute: () => false,
    addEventListener() {}, removeEventListener() {}, querySelector: () => null, querySelectorAll: () => [],
    contains: () => false, children: [], childNodes: [], tagName: 'DIV', textContent: '', innerHTML: '',
  });
  globalThis.document = {
    readyState: 'complete', addEventListener() {}, removeEventListener() {},
    querySelector: () => null, querySelectorAll: () => [], getElementById: () => null,
    createElement: (t) => { const e = stubEl(); e.tagName = String(t).toUpperCase(); return e; },
    createElementNS: () => stubEl(), createTextNode: () => stubEl(), contains: () => false,
    head: stubEl(), body: stubEl(), documentElement: stubEl(),
  };
  globalThis.MutationObserver = class { observe() {} disconnect() {} };
  globalThis.fetch = async () => ({ ok: false, json: async () => ({}) });
  globalThis.requestIdleCallback = (fn) => setTimeout(fn, 0);
  try {
    readFileSync(clientPath, 'utf8');
    globalThis.eval(readFileSync(clientPath, 'utf8'));
    if (!captured) bad('client.js 没有走 window.__ModuleLoader__.load()');
    else {
      const cl = captured.default && typeof captured.default === 'object' ? captured.default : captured;
      typeof cl.apply === 'function' ? ok('client.apply 是函数') : bad('client 未导出 apply（cordis: invalid plugin ... received object）');
      Array.isArray(cl.inject) ? ok('client.inject = ' + JSON.stringify(cl.inject)) : bad('client 未导出 inject 数组');
      typeof cl.name === 'string' && cl.name ? ok('client.name = ' + cl.name) : bad('client 未导出 name');
    }
  } catch (e) {
    bad('client.js 执行抛异常: ' + e.message);
  }
}

console.log('');
if (errs.length) { console.log('RESULT: FAIL (' + errs.length + ' error, ' + warns.length + ' warn) — 别装进 bundles'); process.exit(1); }
console.log('RESULT: PASS (' + warns.length + ' warn) — 契约合法，可装进 bundles');
