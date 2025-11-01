# ArkEcho v15 — Governance & Moral Custody Framework

**Purpose:** Guarantee that ArkEcho’s protection of users—especially children and vulnerable adults—remains **verifiable, reversible, and lawful** over time.

## 1) Objectives
- **Integrity Verification** — every run emits an integrity snapshot (risk, protection index, MHI, rationale).
- **Chain of Custody** — artifacts (logs/audits/manifests) are hashed and timestamped.
- **Jurisdiction-Aware** — UK / EU / US contexts without moral drift.
- **Protection First** — “halt when unsure” is a feature, not a bug.
- **Transparent Change** — any schema/logic update requires an ethical change note.

## 2) Layers
- **Ethics Manifest** — universal moral constants (transparency, empathy, accountability, reversibility).
- **Guardian Framework** — runtime enforcement (pre-check, post-verify).
- **PSI (Psychological Safety Integrity)** — flags manipulative or addictive patterns (enterprise tiers).
- **Audit Engine** — writes `./logs/integrity_*.json` and (optionally) HTML exports.
- **Governance Packager** (enterprise tiers) — bundles signed weekly custody archives.

## 3) Weekly Governance Cycle (optional but recommended)
```bash
# Run integrity suite (example)
python core/runner.py

# Pack custody bundles (where available)
python scripts/pack_governance_week.py

# Verify bundles
python scripts/verify_pack.py governance/<ISO_WEEK>/bundle.zip manifest.json

4) Jurisdictions

Set via environment variable before launch:

export ARKECHO_JURISDICTION=UK   # or EU / US

5) Evidence & Reproducibility

Same input → same decision. Deterministic by design.

Hash all release artifacts and store alongside logs.

Keep a continuity hash when updating editions.

6) Principles

Accountability Before Automation

No Unverifiable Decisions

Every Risk Quantified, Never Hidden

Every Child Protected, No Exceptions

Every Edition Traceable to Its Manifest