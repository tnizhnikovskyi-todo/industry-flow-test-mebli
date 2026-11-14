from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMebliArticles(TransactionCase):

    def test_articles_linked_to_installed_screens(self):
        Article = self.env['td.knowledge.article']
        section = self.env.ref('td_mebli_knowledge.article_mebli_section')
        self.assertTrue(section.is_package)
        self.assertGreaterEqual(len(section.child_ids), 5)
        installed = {m.model for m in self.env['ir.model'].search([('model', 'in', [
            'sale.order', 'td.mebli.measure', 'td.mebli.cutting.job', 'td.mebli.install.act', 'repair.order'])])}
        for model in installed:
            self.assertTrue(Article.td_screen_count(model), f'no article for the screen {model}')
