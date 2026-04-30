# © 2026 Fayna Digital — Volodymyr Shevchenko <admin@fayna.agency>
# License LGPL-3 — see LICENSE file for full text.
from odoo import _, fields, models
from odoo.exceptions import UserError


class FaynaSmsProvider(models.Model):
    """SMS provider configuration record.

    Each row represents one configured provider (e.g. TurboSMS API credentials).
    The abstract implementation lives in :class:`FaynaSmsProviderBase`
    (``fayna.sms.provider.base``) and is looked up via ``provider_type``.

    Only ``base.group_system`` has write access — see ``ir.model.access.csv``.
    ``api_key`` is declared ``password=True`` so it is masked in the UI.
    """

    _name = "fayna.sms.provider"
    _description = "SMS Provider Configuration"
    _order = "sequence, name"
    _rec_name = "name"

    # ── Identity ──────────────────────────────────────────────────────────────
    name = fields.Char(
        string="Provider name",
        required=True,
        help="Human-readable label, e.g. 'TurboSMS Production'.",
    )
    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Lower sequence = higher priority when multiple providers are active.",
    )
    provider_type = fields.Selection(
        selection=[
            ("turbosms", "TurboSMS"),
        ],
        string="Provider type",
        required=True,
        help="Technical adapter class suffix, e.g. 'turbosms' → fayna.sms.turbosms.",
    )

    # ── Credentials ───────────────────────────────────────────────────────────
    api_key = fields.Char(
        string="API key",
        help="Provider API key / token. Masked in the UI via view widget.",
        groups="base.group_system",
    )

    # ── Status ────────────────────────────────────────────────────────────────
    active = fields.Boolean(
        string="Active",
        default=True,
        help="Only the first active provider (by sequence) is used for dispatch.",
    )

    # ── Send-through entry point ──────────────────────────────────────────────
    def send_sms(self, phone: str, body: str) -> dict:
        """Dispatch an SMS through the concrete adapter for this provider.

        Looks up ``fayna.sms.<provider_type>`` model in the registry and
        delegates the call.

        :param phone: E.164 phone number, e.g. ``"+48123456789"``.
        :param body: SMS text.
        :returns: ``{"success": bool, "external_id": str|None, "error": str|None}``
        :raises UserError: If the provider adapter model is not installed.
        """
        self.ensure_one()
        adapter_model = f"fayna.sms.{self.provider_type}"
        if adapter_model not in self.env:
            raise UserError(
                _("SMS provider adapter '%(model)s' is not installed.") % {"model": adapter_model}
            )
        return self.env[adapter_model].send_sms(phone, body)

    # ── Helpers ───────────────────────────────────────────────────────────────
    @classmethod
    def _get_active_provider(cls, env):
        """Return the first active provider record (lowest sequence).

        :returns: :class:`FaynaSmsProvider` singleton or empty recordset.
        """
        return env["fayna.sms.provider"].search([("active", "=", True)], limit=1)
