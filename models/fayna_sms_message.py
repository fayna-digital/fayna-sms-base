# © 2026 Fayna Digital — Volodymyr Shevchenko <admin@fayna.agency>
# License LGPL-3 — see LICENSE file for full text.
import logging
import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

# Selection options contributed by provider modules via _get_provider_selection()
_PROVIDER_SELECTION = [
    ("turbosms", "TurboSMS"),
]


def _sanitize_phone(phone: str) -> str:
    """Strip whitespace and non-digit chars except leading +; ensure + prefix."""
    if not phone:
        return phone
    cleaned = re.sub(r"\s+", "", phone)
    # Remove everything that is not a digit or a leading +
    cleaned = re.sub(r"[^\d+]", "", cleaned)
    # Ensure + prefix
    if cleaned and not cleaned.startswith("+"):
        cleaned = "+" + cleaned
    return cleaned


# Module-level alias used in tests and by provider modules
normalize_phone = _sanitize_phone


class FaynaSmsMessage(models.Model):
    """Outbound SMS queue.

    Each record represents one SMS to be sent.  The cron job
    ``process_sms_queue`` picks up records in state ``queued`` and
    dispatches them via the configured provider adapter.
    """

    _name = "fayna.sms.message"
    _description = "SMS Message Queue"
    _order = "priority desc, create_date asc"
    _rec_name = "phone"

    # ── Recipient ─────────────────────────────────────────────────────────────
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        ondelete="set null",
        index=True,
    )
    phone = fields.Char(
        string="Phone",
        required=True,
        help="E.164 phone number, e.g. +48123456789",
    )

    # ── Content ───────────────────────────────────────────────────────────────
    body = fields.Text(
        string="Message",
        required=True,
        help="SMS text. Messages longer than 160 characters are split into segments.",
    )

    # ── Routing ───────────────────────────────────────────────────────────────
    provider = fields.Selection(
        selection=_PROVIDER_SELECTION,
        string="Provider",
        help="SMS provider to use. Defaults to fayna_sms_base.default_provider system parameter.",
    )

    # ── State machine ─────────────────────────────────────────────────────────
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("queued", "Queued"),
            ("sent", "Sent"),
            ("failed", "Failed"),
        ],
        string="State",
        default="draft",
        required=True,
        index=True,
    )
    sent_at = fields.Datetime(string="Sent at", readonly=True)
    error_message = fields.Char(
        string="Error",
        readonly=True,
        help="Last error message from the provider.",
    )
    external_id = fields.Char(
        string="Provider message ID",
        readonly=True,
        help="Message ID returned by the provider for status tracking.",
    )

    # ── Retry ─────────────────────────────────────────────────────────────────
    retry_count = fields.Integer(string="Retry count", default=0, readonly=True)
    max_retries = fields.Integer(string="Max retries", default=3)

    # ── Priority ──────────────────────────────────────────────────────────────
    priority = fields.Selection(
        selection=[("0", "Normal"), ("1", "High")],
        string="Priority",
        default="0",
    )

    # ── Constraints ───────────────────────────────────────────────────────────
    @api.constrains("phone")
    def _check_phone(self):
        for rec in self:
            if not rec.phone or not re.match(r"^\+\d{7,15}$", rec.phone.strip()):
                raise ValidationError(
                    _("Phone number '%(phone)s' is not valid E.164 format (e.g. +48123456789).")
                    % {"phone": rec.phone}
                )

    # ── ORM ───────────────────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "phone" in vals and vals["phone"]:
                vals["phone"] = _sanitize_phone(vals["phone"])
        return super().create(vals_list)

    def write(self, vals):
        if "phone" in vals and vals["phone"]:
            vals["phone"] = _sanitize_phone(vals["phone"])
        return super().write(vals)

    # ── Convenience factory ───────────────────────────────────────────────────
    @api.model
    def send(self, phone, body, partner_id=None, priority="0"):
        """Queue an SMS for sending.

        :param phone: E.164 phone number string (required).
        :param body: SMS text.
        :param partner_id: ``res.partner`` id (int) or recordset. May be None.
        :param priority: '0' Normal or '1' High.
        :returns: ``fayna.sms.message`` record in state ``queued``.
        """
        if not phone:
            if not partner_id:
                raise ValidationError(_("Either phone or partner_id is required."))
            partner = (
                self.env["res.partner"].browse(partner_id)
                if isinstance(partner_id, int)
                else partner_id
            )
            phone = partner.mobile or partner.phone
        if not phone:
            raise ValidationError(_("No phone number available for this partner."))

        pid = partner_id.id if hasattr(partner_id, "id") else partner_id
        default_provider = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("fayna_sms_base.default_provider", default="turbosms")
        )
        msg = self.create(
            {
                "partner_id": pid,
                "phone": phone,
                "body": body,
                "provider": default_provider,
                "state": "queued",
                "priority": priority,
            }
        )
        return msg

    @staticmethod
    def normalize_phone(phone: str) -> str:
        """Strip spaces/dashes, ensure leading +.

        Return normalized or original if can't normalize.
        Delegates to module-level _sanitize_phone helper.
        """
        return _sanitize_phone(phone) if phone else phone

    # ── Actions ───────────────────────────────────────────────────────────────
    def action_queue(self):
        """Move draft message to queued state."""
        self.filtered(lambda r: r.state == "draft").write({"state": "queued"})

    def action_retry(self):
        """Reset failed message for retry."""
        for rec in self:
            if rec.state == "failed":
                rec.write({"state": "queued", "error_message": False, "retry_count": 0})

    def action_cancel(self):
        """Cancel queued/draft message."""
        self.filtered(lambda r: r.state in ("draft", "queued")).write({"state": "failed"})

    # ── Cron ─────────────────────────────────────────────────────────────────
    @api.model
    def _cron_process_sms_queue(self):
        """Canonical cron entry point.  Delegates to :meth:`process_sms_queue`."""
        return self.process_sms_queue()

    @api.model
    def process_sms_queue(self):
        """Cron: dispatch up to 50 queued SMS messages via the configured provider."""
        queued = self.search(
            [("state", "=", "queued")], limit=50, order="priority desc, create_date asc"
        )
        if not queued:
            return

        _logger.info("fayna_sms_base: processing %d queued messages", len(queued))

        for msg in queued:
            provider_name = msg.provider or self.env["ir.config_parameter"].sudo().get_param(
                "fayna_sms_base.default_provider", default=""
            )
            if not provider_name:
                _logger.warning("fayna_sms_base: no provider configured, skipping msg id=%d", msg.id)
                continue

            try:
                provider = self.env[f"fayna.sms.{provider_name}"]
            except KeyError:
                _logger.error(
                    "fayna_sms_base: provider model 'fayna.sms.%s' not found", provider_name
                )
                msg.write(
                    {
                        "state": "failed",
                        "error_message": f"Provider 'fayna.sms.{provider_name}' not installed.",
                    }
                )
                continue

            try:
                result = provider.send_sms(msg.phone, msg.body)
            except Exception as exc:  # noqa: BLE001
                _logger.exception("fayna_sms_base: provider raised unexpected error for msg id=%d", msg.id)
                result = {"success": False, "external_id": None, "error": str(exc)}

            if result.get("success"):
                msg.write(
                    {
                        "state": "sent",
                        "sent_at": fields.Datetime.now(),
                        "external_id": result.get("external_id"),
                        "error_message": False,
                    }
                )
                # Mirror to delivery log
                self.env["fayna.sms.log"].create(
                    {
                        "provider_name": provider_name,
                        "recipient_number": msg.phone,
                        "body": msg.body,
                        "status": "sent",
                        "external_message_id": result.get("external_id"),
                        "sent_at": fields.Datetime.now(),
                        "partner_id": msg.partner_id.id if msg.partner_id else False,
                    }
                )
            else:
                new_retry = msg.retry_count + 1
                if new_retry >= msg.max_retries:
                    msg.write(
                        {
                            "state": "failed",
                            "retry_count": new_retry,
                            "error_message": result.get("error", "Unknown error"),
                        }
                    )
                    self.env["fayna.sms.log"].create(
                        {
                            "provider_name": provider_name,
                            "recipient_number": msg.phone,
                            "body": msg.body,
                            "status": "failed",
                            "error_message": result.get("error", "Unknown error"),
                            "partner_id": msg.partner_id.id if msg.partner_id else False,
                        }
                    )
                else:
                    msg.write(
                        {
                            "retry_count": new_retry,
                            "error_message": result.get("error", "Unknown error"),
                        }
                    )
