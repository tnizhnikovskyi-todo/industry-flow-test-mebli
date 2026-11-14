from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError


class RepairOrder(models.Model):
    _inherit = 'repair.order'

    td_claim_order_id = fields.Many2one(
        'sale.order', string='Claimed Order', index='btree_not_null', check_company=True,
        help="The furniture order the customer complains about (the standard «Sale Order» of a repair is the order the "
             "repair was sold from, a different thing).")
    td_part_id = fields.Many2one('td.mebli.part', string='Part', domain="[('bom_id.td_sale_order_id', '=', td_claim_order_id)]")
    # the reason of the claim is the standard «Tags» (repair.tags: production, installation, supplier, ...), who pays
    # is the standard «Under Warranty» (the factory pays, the customer gets the parts at price 0): no own fields
    td_photo = fields.Image(string='Photo', max_width=1024, max_height=1024)
    td_remake_production_id = fields.Many2one('mrp.production', string='Remake', readonly=True, copy=False)
    td_visit_task_id = fields.Many2one('project.task', string='Service Visit', readonly=True, copy=False)
    # AC-111 (F-55): the end of the warranty = the date of the final act (the delivery without installation) plus the
    # warranty term of the category of the product (td_mebli_base); no term — the service decides by hand
    td_warranty_end = fields.Date(string='Warranty until', compute='_compute_td_warranty', store=True,
                                  help="Date of the final installation act of the claimed order (the delivery when "
                                       "there is no installation) plus the warranty term of the product category.")
    td_warranty_unset = fields.Boolean(string='Warranty Term Not Set', compute='_compute_td_warranty', store=True)
    td_warranty_note = fields.Char(string='Warranty', compute='_compute_td_warranty_note')
    td_after_warranty = fields.Boolean(string='After Warranty', compute='_compute_td_warranty', store=True)
    td_days_open = fields.Integer(string='Days Open', compute='_compute_td_days_open')
    td_overdue = fields.Boolean(string='Overdue', compute='_compute_td_days_open', search='_search_td_overdue')

    # ------------------------------------------------------------------ AC-110: days open, overdue
    @api.depends('create_date', 'state', 'write_date', 'company_id.td_claim_overdue_days')
    def _compute_td_days_open(self):
        now = fields.Datetime.now()
        for repair in self:
            end = repair.write_date if repair.state in ('done', 'cancel') else now
            start = repair.create_date or now
            repair.td_days_open = max(0, (end - start).days)
            limit = (repair.company_id or self.env.company).td_claim_overdue_days
            repair.td_overdue = repair.state not in ('done', 'cancel') and repair.td_days_open > limit

    def _search_td_overdue(self, operator, value):
        if operator not in ('=', '!=') or not isinstance(value, bool):
            return NotImplemented
        now = fields.Datetime.now()
        ids = []
        # sudo: cron: all the companies, each with its own overdue limit
        for company in self.env['res.company'].sudo().search([]):
            limit = now - relativedelta(days=company.td_claim_overdue_days + 1)
            # sudo: cron: overdue claims of every company, whoever runs it
            ids += self.sudo().search([('company_id', '=', company.id), ('state', 'not in', ('done', 'cancel')),
                                       ('create_date', '<=', limit)]).ids
        positive = (operator == '=') == value
        return [('id', 'in' if positive else 'not in', ids)]

    # ------------------------------------------------------------------ AC-111: warranty of the category
    def _td_warranty_category(self):
        """The category of the claimed product; without it, the first product of the order with a warranty term."""
        self.ensure_one()
        if self.product_id:
            return self.product_id.categ_id
        # sudo: read only: the product categories of the order lines (the service has no sales rights)
        lines = self.td_claim_order_id.sudo().order_line.filtered(lambda line: line.product_id.categ_id.td_warranty_months)
        return lines[:1].product_id.categ_id

    def _td_warranty_start(self):
        self.ensure_one()
        # sudo: read only: the dates of the order for the warranty (the service has no sales rights)
        order = self.td_claim_order_id.sudo()
        final = order.td_act_ids.filtered(lambda act: act.kind == 'final' and act.state == 'signed')[:1]
        start = final.signed_on or order.effective_date
        return start.date() if start else False

    # review A-11: without a product the category comes from the lines of the order — their categories are dependencies
    @api.depends('product_id.categ_id.td_warranty_months', 'td_claim_order_id.effective_date',
                 'td_claim_order_id.order_line.product_id.categ_id.td_warranty_months',
                 'td_claim_order_id.td_act_ids.signed_on', 'td_claim_order_id.td_act_ids.state', 'create_date')
    def _compute_td_warranty(self):
        for repair in self:
            months = repair._td_warranty_category().td_warranty_months if repair.td_claim_order_id else 0
            start = repair._td_warranty_start() if repair.td_claim_order_id else False
            repair.td_warranty_unset = bool(repair.td_claim_order_id) and not months
            repair.td_warranty_end = start + relativedelta(months=months) if start and months else False
            claimed = (repair.create_date or fields.Datetime.now()).date()
            repair.td_after_warranty = bool(repair.td_warranty_end) and claimed > repair.td_warranty_end

    @api.depends('td_warranty_unset', 'td_warranty_end', 'td_after_warranty')
    def _compute_td_warranty_note(self):
        for repair in self:
            if repair.td_warranty_unset:
                repair.td_warranty_note = self.env._("Warranty term is not set")
            elif repair.td_warranty_end:
                repair.td_warranty_note = self.env._("After warranty") if repair.td_after_warranty \
                    else self.env._("On warranty")
            else:
                repair.td_warranty_note = False

    @api.onchange('td_claim_order_id', 'product_id')
    def _onchange_td_claim_warranty(self):
        if self.td_claim_order_id and not self.td_warranty_unset and self.td_warranty_end:
            self.under_warranty = not self.td_after_warranty

    @api.model_create_multi
    def create(self, vals_list):
        repairs = super().create(vals_list)
        for repair, vals in zip(repairs, vals_list):
            # the term is set: «Under Warranty» follows it; not set — the service decides by hand (AC-111)
            if 'under_warranty' not in vals and repair.td_claim_order_id and repair.td_warranty_end:
                repair.under_warranty = not repair.td_after_warranty
        return repairs

    # ------------------------------------------------------------------ AC-080/081: remake
    def action_td_remake(self):
        """Remake in production: a manufacturing order of the part of the claim (a one-part bill of materials of the
        product «Remake part») or, without a part, of the claimed product; the origin is the number of the claim."""
        self.ensure_one()
        # D-08 (AC-080, tr/security.md §1): the service (group «Service», Inventory user) has no Manufacturing rights;
        # who may change the claim may start its remake — the right is checked on the claim, the manufacturing order
        # is made for him with sudo (responsible = the user of the service)
        self.check_access('write')
        if self.td_part_id:
            production = self._td_remake_part()
        elif self.product_id:
            bom = self.env['mrp.bom'].sudo()._bom_find(self.product_id)[self.product_id]
            if not bom:
                raise UserError(self.env._("The product of the claim has no bill of materials: it is bought, not made. "
                                           "Order it again in Purchase."))
            production = self.env['mrp.production'].sudo().create({
                'product_id': self.product_id.id, 'product_qty': 1.0, 'bom_id': bom.id, 'origin': self.name,
                'user_id': self.env.user.id})
        else:
            raise UserError(self.env._("Choose a part or a product to remake"))
        production.action_confirm()
        self.td_remake_production_id = production
        self.message_post(body=self.env._("Remake started: %s", production.name))
        return True

    def _td_remake_part(self):
        """A bill of materials of one part (its board and edge, the operations of the order BoM for one part)."""
        # sudo: read only: the part of the order BoM (the service has no manufacturing rights)
        part = self.td_part_id.sudo()
        source = part.bom_id
        product = self.env.ref('td_mebli_claim.product_remake_part').product_variant_id
        # sudo: the BoM of the remake part is created by the system for the service user
        bom = self.env['mrp.bom'].sudo().create({
            'product_tmpl_id': product.product_tmpl_id.id, 'product_qty': 1.0, 'type': 'normal',
            'code': self.name, 'company_id': (source.company_id or self.company_id).id,
            'consumption': source.consumption})
        part.copy({'bom_id': bom.id})
        bom.write({
            'bom_line_ids': bom._td_prepare_component_lines(self.env['mrp.bom.line'], {'fittings': []}),
            'operation_ids': bom._td_prepare_operations(source),
        })
        # sudo: the manufacturing order of the remake is made for the service user (rights checked on the claim)
        return self.env['mrp.production'].sudo().create({
            'product_id': product.id, 'product_qty': 1.0, 'bom_id': bom.id, 'origin': self.name,
            'company_id': (bom.company_id or self.company_id).id, 'user_id': self.env.user.id})

    # ------------------------------------------------------------------ AC-132: service visit
    def action_td_plan_visit(self):
        """«Plan a visit»: a task in the installation project of the order (the project of its installation visit),
        linked to the claim, at the delivery address of the order; it shows in the calendar and the day plan."""
        self.ensure_one()
        # sudo: read only: the order of the claim (the service has no sales rights)
        order = self.td_claim_order_id.sudo()
        if not order:
            raise UserError(self.env._("Choose the claimed order first: the visit goes to its address."))
        visit = order.tasks_ids.filtered(lambda task: task.td_visit_kind == 'install')[:1] or order.tasks_ids[:1]
        if not visit:
            raise UserError(self.env._("The order %s has no installation visit: the installation project is not known.",
                                       order.name))
        # sudo: the visit of the claim goes to the installation project, the service user is not a project user
        task = self.env['project.task'].sudo().create({
            'name': self.env._("Claim %(claim)s: %(order)s", claim=self.name, order=order.name),
            'project_id': visit.project_id.id, 'sale_line_id': visit.sale_line_id.id,
            'partner_id': (order.partner_shipping_id or order.partner_id).id,
            'date_deadline': self.schedule_date, 'td_visit_kind': 'service', 'td_claim_id': self.id,
            'company_id': visit.company_id.id, 'user_ids': [(6, 0, [])],
        })
        if task.sale_order_id != order:  # a project without billing: the link of the order is set directly
            task.sale_order_id = order
        self.td_visit_task_id = task
        self.message_post(body=self.env._("Service visit planned: %s", task.name))
        return {'type': 'ir.actions.act_window', 'res_model': 'project.task', 'res_id': task.id, 'view_mode': 'form',
                'views': [(False, 'form')]}


class ProjectTask(models.Model):
    _inherit = 'project.task'

    td_claim_id = fields.Many2one('repair.order', string='Claim', readonly=True, index='btree_not_null')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    td_claim_ids = fields.One2many('repair.order', 'td_claim_order_id', string='Claims of the Order',
                                   groups='stock.group_stock_user')
    td_claim_count = fields.Integer(string='Claims', compute='_compute_td_claim_count', groups='stock.group_stock_user')

    @api.depends('td_claim_ids')
    def _compute_td_claim_count(self):
        for order in self:
            order.td_claim_count = len(order.td_claim_ids)

    def action_td_view_claims(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('td_mebli_claim.td_mebli_claim_action')
        action['domain'] = [('td_claim_order_id', '=', self.id)]
        action['context'] = {'default_td_claim_order_id': self.id, 'default_partner_id': self.partner_id.id}
        return action
