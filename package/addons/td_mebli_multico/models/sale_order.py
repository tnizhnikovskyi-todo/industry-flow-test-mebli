from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    """AC-035 (F-25, AI-14): one seller per order. The installation by another legal entity (a sole proprietor, FOP) is
    a separate service order of that company, linked to the main one; the lines of the main order are not split."""
    _inherit = 'sale.order'

    td_install_company_id = fields.Many2one(
        'res.company', string='Installation by', copy=False, tracking=True,
        domain="[('id', 'in', allowed_company_ids), ('id', '!=', company_id)]",
        help="Another legal entity of the group does the installation: on confirmation the installation line goes to a "
             "separate service order of that company (its own task of the installation). Empty — the seller installs.")
    # a link across companies on purpose (check_company is off): the parent is read with sudo, number and date only
    td_parent_order_id = fields.Many2one('sale.order', string='Main Order', readonly=True, copy=False, index='btree_not_null')
    td_parent_order_name = fields.Char(string='Main Order No', compute='_compute_td_install_orders')
    td_install_order_ids = fields.One2many('sale.order', 'td_parent_order_id', string='Installation Orders')
    td_install_order_count = fields.Integer(string='Installation Orders Count', compute='_compute_td_install_orders')

    @api.depends('td_install_order_ids', 'td_parent_order_id')
    def _compute_td_install_orders(self):
        for order in self:
            # sudo: read only — the count and the number of the documents of the other company
            data = order.sudo()
            order.td_install_order_count = len(data.td_install_order_ids)
            order.td_parent_order_name = data.td_parent_order_id.name or False

    @api.constrains('td_install_company_id', 'company_id')
    def _check_td_install_company(self):
        for order in self:
            if order.td_install_company_id and order.td_install_company_id == order.company_id:
                raise ValidationError(self.env._("The installing company must be another legal entity than the seller."))

    def _td_install_lines(self):
        self.ensure_one()
        return self.order_line.filtered(lambda line: not line.display_type and line._td_is_install())

    def _td_create_install_order(self):
        """The service order of the installing company: the same customer, the installation line moved from the main
        order (its price, or 0 when the installation is in the price of the order, VP-16). Created with the rights of
        the user in the installing company."""
        self.ensure_one()
        fop = self.td_install_company_id
        if fop not in self.env.user.company_ids:
            raise UserError(self.env._("You do not have access to the company %s — the installation from it is "
                                       "arranged by a user of that company", fop.name))
        lines = self._td_install_lines()
        if not lines:
            raise UserError(self.env._("Add the installation service line to the order: it goes to the order of %s.",
                                       fop.name))
        in_price = self.company_id.td_install_in_price
        values = [{'product_id': line.product_id.id, 'name': line.name, 'product_uom_qty': line.product_uom_qty,
                   'product_uom_id': line.product_uom_id.id, 'price_unit': 0.0 if in_price else line.price_unit}
                  for line in lines]
        env_fop = self.with_company(fop).with_context(allowed_company_ids=(fop | self.env.companies).ids)
        install = env_fop.env['sale.order'].create({
            'company_id': fop.id, 'partner_id': self.partner_id.id, 'partner_shipping_id': self.partner_shipping_id.id,
            'user_id': self.user_id.id, 'td_parent_order_id': self.id, 'origin': self.name,
            'commitment_date': self.commitment_date,
            'order_line': [(0, 0, vals) for vals in values],
        })
        lines.unlink()  # moved, not duplicated: the seller does not install
        self.message_post(body=self.env._("Installation by %(company)s: order %(order)s.", company=fop.name,
                                          order=install.name), subtype_xmlid='mail.mt_note')
        return install

    def action_confirm(self):
        installs = self.env['sale.order']
        for order in self.filtered(lambda o: o.td_install_company_id and not o.td_install_order_ids
                                   and o.state in ('draft', 'sent')):
            installs |= order._td_create_install_order()
        result = super().action_confirm()
        for install in installs:
            install.with_company(install.company_id).with_context(
                allowed_company_ids=(install.company_id | self.env.companies).ids).action_confirm()
        return result

    def _action_cancel(self):
        result = super()._action_cancel()
        # rule 4: the document of the installing company is not cancelled automatically — its salesperson decides
        # sudo: the documents of the installing company (FOP) are found for a salesperson of the main company
        for install in self.sudo().td_install_order_ids.filtered(lambda o: o.state != 'cancel'):
            install.activity_schedule(
                'mail.mail_activity_data_todo', summary=self.env._("The main order is cancelled"),
                note=self.env._("The main order %s is cancelled: decide on this installation order.",
                                install.td_parent_order_id.name),
                user_id=(install.user_id or self.env.user).id)
        return result

    def action_td_view_install_orders(self):
        self.ensure_one()
        orders = self.td_install_order_ids
        action = {'type': 'ir.actions.act_window', 'res_model': 'sale.order', 'name': self.env._("Installation Orders")}
        if len(orders) == 1:
            return dict(action, view_mode='form', views=[(False, 'form')], res_id=orders.id)
        return dict(action, view_mode='list,form', views=[(False, 'list'), (False, 'form')],
                    domain=[('id', 'in', orders.ids)])

    def action_td_view_parent_order(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window', 'res_model': 'sale.order', 'view_mode': 'form',
                'views': [(False, 'form')], 'res_id': self.td_parent_order_id.id}
