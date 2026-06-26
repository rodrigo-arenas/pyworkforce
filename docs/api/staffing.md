# API — Staffing

`pyworkforce.staffing`

## MultiSkillStaffing

```python
MultiSkillStaffing(
    skills,
    profiles,
    required_positions,
    max_agents=None,
    max_search_time=60.0,
    num_search_workers=2,
)
```

Minimum-cost agent-mix optimiser for multi-skill contact-centre staffing.
Given per-skill staffing requirements and a catalogue of agent skill profiles,
solves the integer programme that minimises total weighted headcount while
ensuring every skill's coverage requirement is met.

**Parameters**

- **skills** (`list[str]`) — names of the distinct skill types that must be
  staffed (e.g. `["English", "Billing", "Technical"]`).
- **profiles** (`list[dict]`) — each element describes one agent skill profile:
  - `name` (`str`) — unique identifier for this profile.
  - `skills` (`list[str]`) — skills covered by agents in this profile. Must be
    a non-empty subset of `skills`.
  - `cost` (`float`, default `1.0`) — cost per agent of this profile, used as
    the objective coefficient.
- **required_positions** (`dict`) — `{"skill_name": n}` — minimum agents needed
  for each skill. Keys must match `skills` exactly. Pass
  `result["raw_positions"]` from `ErlangC` or `ErlangA` here.
- **max_agents** (`int`, optional) — hard cap on the total number of agents
  across all profiles. Omit for an unconstrained search.
- **max_search_time** (`float`, default `60.0`) — maximum solver wall-clock time
  in seconds.
- **num_search_workers** (`int`, default `2`) — number of parallel search workers.

**Attributes**

- **solution_** (`dict` or `None`) — the last result returned by `solve()`, or
  `None` before `solve()` is called.

**Methods**

- `solve()` → `dict`

  Run the CP-SAT integer programme and return a result dict with:

  - `status` (`str`) — `"OPTIMAL"`, `"FEASIBLE"`, or `"INFEASIBLE"`.
  - `cost` (`float`) — objective value (weighted headcount); `-1` when infeasible.
  - `total_agents` (`int`) — sum of agents across all profiles; `-1` when
    infeasible.
  - `agents_per_profile` (`list[dict]`) — one `{"profile": name, "agents": n}`
    entry per profile.
  - `skill_coverage` (`dict`) — `{"skill": n}` total agents covering each skill
    in the solution. Useful for verifying all requirements are met.

- `get_params()` → `dict`

**Validation**

The constructor raises `ValueError` for:

- empty `skills` list or duplicate skill names;
- missing `"name"` or `"skills"` key in any profile;
- duplicate profile names;
- a profile referencing a skill not listed in `skills`;
- `required_positions` keys not matching `skills` exactly;
- any required count that is not a non-negative integer;
- any skill in `skills` not covered by at least one profile.

See the [Multi-skill staffing guide](/guide/staffing).
