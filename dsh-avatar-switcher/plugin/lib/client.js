window.__ModuleLoader__.load({
  id: 'dsh-plugin-avatar-switcher',
  factory: function factory(require) {
    var module = { exports: {} };
    var exports = module.exports;
    Object.defineProperty(exports, Symbol.toStringTag, { value: 'Module' });

    var BASE = '/avatar-switcher';
    var ROW_SELECTOR = '[data-chat-flow-kind="user"], [data-chat-flow-kind="steering"], [data-chat-flow-kind="assistant-step"]';
    var STYLE_ATTR = 'data-das-style';
    var NODE_ATTR = 'data-das-node';
    var OWNER_ATTR = 'data-das-owner';
    var SIZE = 40;
    var GAP = 12;
    var ABI = 1;

    var disposers = [];
    var state = null;
    var layer = null;
    var styleEl = null;
    var observer = null;
    var timer = 0;
    var idleHandle = 0;
    var mountedAt = 0;

    function idle(fn) {
      if (typeof window.requestIdleCallback === 'function') {
        idleHandle = window.requestIdleCallback(fn, { timeout: 300 });
        return idleHandle;
      }
      idleHandle = window.setTimeout(fn, 60);
      return idleHandle;
    }

    function cancelIdle() {
      if (!idleHandle) return;
      if (typeof window.cancelIdleCallback === 'function') window.cancelIdleCallback(idleHandle);
      else window.clearTimeout(idleHandle);
      idleHandle = 0;
    }

    function schedule() {
      cancelIdle();
      if (timer) return;
      timer = 1;
      idle(function () {
        timer = 0;
        try {
          if (layer === 'dom') sweep();
        } catch (err) {
          if (typeof console !== 'undefined') console.error('[avatar-switcher] sweep failed:', err);
        }
      });
    }

    function sideOf(el) {
      var kind = el.getAttribute('data-chat-flow-kind');
      if (kind === 'user' || kind === 'steering') return 'user';
      if (kind === 'assistant-step') return 'ai';
      return null;
    }

    function imgUrl(side, name) {
      return BASE + '/' + side + '?v=' + encodeURIComponent(name || '');
    }

    // ---- layer 1: declarative CSS (no DOM mutation per row) ----
    function buildCss() {
      var u = state.user ? imgUrl('user', state.user) : null;
      var a = state.ai ? imgUrl('ai', state.ai) : null;
      var rules = [];
      rules.push(':root[data-das="on"] [data-chat-flow-kind="user"]::before,');
      rules.push(':root[data-das="on"] [data-chat-flow-kind="steering"]::before,');
      rules.push(':root[data-das="on"] [data-chat-flow-kind="assistant-step"]::before {');
      rules.push('  content: "";');
      rules.push('  display: block;');
      rules.push('  float: left;');
      rules.push('  width: var(--das-size, ' + SIZE + 'px);');
      rules.push('  height: var(--das-size, ' + SIZE + 'px);');
      rules.push('  margin-right: var(--das-gap, ' + GAP + 'px);');
      rules.push('  border-radius: 50%;');
      rules.push('  background-size: cover;');
      rules.push('  background-position: center;');
      rules.push('  background-repeat: no-repeat;');
      rules.push('  flex: 0 0 auto;');
      rules.push('}');
      if (u) {
        rules.push(':root[data-das="on"] [data-chat-flow-kind="user"]::before,');
        rules.push(':root[data-das="on"] [data-chat-flow-kind="steering"]::before { background-image: url("' + u + '"); }');
      }
      if (a) {
        rules.push(':root[data-das="on"] [data-chat-flow-kind="assistant-step"]::before { background-image: url("' + a + '"); }');
      }
      rules.push('@media (max-width: 640px) { :root { --das-size: 32px; --das-gap: 8px; } }');
      rules.push('@media print { :root { --das-print-off: 1; }');
      rules.push(':root[data-das="on"] [data-chat-flow-kind]::before { content: none !important; } }');
      return rules.join('\n');
    }

    function mountCss() {
      var el = document.querySelector('style[' + STYLE_ATTR + ']');
      if (!el) {
        el = document.createElement('style');
        el.setAttribute(STYLE_ATTR, '1');
        (document.head || document.documentElement).appendChild(el);
      }
      el.textContent = buildCss();
      styleEl = el;
      document.documentElement.setAttribute('data-das', 'on');
      disposers.push(function () {
        try { el.remove(); } catch (err) { /* detached */ }
        try { document.documentElement.removeAttribute('data-das'); } catch (err) { /* detached */ }
        styleEl = null;
      });
    }

    function probeCss() {
      var rows = document.querySelectorAll(ROW_SELECTOR);
      for (var i = 0; i < rows.length; i++) {
        var row = rows[i];
        var side = sideOf(row);
        if (!side) continue;
        var want = state[side];
        if (!want) continue;
        var cs = window.getComputedStyle(row);
        if (cs.overflow === 'hidden' || cs.contain === 'paint') continue;
        var pseudo = window.getComputedStyle(row, '::before');
        var bg = pseudo && pseudo.backgroundImage;
        if (bg && bg.indexOf(BASE) !== -1) return { ok: true, rows: rows.length };
      }
      return { ok: false, rows: rows.length };
    }

    // ---- layer 2: DOM overlay (fallback) ----
    function buildNode(side) {
      var node = document.createElement('div');
      node.className = 'das-avatar das-avatar--' + side;
      node.setAttribute(NODE_ATTR, '1');
      node.setAttribute('aria-hidden', 'true');
      node.style.cssText = [
        'position:absolute',
        'left:-' + (SIZE + GAP) + 'px',
        'top:0',
        'width:' + SIZE + 'px',
        'height:' + SIZE + 'px',
        'border-radius:50%',
        'overflow:hidden',
        'background-size:cover',
        'background-position:center',
        'background-repeat:no-repeat',
        'pointer-events:none',
      ].join(';');
      var name = state[side];
      if (name) node.style.backgroundImage = 'url("' + imgUrl(side, name) + '")';
      return node;
    }

    function mountDom() {
      var css = [
        '[data-das-owner]{position:relative}',
        '[data-das-owner]>.das-avatar{pointer-events:none}',
        '@media print{[data-das-owner]>.das-avatar{display:none!important}}',
      ].join('\n');
      var el = document.createElement('style');
      el.setAttribute(STYLE_ATTR + '-dom', '1');
      el.textContent = css;
      (document.head || document.documentElement).appendChild(el);
      disposers.push(function () { try { el.remove(); } catch (err) { /* detached */ } });

      observer = new MutationObserver(schedule);
      observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['data-chat-flow-kind', 'hidden', 'style', 'class'] });
      disposers.push(function () { try { observer.disconnect(); } catch (err) { /* noop */ } observer = null; });

      var onVis = function () { if (!document.hidden) schedule(); };
      document.addEventListener('visibilitychange', onVis);
      disposers.push(function () { document.removeEventListener('visibilitychange', onVis); });

      var onRefresh = function () { loadState().then(schedule); };
      window.addEventListener('das:refresh', onRefresh);
      disposers.push(function () { window.removeEventListener('das:refresh', onRefresh); });

      sweep();
    }

    function sweep() {
      if (layer !== 'dom') return;
      var rows = document.querySelectorAll(ROW_SELECTOR);
      for (var i = 0; i < rows.length; i++) {
        var row = rows[i];
        var side = sideOf(row);
        if (!side || !state[side]) continue;
        if (row.hasAttribute('data-turn-process-hidden')) continue;
        // do not stack on top of wallpaper-engine / other avatar providers
        if (row.querySelector('.we-avatar, [data-we-avatar-node]')) {
          var mine = row.querySelector('[' + NODE_ATTR + ']');
          if (mine) {
            mine.remove();
            row.removeAttribute(OWNER_ATTR);
          }
          continue;
        }
        var existing = row.querySelector('[' + NODE_ATTR + ']');
        if (existing) {
          existing.style.backgroundImage = 'url("' + imgUrl(side, state[side]) + '")';
          continue;
        }
        if (!row.hasAttribute(OWNER_ATTR)) row.setAttribute(OWNER_ATTR, side);
        row.insertBefore(buildNode(side), row.firstChild);
      }
    }

    function purge() {
      var nodes = document.querySelectorAll('[' + NODE_ATTR + ']');
      for (var i = 0; i < nodes.length; i++) nodes[i].remove();
      var owners = document.querySelectorAll('[' + OWNER_ATTR + ']');
      for (var j = 0; j < owners.length; j++) owners[j].removeAttribute(OWNER_ATTR);
    }

    function loadState() {
      return fetch(BASE + '/state', { cache: 'no-store' })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (data) {
          if (!data || !data.ok) return null;
          var prev = state;
          state = data;
          if (layer === 'css' && styleEl) styleEl.textContent = buildCss();
          if (prev && (prev.user !== data.user || prev.ai !== data.ai) && layer === 'dom') schedule();
          return data;
        })
        .catch(function () { return null; });
    }

    function report(layerName, rows) {
      var body = JSON.stringify({ layer: layerName, rows: rows, mountedAt: mountedAt, abi: ABI });
      try {
        fetch(BASE + '/health', {
          method: 'POST',
          headers: { 'content-type': 'application/json', 'x-avatar-token': (state && state.tokens && state.tokens.value) || '' },
          body: body,
        }).catch(function () { /* host without /health */ });
      } catch (err) { /* noop */ }
    }

    function mount() {
      if (disposers.length) return dispose;
      mountedAt = Date.now();
      return loadState().then(function (data) {
        if (!data) {
          layer = 'none';
          return;
        }
        if (!data.user && !data.ai) {
          layer = 'none';
          return;
        }
        mountCss();
        var ok = probeCss();
        if (ok.ok) {
          layer = 'css';
          report('css', ok.rows);
          return;
        }
        // CSS layer not effective here: drop it and use the DOM overlay
        dispose();
        layer = 'dom';
        disposers.push(function () { layer = null; });
        mountDom();
        report('dom', document.querySelectorAll('[' + NODE_ATTR + ']').length);
      }).catch(function (err) {
        if (typeof console !== 'undefined') console.error('[avatar-switcher] mount failed:', err);
        dispose();
        layer = null;
      });
    }

    function dispose() {
      cancelIdle();
      if (timer) timer = 0;
      try { purge(); } catch (err) { /* noop */ }
      for (var i = disposers.length - 1; i >= 0; i--) {
        try { disposers[i](); } catch (err) { /* one broken disposer must not block the rest */ }
      }
      disposers.length = 0;
      if (styleEl) styleEl = null;
      return undefined;
    }

    exports.name = 'dsh-avatar-switcher';
    exports.inject = [];
    exports.apply = function apply() {
      try {
        return mount();
      } catch (err) {
        if (typeof console !== 'undefined') console.error('[avatar-switcher] apply crashed, staying inert:', err);
        return undefined;
      }
    };
    exports.dispose = dispose;
    exports.reload = loadState;
    exports.sweep = sweep;
    exports.layer = function () { return layer; };
    exports.size = SIZE;

    return module.exports;
  },
});
