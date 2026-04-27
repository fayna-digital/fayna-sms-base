# © 2026 Fayna Digital — Volodymyr Shevchenko <admin@fayna.agency>
# License LGPL-3 — see LICENSE file for full text.
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestFaynaSmsLog(TransactionCase):
    """Unit tests for fayna.sms.log model and fayna.sms.provider contract.

    Covers: CRUD, status transitions, log_result() helper, required fields,
    optional fields, and the abstract provider NotImplementedError contract.
    """

    def setUp(self):
        super().setUp()
        self.SmsLog = self.env["fayna.sms.log"]
        self._base_vals = {
            "provider_name": "turbosms",
            "recipient_number": "+48123456789",
            "body": "Hello from Fayna",
        }

    # ── 1. Basic create with status=pending ──────────────────────────────────
    def test_01_create_pending(self):
        """New log record defaults to 'pending' status."""
        log = self.SmsLog.create(self._base_vals)
        self.assertEqual(log.status, "pending")

    # ── 2. Status transition: pending → sent ─────────────────────────────────
    def test_02_transition_pending_to_sent(self):
        """Record can be moved from pending to sent."""
        log = self.SmsLog.create(self._base_vals)
        log.write({"status": "sent"})
        self.assertEqual(log.status, "sent")

    # ── 3. Status transition: pending → failed ───────────────────────────────
    def test_03_transition_pending_to_failed(self):
        """Record can be moved from pending to failed."""
        log = self.SmsLog.create(self._base_vals)
        log.write({"status": "failed"})
        self.assertEqual(log.status, "failed")

    # ── 4. log_result() helper — sent path ───────────────────────────────────
    def test_04_log_result_sent(self):
        """log_result() creates a log with status=sent and populates sent_at."""
        result = {"status": "sent", "message_id": "MSG-001", "error": None}
        log = self.SmsLog.log_result(
            self.env,
            provider_name="turbosms",
            number="+48987654321",
            body="Test sent",
            result_dict=result,
        )
        self.assertEqual(log.status, "sent")
        self.assertEqual(log.external_message_id, "MSG-001")
        self.assertIsNone(log.error_message)
        self.assertTrue(log.sent_at, "sent_at should be populated on successful send")

    # ── 5. log_result() helper — failed path ─────────────────────────────────
    def test_05_log_result_failed(self):
        """log_result() creates a log with status=failed and records the error."""
        result = {
            "status": "failed",
            "message_id": None,
            "error": "Insufficient credits",
        }
        log = self.SmsLog.log_result(
            self.env,
            provider_name="turbosms",
            number="+48111222333",
            body="Test failed",
            result_dict=result,
        )
        self.assertEqual(log.status, "failed")
        self.assertIsNone(log.external_message_id)
        self.assertEqual(log.error_message, "Insufficient credits")
        self.assertFalse(log.sent_at, "sent_at must be empty for failed sends")

    # ── 6. Records ordered by create_date desc ───────────────────────────────
    def test_06_order_create_date_desc(self):
        """The model's _order guarantees newest records first."""
        log1 = self.SmsLog.create(dict(self._base_vals, body="First"))
        log2 = self.SmsLog.create(dict(self._base_vals, body="Second"))
        # Both share the same transaction second; fall back to id ordering desc
        logs = self.SmsLog.search(
            [("id", "in", [log1.id, log2.id])],
        )
        # _order = "create_date desc" — when timestamps equal, DB returns last-inserted first
        self.assertIn(log1, logs)
        self.assertIn(log2, logs)
        # Verify the model-level _order declaration
        self.assertEqual(self.SmsLog._order, "create_date desc")

    # ── 7. provider_name is required ─────────────────────────────────────────
    def test_07_provider_name_required(self):
        """Creating a log without provider_name raises an error."""
        vals = dict(self._base_vals)
        del vals["provider_name"]
        with self.assertRaises((ValidationError, Exception)):
            self.SmsLog.create(vals)

    # ── 8. recipient_number is required ──────────────────────────────────────
    def test_08_recipient_number_required(self):
        """Creating a log without recipient_number raises an error."""
        vals = dict(self._base_vals)
        del vals["recipient_number"]
        with self.assertRaises((ValidationError, Exception)):
            self.SmsLog.create(vals)

    # ── 9. body is required ───────────────────────────────────────────────────
    def test_09_body_required(self):
        """Creating a log without body raises an error."""
        vals = dict(self._base_vals)
        del vals["body"]
        with self.assertRaises((ValidationError, Exception)):
            self.SmsLog.create(vals)

    # ── 10. partner_id is optional ────────────────────────────────────────────
    def test_10_partner_id_optional(self):
        """partner_id is not required — log can be created without it."""
        log = self.SmsLog.create(self._base_vals)
        self.assertFalse(log.partner_id)

    # ── 11. external_message_id stores provider reference ─────────────────────
    def test_11_external_message_id(self):
        """external_message_id stores an arbitrary string reference."""
        log = self.SmsLog.create(dict(self._base_vals, external_message_id="PROVIDER-XYZ-42"))
        self.assertEqual(log.external_message_id, "PROVIDER-XYZ-42")

    # ── 12. error_message populated on failure ────────────────────────────────
    def test_12_error_message_on_failure(self):
        """error_message can be set independently of status."""
        log = self.SmsLog.create(
            dict(self._base_vals, status="failed", error_message="Gateway timeout")
        )
        self.assertEqual(log.status, "failed")
        self.assertEqual(log.error_message, "Gateway timeout")

    # ── 13. Abstract provider raises NotImplementedError ─────────────────────
    def test_13_abstract_provider_raises_not_implemented(self):
        """Calling _send_sms() directly on the abstract model raises NotImplementedError."""
        provider = self.env["fayna.sms.provider"]
        with self.assertRaises(NotImplementedError):
            provider._send_sms(["+48000000000"], "test")

    # ── 14. log_result() with partner_id links the partner ───────────────────
    def test_14_log_result_with_partner(self):
        """log_result() respects the optional partner_id argument."""
        partner = self.env["res.partner"].create({"name": "Test Partner"})
        result = {"status": "sent", "message_id": "MSG-002", "error": None}
        log = self.SmsLog.log_result(
            self.env,
            provider_name="turbosms",
            number=partner.phone or "+48999888777",
            body="Linked partner SMS",
            result_dict=result,
            partner_id=partner.id,
        )
        self.assertEqual(log.partner_id, partner)
