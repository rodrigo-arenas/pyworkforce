# Multi-skill staffing

Real contact centres route contacts by skill — a **Billing** call can only be
handled by an agent who holds the Billing skill; a **Technical** call requires
the Technical skill. Many agents are **multi-skilled** (flexible), so they can
handle contacts of more than one type.

Given per-skill staffing requirements — typically the `raw_positions` output of
[Erlang C](/guide/erlangc) or [Erlang A](/guide/erlanga) — `MultiSkillStaffing`
solves the integer programme that selects how many agents of each skill profile
to hire so that every skill's demand is met at minimum total cost.

## The problem

The optimisation model is:

$$\min_{n} \quad \sum_{s} \text{cost}_s \cdot n_s$$

$$\text{subject to} \quad \sum_{s\,:\,k \in \text{profile}(s)} n_s \geq \text{required}[k] \quad \forall\,k$$

$$n_s \geq 0, \; \text{integer} \quad \forall\,s$$

A **profile** is a named set of skills. An agent with profile $s$ contributes to
the coverage of every skill $k \in \text{profile}(s)$, so a flexible agent
simultaneously fulfils requirements across all skills they hold.

## Basic usage

```python
from pyworkforce.staffing import MultiSkillStaffing

skills = ["Billing", "Technical"]

profiles = [
    {"name": "Billing_only",   "skills": ["Billing"],              "cost": 1.0},
    {"name": "Technical_only", "skills": ["Technical"],            "cost": 1.0},
    {"name": "Flexible",       "skills": ["Billing", "Technical"], "cost": 1.5},
]

required = {"Billing": 5, "Technical": 3}

ms = MultiSkillStaffing(skills=skills, profiles=profiles, required_positions=required)
result = ms.solve()
print(result)
```

```text
{'status': 'OPTIMAL',
 'cost': 6.5,
 'total_agents': 5,
 'agents_per_profile': [
     {'profile': 'Billing_only',   'agents': 2},
     {'profile': 'Technical_only', 'agents': 0},
     {'profile': 'Flexible',       'agents': 3},
 ],
 'skill_coverage': {'Billing': 5, 'Technical': 3}}
```

3 flexible agents + 2 billing-only = 5 agents at cost 6.5. The pure-dedicated
alternative (5 Billing_only + 3 Technical_only = 8 agents, cost 8.0) costs more
because flexible agents count towards both skills simultaneously.

::: tip Cost modelling
If all agents cost the same regardless of skill breadth, omit `"cost"` (it
defaults to `1.0`) or set it to `1.0` for every profile. The solver then simply
minimises total headcount.

When multi-skilled agents are more expensive to hire or train, raise their cost
proportionally. The solver will automatically balance dedication vs. flexibility.
:::

## Connecting to Erlang C / Erlang A output

Pass `raw_positions` directly from the queuing step:

```python
from pyworkforce.queuing import ErlangC, ErlangA
from pyworkforce.staffing import MultiSkillStaffing

# Queuing step ---------------------------------------------------------------
billing = ErlangC(
    transactions=100, aht=4, asa=20 / 60, interval=60, shrinkage=0.3
)
technical = ErlangA(
    transactions=50, aht=8, asa=20 / 60, interval=60, patience=10, shrinkage=0.3
)

required = {
    "Billing":   billing.required_positions(service_level=0.8)["raw_positions"],
    "Technical": technical.required_positions(service_level=0.8)["raw_positions"],
}
print("Required:", required)

# Staffing step --------------------------------------------------------------
profiles = [
    {"name": "Billing_only",   "skills": ["Billing"],              "cost": 1.0},
    {"name": "Technical_only", "skills": ["Technical"],            "cost": 1.0},
    {"name": "Flexible",       "skills": ["Billing", "Technical"], "cost": 1.4},
]

ms = MultiSkillStaffing(
    skills=list(required), profiles=profiles, required_positions=required
)
result = ms.solve()

print(f"Total agents: {result['total_agents']}  cost: {result['cost']:.1f}")
for entry in result["agents_per_profile"]:
    if entry["agents"] > 0:
        print(f"  {entry['profile']:20s}: {entry['agents']}")
```

```text
Required: {'Billing': 13, 'Technical': 6}
Total agents: 13  cost: 15.4
  Billing_only        : 7
  Flexible            : 6
```

## Capping the total headcount

Pass `max_agents` to impose a hard budget on the total number of agents:

```python
ms = MultiSkillStaffing(
    skills=skills, profiles=profiles,
    required_positions=required,
    max_agents=12,
)
result = ms.solve()
print(result["status"])   # "INFEASIBLE" if 12 cannot cover all requirements
```

## Output structure

`solve()` returns a dict with:

| Key | Type | Description |
| --- | --- | --- |
| `status` | `str` | `"OPTIMAL"`, `"FEASIBLE"`, or `"INFEASIBLE"` |
| `cost` | `float` | Objective value (weighted headcount); `−1` when infeasible |
| `total_agents` | `int` | Sum of agents across all profiles; `−1` when infeasible |
| `agents_per_profile` | `list[dict]` | One `{"profile", "agents"}` entry per profile |
| `skill_coverage` | `dict` | `{"skill": n}` — agents covering each skill in the solution |

## Defining profiles

Each profile dict has:

| Key | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | `str` | Yes | Unique identifier |
| `skills` | `list[str]` | Yes | Skills covered (must be a subset of `skills`) |
| `cost` | `float` | No (default `1.0`) | Cost per agent of this profile |

Every skill in `skills` must be covered by at least one profile. The constructor
raises `ValueError` if any skill has no profile that covers it, since the problem
would be trivially infeasible.

::: tip Three or more skills
The solver handles any number of skills and profiles. Scenarios with English,
Spanish, Portuguese plus bilingual and trilingual profiles are simply larger
integer programmes and typically solve in under a second at contact-centre scale.
:::

## See also

- [Erlang C guide](/guide/erlangc) — sizing per-skill requirements
- [Erlang A guide](/guide/erlanga) — requirements with abandonment
- [Scheduling guide](/guide/scheduling) — placing the staffed mix across shifts
- [End-to-end tutorial](/guide/end-to-end) — full planning pipeline
- [API — Staffing](/api/staffing)
