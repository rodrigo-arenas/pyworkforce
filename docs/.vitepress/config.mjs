import { defineConfig } from 'vitepress'

// "stable" on tag releases, "development" on main-branch pushes.
const docsVersion = process.env.DOCS_VERSION ?? 'development'
const base = `/${docsVersion}/`
const hostname = 'https://pyworkforce.rodrigo-arenas.com'
const description = 'Tools for workforce management: queue staffing (Erlang C / Erlang A), ' +
  'shift scheduling, rostering and operations-research optimization.'

// Google Analytics measurement ID (e.g. "G-XXXXXXXXXX"), injected at build time.
// This is a PUBLIC identifier (it ships in the page), not a credential.
const gaId = process.env.GA_MEASUREMENT_ID

const analyticsHead = gaId
  ? [
      ['script', { async: '', src: `https://www.googletagmanager.com/gtag/js?id=${gaId}` }],
      [
        'script',
        {},
        `window.dataLayer = window.dataLayer || [];\n` +
          `function gtag(){dataLayer.push(arguments);}\n` +
          `gtag('js', new Date());\n` +
          `gtag('config', '${gaId}');`,
      ],
    ]
  : []

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: 'pyworkforce',
  description,

  // The custom host serves /stable/ or /development/ depending on DOCS_VERSION.
  base,
  lang: 'en-US',
  cleanUrls: true,
  lastUpdated: true,
  srcExclude: ['README.md'],

  sitemap: docsVersion === 'stable' ? {
    hostname,
    transformItems: (items) => items
      .filter((item) => item.url !== '404')
      .map((item) => ({ ...item, url: `${base}${item.url}` })),
  } : undefined,

  transformPageData(pageData) {
    const path = pageData.relativePath.replace(/\\/g, '/').replace(/index\.md$/, '').replace(/\.md$/, '')
    const canonical = `${hostname}${base}${path}`
    pageData.frontmatter.head ??= []
    pageData.frontmatter.head.push(
      ['link', { rel: 'canonical', href: canonical }],
      ['meta', { property: 'og:url', content: canonical }],
      ['meta', { property: 'og:type', content: 'website' }],
      ['meta', { property: 'og:title', content: pageData.title }],
      ['meta', { property: 'og:description', content: pageData.description || description }],
      ['meta', { property: 'og:image', content: `${hostname}${base}brand/social-preview.png` }],
      ['meta', { property: 'og:image:width', content: '1200' }],
      ['meta', { property: 'og:image:height', content: '630' }],
      ['meta', { property: 'og:image:alt', content: 'PyWorkforce shift coverage illustration' }],
    )
    if (docsVersion === 'development') {
      pageData.frontmatter.head.push(['meta', { name: 'robots', content: 'noindex,follow' }])
    }
  },

  // VitePress's default 404 bypasses the Markdown page-data transform.
  transformHead({ page }) {
    return page === '404.md' ? [['meta', { name: 'robots', content: 'noindex,follow' }]] : []
  },

  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: `${base}favicon.svg` }],
    ...analyticsHead,
  ],

  themeConfig: {
    nav: [
      { text: 'Guide', link: '/guide/introduction' },
      { text: 'Recipes', link: '/recipes/' },
      { text: 'API', link: '/api/queuing' },
      { text: 'Contributing', link: '/contributing' },
      { text: 'Release Notes', link: '/release-notes' },
      { text: 'PyPI', link: 'https://pypi.org/project/pyworkforce/' },
      {
        text: docsVersion,
        items: [
          { text: 'stable', link: 'https://pyworkforce.rodrigo-arenas.com/stable/' },
          { text: 'development', link: 'https://pyworkforce.rodrigo-arenas.com/development/' },
        ],
      },
    ],

    sidebar: {
      '/guide/': [
        {
          text: 'Getting Started',
          items: [
            { text: 'Introduction', link: '/guide/introduction' },
            { text: 'Installation', link: '/guide/installation' },
            { text: 'Quick Start', link: '/guide/quickstart' },
            { text: 'Contributing', link: '/contributing' },
          ],
        },
        {
          text: 'Tutorials',
          items: [
            { text: 'End-to-end planning', link: '/guide/end-to-end' },
            { text: 'Comparing scenarios', link: '/guide/scenarios' },
            { text: 'Stress-test a shift schedule', link: '/guide/coverage-scenarios' },
            { text: 'Choose staffing with Erlang C', link: '/guide/staffing-curve' },
            { text: 'Recipes', link: '/recipes/' },
          ],
        },
        {
          text: 'Queuing',
          items: [
            { text: 'Erlang C', link: '/guide/erlangc' },
            { text: 'Erlang A (abandonment)', link: '/guide/erlanga' },
            { text: 'Erlang B (loss systems)', link: '/guide/erlangb' },
            { text: 'Running many scenarios', link: '/guide/multierlang' },
          ],
        },
        {
          text: 'Workforce Planning',
          items: [
            { text: 'Multi-skill staffing', link: '/guide/staffing' },
            { text: 'Building shift coverage', link: '/guide/shifts' },
            { text: 'Scheduling', link: '/guide/scheduling' },
            { text: 'Rostering', link: '/guide/rostering' },
            { text: 'Break scheduling', link: '/guide/breaks' },
          ],
        },
      ],
      '/api/': [
        {
          text: 'API Reference',
          items: [
            { text: 'Queuing', link: '/api/queuing' },
            { text: 'Staffing', link: '/api/staffing' },
            { text: 'Scheduling', link: '/api/scheduling' },
            { text: 'Rostering', link: '/api/rostering' },
            { text: 'Shifts', link: '/api/shifts' },
            { text: 'Breaks', link: '/api/breaks' },
            { text: 'Plotting', link: '/api/plotting' },
          ],
        },
      ],
      '/recipes/': [
        {
          text: 'Recipes',
          items: [
            { text: 'Overview', link: '/recipes/' },
          ],
        },
      ],
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/rodrigo-arenas/pyworkforce' },
    ],

    search: {
      provider: 'local',
    },

    editLink: {
      pattern:
        'https://github.com/rodrigo-arenas/pyworkforce/edit/main/docs/:path',
      text: 'Edit this page on GitHub',
    },

    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright © 2021-present Rodrigo Arenas',
    },
  },
})
