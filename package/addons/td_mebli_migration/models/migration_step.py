from odoo import fields, models
from odoo.exceptions import UserError


class TdMebliMigrationStep(models.Model):
    """One step of the import order of the master data: a CSV template of A-13 (package/master-data/README.md, «Import
    order») and the model it goes into. The templates live in the package, not in this module."""
    _name = 'td.mebli.migration.step'
    _description = 'Migration Import Step'
    _order = 'sequence, id'

    sequence = fields.Integer(string='No.', required=True)
    name = fields.Char(string='Step', required=True, translate=True)
    template = fields.Char(string='Template (A-13)', required=True,
                           help="File of package/master-data (the CSV templates of the package, step A-13).")
    model_name = fields.Char(string='Model', required=True)
    depends_on = fields.Char(string='After Steps')
    box = fields.Selection([('A', 'A'), ('B', 'B')], string='Box', default='A', required=True)
    module_name = fields.Char(string='Module',
                              help="Module of the package that adds the fields td_* of the template (files td/ of A-13); "
                                   "the step is available only when it is installed (e.g. td_mebli_bas is not in the "
                                   "light profile).")
    note = fields.Char(string='Note', translate=True)
    model_installed = fields.Boolean(string='Model Installed', compute='_compute_model_installed')

    def _compute_model_installed(self):
        names = set(self.mapped('module_name')) - {False, ''}
        # sudo: read only: whether a module is installed (ir.module.module is admin only)
        installed = set(self.env['ir.module.module'].sudo().search(
            [('name', 'in', list(names)), ('state', '=', 'installed')]).mapped('name')) if names else set()
        for step in self:
            step.model_installed = step.model_name in self.env and (
                not step.module_name or step.module_name in installed)

    def action_td_import(self):
        """Opens the standard import of Odoo (base_import) for the model of the step."""
        self.ensure_one()
        if self.model_name not in self.env:
            raise UserError(self.env._("The model %s is not installed: install its module first.", self.model_name))
        if not self.model_installed:
            raise UserError(self.env._("The module %s is not installed: this template is not imported in this database.",
                                       self.module_name))
        return {
            'type': 'ir.actions.client', 'tag': 'import',
            'name': self.env._("Import: %s", self.name),
            'params': {'model': self.model_name, 'active_model': self.model_name, 'context': self.env.context},
        }
