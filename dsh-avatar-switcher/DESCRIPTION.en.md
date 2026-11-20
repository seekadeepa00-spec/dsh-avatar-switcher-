# dsh-avatar-switcher — English

**Set your own avatar and the assistant's avatar in DeepSeek Harness, from any local image — no wallpaper-engine plugin required.**

DSH stock ships only an account-level profile picture. Chat-side avatars are rendered by plugins, so without one you get generic glyphs. This plugin fills that gap: it registers its own image store, its own routes and its own renderer, and it works on a stock DSH install.

## Short description (GitHub About, 350 chars)

> Custom avatars and mascot art for DeepSeek Harness on a stock install, no wallpaper-engine needed. Upload any PNG/JPG/WebP, switch sides independently, keep a 60-image library, built-in background remover, and a WinForms desktop switcher. Zero dependencies.

## What it does

**Avatar sides.** Two independent slots: `user` (your messages) and `ai` (assistant turns). Each keeps its own image, switchable at any time without touching the other.

**Image library.** Uploads are content-addressed (`user-<sha256[:12]>.png`), so re-uploading the same picture is a no-op instead of a duplicate. Every image you ever picked stays listed: re-apply an old one, delete a single item, or clear the whole library. Deleting the active image falls back to the newest remaining one. Library cap 60 items, storage quota 64 MB, oldest unused images evicted first.

**Renderer with four adapters.** The client works out what the host supports and picks the cheapest layer that actually renders:
`slot` (host slot API) -> `css` (declarative pseudo-element, zero injected nodes) -> `dom` (overlay node fallback) -> `none`.
The chosen layer is verified by reading the computed style of a real row, not by trusting a version number. When the CSS layer is swallowed by `overflow:hidden` or paint containment, it falls back to DOM in the same page load.

**Plays well with others.** If wallpaper-engine (or any other avatar plugin) already placed a node in a row, this plugin steps aside instead of stacking a second avatar. Default mode never mutates row layout: the avatar is drawn outside the row box. Opt into row shifting with `localStorage['das-shift'] = '1'`.

**No polling.** State is fetched on mount, on tab visibility change, on a `das:refresh` event and on storage change. DOM updates are debounced through `requestIdleCallback`. Nothing runs on a timer.

**Honest cleanup.** `apply()` returns a dispose function. Every observer, listener, injected style tag, attribute and node is registered in a disposer stack and removed in reverse order, so disabling or hot-reloading the plugin leaves no residue.

**Background remover.** Two algorithms, no ML, no network, no extra dependencies: `detail` (high-frequency energy, separates a sharp character from a blurred background) and `warm` (red-minus-blue warmth segmentation with row-span fill and border-flood hole filling, separates a character from a warm sand or wall background). Both emit a 1024 px transparent PNG plus a multi-size `.ico` (16/32/48/64/128/256).

**Desktop GUI.** `gui/AvatarTool.cs` is a single-file C# 5 WinForms app built by the `csc.exe` shipped with .NET Framework 4: no SDK, no NuGet. Buttons: pick image, set as your avatar, set as assistant avatar, set as mascot, check connection, open avatar folder, remove background, restore default.

## Interface

Host half, mounted at `/avatar-switcher`:

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/state` | active names, capabilities, limits, health |
| GET | `/library` | every stored image with side/bytes/mtime/sha/active |
| POST | `/library/apply` | `{"name":"user-abc123.png"}` switch to a stored image |
| DELETE | `/library/item/<name>` | delete one stored image |
| DELETE | `/library` | clear the whole library |
| GET | `/user`, `/ai` | serve the active image |
| POST | `/user`, `/ai` | upload and activate (raw body, image/png, jpeg, webp) |
| DELETE | `/user`, `/ai` | unset that side, image stays in the library |
| DELETE | `/all` | unset both sides |
| GET/POST | `/health` | renderer receipt: layer, rows, mountedAt, abi |

Write requests from a browser (an `Origin` or `Sec-Fetch-Site` header is present) must carry `x-avatar-token`, compared against `~/.dsh-avatar-switcher/token` (0600, 16 random bytes). Local non-browser clients pass. Uploads are validated by magic number rather than by `Content-Type`: 401 `token-required`, 415 `not a real png/jpeg/webp`, 507 `quota exceeded`. Every response carries `x-content-type-options: nosniff`.

## Install

```cmd
python install_bundle.py    :: contract gate, copies to %USERPROFILE%/.dsh/plugins, junction, adds to profile bundles
python check.py             :: after restart: prints "avatar-switcher LIVE" plus /state
node verify-plugin.mjs .    :: static contract check, exit code 0 = PASS
node test-host.mjs          :: smoke test against a fake webServer with a temp data dir
```

The installer refuses to install when `verify-plugin.mjs` fails. A plugin that cannot honour the export contract breaks DSH bootstrap, and that failure mode is not worth shipping.

## Requirements

- DeepSeek Harness desktop `0.2.2-rc.1` (`dshTarget`), cordis `4.1.0`
- Node `>= 22.5` (host half uses built-ins only)
- A host that exposes the `webServer` service
- Bundle-style install: a `cordis.patch.yml` insert alone gets wiped when the app rewrites its patch file

## Layout

```
plugin/    host half (lib/index.js), client half (lib/client.js), installer, verifier, smoke test
scripts/   set_avatar.py (user|ai|mascot|list|probe), cutout.py (detail|warm)
gui/       AvatarTool.cs  ->  DSH头像切换器.exe
tools/     development scripts: probes, sync, market de-duplication, backup
```
