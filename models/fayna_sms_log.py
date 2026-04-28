# © 2026 Fayna Digital — Volodymyr Shevchenko <admin@fayna.agency>
# License LGPL-3 — see LICENSE file for full text.
from odoo import _, fields, models
from odoo.exceptions import UserError


class FaynaSmsLog(models.Model):
    """Delivery log for every SMS dispatched through a Fayna provider."""

    _name = "fayna.sms.log"
    _description = "SMS delivery log"
    _order = "create_date desc"
    _rec_name = "recipient_number"

    # ── Who ──────────────────────────────────────────────────────────────────
    provider_name = fields.Char(
        string="Provider",
        required=True,
        index=True,
    )
    recipient_number = fields.Char(
        string="Recipient",
        required=True,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        ondelete="set null",
        index=True,
    )

    # ── What ─────────────────────────────────────────────────────────────────
    body = fields.Text(
        string="Message body",
        required=True,
    )

    # ── Result ───────────────────────────────────────────────────────────────
    status = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("sent", "Sent"),
            ("failed", "Failed"),
            ("delivered", "Delivered"),
        ],
        string="Status",
        default="pending",
        required=True,
        index=True,
    )
    external_message_id = fields.Char(string="Provider message ID")
    sent_at = fields.Datetime(string="Sent at")
    error_message = fields.Text(string="Error detail")

    # ── Source traceability ───────────────────────────────────────────────────
    model_name = fields.Char(string="Source model")
    record_id = fields.Integer(string="Source record ID")

    # ── Immutability ─────────────────────────────────────────────────────────
    def write(self, vals):
        """Block all writes after create — log records are immutable."""
        raise UserError(
            _("SMS log records are immutable and cannot be modified after creation.")
        )

    def unlink(self):
        """Block deletion — log records are immutable."""
        raise UserError(
            _("SMS log records are immutable and cannot be deleted.")
        )

    # ── Helper ───────────────────────────────────────────────────────────────
    @classmethod
    def log_result(
        cls,
        env,
        provider_name: str,
        number: str,
        body: str,
        result_dict: dict,
        partner_id: int | None = None,
    ) -> "FaynaSmsLog":
        """Create a :class:`FaynaSmsLog` record from a ``_send_sms`` result.

        :param env: Odoo environment (``self.env`` from the caller).
        :param provider_name: Technical name of the provider, e.g. ``"turbosms"``.
        :param number: E.164 recipient phone number.
        :param body: Original message text.
        :param result_dict: Single-number entry from the dict returned by
            :meth:`fayna.sms.provider._send_sms`, i.e.
            ``{"status": "sent"|"failed", "message_id": str|None, "error": str|None}``.
        :param partner_id: Optional ``res.partner`` database ID to link.
        :returns: Newly created ``fayna.sms.log`` record.
        """
        status = result_dict.get("status", "failed")
        vals = {
            "provider_name": provider_name,
            "recipient_number": number,
            "body": body,
            "status": status,
            "external_message_id": result_dict.get("message_id"),
            "error_message": result_dict.get("error"),
        }
        if status == "sent":
            vals["sent_at"] = fields.Datetime.now()
        if partner_id:
            vals["partner_id"] = partner_id
        return env["fayna.sms.log"].create(vals)

    # ── Display ───────────────────────────────────────────────────────────────
    def name_get(self):
        result = []
        for rec in self:
            label = _("%(number)s [%(status)s]") % {
                "number": rec.recipient_number,
                "status": rec.status,
            }
            result.append((rec.id, label))
        return result
