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

## Structure

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
