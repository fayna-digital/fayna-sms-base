# Fayna SMS Base — Odoo 17 (v17.0.2.1.0)

![Odoo Version](https://img.shields.io/badge/Odoo-17.0%20Community-purple)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Phase](https://img.shields.io/badge/Phase-4-red)
![License](https://img.shields.io/badge/License-LGPL--3-green.svg)
![Status](https://img.shields.io/badge/Status-Production-brightgreen)

**Opracowane przez [Fayna Digital](https://www.fayna.agency) dla CampScout.**
**Autor: Volodymyr Shevchenko**

---

## Co to jest

Bazowy moduł integracji SMS dla Odoo 17. Dostarcza abstrakcyjny adapter dla
dowolnego providera SMS, kolejkę wysyłki oraz dziennik dostarczenia.

Konkretni providerzy (np. `fayna_sms_turbosms`) dziedziczą ten moduł i
implementują `send_sms()`.

---

## Możliwości

- `fayna.sms.provider.base` — abstrakcyjny adapter providera (wzorzec Strangler Fig)
- `fayna.sms.message` — kolejka wychodzących SMS ze stanami `draft → queued → sent / failed`
- `fayna.sms.log` — niezmienny dziennik każdego wysłanego SMS
- Logika ponawiania: `max_retries`, `retry_count`, automatyczne oznaczanie `failed`
- Wygodna metoda: `fayna.sms.message.send(phone, body, partner_id=None)`
- Normalizacja telefonu do formatu E.164
- Cron co 5 minut (aktywowany przez feature flag `fayna_sms_base.active`)
- Widoki dla kolejki i dziennika w menu Settings → SMS
- i18n: `uk_UA` + `pl_PL`

---

## Architektura

```
fayna_sms_base/
├── __manifest__.py
├── __init__.py
├── data/
│   ├── cron.xml                    # cron co 5 min
│   └── ir_config_parameter.xml     # feature flag + default_provider
├── models/
│   ├── sms_provider_base.py        # fayna.sms.provider (legacy alias)
│   ├── fayna_sms_provider.py       # fayna.sms.provider.base (AbstractModel)
│   ├── fayna_sms_log.py            # fayna.sms.log
│   └── fayna_sms_message.py        # fayna.sms.message + process_sms_queue()
├── security/
│   └── ir.model.access.csv         # ACL dla log i message
├── views/
│   ├── fayna_sms_log_views.xml
│   ├── fayna_sms_message_views.xml
│   ├── fayna_sms_provider_views.xml
│   └── fayna_sms_menus.xml
├── tests/
│   ├── test_scaffold.py
│   ├── test_fayna_sms_base.py      # 14 testów dla fayna.sms.log
│   └── test_fayna_sms_message.py   # 22 testy dla kolejki i crona
├── i18n/
│   ├── uk_UA.po
│   └── pl_PL.po
├── docs/
│   ├── TZ.md                       # specyfikacja (6 obszarów spec-driven)
│   └── PLAN.md                     # dependency graph + fazy + checkpointy
├── pyproject.toml
├── LICENSE
├── CHANGELOG.md
└── README.md
```

---

## Feature flag (Strangler Fig)

Po instalacji cron **nie wysyła SMS** — flaga `fayna_sms_base.active` domyślnie `False`.

Aby aktywować:

```python
env["ir.config_parameter"].sudo().set_param("fayna_sms_base.active", "True")
```

Lub przez Settings → Technical → System Parameters.

---

## Jak napisać własnego providera

```python
class MyProvider(models.AbstractModel):
    _name = "fayna.sms.myprovider"
    _inherit = "fayna.sms.provider.base"

    def send_sms(self, phone: str, body: str) -> dict:
        # ... wywołaj swoje API ...
        return {"success": True, "external_id": "MSG-ID", "error": None}

    def get_delivery_status(self, external_id: str) -> str:
        return "pending"  # or "delivered" / "failed"
```

Ustaw `fayna_sms_base.default_provider = "myprovider"` w System Parameters.

---

## Instalacja

```bash
cd /opt/campscout/custom-addons
sudo -u \#1000 git clone https://github.com/fayna-digital/fayna-sms-base.git fayna_sms_base
docker exec campscout_web odoo -c /etc/odoo/odoo.conf -d campscout \
    -i fayna_sms_base --stop-after-init --no-http
docker restart campscout_web
```

---

## Dokumentacja

- [docs/TZ.md](docs/TZ.md) — kanoniczna specyfikacja (6 obszarów: Objective / Commands / Project Structure / Code Style / Testing / Boundaries).
- [docs/PLAN.md](docs/PLAN.md) — plan implementacji: dependency graph, fazy, checkpointy.
- [CHANGELOG.md](CHANGELOG.md) — historia wersji.

---

## Licencja

LGPL-3 — patrz [LICENSE](LICENSE).

---

*Opracowane przez [Fayna Digital](https://www.fayna.agency) · Volodymyr Shevchenko*
