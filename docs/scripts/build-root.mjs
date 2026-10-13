// Root aliases live outside the versioned VitePress artifact on GitHub Pages.
import { mkdirSync, writeFileSync } from 'node:fs'
import { join, resolve } from 'node:path'

if (!process.argv[2]) throw new Error('Usage: node docs/scripts/build-root.mjs <output-directory>')
const output = resolve(process.argv[2])
const hostname = 'https://pyworkforce.rodrigo-arenas.com'
const aliases = [
  ['', '/stable/'],
  ['api/scheduling', '/stable/api/scheduling'],
]

for (const [path, targetPath] of aliases) {
  const target = `${hostname}${targetPath}`
  const directory = join(output, path)
  mkdirSync(directory, { recursive: true })
  writeFileSync(join(directory, 'index.html'), `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="0; url=${target}">
  <meta name="robots" content="noindex,follow">
  <link rel="canonical" href="${target}">
  <title>pyworkforce documentation</title>
</head>
<body><p>Continue to <a href="${target}">stable documentation</a>.</p></body>
</html>
`)
}

writeFileSync(join(output, 'robots.txt'), `User-agent: *
Allow: /
Sitemap: ${hostname}/stable/sitemap.xml
`)
