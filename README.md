# Fayna SMS Base — Odoo 17 (v17.0.2.0.0)

![Odoo Version](https://img.shields.io/badge/Odoo-17.0%20Community-purple)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Phase](https://img.shields.io/badge/Phase-4-red)
![License](https://img.shields.io/badge/License-LGPL--3-green.svg)
![Status](https://img.shields.io/badge/Status-Production-brightgreen)

**Розроблено [Fayna Digital](https://www.fayna.agency) для CampScout.**
**Автор: Volodymyr Shevchenko**

---

## Що це

Базовий модуль SMS-інтеграції для Odoo 17. Надає абстрактний адаптер для будь-якого SMS-провайдера, чергу відправлення та журнал доставки.

Конкретні провайдери (наприклад `fayna_sms_turbosms`) наслідують цей модуль і реалізують `send_sms()`.

---

## Можливості

- `fayna.sms.provider.base` — абстрактний адаптер провайдера (патерн Strangler Fig)
- `fayna.sms.message` — черга вихідних SMS зі станами `draft → queued → sent / failed`
- `fayna.sms.log` — незмінний журнал кожного надісланого SMS
- Логіка повтору: `max_retries`, `retry_count`, автоматичне позначення `failed`
- Зручний метод: `fayna.sms.message.send(phone, body, partner_id=None)`
- Нормалізація телефону у форматі E.164
- Cron кожні 5 хвилин (активується через feature flag `fayna_sms_base.active`)
- Views для черги та журналу у меню Settings → SMS
- i18n: `uk_UA` + `pl_PL`

---

## Архітектура

```
fayna_sms_base/
├── __manifest__.py
├── __init__.py
├── data/
│   ├── cron.xml                    # cron кожні 5 хв
│   └── ir_config_parameter.xml     # feature flag + default_provider
├── models/
│   ├── sms_provider_base.py        # fayna.sms.provider (legacy alias)
│   ├── fayna_sms_provider.py       # fayna.sms.provider.base (AbstractModel)
│   ├── fayna_sms_log.py            # fayna.sms.log
│   └── fayna_sms_message.py        # fayna.sms.message + process_sms_queue()
├── security/
│   └── ir.model.access.csv         # ACL для log і message
├── views/
│   ├── fayna_sms_log_views.xml
│   └── fayna_sms_message_views.xml
├── tests/
│   ├── test_scaffold.py
│   ├── test_fayna_sms_base.py      # 14 тестів для fayna.sms.log
│   └── test_fayna_sms_message.py   # 22 тести для черги та cron
├── i18n/
│   ├── uk_UA.po
│   └── pl_PL.po
├── docs/TZ.md
├── pyproject.toml
├── LICENSE
├── CHANGELOG.md
└── README.md
```

---

## Feature flag (Strangler Fig)

Після встановлення cron **не відправляє SMS** — флаг `fayna_sms_base.active` за замовчуванням `False`.

Щоб активувати:

```python
env["ir.config_parameter"].sudo().set_param("fayna_sms_base.active", "True")
```

Або через Settings → Technical → System Parameters.

---

## Як написати власний провайдер

```python
class MyProvider(models.AbstractModel):
    _name = "fayna.sms.myprovider"
    _inherit = "fayna.sms.provider.base"

    def send_sms(self, phone: str, body: str) -> dict:
        # ... call your API ...
        return {"success": True, "external_id": "MSG-ID", "error": None}

    def get_delivery_status(self, external_id: str) -> str:
        return "pending"  # or "delivered" / "failed"
```

Встановіть `fayna_sms_base.default_provider = "myprovider"` у System Parameters.

---

## Встановлення

```bash
cd /opt/campscout/custom-addons
sudo -u \#1000 git clone https://github.com/VladSh77/fayna-sms-base.git fayna_sms_base
docker exec campscout_web odoo -c /etc/odoo/odoo.conf -d campscout \
    -i fayna_sms_base --stop-after-init --no-http
docker restart campscout_web
```

---

## Ліцензія

LGPL-3 — дивись [LICENSE](LICENSE).

---

*Розроблено [Fayna Digital](https://www.fayna.agency) · Volodymyr Shevchenko*
