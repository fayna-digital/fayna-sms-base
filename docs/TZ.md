# TZ — fayna_sms_base

> Канонічна специфікація модуля за [[REPO_STANDARD]] (6 областей spec-driven + Success Criteria + Open Questions).
> Версія модуля: **17.0.2.1.0** | License: LGPL-3 | depends: `base`, `mail`.
> Scope: master TZ `CAMPSCOUT_MASTER_TZ.md` §16 Phase 4 (Strangler Fig). Owner: Fayna Digital (Volodymyr Shevchenko).

---

## 1. Objective

**Що:** базовий, незалежний від провайдера, SMS-адаптер для Odoo 17 Community.

**Для кого:** CampScout (`campscout.eu`) — табірна платформа; SMS-нотифікації клієнтам/батькам.

**Можливості:**
- `fayna.sms.provider.base` — абстрактний адаптер (`send_sms`, `get_delivery_status`); провайдери-модулі (напр. `fayna_sms_turbosms`) наслідують і реалізують.
- `fayna.sms.provider` — DB-конфіг провайдера (name, sequence, provider_type, api_key, active); `api_key` захищене полем `base.group_system`.
- `fayna.sms.message` — черга вихідних із машиною станів `draft → queued → sent / failed`, retry-логікою (`retry_count` / `max_retries`), пріоритетом, нормалізацією телефону E.164.
- `fayna.sms.log` — **незмінний** журнал доставки (write/unlink заблоковані після create).
- Cron кожні 5 хв (`_cron_process_sms_queue`) — диспетчеризує до 50 черг за прохід через активного провайдера.
- Зручний фабричний метод `fayna.sms.message.send(phone, body, partner_id=None, priority='0', provider_id=None)`.
- **Feature flag** `fayna_sms_base.active` (default `False`) — Strangler Fig: модуль інертний до свідомого flip.

**Успіх:** черга диспетчеризується через провайдера, результат дзеркалиться в незмінний log, retry/failed працюють, секрети не витікають, флаг тримає модуль інертним до активації.

**Технології:** [[library/tools/python]] · Odoo 17 Community · [[library/tools/postgresql]] · [[library/tools/docker]] · pytest · ruff.

---

## 2. Commands

```bash
# Тести
cd fayna_sms_base
python -m pytest tests/ -v                 # 36 тестів (log + message + scaffold)
python -m pytest tests/ --cov --cov-report=term-missing   # покриття (ціль ≥70%, pyproject fail_under=70)

# Lint + format (pre-commit: ruff + ruff-format + OCA + bandit + gitleaks)
pre-commit run --all-files
ruff check .                               # тільки lint
ruff format .                              # тільки форматування

# Деплой #4ZONES (Mac → GitHub → staging → prod)
git push origin main
ssh prod 'cd /opt/campscout/addons/fayna_sms_base && git pull && sudo chmod -R o+rX .'
# Python-only fix → достатньо рестарту:
ssh prod 'docker restart campscout_web'
# Зміна моделей/views/security → update модуля:
ssh prod 'docker exec campscout_web odoo -u fayna_sms_base --stop-after-init -d campscout && docker restart campscout_web'
```

---

## 3. Project Structure

```
fayna_sms_base/
  __manifest__.py          # v17.0.2.1.0, depends: base, mail
  models/
    sms_provider_base.py   # fayna.sms.provider.base — AbstractModel (send_sms / get_delivery_status / _send_sms legacy)
    fayna_sms_provider.py  # fayna.sms.provider — DB-конфіг + send_sms() делегує до fayna.sms.<provider_type>
    fayna_sms_message.py   # fayna.sms.message — черга, машина станів, send(), cron, _sanitize_phone()
    fayna_sms_log.py       # fayna.sms.log — незмінний журнал доставки
  data/
    cron.xml                   # ir.cron кожні 5 хв → model._cron_process_sms_queue()
    ir_config_parameter.xml    # fayna_sms_base.active (False) + .default_provider (turbosms)
  views/
    fayna_sms_provider_views.xml   # provider config tree/form
    fayna_sms_message_views.xml    # message queue tree/form/search + retry button
    fayna_sms_log_views.xml        # sms log tree/form
    fayna_sms_menus.xml            # меню Settings → SMS
  security/
    ir.model.access.csv      # ACL: admin r/w/c/d, user r/o (provider тільки admin)
    record_rules.xml
  tests/                     # test_fayna_sms_base.py (log), test_fayna_sms_message.py (черга+cron), test_scaffold.py
  i18n/                      # uk_UA.po + pl_PL.po
  docs/                      # TZ.md (цей), PLAN.md
```

---

## 4. Code Style

