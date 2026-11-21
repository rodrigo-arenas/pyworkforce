---
layout: home
title: 'PyWorkforce: Shift Scheduling and Workforce Planning in Python'
titleTemplate: false
description: Use PyWorkforce to estimate staffing with Erlang models, schedule shifts with OR-Tools, and build employee rosters. Run a Python example to get started.

hero:
  name: pyworkforce
  text: Practical workforce optimization in Python
  tagline: >-
    Queue staffing, multi-skill staffing, shift scheduling, rostering and break
    scheduling for operations that need the right people at the right time.
  actions:
    - theme: brand
      text: Run the Python quickstart
      link: /guide/quickstart
    - theme: alt
      text: Read the guide
      link: /guide/introduction
    - theme: alt
      text: Recipes
      link: /recipes/
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

## Planning pipeline

![Queue sizing and optional skill-mix planning, shift scheduling and coverage analysis, then independent rostering and break scheduling.](./images/planning_pipeline.svg)

pyworkforce is useful beyond contact centers: healthcare staffing, retail
operations, logistics, support teams, service desks and field operations all
share the same planning problem of matching variable demand to finite resources.

## Where should I start?

| Goal | Page |
| --- | --- |
| Install and run the first example | [Quick Start](/guide/quickstart) |
| Understand the full workflow | [End-to-end planning tutorial](/guide/end-to-end) |
| Size call-center agents for 80/20 | [Erlang C](/guide/erlangc) |
| Compare service and occupancy by headcount | [Erlang C staffing curve](/guide/staffing-curve) |
| Check a solved schedule against another forecast | [Schedule stress test](/guide/coverage-scenarios) |
| Model abandonment | [Erlang A](/guide/erlanga) |
| Size SIP trunks or channels | [Erlang B](/guide/erlangb) |
| Solve short practical tasks | [Recipes](/recipes/) |
| Check constructor and output details | [API Reference](/api/queuing) |
| Contribute examples, docs or solvers | [Contributing](/contributing) |
