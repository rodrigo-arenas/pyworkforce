# Introduction

**pyworkforce** is a Python package with tools for workforce management
problems such as queue staffing, shift scheduling, rostering and
operations-research optimization. It is especially well suited to contact /
call centers, but the same techniques apply to hospitals, retail, logistics,
network capacity planning and any operation that has to match a variable
demand with a finite number of resources.

The package is organized around three planning steps that usually happen in
sequence:

## 1. Queuing — *how many resources do I need?*

Given an incoming demand (for example, calls arriving at a call center), how
many agents or channels are required to hit a service target?

- [`ErlangC`](/guide/erlangc) — the classic M/M/c queue: Poisson arrivals,
  exponential handling times, an infinite queue and no abandonment.
- [`ErlangA`](/guide/erlanga) — the M/M/c+M queue, which additionally models
  customers who **abandon** the queue if they wait too long. This is closer to
  reality for most contact centers.
- [`ErlangB`](/guide/erlangb) — the M/M/c/c **loss queue**: no waiting room,
  blocked calls are shed. Use this for trunk / SIP channel sizing.
- [`MultiErlangC`](/guide/multierlang) / `MultiErlangA` / `MultiErlangB` —
  evaluate many scenarios at once from a parameter grid, with a scikit-learn-like
  interface.

## 2. Staffing — *what is the optimal skill mix?*

When your team handles multiple contact types (languages, queues, skill groups),
you need to decide how many agents of each skill profile to hire so that every
skill's coverage requirement is met at the lowest possible cost.

- [`MultiSkillStaffing`](/guide/staffing) — solves the integer programme that
  minimises total weighted headcount given per-skill requirements. Flexible
  (multi-skilled) agents count towards every skill they hold, so the solver
  automatically trades off dedicated vs. flexible hiring.

## 3. Scheduling — *how many people per shift?*

Once you know the resources required per period of the day, decide how many
people to place on each predefined shift.

- [`MinAbsDifference`](/guide/scheduling) — minimize the absolute difference
  between required and scheduled resources.
- [`MinRequiredResources`](/guide/scheduling) — minimize the (optionally
  weighted) number of scheduled resources while covering every period.

The [shift coverage builders](/guide/shifts) help you create the
`shifts_coverage` definitions these solvers expect without writing 0/1 arrays
by hand.

## 4. Rostering — *who works when?*

Assign **named** resources to days and shifts while respecting rules such as
banned shifts, rest days, minimum working hours, non-sequential shifts and
personal preferences.

- [`MinHoursRoster`](/guide/rostering) — build a resource-level roster that
  covers the shift requirements with the minimum scheduled hours.

## 5. Break scheduling — *when do breaks happen?*

Once the roster is set, assign a start time to every break for every agent slot
while ensuring that simultaneous breaks never drop coverage below the required
minimum.

- [`BreakScheduler`](/guide/breaks) — CP-SAT solver that places breaks inside
  shift windows, prevents overlaps, and respects per-period coverage constraints.

## Design principles

pyworkforce aims for a **scikit-learn level of friendliness**:

- consistent constructors and clear, actionable error messages;
- `get_params()` and readable `repr()` on every estimator;
- the last result is stored on the estimator (`solution_`) after solving;
- deterministic, well-tested numerical methods.

Ready? Head to [Installation](/guide/installation) and the
[Quick Start](/guide/quickstart), or jump straight into the
[end-to-end tutorial](/guide/end-to-end).
