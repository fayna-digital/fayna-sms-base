# PLAN — fayna_sms_base (план реалізації)

> Друга черга після [docs/TZ.md](TZ.md). Dependency graph + фази + checkpoints (skill `planning-and-task-breakdown`).
> Що ВЖЕ зроблено — у CHANGELOG.md (база: адаптер, черга, log, cron, feature flag — реалізовано, v17.0.2.1.0).

---

## Overview

Базовий функціонал (абстрактний адаптер, черга з машиною станів, незмінний log, cron, feature flag) — **готовий**. Модуль інертний за замовчуванням (Strangler Fig). Цей план — про **активацію** і **відкриті покращення**, не про MVP.

---

## Dependency graph

```
[fayna_sms_base] ── готовий ── база для всіх провайдерів
    │
    ├── [fayna_sms_turbosms] ── окремий модуль ── наслідує provider.base, реалізує send_sms
    │        │
    │        └── [Feature flag flip .active=True] ── після QA провайдера на staging
    │
    ├── [Delivery-status polling] ── залежить від get_delivery_status у провайдері
    │
    └── [Long-message segmentation] ── незалежний ── низький пріоритет
```

Правило: конкретні провайдери НЕ живуть у цьому base-модулі — кожен окремий модуль, що наслідує `fayna.sms.provider.base`.

---

## Task List

### Phase 0: База ✅ (готово, v17.0.2.1.0)

- [x] `fayna.sms.provider.base` — абстрактний адаптер (`send_sms` / `get_delivery_status`)
- [x] `fayna.sms.provider` — DB-конфіг + захищений `api_key`
- [x] `fayna.sms.message` — черга + машина станів + retry + send()
- [x] `fayna.sms.log` — незмінний журнал
- [x] Cron 5 хв + feature flag `fayna_sms_base.active`
- [x] Security ACL + record rules; i18n uk/pl; 36 тестів

### Phase 1: Concrete provider + активація

- [ ] **Task: `fayna_sms_turbosms` (окремий модуль)**
  - Acceptance: наслідує `fayna.sms.provider.base`, реалізує `send_sms()` → реальний TurboSMS API; повертає `{"success","external_id","error"}`
  - Verify: інтеграційний тест із mock API + ручний прохід через чергу на staging
  - Files: новий репо `fayna_sms_turbosms` (НЕ цей модуль)

- [ ] **Task: Flip feature flag на staging після QA**
  - Acceptance: `fayna_sms_base.active=True`, cron реально відправляє; QA green
  - Verify: створити чергу → cron → перевірити state `sent` + запис у log

### Checkpoint: Phase 1
Реальний провайдер відправляє SMS через чергу на staging; флаг активовано свідомо; log заповнюється.

### Phase 2: Delivery-status polling

- [ ] **Task: Cron опитування статусу доставки**
  - Acceptance: окремий cron викликає `get_delivery_status(external_id)` для `sent` → оновлює `fayna.sms.log.status` на `delivered`/`failed`
  - Verify: тест із mock провайдером, що повертає `delivered`
  - Files: `models/fayna_sms_message.py` (новий cron-метод), `data/cron.xml`

### Checkpoint: Phase 2
Журнал відображає фактичну доставку, не лише факт відправки.

### Phase 3: Polish / технічний борг

- [ ] **Task: Сегментація довгих повідомлень (>160 символів)** — явний облік сегментів
- [ ] **Task: Виведення legacy** — поле `provider` (Selection) і `_send_sms()` batch після міграції записів
- [ ] **Task: Алерти при застряганні черги** (повідомлення в `queued` > N годин)

### Checkpoint: Phase 3
Чистий контракт без legacy; моніторинг черги; коректний облік довгих SMS.

---

## Боротьба з технічним боргом (із приведення до REPO_STANDARD 2026-06-08)

- [x] CLAUDE.md створено (#4ZONES банер + призначення + deploy)
- [x] TZ.md переписано у 6 областей spec-driven
- [x] PLAN.md створено (цей файл)
- [x] .gitignore — додано ігнор секретів
- [ ] CHANGELOG: тримати верх синхронним з `__manifest__.py` (наступний bump = запис)

---

## Зв'язки
[docs/TZ.md](TZ.md) · [[REPO_STANDARD]] · [[CAMPSCOUT_MASTER_TZ]] §16 Phase 4 · CLAUDE.md
