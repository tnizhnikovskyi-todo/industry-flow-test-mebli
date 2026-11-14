import base64
from unittest.mock import patch

from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, new_test_user, tagged

from odoo.addons.td_support.models.td_support_request import sanitize_text

TRACE = """Traceback (most recent call last):
  File "/odoo/http.py", line 10, in dispatch
    login(password='S3cret!', token="abcdef123456")
Cookie: session_id=0123456789abcdef; frontend_lang=uk_UA
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig
{"api_key": "k-123", "csrf_token": "c-456", "name": "Order 15"}
url=https://erp.example.com/web?access_token=xyz789&id=5
odoo.exceptions.ValidationError: something broke"""


@tagged('post_install', '-at_install')
class TestSupportRequest(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ICP = cls.env['ir.config_parameter'].sudo()
        cls.ICP.set_param('td_support.email', 'support@example.com')
        cls.uuid = cls.ICP.get_param('database.uuid')
        cls.user = new_test_user(cls.env, login='td_support_user', groups='base.group_user',
                                 email='user@example.com')
        cls.other = new_test_user(cls.env, login='td_support_other', groups='base.group_user')
        cls.support_admin = new_test_user(cls.env, login='td_support_admin',
                                          groups='base.group_user,td_support.group_td_support_admin')
        cls.portal = new_test_user(cls.env, login='td_support_portal', groups='base.group_portal')
        cls.Request = cls.env['td.support.request']

    def _payload(self, **kw):
        payload = {'subject': 'Cannot confirm the order', 'description': 'Nothing happens', 'consent': True,
                   'contact': 'user@example.com', 'page_url': 'https://erp.example.com/odoo/sales/15'}
        payload.update(kw)
        return payload

    def test_01_request_created_and_mail_queued(self):
        png = base64.b64encode(b'\x89PNG fake screenshot').decode()
        result = self.Request.with_user(self.user).td_submit(self._payload(
            attachments=[{'name': 'screen.png', 'mimetype': 'image/png', 'datas': png}]))
        request = self.Request.browse(result['id'])
        self.assertEqual(request.state, 'sent')
        self.assertTrue(request.name.startswith('TDS/'))
        self.assertEqual(request.user_id, self.user)
        self.assertEqual(request.user_login, 'td_support_user')
        self.assertEqual(request.db_uuid, self.uuid)
        self.assertTrue(request.odoo_version.startswith('19.'))
        self.assertIn('td_support', request.td_modules)
        mail = request.mail_id
        self.assertEqual(mail.state, 'outgoing')
        self.assertEqual(mail.email_to, 'support@example.com')
        self.assertEqual(mail.subject, f'[ToDo-support][{self.uuid}] {request.name}: Cannot confirm the order')
        self.assertIn('Nothing happens', mail.body_html)
        self.assertEqual(mail.attachment_ids.mapped('name'), ['screen.png'])
        self.assertEqual(mail.reply_to, 'user@example.com')

    def test_02_error_report_trace_is_sanitized_in_record_and_mail(self):
        result = self.Request.with_user(self.user).td_submit(self._payload(kind='error', trace=TRACE))
        request = self.Request.browse(result['id'])
        self.assertEqual(request.kind, 'error')
        for secret in ('S3cret!', 'abcdef123456', '0123456789abcdef', 'eyJhbGciOiJIUzI1NiJ9', 'k-123', 'c-456',
                       'xyz789'):
            self.assertNotIn(secret, request.trace)
            self.assertNotIn(secret, request.mail_id.body_html)
        self.assertIn('Order 15', request.trace)
        self.assertIn('ValidationError: something broke', request.trace)

    def test_03_sanitize_limits_size(self):
        text = 'A' * 50000 + 'END'
        clean = sanitize_text(text, 1000)
        self.assertLess(len(clean), 1100)
        self.assertTrue(clean.endswith('END'))
        self.assertIn('characters removed', clean)

    def test_04_rate_limit(self):
        self.ICP.set_param('td_support.rate_limit_per_hour', '3')
        for i in range(3):
            self.Request.with_user(self.user).td_submit(self._payload(subject=f'Request {i}'))
        with self.assertRaises(UserError):
            self.Request.with_user(self.user).td_submit(self._payload(subject='Request 4'))
        # the limit is per user
        self.Request.with_user(self.other).td_submit(self._payload(subject='Request 4'))

    def test_05_duplicate_is_refused(self):
        self.Request.with_user(self.user).td_submit(self._payload(kind='error', trace=TRACE))
        with self.assertRaises(UserError):
            self.Request.with_user(self.user).td_submit(self._payload(kind='error', trace=TRACE))

    def test_06_consent_and_subject_required(self):
        with self.assertRaises(UserError):
            self.Request.with_user(self.user).td_submit(self._payload(consent=False))
        with self.assertRaises(UserError):
            self.Request.with_user(self.user).td_submit(self._payload(subject='  '))

    def test_07_attachment_limits(self):
        self.ICP.set_param('td_support.max_attachments_mb', '1')
        big = base64.b64encode(b'0' * (1024 * 1024 + 1)).decode()
        with self.assertRaises(UserError):
            self.Request.with_user(self.user).td_submit(self._payload(
                attachments=[{'name': 'big.bin', 'datas': big}]))
        small = base64.b64encode(b'1').decode()
        with self.assertRaises(UserError):
            self.Request.with_user(self.user).td_submit(self._payload(
                attachments=[{'name': f'{i}.txt', 'datas': small} for i in range(6)]))

    def test_08_rights(self):
        mine = self.Request.browse(self.Request.with_user(self.user).td_submit(self._payload())['id'])
        theirs = self.Request.browse(self.Request.with_user(self.other).td_submit(
            self._payload(subject='Other'))['id'])
        # an internal user sees only own requests
        visible = self.Request.with_user(self.user).search([])
        self.assertIn(mine, visible)
        self.assertNotIn(theirs, visible)
        with self.assertRaises(AccessError):
            theirs.with_user(self.user).read(['subject'])
        # and cannot change or delete them
        with self.assertRaises(AccessError):
            mine.with_user(self.user).write({'subject': 'changed'})
        with self.assertRaises(AccessError):
            mine.with_user(self.user).unlink()
        # the support administrator sees all
        visible = self.Request.with_user(self.support_admin).search([])
        self.assertIn(mine, visible)
        self.assertIn(theirs, visible)
        # a portal user cannot write to the support
        with self.assertRaises(AccessError):
            self.Request.with_user(self.portal).td_submit(self._payload())

    def test_09_system_admin_is_support_admin(self):
        self.assertIn(self.env.ref('td_support.group_td_support_admin'),
                      self.env.ref('base.group_system').all_implied_ids)

    def test_10_no_address_saves_failed_request(self):
        self.ICP.set_param('td_support.email', '')
        result = self.Request.with_user(self.user).td_submit(self._payload())
        self.assertEqual(result['state'], 'failed')
        request = self.Request.browse(result['id'])
        self.assertFalse(request.mail_id)
        self.assertIn('td_support.email', request.failure_reason)

    def test_11_webhook_off_by_default_and_signed_when_on(self):
        target = 'odoo.addons.td_support.models.td_support_request.requests.post'
        with patch(target) as post:
            self.Request.with_user(self.user).td_submit(self._payload(subject='No webhook'))
            post.assert_not_called()
        self.ICP.set_param('td_support.webhook_enabled', 'True')
        self.ICP.set_param('td_support.webhook_url', 'https://hooks.example.com/support')
        self.ICP.set_param('td_support.webhook_secret', 'hook-secret')
        with patch(target) as post:
            post.return_value.status_code = 200
            result = self.Request.with_user(self.user).td_submit(self._payload(subject='Webhook'))
            post.assert_called_once()
            headers = post.call_args.kwargs['headers']
            self.assertTrue(headers['X-ToDo-Signature'].startswith('sha256='))
            self.assertNotIn('hook-secret', post.call_args.kwargs['data'].decode())
        self.assertEqual(self.Request.browse(result['id']).webhook_status, 'HTTP 200')

    def test_12_context_for_preview(self):
        ctx = self.Request.with_user(self.user).td_get_context()
        self.assertEqual(ctx['login'], 'td_support_user')
        self.assertEqual(ctx['db_uuid'], self.uuid)
        self.assertEqual(ctx['email_to'], 'support@example.com')
        self.assertIn('td_support', ctx['td_modules'])
