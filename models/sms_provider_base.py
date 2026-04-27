# © 2026 Fayna Digital — Volodymyr Shevchenko <admin@fayna.agency>
# License LGPL-3 — see LICENSE file for full text.
from odoo import models


class FaynaSmsProviderLegacyAlias(models.AbstractModel):
    """Legacy alias for backward compatibility.

    New provider modules should inherit ``fayna.sms.provider.base``.
    This model delegates to it so existing ``_inherit = "fayna.sms.provider"``
    code continues to work.
    """

    _name = "fayna.sms.provider"
    _inherit = "fayna.sms.provider.base"
    _description = "Abstract SMS provider (inherit and implement send_sms)"
