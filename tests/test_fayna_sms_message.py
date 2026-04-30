# © 2026 Fayna Digital — Volodymyr Shevchenko <admin@fayna.agency>
# License LGPL-3 — see LICENSE file for full text.
from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestFaynaSmsMessage(TransactionCase):
    """Tests for fayna.sms.message outbound queue model.

    Covers: state machine, phone sanitisation, cron dispatch,
    retry logic, send() convenience method, and abstract provider contract.
    """

    def setUp(self):
        super().setUp()
        self.Msg = self.env["fayna.sms.message"]
        self._base_vals = {
            "phone": "+48123456789",
            "body": "Hello from Fayna",
            "provider": "turbosms",
        }

    # ── 1. Create with default state=draft ───────────────────────────────────
    def test_01_create_defaults_to_draft(self):
        msg = self.Msg.create(self._base_vals)
        self.assertEqual(msg.state, "draft")
        self.assertEqual(msg.retry_count, 0)
        self.assertEqual(msg.max_retries, 3)
        self.assertEqual(msg.priority, "0")

    # ── 2. Mark sent manually ────────────────────────────────────────────────
    def test_02_mark_sent(self):
        from odoo import fields

        msg = self.Msg.create(self._base_vals)
        now = fields.Datetime.now()
        msg.write({"state": "sent", "sent_at": now, "external_id": "EXT-001"})
        self.assertEqual(msg.state, "sent")
        self.assertEqual(msg.external_id, "EXT-001")
        self.assertTrue(msg.sent_at)

    # ── 3. Phone sanitisation — strips spaces ────────────────────────────────
    def test_03_phone_sanitise_spaces(self):
        msg = self.Msg.create(dict(self._base_vals, phone="+48 123 456 789"))
        self.assertEqual(msg.phone, "+48123456789")

    # ── 4. Phone sanitisation — adds + prefix ────────────────────────────────
    def test_04_phone_sanitise_adds_plus(self):
        msg = self.Msg.create(dict(self._base_vals, phone="48123456789"))
        self.assertEqual(msg.phone, "+48123456789")

    # ── 5. Invalid phone raises ValidationError ───────────────────────────────
    def test_05_invalid_phone_raises(self):
        with self.assertRaises(ValidationError):
            self.Msg.create(dict(self._base_vals, phone="not-a-phone"))

    # ── 6. action_queue moves draft → queued ─────────────────────────────────
    def test_06_action_queue(self):
        msg = self.Msg.create(self._base_vals)
        self.assertEqual(msg.state, "draft")
        msg.action_queue()
        self.assertEqual(msg.state, "queued")

    # ── 7. action_retry resets failed → queued ───────────────────────────────
    def test_07_action_retry(self):
        msg = self.Msg.create(
            dict(self._base_vals, state="failed", retry_count=3, error_message="Timeout")
        )
        msg.action_retry()
        self.assertEqual(msg.state, "queued")
        self.assertEqual(msg.retry_count, 0)
        self.assertFalse(msg.error_message)

    # ── 8. Cron processes queued message — success path ──────────────────────
    def test_08_cron_processes_queued_success(self):
        msg = self.Msg.create(dict(self._base_vals, state="queued"))
        success_result = {"success": True, "external_id": "TURBO-111", "error": None}

        with patch.object(
            type(self.env["fayna.sms.turbosms"]), "send_sms", return_value=success_result
        ):
            self.Msg.process_sms_queue()

        msg.invalidate_recordset()
        self.assertEqual(msg.state, "sent")
        self.assertEqual(msg.external_id, "TURBO-111")
        self.assertTrue(msg.sent_at)

    # ── 9. Cron increments retry_count on failure ─────────────────────────────
    def test_09_cron_failure_increments_retry(self):
        msg = self.Msg.create(dict(self._base_vals, state="queued", max_retries=3))
        fail_result = {"success": False, "external_id": None, "error": "Gateway error"}

        with patch.object(
            type(self.env["fayna.sms.turbosms"]), "send_sms", return_value=fail_result
        ):
            self.Msg.process_sms_queue()

        msg.invalidate_recordset()
        self.assertEqual(msg.retry_count, 1)
        self.assertEqual(msg.state, "queued")  # not failed yet — below max_retries
        self.assertEqual(msg.error_message, "Gateway error")

    # ── 10. Cron marks failed after max_retries exceeded ─────────────────────
    def test_10_cron_max_retries_reached(self):
        msg = self.Msg.create(dict(self._base_vals, state="queued", retry_count=2, max_retries=3))
        fail_result = {"success": False, "external_id": None, "error": "Persistent error"}

        with patch.object(
            type(self.env["fayna.sms.turbosms"]), "send_sms", return_value=fail_result
        ):
            self.Msg.process_sms_queue()

        msg.invalidate_recordset()
        self.assertEqual(msg.state, "failed")
        self.assertEqual(msg.retry_count, 3)
        self.assertEqual(msg.error_message, "Persistent error")

    # ── 11. send() convenience method queues message via partner ─────────────
    def test_11_send_convenience_method(self):
        partner = self.env["res.partner"].create({"name": "Test Partner", "phone": "+48987654321"})
        msg = self.Msg.send(phone=None, body="Test body", partner_id=partner.id)
        self.assertEqual(msg.state, "queued")
        self.assertEqual(msg.phone, "+48987654321")
        self.assertEqual(msg.body, "Test body")

    # ── 12. send() with explicit phone creates record directly ───────────────
    def test_12_send_explicit_phone(self):
        msg = self.Msg.send(phone="+48222222222", body="Override phone")
        self.assertEqual(msg.phone, "+48222222222")
        self.assertEqual(msg.state, "queued")

    # ── 13. Abstract provider base send_sms raises NotImplementedError ─────────
    def test_13_abstract_provider_send_sms_raises(self):
        """fayna.sms.provider.base.send_sms raises NotImplementedError."""
        provider = self.env["fayna.sms.provider.base"]
        with self.assertRaises(NotImplementedError):
            provider.send_sms("+48000000000", "test")

    # ── 14. Abstract provider base get_delivery_status raises NotImplementedError
    def test_14_abstract_provider_get_delivery_status_raises(self):
        """fayna.sms.provider.base.get_delivery_status raises NotImplementedError."""
        provider = self.env["fayna.sms.provider.base"]
        with self.assertRaises(NotImplementedError):
            provider.get_delivery_status("some-external-id")

    # ── 15. Cron skips draft messages ─────────────────────────────────────────
    def test_15_cron_skips_draft(self):
        msg = self.Msg.create(dict(self._base_vals, state="draft"))
        self.Msg.process_sms_queue()
        msg.invalidate_recordset()
        # Draft messages are not touched by cron
        self.assertEqual(msg.state, "draft")

    # ── 16. High priority message has priority='1' ───────────────────────────
    def test_16_high_priority(self):
        msg = self.Msg.create(dict(self._base_vals, priority="1"))
        self.assertEqual(msg.priority, "1")

    # ── 17. Cron creates sms.log entry on success ─────────────────────────────
    def test_17_cron_creates_log_on_success(self):
        msg = self.Msg.create(dict(self._base_vals, state="queued"))
        success_result = {"success": True, "external_id": "TURBO-LOG-TEST", "error": None}

        with patch.object(
            type(self.env["fayna.sms.turbosms"]), "send_sms", return_value=success_result
        ):
            self.Msg.process_sms_queue()

        log = self.env["fayna.sms.log"].search(
            [("recipient_number", "=", msg.phone), ("status", "=", "sent")], limit=1
        )
        self.assertTrue(log, "A log entry should be created on successful send")
        self.assertEqual(log.external_message_id, "TURBO-LOG-TEST")

    # ── 18. normalize_phone static method ─────────────────────────────────────
    def test_18_normalize_phone_static(self):
        """normalize_phone is a static method on the model class."""
        self.assertEqual(self.Msg.normalize_phone("+48 123 456 789"), "+48123456789")
        self.assertEqual(self.Msg.normalize_phone("48123456789"), "+48123456789")
        self.assertEqual(self.Msg.normalize_phone("+380991234567"), "+380991234567")

    # ── 19. _cron_process_sms_queue is an alias for process_sms_queue ─────────
    def test_19_cron_alias_method_exists(self):
        """_cron_process_sms_queue is callable and delegates to process_sms_queue."""
        self.assertTrue(
            callable(getattr(self.Msg, "_cron_process_sms_queue", None)),
            "_cron_process_sms_queue must be callable",
        )

    # ── 20. send() with priority='1' sets high priority ───────────────────────
    def test_20_send_with_priority(self):
        msg = self.Msg.send(phone="+48555666777", body="Urgent!", priority="1")
        self.assertEqual(msg.priority, "1")
        self.assertEqual(msg.state, "queued")

    # ── 21. Cron respects feature flag — skips when active=False ──────────────
    def test_21_cron_respects_feature_flag(self):
        """_cron_process_sms_queue is a no-op when fayna_sms_base.active != 'True'."""
        # Ensure flag is False (it should be by default after install)
        self.env["ir.config_parameter"].sudo().set_param("fayna_sms_base.active", "False")

        msg = self.Msg.create(dict(self._base_vals, state="queued"))
        # Cron entry point must skip — msg stays queued
        self.Msg._cron_process_sms_queue()
        msg.invalidate_recordset()
        self.assertEqual(msg.state, "queued", "Cron must be a no-op when feature flag is False")

    # ── 22. Cron dispatches when feature flag is True ─────────────────────────
    def test_22_cron_dispatches_when_flag_true(self):
        """_cron_process_sms_queue dispatches messages when fayna_sms_base.active = 'True'."""
        self.env["ir.config_parameter"].sudo().set_param("fayna_sms_base.active", "True")

        msg = self.Msg.create(dict(self._base_vals, state="queued"))
        success_result = {"success": True, "external_id": "FLAG-TRUE-1", "error": None}

        with patch.object(
            type(self.env["fayna.sms.turbosms"]), "send_sms", return_value=success_result
        ):
            self.Msg._cron_process_sms_queue()

        msg.invalidate_recordset()
        self.assertEqual(msg.state, "sent")

        # Restore flag for other tests
        self.env["ir.config_parameter"].sudo().set_param("fayna_sms_base.active", "False")
