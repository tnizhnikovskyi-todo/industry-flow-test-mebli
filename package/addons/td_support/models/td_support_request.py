import base64
import binascii
import hashlib
import hmac
import json
import logging
import re
from datetime import timedelta

import requests
from markupsafe import Markup, escape

import odoo
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.tools import str2bool

_logger = logging.getLogger(__name__)

# System parameters (ir.config_parameter); README «Параметри».
PARAM_EMAIL = 'td_support.email'
PARAM_WEBHOOK_ENABLED = 'td_support.webhook_enabled'
PARAM_WEBHOOK_URL = 'td_support.webhook_url'
PARAM_WEBHOOK_SECRET = 'td_support.webhook_secret'
PARAM_RATE_LIMIT = 'td_support.rate_limit_per_hour'
PARAM_MAX_TEXT = 'td_support.max_text_chars'
PARAM_MAX_FILES = 'td_support.max_attachments'
PARAM_MAX_MB = 'td_support.max_attachments_mb'

DEFAULT_RATE_LIMIT = 5          # requests of one user per hour
DUPLICATE_MINUTES = 10          # the same request (same subject and trace) is not accepted twice in this window
DEFAULT_MAX_TEXT = 20000        # characters of the trace / description kept
DEFAULT_MAX_FILES = 5
DEFAULT_MAX_MB = 10             # all the attachments of one request together
SUBJECT_MAX = 200
SUBJECT_TAG = '[ToDo-support]'
REDACTED = '***'

_SECRET_KEY = (r'(?:passw(?:or)?d|pwd|secret|token|api[_-]?key|apikey|session_?id|csrf(?:_token)?|cookie'
               r'|authorization|private[_-]?key|signature)')
# key = value, key: value, "key": "value", ?key=value — the value is replaced, the key stays visible
_KEY_VALUE_RE = re.compile(
    r'''(?i)(["']?[\w.-]*''' + _SECRET_KEY + r'''[\w.-]*["']?\s*[:=]\s*)(?:"[^"\n]*"|'[^'\n]*'|[^\s,;&}\])'"]+)''')
_HEADER_RE = re.compile(r'(?im)^(\s*(?:set-)?cookie\s*:|\s*authorization\s*:|\s*x-[\w-]*(?:token|key)\s*:).*$')
_BEARER_RE = re.compile(r'(?i)\b(bearer|basic)\s+[\w\-.~+/=]{8,}')


def sanitize_text(text, limit=DEFAULT_MAX_TEXT):
    """Remove passwords, tokens and cookies; keep the head and the tail of a long text (the end of a traceback is the
    most useful part)."""
    if not text:
        return ''
    text = str(text).replace('\x00', '')
    text = _HEADER_RE.sub(lambda m: f'{m.group(1)} {REDACTED}', text)
    text = _BEARER_RE.sub(lambda m: f'{m.group(1)} {REDACTED}', text)
    text = _KEY_VALUE_RE.sub(lambda m: f'{m.group(1)}{REDACTED}', text)
    if limit and len(text) > limit:
        half = limit // 2
        cut = len(text) - 2 * half
        text = f'{text[:half]}\n… [{cut} characters removed] …\n{text[-half:]}'
    return text


