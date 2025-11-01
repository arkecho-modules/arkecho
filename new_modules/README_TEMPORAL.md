# Temporal Ethics / User-Time Respect Governor (ArkEcho v13)

**What it is**  
A deterministic governor that respects *user time* and *universal time* to decide whether to **proceed**, **batch (defer)**, or **halt** an operation. It encodes:
- Quiet windows (do less when danger increases / respect downtime)
- Focus windows (reduce distraction)
- Minor vs adult safeguards
- Protection Index thresholds
- Simple jurisdiction-aware legal basis notes (narrative only)

**Why it’s separate**  
This is a **clean-integration add-on**: it doesn’t modify existing modules. Remove the three new files and your repo is exactly as before.

## Files

- `new_modules/temporal_governor.py` — the module; deterministic, offline-first
- `configs/temporal_policy.cov` — JSON policy (extension .cov to match ArkEcho DSL naming)
- *(this doc)* `new_modules/README_TEMPORAL.md`

## How to run (ad-hoc)

```bash
python new_modules/temporal_governor.py
