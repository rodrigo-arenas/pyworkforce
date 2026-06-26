import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: 'pyworkforce',
  description:
    'Tools for workforce management: queue staffing (Erlang C / Erlang A), ' +
    'shift scheduling, rostering and operations-research optimization.',

  // Deployed to https://rodrigo-arenas.github.io/pyworkforce/
  base: '/pyworkforce/',
  lang: 'en-US',
  cleanUrls: true,
  lastUpdated: true,
  ignoreDeadLinks: true,

  head: [
    ['link', { rel: 'icon', href: '/pyworkforce/favicon.ico' }],
  ],

  themeConfig: {
    nav: [
      { text: 'Guide', link: '/guide/introduction' },
      { text: 'API', link: '/api/queuing' },
      { text: 'Release Notes', link: '/release-notes' },
      {
        text: 'PyPI',
        link: 'https://pypi.org/project/pyworkforce/',
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
            { text: 'Running many scenarios', link: '/guide/multierlang' },
          ],
        },
        {
          text: 'Workforce Planning',
          items: [
            { text: 'Building shift coverage', link: '/guide/shifts' },
            { text: 'Scheduling', link: '/guide/scheduling' },
            { text: 'Rostering', link: '/guide/rostering' },
          ],
        },
      ],
      '/api/': [
        {
          text: 'API Reference',
          items: [
            { text: 'Queuing', link: '/api/queuing' },
            { text: 'Scheduling', link: '/api/scheduling' },
            { text: 'Rostering', link: '/api/rostering' },
            { text: 'Shifts', link: '/api/shifts' },
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
