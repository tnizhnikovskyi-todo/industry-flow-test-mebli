import base64

from odoo import models


class TdMebliSignMixin(models.AbstractModel):
    """AC-129: a document of the package (PDF of our template) → Sign request; the signed file → chatter of the record.
    Fields of sign.template / sign.request — assumption until ВП-4 (checked by the test of this module on EE)."""
    _name = 'td.mebli.sign.mixin'
    _description = 'Furniture: Sign Request from a Report'

    def _td_sign_report(self):
        raise NotImplementedError

    def action_td_send_sign(self):
        self.ensure_one()
        report = self.env.ref(self._td_sign_report())
        pdf, _type = self.env['ir.actions.report']._render_qweb_pdf(report, self.ids)
        attachment = self.env['ir.attachment'].create({
            'name': f'{self.display_name}.pdf', 'datas': base64.b64encode(pdf), 'mimetype': 'application/pdf'})
        template = self.env['sign.template'].create({'attachment_id': attachment.id})
        return {
            'type': 'ir.actions.act_window', 'res_model': 'sign.send.request', 'view_mode': 'form', 'target': 'new',
            'context': {'default_template_id': template.id, 'default_reference_doc': f'{self._name},{self.id}',
                        'sign_directly_without_mail': False},
        }


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'td.mebli.sign.mixin']

    def _td_sign_report(self):
        return 'td_mebli_sale.action_report_contract'


class TdMebliInstallAct(models.Model):
    _name = 'td.mebli.install.act'
    _inherit = ['td.mebli.install.act', 'td.mebli.sign.mixin']

    def _td_sign_report(self):
        return 'td_mebli_install.action_report_install_act'


class SignRequest(models.Model):
    _inherit = 'sign.request'

    def write(self, vals):
        result = super().write(vals)
        if vals.get('state') == 'signed':
            self._td_post_signed()
        return result

    def _td_post_signed(self):
        """The signed file goes back to the chatter of the order / the act (reference_doc of the request)."""
        for request in self:
            record = request.reference_doc
            if record and record._name in ('sale.order', 'td.mebli.install.act') and request.completed_document:
                record.message_post(
                    body=self.env._("Signed in Sign: %s", request.display_name),
                    attachments=[(f'{request.display_name}.pdf', base64.b64decode(request.completed_document))])
