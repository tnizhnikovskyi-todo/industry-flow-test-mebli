import base64

from odoo import api, models


class IrActionsReport(models.AbstractModel):
    _inherit = 'ir.actions.report'

    @api.model
    def _td_qr_data_uri(self, value, size=120):
        """QR of a label: the standard barcode generator of the reports (ir.actions.report.barcode, the same as
        /report/barcode) as PNG; where the PNG backend of reportlab (rl_renderPM, shipped with the Debian package of Odoo)
        is not installed, the same reportlab QR drawing is rendered as SVG."""
        try:
            png = self.barcode('QR', value, width=size, height=size)
            return 'data:image/png;base64,' + base64.b64encode(png).decode()
        except Exception:  # noqa: BLE001 — no PNG backend: the same drawing as SVG
            from reportlab.graphics import renderSVG  # noqa: PLC0415
            from reportlab.graphics.barcode import createBarcodeDrawing  # noqa: PLC0415
            drawing = createBarcodeDrawing('QR', value=value, width=size, height=size, barBorder=4)
            return 'data:image/svg+xml;base64,' + base64.b64encode(renderSVG.drawToString(drawing).encode()).decode()


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _td_label_rows(self):
        """Position 5 (F-29): one label per packing list line with a part — part, order, place, size, QR of the label
        code (the code of the packing list line: the crew scans it on arrival)."""
        self.ensure_one()
        rows = []
        for line in self.td_kit_line_ids.filtered(lambda l: l.kind != 'fitting'):
            part = line.part_id
            rows.append({
                'code': line.label, 'item': line.item, 'order': self.name, 'customer': self.partner_id.name,
                'place': line.place, 'qty': line.qty,
                'size': f"{int(part.length_mm)} × {int(part.width_mm)}" if part else '',
                'material': part.material_id.name if part else '',
            })
        return rows


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _td_label_rows(self):
        """Labels straight from the parts of the order BoM (before the packing list exists): no place yet."""
        self.ensure_one()
        rows = []
        order = (self.sudo().reference_ids.sale_ids | self.sudo().sale_line_id.order_id)[:1]
        for index, part in enumerate(self.bom_id.td_part_ids, start=1):
            rows.append({
                'code': f"{self.name}-{index:02d}", 'item': part.name, 'order': order.name or self.origin or '',
                'customer': order.partner_id.name or '', 'place': False,
                'qty': part.qty * self.product_qty,
                'size': f"{int(part.length_mm)} × {int(part.width_mm)}", 'material': part.material_id.name,
            })
        return rows
