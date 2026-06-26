import { defineConfig } from 'vitepress'

// "stable" on tag releases, "development" on main-branch pushes.
const docsVersion = process.env.DOCS_VERSION ?? 'development'
const base = `/pyworkforce/${docsVersion}/`

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
  description:
    'Tools for workforce management: queue staffing (Erlang C / Erlang A), ' +
    'shift scheduling, rostering and operations-research optimization.',

  // base is /pyworkforce/stable/ or /pyworkforce/development/ depending on DOCS_VERSION.
  base,
  lang: 'en-US',
  cleanUrls: true,
  lastUpdated: true,
  ignoreDeadLinks: true,

  head: [
    ['link', { rel: 'icon', href: `${base}favicon.ico` }],
    ...analyticsHead,
  ],

  themeConfig: {
    nav: [
      { text: 'Guide', link: '/guide/introduction' },
      { text: 'API', link: '/api/queuing' },
      { text: 'Release Notes', link: '/release-notes' },
      { text: 'PyPI', link: 'https://pypi.org/project/pyworkforce/' },
      {
        text: docsVersion,
        items: [
          { text: 'stable', link: 'https://rodrigo-arenas.github.io/pyworkforce/stable/' },
          { text: 'development', link: 'https://rodrigo-arenas.github.io/pyworkforce/development/' },
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
          ],
        },
        {
          text: 'Tutorials',
          items: [
            { text: 'End-to-end planning', link: '/guide/end-to-end' },
            { text: 'Comparing scenarios', link: '/guide/scenarios' },
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
