# Changelog

All notable changes to `fayna_sms_base` are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: Odoo `17.0.MAJOR.MINOR.PATCH`.

---

## [17.0.1.0.0] — 2026-04-27

### Added (full implementation)
- `fayna.sms.provider.base` — canonical abstract provider model name; replaces
  previous `fayna.sms.provider` (legacy alias kept for backward compatibility).
- `sms_provider_base.py` — new file declaring `fayna.sms.provider.base` with
  `fayna.sms.provider` alias.
- `FaynaSmsMessage.normalize_phone(phone)` — static method on the model for
  external callers; delegates to the module-level `_sanitize_phone()` helper.
- `FaynaSmsMessage._cron_process_sms_queue()` — canonical cron entry point
  (delegates to `process_sms_queue()`).
- `process_sms_queue()` now limits batch to 50 messages per run (was unlimited).
- `send()` signature updated to `send(phone, body, partner_id=None, priority='0')`
  matching the TZ spec; `phone` is now the first positional parameter.
- `send()` passes `priority` through to the created record.
- Tests 18-20: normalize_phone, _cron_process_sms_queue alias, priority in send().

---

## [17.0.1.0.0] — 2026-04-27 (revised)

### Added
- `fayna.sms.message` — outbound SMS queue model with full state machine
  (`draft` → `queued` → `sent` / `failed`), retry logic, priority field,
  phone sanitisation (E.164 normalisation, strip whitespace/non-digit chars).
- `fayna.sms.message.send()` — convenience factory method: queues an SMS
  given a partner_id, body and optional explicit phone override.
- `fayna.sms.message.process_sms_queue()` — cron method dispatching queued
  messages via configured provider; increments `retry_count`, marks `failed`
  after `max_retries` exhausted; mirrors result to `fayna.sms.log`.
- Cron job `ir_cron_process_sms_queue` — every 5 minutes, active by default.
- `fayna.sms.provider.send_sms(phone, body)` — new single-message abstract
  interface returning `{"success", "external_id", "error"}`.
- `fayna.sms.provider.get_delivery_status(external_id)` — new abstract
  delivery-status interface returning `"delivered" | "failed" | "pending"`.
- Views: `fayna.sms.message` tree + form + search; retry button on form.
- Menu: Settings → SMS → **Message Queue** (seq 5) + SMS Log (seq 10).
- Security: `ir.model.access.csv` rows for `fayna.sms.message` (admin r/w/c/d,
  user r/o).
- i18n: `uk_UA.po` + `pl_PL.po` updated with all new user-facing strings.
- 17 tests covering state transitions, phone sanitisation, cron success/failure/
  retry paths, send() helper, abstract provider contracts, and log creation.

### Changed
- `fayna.sms.provider._send_sms()` retained as legacy batch interface
  (NotImplementedError); new primary interface is `send_sms()`.
- `data/ir_config_parameter.xml`: `fayna_sms_base.default_provider` now
  defaults to `turbosms` (previously empty).
- Manifest description updated to reflect full feature set.

---

## [17.0.0.1.0] — 2026-04-24

### Added
- Initial scaffold (empty-but-installable).
- Feature flag `fayna_sms_base.active` (default `False`) per master TZ §2 Strangler Fig.
- Canonical tooling (pre-commit, pyproject, GitHub Actions CI).
- Placeholder tests (install + flag + deps sanity).
- `docs/TZ.md` per-module TZ aligned with CAMPSCOUT_MASTER_TZ.md §16 Phase 4.

### Notes
- Module is **inert** until Phase 4 implementation lands.
