# Fayna SMS Base — CLAUDE.md

> 🚫 **#4ZONES — НІКОЛИ не працювати напряму на сервері.**
> Єдиний шлях: **локально → GitHub (push) → staging → prod (pull)**. Жодних правок файлів на сервері (nano/vim/scp/docker exec з редагуванням), жодних тимчасових скриптів на проді — спершу локально, коміт, push, тоді pull на сервер. Зміни «на сервері» зникають при наступному `git pull`/rebuild. Git — єдине джерело правди. ([[meta/golden-rules-developer]] #3)

> Як працювати з репо. **Що** будуємо — у [docs/TZ.md](docs/TZ.md) (специфікація за REPO_STANDARD). **Як реалізуємо** — у [docs/PLAN.md](docs/PLAN.md).

## Призначення

Базовий, незалежний від провайдера, SMS-адаптер для Odoo 17 Community. Дає абстрактний інтерфейс відправки, чергу вихідних повідомлень із машиною станів і незмінний журнал доставки. Конкретні провайдери (напр. `fayna_sms_turbosms`) наслідують `fayna.sms.provider.base` і реалізують `send_sms()` / `get_delivery_status()`.

Phase 4 вертикального стеку Fayna Camp (Strangler Fig decomposition, `CAMPSCOUT_MASTER_TZ.md` §16).

**Версія:** `17.0.2.1.0` | Модуль: `fayna_sms_base` | License: LGPL-3 | depends: `base`, `mail`

## Структура модуля

```
fayna_sms_base/
  models/
    sms_provider_base.py   # fayna.sms.provider.base — AbstractModel (send_sms / get_delivery_status)
    fayna_sms_provider.py  # fayna.sms.provider — DB-конфіг провайдера (name, provider_type, api_key)
    fayna_sms_message.py   # fayna.sms.message — черга вихідних + machine станів + cron
    fayna_sms_log.py       # fayna.sms.log — незмінний журнал доставки (write/unlink заблоковані)
  data/
    cron.xml                   # cron кожні 5 хв → _cron_process_sms_queue()
    ir_config_parameter.xml    # feature flag .active + .default_provider
  views/                       # provider config, message queue, sms log, menus
  security/                    # ir.model.access.csv + record_rules.xml
  tests/  i18n/  docs/
```

## Deploy — #4ZONES (Mac → GitHub → staging → prod)

```bash
git push origin main
ssh prod 'cd /opt/campscout/addons/fayna_sms_base && git pull && sudo chmod -R o+rX .'
# Python-only fix → достатньо рестарту:
ssh prod 'docker restart campscout_web'
# Зміна моделей/views/security → update модуля:
ssh prod 'docker exec campscout_web odoo -u fayna_sms_base --stop-after-init -d campscout && docker restart campscout_web'
```

## Feature flag (Strangler Fig)

Після встановлення модуль **інертний**: cron-флаг `fayna_sms_base.active` за замовчуванням `False`, тож черга не відправляє SMS, доки legacy-поведінка ще володіє доменом. Активація — лише свідомий flip:

```python
env["ir.config_parameter"].sudo().set_param("fayna_sms_base.active", "True")
```

`process_sms_queue()` обходить флаг (для програмних викликів і тестів); `_cron_process_sms_queue()` його поважає.

## Coding conventions

- **Секрети** (`api_key`) — поле з `groups="base.group_system"`, маскується в UI; ніколи не хардкод, ніколи в лог/чат.
- **Телефони** — лише E.164 (`+\d{7,15}`), нормалізація через `_sanitize_phone()` у `create`/`write`.
- **`fayna.sms.log` незмінний** — `write`/`unlink` кидають `UserError`; не обходити sudo.
- **Cron батч** — максимум 50 повідомлень за прохід; не знімати ліміт.
- **Provider lookup** — `fayna.sms.<provider_type>` у реєстрі; нові провайдери = окремий модуль, не правки тут.
- **Semantic Versioning** у `__manifest__.py`: одна сесія = один bump + запис у CHANGELOG.

## Тестування

```bash
python -m pytest tests/ -v          # 36 тестів (log + message + scaffold)
pre-commit run --all-files          # ruff + ruff-format + OCA + bandit + gitleaks
```

## Документація репо

- **docs/TZ.md** — специфікація (6 областей: Objective / Commands / Project Structure / Code Style / Testing / Boundaries) ← за REPO_STANDARD
- **docs/PLAN.md** — dependency graph + фази + checkpoints
- **CHANGELOG.md** — історія версій (Keep a Changelog)
- **README.md** — вступ + фічі + встановлення

## Зв'язки

Стандарт: [[REPO_STANDARD]] · Master: [[CAMPSCOUT_MASTER_TZ]] §16 Phase 4 · Інструменти: [[library/tools/python]] · [[library/tools/postgresql]] · [[library/tools/docker]] · [[library/tools/git]] · Golden rules: [[meta/golden-rules-developer]]
