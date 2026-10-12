# Documentation crawl identity — 2026-10-12

Search Console reported `stable/` and two development guides as duplicates
without a user canonical. Public HTML confirmed that those pages had no
canonical or robots metadata. This change keeps documentation identity on
`https://pyworkforce.rodrigo-arenas.com/`, separate from the author's portfolio
and Ciaren.

Every generated content page declares its own version URL as canonical.
Stable documentation remains indexable. Development documentation uses
`noindex,follow` and remains crawlable, allowing Google to observe the directive.
The stable sitemap contains canonical content pages only; development has no
sitemap. Repository setup instructions (`README.md`) are excluded from the site,
and the default 404 declares `noindex,follow`.

The root deployment advertises the stable sitemap in `robots.txt`. Its landing
alias declares an absolute stable canonical. The known legacy reference
`/api/scheduling` now has a static alias to `/stable/api/scheduling`. GitHub Pages
does not provide a native HTTP redirect in this workflow: the alias returns HTML
with an immediate meta refresh, an explicit link and `noindex,follow`.

Versioned deployments replace their selected `destination_dir`, so obsolete
HTML such as `README.html` is removed. Root publication retains merge behavior
to preserve both versions. This follows the [deployment action's documented
semantics](https://github.com/peaceiris/actions-gh-pages#%EF%B8%8F-keeping-existing-files-keep_files);
actual GitHub execution is unverified.

Validation:

- Both baseline builds passed; six regressions failed against their generated
  artifacts and the original root redirect.
- Final VitePress 1.6.4 stable/development builds passed in 12.41/7.22 seconds,
  with strict internal-link validation. Both generated modes pass six focused
  artifact tests. A global robots-block mutant fails the crawler permission test.
- Independent review closed stale-file retention and crawler-check coverage
  findings. Test guard, Ruff 0.15.20 lint/format and diff checks passed.
- Nine Chrome cases passed: stable/development at 1280/390 px in light/dark,
  plus a missing route with actual HTTP 404 and visible not-found content.
  Client navigation updates canonical/robots; no runtime errors or horizontal
  document overflow occurred. Four mobile cases were checked again after the
  sidebar finished closing, and screenshots were inspected.
- A missing favicon request found during browser checks was repaired with a
  real versioned SVG asset. Library code and behavior were unchanged; the backend
  suite and package release gates were not run.

The original checkout is untouched. Changes are local: no push, release tag,
deployment or PyWorkforce indexing request occurred. Stable deployment must be
checked publicly before advertising its new sitemap in Search Console. These
checks establish local crawl signals, not indexing or rankings.
