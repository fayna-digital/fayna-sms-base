# © 2026 Fayna Digital — Volodymyr Shevchenko <admin@fayna.agency>
# License LGPL-3 — see LICENSE file for full text.
from odoo import models


class FaynaSmsProvider(models.AbstractModel):
    """Abstract SMS provider.

    Concrete provider modules (e.g. fayna_sms_turbosms) must:
      1. ``_inherit = "fayna.sms.provider"``
      2. Override :meth:`_send_sms`.

    The model is declared ``_abstract = True`` so no database table is created.
    """

    _name = "fayna.sms.provider"
    _description = "Abstract SMS provider (inherit and implement _send_sms)"

    def _send_sms(self, numbers: list, body: str) -> dict:
        """Send SMS to one or more phone numbers.

        :param numbers: List of E.164 phone numbers, e.g. ``["+48123456789"]``.
        :param body: SMS text content.  Long messages are split by the carrier
            into 160-character segments.
        :returns: Mapping ``{number: {"status": "sent"|"failed",
            "message_id": str|None, "error": str|None}}``.
        :raises NotImplementedError: Always — subclasses must override this.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement _send_sms()")