```python
# Телефон — нормалізація E.164 у create/write (fayna_sms_message.py)
def _sanitize_phone(phone: str) -> str:
    cleaned = re.sub(r"\s+", "", phone)
    cleaned = re.sub(r"[^\d+]", "", cleaned)   # лише цифри + leading +
    if cleaned and not cleaned.startswith("+"):
        cleaned = "+" + cleaned
    return cleaned

# Валідація E.164 (constraint)
@api.constrains("phone")
def _check_phone(self):
    if not re.match(r"^\+\d{7,15}$", rec.phone.strip()):
        raise ValidationError(...)
```

- **Секрети:** `api_key = fields.Char(..., groups="base.group_system")` — маскується в UI, ніколи не хардкод/лог/чат.
- **Незмінність log:** `fayna.sms.log.write`/`unlink` кидають `UserError` — порушувати не можна.
- **Provider lookup:** `f"fayna.sms.{provider_type}"`, перевірка `adapter_model in self.env` перед викликом.
- **Cron батч:** `limit=50`, `order="priority desc, create_date asc"`.
- **Lint:** ruff `select = E,F,W,I,N,UP,B,S,C4,SIM`, line-length 100, double quotes (див. `pyproject.toml`).
- **Header кожного .py:** `# © 2026 Fayna Digital — Volodymyr Shevchenko` + `# License LGPL-3`.
- **Semantic Versioning:** одна сесія = один bump у `__manifest__.py` + запис у CHANGELOG.

---

## 5. Testing

- **Фреймворк:** pytest, тести в `tests/` (`testpaths = ["tests"]`, `pyproject.toml`).
- **Покриття:** 36 тестів — `test_fayna_sms_base.py` (журнал доставки), `test_fayna_sms_message.py` (стани черги, sanitisation, cron success/failure/retry, send(), контракти провайдера), `test_scaffold.py` (install + флаг + deps). Ціль ≥70% (`fail_under = 70`).
- **Критичні шляхи:** машина станів `draft→queued→sent/failed`, retry до `max_retries`, дзеркалення результату в `fayna.sms.log`, поважання feature flag у cron.
- **Кожен bug-fix** → характеризаційний/regression тест.
- **Pre-commit зелений** на кожному коміті (ruff + ruff-format + OCA + bandit + gitleaks).

---

## 6. Boundaries

**Always:**
- Деплой лише #4ZONES: Mac → GitHub → staging → prod (golden rule #3 — [[meta/golden-rules-developer]]).
- `chmod -R o+rX` після git pull на сервері ([[claude-memory/feedback_git_pull_permissions]]).
- ≥1 тест на кожен fix; CHANGELOG-запис; Semantic Version bump.
- `api_key` лише через захищене поле `base.group_system`.

**Ask first:**
- Зміна дефолту feature flag `fayna_sms_base.active` (зараз `False` — навмисно інертний).
- Зміна публічного контракту адаптера (`send_sms` / `get_delivery_status` сигнатури) — ламає провайдери-модулі.
- Зміна машини станів `fayna.sms.message` чи інтервалу cron.

**Never:**
- Редагувати файли напряму на сервері (nano/vim/scp/docker exec edit) — golden rule #3.
- Секрети (`api_key`) у код / UI / лог / чат.
- Обходити незмінність `fayna.sms.log` через sudo.
- Додавати конкретного провайдера в цей base-модуль — провайдери = окремі модулі, що наслідують `fayna.sms.provider.base`.

---

## Success Criteria

- [x] Абстрактний адаптер `fayna.sms.provider.base` із `send_sms` / `get_delivery_status` (наслідується провайдерами).
- [x] Черга `fayna.sms.message` з машиною станів `draft→queued→sent/failed` + retry.
- [x] Cron кожні 5 хв диспетчеризує до 50 черг через активного провайдера.
- [x] `fayna.sms.log` незмінний, дзеркалить кожен результат.
- [x] Feature flag тримає модуль інертним до свідомого flip.
- [x] `api_key` захищений `base.group_system`; portal без доступу.
- [x] i18n uk_UA + pl_PL.
- [ ] Concrete provider `fayna_sms_turbosms` — окремий модуль (поза цим репо).

---

## Open Questions

- Інтеграція delivery-status: cron опитування `get_delivery_status` → оновлення log зі `sent` на `delivered` (зараз log фіксує лише момент відправки).
- Сегментація довгих повідомлень (>160 символів) — наразі лише help-текст, без явного split-обліку.
- Legacy поля (`provider` Selection, `_send_sms` batch) — план виведення з ужитку.

---

## Зв'язки

- Стандарт: [[REPO_STANDARD]] · Master: [[CAMPSCOUT_MASTER_TZ]] §16 Phase 4
- План реалізації: **docs/PLAN.md** · Як працювати: **CLAUDE.md**
- Інструменти: [[library/tools/python]] · [[library/tools/postgresql]] · [[library/tools/docker]] · [[library/tools/git]]
- Repo: `VladSh77/fayna-sms-base`
