# © 2026 Fayna Digital — Volodymyr Shevchenko <admin@fayna.agency>
# License LGPL-3 — see LICENSE file for full text.
from odoo import models


class FaynaSmsProviderBase(models.AbstractModel):
    """Abstract SMS provider adapter base.

    Concrete provider modules (e.g. fayna_sms_turbosms) must:
      1. ``_inherit = "fayna.sms.provider.base"``
      2. Override :meth:`send_sms`.
      3. Override :meth:`get_delivery_status` if the API supports it.
    """

    _name = "fayna.sms.provider.base"
    _description = "Abstract SMS provider adapter (override in provider modules)"

    # ── New single-message interface (used by fayna.sms.provider.send_sms) ──

    def send_sms(self, phone: str, body: str) -> dict:
        """Send SMS to a single phone number.

        :param phone: E.164 phone number, e.g. ``"+48123456789"``.
        :param body: SMS text content.
        :returns: ``{"success": bool, "external_id": str|None, "error": str|None}``
        :raises NotImplementedError: Always — subclasses must override this.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement send_sms()")

    def get_delivery_status(self, external_id: str) -> str:
        """Return delivery status for a previously sent message.

        :param external_id: Provider-assigned message ID returned by :meth:`send_sms`.
        :returns: One of ``"delivered"``, ``"failed"``, ``"pending"``.
        :raises NotImplementedError: Always — subclasses must override this.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement get_delivery_status()"
        )

    # ── Legacy batch interface (kept for backward compatibility) ───────────────

    def _send_sms(self, numbers: list, body: str) -> dict:
        """Send SMS to one or more phone numbers (legacy batch interface).

        :param numbers: List of E.164 phone numbers, e.g. ``["+48123456789"]``.
        :param body: SMS text content.
        :returns: Mapping ``{number: {"status": "sent"|"failed",
            "message_id": str|None, "error": str|None}}``.
        :raises NotImplementedError: Always — subclasses must override this.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement _send_sms()")
