from odoo import api, models


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    def _td_quality_point_vals(self):
        """Quality point of Enterprise from the quality step of the operation (td_quality_point of td_mebli_shop).
        Field names of quality.point — assumption until ВП-4 (checked by the test of this module on EE)."""
        self.ensure_one()
        return {'title': self.td_quality_point, 'operation_id': self.id,
                'product_ids': [(6, 0, self.bom_id.product_tmpl_id.product_variant_ids.ids)],
                'picking_type_ids': [(6, 0, self.bom_id.picking_type_id.ids)], 'company_id': self.company_id.id}

    def _td_sync_quality_points(self):
        """AC-127: an operation with a quality step gets one quality point of Quality (not doubled on a repeat)."""
        Point = self.env['quality.point'].sudo()
        created = Point
        for operation in self.filtered('td_quality_point'):
            if not Point.search_count([('operation_id', '=', operation.id)]):
                created |= Point.create(operation._td_quality_point_vals())
        return created


class QualityCheck(models.Model):
    _inherit = 'quality.check'

    @api.model
    def _td_nonconformity_count(self, domain=None):
        """Failed checks of Quality for the dashboard of the package (AC-127; the dashboard of G3 reads it when the
        bridge is installed, the historical td.mebli.quality.check stay a second source)."""
        return self.search_count([('quality_state', '=', 'fail')] + list(domain or []))
