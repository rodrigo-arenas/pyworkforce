# pyworkforce documentation

This folder contains the [VitePress](https://vitepress.dev/) documentation site
for pyworkforce, published to GitHub Pages at
<https://pyworkforce.rodrigo-arenas.com/>.

## Local development

```bash
cd docs
npm install
npm run docs:dev      # start a local dev server with hot reload
npm run docs:build    # build the static site into .vitepress/dist
npm run docs:preview  # preview the built site
```

## Crawl-signal checks

The focused artifact tests require Python with pytest and the installed Node
dependencies. From this directory, build both modes sequentially into ignored
output folders, generate the root Pages artifact, then run the tests (PowerShell):

```powershell
$env:PYWORKFORCE_BUILD_ROOT = Join-Path (Get-Location) '.vitepress/dist'
$env:DOCS_VERSION = 'stable'
node node_modules/vitepress/bin/vitepress.js build . --outDir .vitepress/dist/stable
$env:DOCS_VERSION = 'development'
node node_modules/vitepress/bin/vitepress.js build . --outDir .vitepress/dist/development
node scripts/build-root.mjs .vitepress/dist/root
python -m pytest scripts/test_site_contract.py -q
Remove-Item Env:DOCS_VERSION, Env:PYWORKFORCE_BUILD_ROOT
```

Normal `docs:build` still produces `.vitepress/dist`; the checks do not change
the production publishing layout. `README.md` is repository guidance and is
excluded from the public documentation build.

## Documentation files

- `index.md` — landing page.
- `guide/` — narrative guides (queuing, scheduling, rostering, shifts).
- `api/` — API reference.
- `release-notes.md` — changelog.
- `.vitepress/config.mjs` — site configuration and sidebar.

## Deployment

Pushes to `main` that touch `docs/**` trigger the
`.github/workflows/docs.yml` workflow, which builds the site and deploys it to
GitHub Pages. Enable Pages once in the repository settings with
**Settings → Pages → Build and deployment → Source: GitHub Actions**.
