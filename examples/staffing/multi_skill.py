"""Multi-skill staffing example.

Demonstrates how to find the minimum-cost agent mix for a contact centre
that routes contacts by skill.  The workflow has two steps:

1. Size each skill queue independently with Erlang C or Erlang A.
2. Feed the per-skill requirements into MultiSkillStaffing to find the
   cheapest profile mix.
"""

from pyworkforce.queuing import ErlangA, ErlangC
from pyworkforce.staffing import MultiSkillStaffing

# ---------------------------------------------------------------------------
# Step 1 — queue sizing per skill
# ---------------------------------------------------------------------------

# Billing queue: standard queue, moderate load
billing_q = ErlangC(
    transactions=100, aht=4, asa=20 / 60, interval=60, shrinkage=0.3
)

# Technical queue: longer handling time, callers have some patience
technical_q = ErlangA(
    transactions=50, aht=8, asa=20 / 60, interval=60, patience=10, shrinkage=0.3
)

req_billing = billing_q.required_positions(service_level=0.8, max_occupancy=0.85)
req_technical = technical_q.required_positions(service_level=0.8, max_occupancy=0.85)

print("=== Queuing results ===")
print(
    f"Billing   raw_positions={req_billing['raw_positions']}"
    f"  (positions with shrinkage={req_billing['positions']})"
)
print(
    f"Technical raw_positions={req_technical['raw_positions']}"
    f"  (positions with shrinkage={req_technical['positions']})"
)

# ---------------------------------------------------------------------------
# Step 2 — find the optimal skill-profile mix (using raw_positions)
# ---------------------------------------------------------------------------

skills = ["Billing", "Technical"]

# Dedicated agents cost 1.0; flexible agents cost 1.4
profiles = [
    {"name": "Billing_only",   "skills": ["Billing"],              "cost": 1.0},
    {"name": "Technical_only", "skills": ["Technical"],            "cost": 1.0},
    {"name": "Flexible",       "skills": ["Billing", "Technical"], "cost": 1.4},
]

required = {
    "Billing":   req_billing["raw_positions"],
    "Technical": req_technical["raw_positions"],
}

ms = MultiSkillStaffing(
    skills=skills,
    profiles=profiles,
    required_positions=required,
)

result = ms.solve()

print("\n=== Staffing solution ===")
print(f"Status : {result['status']}")
print(f"Cost   : {result['cost']:.1f}")
print(f"Total  : {result['total_agents']} agents")
print()
print("Agents per profile:")
for entry in result["agents_per_profile"]:
    print(f"  {entry['profile']:20s}: {entry['agents']}")
print()
print("Skill coverage (must be >= required):")
for skill, cov in result["skill_coverage"].items():
    print(f"  {skill:20s}: {cov}  (required {required[skill]})")

# ---------------------------------------------------------------------------
# Bonus: compare against pure-dedicated baseline
# ---------------------------------------------------------------------------

print("\n=== Dedicated-only baseline ===")
dedicated_profiles = [
    {"name": "Billing_only",   "skills": ["Billing"]},
    {"name": "Technical_only", "skills": ["Technical"]},
]

ms_ded = MultiSkillStaffing(
    skills=skills,
    profiles=dedicated_profiles,
    required_positions=required,
)

ded = ms_ded.solve()
print(f"Cost: {ded['cost']:.1f}  (vs {result['cost']:.1f} with flexible agents)")
savings = ded["cost"] - result["cost"]
print(f"Savings from flexibility: {savings:.1f} agent-equivalents per interval")
