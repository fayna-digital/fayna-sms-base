{
    "name": "Fayna SMS Base",
    "version": "17.0.2.0.0",
    "category": "Tools/Camp Management",
    "summary": "Provider-agnostic SMS adapter base (abstract send + outbound queue + delivery log)",
    "description": """
Fayna SMS Base
==============

Phase 4 of the Fayna Camp vertical stack (Strangler Fig decomposition
per CAMPSCOUT_MASTER_TZ.md §16).

Abstract SMS adapter interface + outbound queue model (fayna.sms.message).
Provider modules (e.g. fayna_sms_turbosms) inherit fayna.sms.provider and
implement send_sms() / get_delivery_status().

Features:
- fayna.sms.message: outbound SMS queue with state machine (draft/queued/sent/failed)
- fayna.sms.log: immutable delivery log
- fayna.sms.provider: abstract adapter (NotImplementedError contract)
- Cron every 5 min: dispatches queued messages via the configured provider
- Convenience method: fayna.sms.message.send(partner_id, body, phone=None)
- Phone sanitization (E.164 normalisation, strip spaces)
- Views: Message Queue tree/form + SMS Log tree/form under Settings > SMS menu
- i18n: uk_UA + pl_PL

Author: Fayna Digital — Volodymyr Shevchenko
License: LGPL-3
TZ: fayna-digital-docs/contributing/CAMPSCOUT_MASTER_TZ.md §16 Phase 4
    """,
    "author": "Fayna Digital — Volodymyr Shevchenko",
    "website": "https://fayna.agency",
    "license": "LGPL-3",
    "depends": ["base", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_config_parameter.xml",
        "data/cron.xml",
        "views/fayna_sms_message_views.xml",
        "views/fayna_sms_log_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
