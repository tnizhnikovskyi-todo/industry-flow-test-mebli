from odoo.tests import TransactionCase, new_test_user, tagged

from odoo.addons.td_knowledge.models.stemmer import stem


@tagged('post_install', '-at_install')
class TestWordForms(TransactionCase):

    def test_01_stems_of_word_forms(self):
        groups = [
            ['монтаж', 'монтажу', 'монтажем', 'монтажі'],
            ['обрізки', 'обрізків', 'обрізками'],
            ['розкрій', 'розкрою', 'розкрої'],
            ['замовлення', 'замовлень', 'замовленням', 'замовленні', 'замовленнями'],
            ['рекламація', 'рекламації', 'рекламацією', 'рекламацій'],
            ['оплата', 'оплати', 'оплату', 'оплатою', 'оплат'],
            ['фасад', 'фасади', 'фасадів', 'фасадами'],
            ["пам'ять", 'пам’яті'],
        ]
        for forms in groups:
            self.assertEqual(len({stem(w) for w in forms}), 1, forms)
        self.assertEqual(stem('ДСП'), 'дсп')          # short words are kept

    def test_02_search_finds_other_forms(self):
        Article = self.env['td.knowledge.article']
        install = Article.create({'name': 'Монтаж і акт', 'body': '<p>Підписаний акт дає бригаді нарахування.</p>'})
        offcuts = Article.create({'name': 'Залишки', 'body': '<p>Ділові обрізки стають новими партіями.</p>'})
        orders = Article.create({'name': 'Замовлення меблів', 'body': '<p>Графік оплат і маржа.</p>'})
        user = new_test_user(self.env, login='td_kb_forms', groups='base.group_user')
        Search = Article.with_user(user)
        cases = {
            'монтажу': install, 'монтажем': install, 'акти': install, 'бригада': install,
            'обрізками': offcuts, 'обрізків': offcuts, 'партія': offcuts,
            'замовлень': orders, 'оплата': orders, 'оплатою': orders,
        }
        for query, article in cases.items():
            self.assertIn(article, Search.search([('text_search', 'ilike', query)]), query)
        # several words: every word must match (in any form)
        found = Search.search([('text_search', 'ilike', 'монтажу бригадою')])
        self.assertIn(install, found)
        self.assertNotIn(offcuts, found)
        self.assertNotIn(orders, found)
        self.assertFalse(Search.search([('text_search', 'ilike', 'монтажу обрізками')]) & (install | offcuts | orders))
        # the reader uses the same search
        tree = Search.td_reader_tree('обрізками')
        self.assertIn(offcuts.id, [a['id'] for a in tree['articles'] if a['match']])

    def test_03_index_follows_the_text(self):
        article = self.env['td.knowledge.article'].create({'name': 'Кромка', 'body': '<p>текст</p>'})
        self.assertIn(' кромк ', article.search_terms)
        article.body = '<p>Фасади фарбує постачальник</p>'
        self.assertIn(' фасад ', article.search_terms)
        self.assertNotIn(' текст ', article.search_terms)
