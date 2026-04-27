{
    "name": "Fayna SMS Base",
    "version": "17.0.1.0.0",
    "category": "Tools/Camp Management",
    "summary": "Provider-agnostic SMS adapter base (abstract send + delivery log)",
    "description": """
Fayna SMS Base
==============

Phase 4 of the Fayna Camp vertical stack (Strangler Fig decomposition
per CAMPSCOUT_MASTER_TZ.md §16).

Abstract SMS adapter interface. Provider modules (e.g. fayna_sms_turbosms) inherit.

Current status: scaffold — installable but inert. Feature flag
`fayna_sms_base.active` defaults to `False`; implementation lands in incremental
milestones defined in docs/TZ.md.

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
        "views/fayna_sms_log_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
