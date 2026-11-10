import base64
import csv
import io
from collections import defaultdict

from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare
from odoo.tools.misc import formatLang

from . import optimizer, sheet_map

# the offcuts of one order take at most this share of its cost: the rest of the sheet is paid by the order
OFFCUT_COST_SHARE_CAP = 10.0


class TdMebliCuttingJob(models.Model):
    _name = 'td.mebli.cutting.job'
    _description = 'Cutting Job'
    _inherit = ['mail.thread']
    _order = 'id desc'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default='New')
    state = fields.Selection(
        [('draft', 'Draft'), ('sent', 'Sent to cutting'), ('result', 'Result received'),
         ('done', 'Done'), ('cancel', 'Cancelled')],
        default='draft', required=True, copy=False, tracking=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    production_ids = fields.Many2many(
        'mrp.production', relation='td_mebli_cutting_job_production_rel', column1='job_id', column2='production_id',
        string='Manufacturing Orders', required=True)
    part_ids = fields.Many2many('td.mebli.part', string='Parts', compute='_compute_part_ids')
    part_count = fields.Integer(string='Pieces', compute='_compute_part_ids')
    sheet_ids = fields.One2many('td.mebli.cutting.sheet', 'job_id', string='Sheets')
    kerf_mm = fields.Integer(string='Kerf, mm', default=4)
    trim_mm = fields.Integer(string='Edge Trim, mm', default=10)
    min_offcut_mm = fields.Integer(string='Min Offcut Side, mm', default=300)
    result_source = fields.Selection([('simulated', 'Simulation'), ('imported', 'Imported')],
                                     string='Result Source', readonly=True, copy=False)
    waste_pct = fields.Float(string='Waste, %', compute='_compute_waste_pct', digits=(16, 1))
    export_attachment_id = fields.Many2one('ir.attachment', string='Cutting File', readonly=True, copy=False)
    currency_id = fields.Many2one(related='company_id.currency_id')
    offcut_used_m2 = fields.Float(string='Cut from Offcuts, m2', compute='_compute_offcut_saving', digits=(16, 2))
    offcut_saving = fields.Monetary(string='Saved by Offcuts', compute='_compute_offcut_saving')

    map_html = fields.Html(string='Cutting Map', compute='_compute_map_html', sanitize=False)

    @api.depends('sheet_ids.placement_ids', 'sheet_ids.offcut_ids')
    def _compute_map_html(self):
        for job in self:
            # whole sheets first (the typical picture of a cut), then offcuts used up; at most four drawings
            ordered = job.sheet_ids.sorted(key=lambda sheet: (bool(sheet.lot_id.td_is_offcut), -sheet.length_mm * sheet.width_mm,
                                                              sheet.sequence))
            # a whole sheet and a sheet taken from an offcut go side by side first: that is the point of the map
            first = ordered[:1] | ordered.filtered(lambda sheet: sheet.lot_id.td_is_offcut)[:1]
            sheets = first + (ordered - first)[:4 - len(first)]
            job.map_html = Markup('%s<div class="d-flex flex-wrap gap-3">%s</div>') % (
                sheet_map.legend(self.env._("part (colour = order)"), self.env._("business offcut"), self.env._("waste")),
                Markup('').join(sheet._td_map_block() for sheet in sheets))

    @api.depends('production_ids.bom_id.td_part_ids', 'production_ids.product_qty')
    def _compute_part_ids(self):
        for job in self:
            job.part_ids = job.production_ids.bom_id.td_part_ids
            job.part_count = sum(
                part.qty * int(production.product_qty)
                for production in job.production_ids for part in production.bom_id.td_part_ids)

    @api.depends('sheet_ids.waste_pct', 'sheet_ids.length_mm', 'sheet_ids.width_mm')
    def _compute_waste_pct(self):
        for job in self:
            total = sum(sheet.length_mm * sheet.width_mm for sheet in job.sheet_ids)
            waste = sum(sheet.length_mm * sheet.width_mm * sheet.waste_pct / 100.0 for sheet in job.sheet_ids)
            job.waste_pct = waste / total * 100.0 if total else 0.0

    @api.depends('sheet_ids.lot_id.td_is_offcut', 'sheet_ids.used_area_m2', 'sheet_ids.product_id.standard_price')
    def _compute_offcut_saving(self):
        """Parts cut from a business offcut instead of a new sheet: saved area and its cost at the board price."""
        for job in self:
            from_offcuts = job.sheet_ids.filtered(lambda sheet: sheet.lot_id.td_is_offcut)
            job.offcut_used_m2 = sum(from_offcuts.mapped('used_area_m2'))
            job.offcut_saving = sum(sheet.used_area_m2 * sheet.product_id.standard_price for sheet in from_offcuts)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('td.mebli.cutting.job') or 'New'
        return super().create(vals_list)

    def _check_state(self, *states):
        for job in self:
            if job.state not in states:
                raise UserError(self.env._("%(job)s: this action is not available in state %(state)s.",
                                           job=job.name, state=job.state))

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    def _td_pieces(self):
        """Pieces to cut, grouped by material: {product: [piece dict]}."""
        self.ensure_one()
        pieces = defaultdict(list)
        for production in self.production_ids:
            copies = max(int(production.product_qty), 1)
            for part in production.bom_id.td_part_ids:
                for copy_index in range(copies):
                    for index in range(part.qty):
                        pieces[part.material_id].append({
                            'part_id': part.id, 'production_id': production.id,
                            'index': copy_index * part.qty + index,
                            'length': int(round(part.length_mm)), 'width': int(round(part.width_mm)),
                        })
        return pieces

    def action_send(self):
        """Create the cutting file (draft format) and mark the job as sent."""
        self._check_state('draft')
        for job in self:
            if not job.part_count:
                raise UserError(self.env._("%s has no parts to cut.", job.name))
            buffer = io.StringIO()
            writer = csv.writer(buffer, delimiter=';')
            writer.writerow(['material', 'length_mm', 'width_mm', 'qty', 'edge_long', 'edge_short', 'order', 'part'])
            for production in job.production_ids:
                for part in production.bom_id.td_part_ids:
                    writer.writerow([
                        part.material_id.display_name, part.length_mm, part.width_mm,
                        part.qty * int(production.product_qty), part.edge_long_sides, part.edge_short_sides,
                        production.origin or production.name, part.name])
            attachment = self.env['ir.attachment'].create({
                'name': f'{job.name.replace("/", "-")}-{self.env._("parts")}.csv',
                'datas': base64.b64encode(buffer.getvalue().encode()),
                'res_model': job._name, 'res_id': job.id, 'mimetype': 'text/csv',
            })
            job.write({'export_attachment_id': attachment.id, 'state': 'sent'})
            job.production_ids.write({'td_cutting_job_ids': [(4, job.id)]})
        return True

    def action_simulate(self):
        """SIMULATION of the external cutting program: build the payload and apply it."""
        self._check_state('sent', 'result')
        for job in self:
            job._td_apply_result(job._td_simulate_optimizer())
        return True

    def action_done(self):
        self._check_state('result')
        for job in self:
            job._td_reserve_and_create_offcuts()
            job.state = 'done'
        return True

    def action_cancel(self):
        self._check_state('draft', 'sent', 'result')
        self.write({'state': 'cancel'})
        return True

    def action_draft(self):
        self._check_state('cancel')
        self.sheet_ids.unlink()
        self.write({'state': 'draft', 'result_source': False})
        return True

    # ------------------------------------------------------------------
    # Simulation
    # ------------------------------------------------------------------
    def _td_free_lots(self, product):
        """Lots of the material that can be cut: [(lot, free quantity)] by lot id.

        A lot reserved only by manufacturing orders of this job counts as free.
        """
        self.ensure_one()
        location = self.production_ids[:1].location_src_id
        quants = self.env['stock.quant'].search([
            ('product_id', '=', product.id), ('lot_id', '!=', False),
            ('location_id', 'child_of', location.id), ('quantity', '>', 0)])
        own = self.env['stock.move.line'].search([
            ('move_id.raw_material_production_id', 'in', self.production_ids.ids),
            ('product_id', '=', product.id), ('lot_id', '!=', False)])
        own_reserved = defaultdict(float)
        for line in own:
            own_reserved[line.lot_id.id] += line.quantity
        free = {}
        for quant in quants:
            free[quant.lot_id] = free.get(quant.lot_id, 0.0) + quant.quantity - quant.reserved_quantity \
                + own_reserved.get(quant.lot_id.id, 0.0)
        return free

    def _td_simulate_optimizer(self):
        self.ensure_one()
        payload_sheets = []
        for product, pieces in sorted(self._td_pieces().items(), key=lambda item: item[0].id):
            lots = self._td_free_lots(product)
            offcuts, whole = [], []
            for lot, free in lots.items():
                if not (lot.td_length_mm and lot.td_width_mm):
                    continue
                if float_compare(free, lot.td_area_m2, precision_digits=3) < 0:
                    continue  # the lot is partly used elsewhere
                source = {'lot_id': lot.id, 'length': lot.td_length_mm, 'width': lot.td_width_mm,
                          'is_offcut': lot.td_is_offcut}
                (offcuts if lot.td_is_offcut else whole).append(source)
            offcuts.sort(key=lambda s: (s['length'] * s['width'], s['lot_id']))
            whole.sort(key=lambda s: s['lot_id'])
            virtual = None
            if product.td_sheet_length_mm and product.td_sheet_width_mm:
                virtual = {'length': product.td_sheet_length_mm, 'width': product.td_sheet_width_mm}
            try:
                sheets = optimizer.pack(
                    pieces, offcuts + whole, virtual, kerf=self.kerf_mm, trim=self.trim_mm,
                    min_offcut=self.min_offcut_mm)
            except optimizer.PieceTooLarge as err:
                raise UserError(self.env._(
                    "Cannot cut %(product)s: %(reason)s.", product=product.display_name, reason=err)) from err
            for sheet in sheets:
                payload_sheets.append(dict(sheet, product_id=product.id))
        return {'source': 'simulated', 'sheets': payload_sheets}

    # ------------------------------------------------------------------
    # Result import (single entry point, also for a real cutting program)
    # ------------------------------------------------------------------
    def _td_apply_result(self, payload):
        """Store a cutting result.

        payload = {'source': 'simulated' | 'imported', 'sheets': [{
            'product_id', 'lot_id' (or False), 'length', 'width',
            'placements': [{'part_id', 'production_id', 'index', 'x', 'y', 'length', 'width', 'rotated'}],
            'offcuts': [{'x', 'y', 'length', 'width'}]}]}
        """
        self.ensure_one()
        self._check_state('sent', 'result')
        self.sheet_ids.unlink()
        for sequence, sheet in enumerate(payload['sheets'], start=1):
            self.env['td.mebli.cutting.sheet'].create({
                'job_id': self.id, 'sequence': sequence,
                'product_id': sheet['product_id'], 'lot_id': sheet.get('lot_id') or False,
                'length_mm': sheet['length'], 'width_mm': sheet['width'],
                'placement_ids': [(0, 0, {
                    'part_id': p['part_id'], 'production_id': p['production_id'], 'index': p['index'],
                    'x_mm': p['x'], 'y_mm': p['y'], 'length_mm': p['length'], 'width_mm': p['width'],
                    'rotated': p['rotated']}) for p in sheet['placements']],
                'offcut_ids': [(0, 0, {
                    'x_mm': o['x'], 'y_mm': o['y'], 'length_mm': o['length'], 'width_mm': o['width']})
                    for o in sheet['offcuts']],
            })
        self.write({'result_source': payload['source'], 'state': 'result'})
        kind = {'simulated': self.env._("simulation"), 'imported': self.env._("cutting program file")}[payload['source']]
        self.message_post(body=self.env._(
            "Cutting result received (%(kind)s): %(sheets)s sheets, waste %(waste)s%%.",
            kind=kind, sheets=len(self.sheet_ids), waste=formatLang(self.env, self.waste_pct, digits=1)))

    # ------------------------------------------------------------------
    # Done: reserve sheets by lot and create offcuts as by-products
    # ------------------------------------------------------------------
    def _td_reserve_and_create_offcuts(self):
        self.ensure_one()
        uom_m2 = self.env.ref('uom.product_uom_square_meter')
        raw_moves = self.production_ids.move_raw_ids.filtered(
            lambda m: m.state not in ('done', 'cancel') and m.product_id in self.sheet_ids.product_id)
        raw_moves._do_unreserve()
        no_lot_sheets = 0
        offcut_jobs = []
        for sheet in self.sheet_ids:
            share = sheet._td_production_shares()
            if sheet.lot_id:
                for production, fraction in share.items():
                    move = raw_moves.filtered(
                        lambda m: m.raw_material_production_id == production and m.product_id == sheet.product_id)[:1]
                    if not move:
                        continue
                    quantity = sheet.lot_id.td_area_m2 * fraction
                    taken = move._update_reserved_quantity(
                        quantity, move.location_id, lot_id=sheet.lot_id, strict=True)
                    # tolerance 0.01 m2: shares of one sheet between several orders are rounded by the reservation
                    if float_compare(taken, quantity, precision_digits=2) < 0:
                        raise UserError(self.env._(
                            "Lot %(lot)s is not available in full for %(production)s.",
                            lot=sheet.lot_id.name, production=production.name))
            else:
                no_lot_sheets += 1
            main_production = max(share, key=lambda mo: share[mo]) if share else self.production_ids[:1]
            offcut_jobs.extend((main_production, sheet, offcut) for offcut in sheet.offcut_ids)
        # cost share of the by-products: value of the offcut against the material cost consumed by the order
        base = {production: production._td_material_cost() for production in self.production_ids}
        allocated = defaultdict(float)  # cost share already given to the by-products of one order
        for production, sheet, offcut in offcut_jobs:
            lot = self.env['stock.lot'].create({
                'name': sheet._td_next_offcut_name(),
                'product_id': sheet.product_id.id, 'company_id': self.company_id.id,
                'td_length_mm': offcut.length_mm, 'td_width_mm': offcut.width_mm,
                'td_is_offcut': True, 'td_cutting_job_id': self.id,
            })
            offcut.lot_id = lot
            value = offcut.area_m2 * sheet.product_id.standard_price
            cost_share = min(value / base[production] * 100.0, OFFCUT_COST_SHARE_CAP - allocated[production]) if base[production] else 0.0
            cost_share = max(cost_share, 0.0)
            allocated[production] += cost_share
            self._td_create_byproduct_move(production, lot, offcut.area_m2, uom_m2, cost_share)
        if no_lot_sheets:
            self.message_post(body=self.env._(
                "%s sheets have no lot in stock: they are not reserved, receive the material first.", no_lot_sheets))

    def _td_create_byproduct_move(self, production, lot, area, uom, cost_share=0.0):
        values = production._get_move_finished_values(lot.product_id.id, area, uom.id)
        values['location_final_id'] = False
        values['cost_share'] = cost_share
        move = self.env['stock.move'].create(values)
        move._action_confirm(merge=False)
        line_vals = {'lot_id': lot.id, 'quantity': area, 'picked': True}
        line = move.move_line_ids[:1]
        if line:
            line.write(line_vals)
        else:
            self.env['stock.move.line'].create(dict(
                line_vals, move_id=move.id, product_id=lot.product_id.id, product_uom_id=uom.id,
                location_id=move.location_id.id, location_dest_id=move.location_dest_id.id,
                company_id=self.company_id.id))
        return move


class TdMebliCuttingSheet(models.Model):
    _name = 'td.mebli.cutting.sheet'
    _description = 'Cutting Sheet'
    _order = 'job_id, sequence, id'

    job_id = fields.Many2one('td.mebli.cutting.job', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(compute='_compute_name')
    product_id = fields.Many2one('product.product', string='Board', required=True)
    lot_id = fields.Many2one('stock.lot', string='Sheet / Offcut Lot')
    length_mm = fields.Integer(string='Length, mm')
    width_mm = fields.Integer(string='Width, mm')
    placement_ids = fields.One2many('td.mebli.cutting.placement', 'sheet_id', string='Placement')
    offcut_ids = fields.One2many('td.mebli.cutting.offcut', 'sheet_id', string='Offcuts')
    used_area_m2 = fields.Float(string='Used, m2', compute='_compute_areas', store=True, digits=(16, 3))
    offcut_area_m2 = fields.Float(string='Offcuts, m2', compute='_compute_areas', store=True, digits=(16, 3))
    waste_pct = fields.Float(string='Waste, %', compute='_compute_areas', store=True, digits=(16, 1))
    result_source = fields.Selection(related='job_id.result_source')
    map_html = fields.Html(string='Cutting Map', compute='_compute_map_html', sanitize=False)

    def _td_map_svg(self):
        self.ensure_one()
        productions = self.job_id.production_ids.ids
        placements = [{
            'x': p.x_mm, 'y': p.y_mm, 'length': p.length_mm, 'width': p.width_mm, 'production_id': p.production_id.id,
            'label': p.part_id.name or ''} for p in self.placement_ids]
        offcuts = [{'x': o.x_mm, 'y': o.y_mm, 'length': o.length_mm, 'width': o.width_mm} for o in self.offcut_ids]
        return sheet_map.render_svg(self.length_mm, self.width_mm, placements, offcuts, productions,
                                    self.env._("offcut"))

    def _td_map_block(self):
        """Heading and drawing of the sheet, for the cutting map of a job."""
        self.ensure_one()
        lot = f' · {self.lot_id.name}' if self.lot_id else ''
        kind = self.env._("from offcut") if self.lot_id.td_is_offcut else self.env._("new sheet")
        title = self.env._("%(kind)s%(lot)s: %(board)s, %(size)s mm, waste %(waste)s%%",
                           kind=kind, board=self.product_id.name, lot=lot,
                           size=f'{self.length_mm}×{self.width_mm}', waste=formatLang(self.env, self.waste_pct, digits=1))
        return Markup('<div style="flex:1 1 47%%;min-width:380px"><div class="fw-bold small mb-1">%s</div>%s</div>') % (
            title, self._td_map_svg())

    @api.depends('placement_ids', 'offcut_ids', 'length_mm', 'width_mm')
    def _compute_map_html(self):
        for sheet in self:
            sheet.map_html = sheet._td_map_svg()

    @api.depends('sequence', 'product_id')
    def _compute_name(self):
        for sheet in self:
            sheet.name = f'{sheet.job_id.name or ""} #{sheet.sequence} {sheet.product_id.display_name or ""}'

    @api.depends('placement_ids.area_m2', 'offcut_ids.area_m2', 'length_mm', 'width_mm')
    def _compute_areas(self):
        for sheet in self:
            sheet.used_area_m2 = sum(sheet.placement_ids.mapped('area_m2'))
            sheet.offcut_area_m2 = sum(sheet.offcut_ids.mapped('area_m2'))
            total = sheet.length_mm * sheet.width_mm / 1_000_000.0
            sheet.waste_pct = (1 - (sheet.used_area_m2 + sheet.offcut_area_m2) / total) * 100.0 if total else 0.0

    def _td_production_shares(self):
        """Share of the sheet taken by every manufacturing order, by placed area."""
        self.ensure_one()
        areas = defaultdict(float)
        for placement in self.placement_ids:
            areas[placement.production_id] += placement.area_m2
        total = sum(areas.values())
        return {production: area / total for production, area in areas.items()} if total else {}

    def _td_next_offcut_name(self):
        self.ensure_one()
        code = self.product_id.default_code or str(self.product_id.id)
        count = self.env['stock.lot'].search_count([
            ('product_id', '=', self.product_id.id), ('td_is_offcut', '=', True)])
        return f'ОБР-{code}-{count + 1}'


class TdMebliCuttingPlacement(models.Model):
    _name = 'td.mebli.cutting.placement'
    _description = 'Part Placement on a Sheet'
    _order = 'sheet_id, y_mm, x_mm'

    sheet_id = fields.Many2one('td.mebli.cutting.sheet', required=True, ondelete='cascade', index=True)
    part_id = fields.Many2one('td.mebli.part', string='Part', required=True)
    production_id = fields.Many2one('mrp.production', string='Manufacturing Order')
    index = fields.Integer(string='Piece No.')
    x_mm = fields.Integer(string='X, mm')
    y_mm = fields.Integer(string='Y, mm')
    length_mm = fields.Integer(string='Length, mm')
    width_mm = fields.Integer(string='Width, mm')
    rotated = fields.Boolean(string='Rotated by 90°')
    area_m2 = fields.Float(compute='_compute_area_m2', store=True, digits=(16, 4))

    @api.depends('length_mm', 'width_mm')
    def _compute_area_m2(self):
        for placement in self:
            placement.area_m2 = placement.length_mm * placement.width_mm / 1_000_000.0


class TdMebliCuttingOffcut(models.Model):
    _name = 'td.mebli.cutting.offcut'
    _description = 'Cutting Offcut'
    _order = 'sheet_id, id'

    sheet_id = fields.Many2one('td.mebli.cutting.sheet', required=True, ondelete='cascade', index=True)
    x_mm = fields.Integer(string='X, mm')
    y_mm = fields.Integer(string='Y, mm')
    length_mm = fields.Integer(string='Length, mm')
    width_mm = fields.Integer(string='Width, mm')
    area_m2 = fields.Float(compute='_compute_area_m2', store=True, digits=(16, 4))
    lot_id = fields.Many2one('stock.lot', string='Offcut Lot', readonly=True, copy=False)

    @api.depends('length_mm', 'width_mm')
    def _compute_area_m2(self):
        for offcut in self:
            offcut.area_m2 = offcut.length_mm * offcut.width_mm / 1_000_000.0
