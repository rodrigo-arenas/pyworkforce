---
layout: home

hero:
  name: pyworkforce
  text: Workforce management, made practical
  tagline: >-
    Queue staffing, shift scheduling and rostering for call centers and any
    operation that needs the right people at the right time.
  actions:
    - theme: brand
      text: Get Started
      link: /guide/introduction
    - theme: alt
      text: Quick Start
      link: /guide/quickstart
    - theme: alt
      text: View on GitHub
      link: https://github.com/rodrigo-arenas/pyworkforce

features:
  - title: Queue staffing
    details: >-
      Size your team with Erlang C (infinite queue), Erlang A (abandonment), or
      Erlang B (loss/trunk sizing). Sweep many scenarios at once with the
      Multi* variants.
    link: /guide/erlangc
  - title: Shift scheduling
    details: >-
      Given the resources required per period, decide how many people to place
      on each shift using constraint-programming solvers built on OR-Tools.
    link: /guide/scheduling
  - title: Rostering & break scheduling
    details: >-
      Assign named people to days and shifts while respecting rest days, banned
      shifts, minimum hours and preferences. Then schedule breaks to maintain
      coverage.
    link: /guide/rostering
  - title: Friendly, scikit-learn-like API
    details: >-
      Consistent constructors, helpful validation messages, get_params() and
      readable reprs, plus helpers to build shift coverage without hand-writing
      0/1 arrays.
    link: /guide/shifts
---