class TdSupportRequest(models.Model):
    _name = 'td.support.request'
    _description = 'ToDo support request'
    _order = 'id desc'

    name = fields.Char('Number', readonly=True, copy=False, default='/')
    subject = fields.Char('Subject', required=True)
    description = fields.Text('Description')
    contact = fields.Char('Contact for the answer')
    consent = fields.Boolean('Consent to send', help='The user agreed to send the request and the technical data '
                                                     'shown in the form to the ToDo support.')
    kind = fields.Selection([('manual', 'Request'), ('error', 'Error report')], 'Type', required=True,
                            default='manual')
    state = fields.Selection([('sent', 'Queued for sending'), ('failed', 'Not sent')], 'Status', readonly=True,
                             default='sent')
    failure_reason = fields.Text('Reason of the failure', readonly=True)
    user_id = fields.Many2one('res.users', 'User', required=True, readonly=True, index=True,
                              default=lambda self: self.env.user)
    user_login = fields.Char('Login', readonly=True)
    page_url = fields.Char('Page', readonly=True)
    odoo_version = fields.Char('Odoo version', readonly=True)
    td_modules = fields.Text('ToDo modules', readonly=True)
    db_uuid = fields.Char('Database identifier', readonly=True)
    trace = fields.Text('Technical details', readonly=True)
    trace_hash = fields.Char(readonly=True, index=True)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments', readonly=True)
    mail_id = fields.Many2one('mail.mail', 'Email', readonly=True, index='btree_not_null')
    email_to = fields.Char('Sent to', readonly=True)
    webhook_status = fields.Char('Webhook', readonly=True)

    # ------------------------------------------------------------------
    # Technical context shown to the user before sending
    # ------------------------------------------------------------------
    @api.model
    def _td_param(self, key, default=None):
        return self.env['ir.config_parameter'].sudo().get_param(key, default)

    @api.model
    def _td_int_param(self, key, default):
        try:
            return int(self._td_param(key, default))
        except (TypeError, ValueError):
            return default

    @api.model
    def _td_modules(self):
        modules = self.env['ir.module.module'].sudo().search(
            [('name', '=like', 'td\\_%'), ('state', '=', 'installed')], order='name')
        return '\n'.join(f'{m.name} {m.installed_version or m.latest_version or ""}'.strip() for m in modules)

    @api.model
    def td_get_context(self):
        """Data the form shows under «What will be sent» (the server, not the browser, is the source)."""
        self._td_check_user()
        user = self.env.user
        return {
            'login': user.login,
            'contact': user.email or user.phone or '',
            'odoo_version': odoo.service.common.exp_version()['server_version'],
            'td_modules': self._td_modules(),
            'db_uuid': self._td_param('database.uuid', ''),
            'email_to': self._td_param(PARAM_EMAIL, ''),
            'max_files': self._td_int_param(PARAM_MAX_FILES, DEFAULT_MAX_FILES),
            'max_mb': self._td_int_param(PARAM_MAX_MB, DEFAULT_MAX_MB),
        }

    # ------------------------------------------------------------------
    # Submit
    # ------------------------------------------------------------------
    @api.model
    def _td_check_user(self):
        if not self.env.user._is_internal():
            raise AccessError(_('Only internal users can write to the ToDo support.'))

    @api.model
    def _td_check_rate(self, trace_hash):
        user = self.env.user
        since = fields.Datetime.now() - timedelta(hours=1)
        limit = self._td_int_param(PARAM_RATE_LIMIT, DEFAULT_RATE_LIMIT)
        requests_sudo = self.sudo()
        if requests_sudo.search_count([('user_id', '=', user.id), ('create_date', '>=', since)]) >= limit:
            raise UserError(_('Too many requests: no more than %(limit)s per hour. Please try again later.',
                              limit=limit))
        recent = fields.Datetime.now() - timedelta(minutes=DUPLICATE_MINUTES)
        if requests_sudo.search_count([('user_id', '=', user.id), ('trace_hash', '=', trace_hash),
                                       ('create_date', '>=', recent)]):
            raise UserError(_('This request has already been sent. The ToDo support has received it.'))

    @api.model
    def _td_prepare_attachments(self, files):
        max_files = self._td_int_param(PARAM_MAX_FILES, DEFAULT_MAX_FILES)
        max_bytes = self._td_int_param(PARAM_MAX_MB, DEFAULT_MAX_MB) * 1024 * 1024
        files = files or []
        if len(files) > max_files:
            raise UserError(_('No more than %(count)s files can be attached.', count=max_files))
        prepared, total = [], 0
        for item in files:
            try:
                raw = base64.b64decode(item.get('datas') or '', validate=True)
            except (binascii.Error, ValueError) as e:
                raise UserError(_('The file %(name)s could not be read.', name=item.get('name') or '?')) from e
            total += len(raw)
            if total > max_bytes:
                raise UserError(_('The attachments are too large: no more than %(mb)s MB together.',
                                  mb=max_bytes // (1024 * 1024)))
            name = re.sub(r'[\\/\x00-\x1f]', '_', (item.get('name') or 'file'))[:120]
            prepared.append({'name': name, 'raw': raw})
        return prepared

    @api.model
    def td_submit(self, payload):
        """Create the request and queue it for the ToDo support. `payload` comes from the form (systray or error
        dialog); the technical context is computed here, only the trace and the URL come from the browser."""
        self._td_check_user()
        payload = dict(payload or {})
        if not payload.get('consent'):
            raise UserError(_('Please confirm that the request and the technical data can be sent.'))
        limit = self._td_int_param(PARAM_MAX_TEXT, DEFAULT_MAX_TEXT)
        subject = sanitize_text(payload.get('subject'), SUBJECT_MAX).strip().replace('\n', ' ')
        if not subject:
            raise UserError(_('Please fill in the subject.'))
        kind = 'error' if payload.get('kind') == 'error' else 'manual'
        trace = sanitize_text(payload.get('trace'), limit)
        trace_hash = hashlib.sha256(f'{subject}\n{trace}'.encode()).hexdigest()
        self._td_check_rate(trace_hash)
        files = self._td_prepare_attachments(payload.get('attachments'))

        user = self.env.user
        request = self.create({
            'subject': subject,
            'description': sanitize_text(payload.get('description'), limit),
            'contact': sanitize_text(payload.get('contact'), 200).strip(),
            'consent': True,
            'kind': kind,
            'user_id': user.id,
            'user_login': user.login,
            'page_url': sanitize_text(payload.get('page_url'), 2000),
            'odoo_version': odoo.service.common.exp_version()['server_version'],
            'td_modules': self._td_modules(),
            'db_uuid': self._td_param('database.uuid', ''),
            'trace': trace,
            'trace_hash': trace_hash,
        })
        request_sudo = request.sudo()
        request_sudo.name = self.env['ir.sequence'].sudo().next_by_code('td.support.request') or '/'
        if files:
            attachments = self.env['ir.attachment'].sudo().create([{
                'name': f['name'],
                'raw': f['raw'],
                'res_model': self._name,
                'res_id': request.id,
            } for f in files])
            request_sudo.attachment_ids = [(6, 0, attachments.ids)]
        request_sudo._td_send()
        return {'id': request.id, 'name': request_sudo.name, 'state': request_sudo.state,
                'failure_reason': request_sudo.failure_reason or ''}

    # ------------------------------------------------------------------
    # Channels: email (default) and webhook (skeleton, off by default)
    # ------------------------------------------------------------------
    def _td_mail_subject(self):
        self.ensure_one()
        return f'{SUBJECT_TAG}[{self.db_uuid or "-"}] {self.name}: {self.subject}'

    def _td_mail_body(self):
        self.ensure_one()
        rows = [
            (_('Number'), self.name),
            (_('Type'), dict(self._fields['kind']._description_selection(self.env)).get(self.kind)),
            (_('Login'), self.user_login),
            (_('Contact for the answer'), self.contact),
            (_('Page'), self.page_url),
            (_('Odoo version'), self.odoo_version),
            (_('Database identifier'), self.db_uuid),
        ]
        table = Markup('').join(
            Markup('<tr><td style="padding:2px 12px 2px 0;color:#555;">%s</td><td>%s</td></tr>') % (label, value or '—')
            for label, value in rows)
        parts = [Markup('<table>%s</table>') % table]
        if self.description:
            parts.append(Markup('<h4>%s</h4><p style="white-space:pre-wrap;">%s</p>') % (_('Description'),
                                                                                      self.description))
        parts.append(Markup('<h4>%s</h4><pre>%s</pre>') % (_('ToDo modules'), self.td_modules or '—'))
        if self.trace:
            parts.append(Markup('<h4>%s</h4><pre style="white-space:pre-wrap;">%s</pre>') % (
                _('Technical details'), self.trace))
        return Markup('').join(parts)

    def _td_send(self):
        for request in self:
            errors = []
            email_to = request._td_param(PARAM_EMAIL, '').strip()
            if email_to:
                user = request.user_id
                email_from = (user.email_formatted if user.email else None) \
                    or request.env.company.email_formatted \
                    or request.env['ir.mail_server']._get_default_from_address()
                mail = request.env['mail.mail'].sudo().create({
                    'subject': request._td_mail_subject(),
                    'email_from': email_from,
                    'email_to': email_to,
                    'reply_to': request.contact if request.contact and '@' in request.contact else False,
                    'body_html': request._td_mail_body(),
                    'attachment_ids': [(6, 0, request.attachment_ids.ids)],
                    'auto_delete': False,
                })
                request.write({'mail_id': mail.id, 'email_to': email_to})
                cron = request.env.ref('mail.ir_cron_mail_scheduler_action', raise_if_not_found=False)
                if cron:
                    cron.sudo()._trigger()
            else:
                errors.append(_('The address of the ToDo support is not set (system parameter %(param)s).',
                                param=PARAM_EMAIL))
            webhook = request._td_send_webhook()
            request.webhook_status = webhook
            if webhook.startswith('error'):
                errors.append(webhook)
            if errors and not request.mail_id and not webhook.startswith('HTTP 2'):
                request.write({'state': 'failed', 'failure_reason': '\n'.join(errors)})

    def _td_webhook_payload(self):
        self.ensure_one()
        return {
            'number': self.name,
            'subject': self.subject,
            'kind': self.kind,
            'description': self.description or '',
            'contact': self.contact or '',
            'login': self.user_login,
            'page_url': self.page_url or '',
            'odoo_version': self.odoo_version,
            'td_modules': (self.td_modules or '').splitlines(),
            'db_uuid': self.db_uuid,
            'trace': self.trace or '',
            'attachments': self.attachment_ids.mapped('name'),
        }

    def _td_send_webhook(self):
        """Skeleton, off by default: POST of the request as JSON, signed with HMAC-SHA256 of the body
        (header X-ToDo-Signature: sha256=<hex>). Only https URLs."""
        self.ensure_one()
        if not str2bool(self._td_param(PARAM_WEBHOOK_ENABLED, 'False') or 'False', False):
            return 'disabled'
        url = (self._td_param(PARAM_WEBHOOK_URL, '') or '').strip()
        secret = self._td_param(PARAM_WEBHOOK_SECRET, '') or ''
        if not url.startswith('https://') or not secret:
            return 'error: webhook URL (https) or secret is not set'
        body = json.dumps(self._td_webhook_payload(), ensure_ascii=False, sort_keys=True).encode()
        signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        try:
            response = requests.post(url, data=body, timeout=5, headers={
                'Content-Type': 'application/json',
                'X-ToDo-Signature': f'sha256={signature}',
            })
        except requests.RequestException as e:
            _logger.warning('td_support webhook failed: %s', e)
            return f'error: {type(e).__name__}'
        return f'HTTP {response.status_code}'
