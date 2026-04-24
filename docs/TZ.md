# fayna_sms_base — Per-module TZ

Scope: master TZ §16 Phase 4. Owner: Fayna Digital (Volodymyr Shevchenko).

## Mission

Provider-agnostic SMS adapter base (abstract send + delivery log).

Abstract SMS adapter interface. Provider modules (e.g. fayna_sms_turbosms) inherit.

## Non-goals

- Anything outside Phase 4 scope per master TZ.
- Production deployment before all 26 modules are on Hetzner staging with
  human QA green (see `feedback_prod_deploy_gate.md` — ЗАКОН).

## Incremental milestones

### M.0 Scaffold ✅ (2026-04-24)

Empty module, installable, feature flag seeded `False`, CI green.

### M.1 — TBD

First concrete behaviour. Details land when Phase 4 starts active development.

## Quality (per master TZ §4.6 ЗАКОН)

- pre-commit gates green on every commit (ruff + ruff-format + OCA + bandit + gitleaks + base hooks)
- tests ≥ 70% coverage on critical paths
- QUALITY_AUDIT_*.md entry before each phase gate promotion

## Rollback

- Flip `fayna_sms_base.active` → `False`.
- If still misbehaving, uninstall the module; core Odoo tables remain untouched.

## Reference

- Master TZ `CAMPSCOUT_MASTER_TZ.md` §16 Phase 4
- Sister modules per deps
