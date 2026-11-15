from odoo.exceptions import AccessError, UserError
from odoo.tests import HttpCase, TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestKnowledge(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Article = cls.env['td.knowledge.article']
        cls.user = new_test_user(cls.env, login='td_kb_user', groups='base.group_user')
        cls.editor = new_test_user(cls.env, login='td_kb_editor',
                                   groups='base.group_user,td_knowledge.group_td_knowledge_editor')
        cls.section = cls.Article.create({'name': 'Sales', 'body': '<p>Section</p>'})
        cls.article = cls.Article.create({
            'name': 'Partner card', 'parent_id': cls.section.id,
            'body': '<p>How to fill the <b>VAT number</b> of a customer</p>',
            'model_ids': [(6, 0, cls.env['ir.model']._get('res.partner').ids)],
        })
        cls.secret = cls.Article.create({
            'name': 'Settings of the mail server', 'body': '<p>password policy</p>',
            'group_ids': [(6, 0, cls.env.ref('base.group_system').ids)],
        })

    def test_01_reader_can_read_not_write(self):
        articles = self.Article.with_user(self.user)
        self.assertIn(self.article, articles.search([]))
        with self.assertRaises(AccessError):
            articles.create({'name': 'By a user'})
        with self.assertRaises(AccessError):
            self.article.with_user(self.user).write({'name': 'changed'})

    def test_02_editor_writes(self):
        new = self.Article.with_user(self.editor).create({'name': 'By an editor', 'parent_id': self.section.id})
        new.with_user(self.editor).write({'body': '<p>text</p>'})
        self.assertEqual(new.parent_id, self.section)
        # an editor (not an administrator) chooses the screens of the article
        new.with_user(self.editor).model_ids = self.env['ir.model'].with_user(self.editor).search(
            [('model', '=', 'res.partner')])
        self.assertEqual(new.model_ids.model, 'res.partner')

    def test_03_group_restriction(self):
        self.assertNotIn(self.secret, self.Article.with_user(self.user).search([]))
        with self.assertRaises(AccessError):
            self.secret.with_user(self.user).read(['name'])
        self.assertIn(self.secret, self.Article.with_user(self.editor).search([]))
        tree = self.Article.with_user(self.user).td_reader_tree()
        self.assertNotIn(self.secret.id, [a['id'] for a in tree['articles']])

    def test_04_search_in_text_keeps_sections(self):
        tree = self.Article.with_user(self.user).td_reader_tree('VAT number')
        ids = {a['id']: a for a in tree['articles']}
        self.assertTrue(ids[self.article.id]['match'])
        self.assertIn(self.section.id, ids)          # the section of the match stays in the tree
        self.assertFalse(ids[self.section.id]['match'])
        self.assertFalse(tree['is_editor'])
        self.assertTrue(self.Article.with_user(self.editor).td_reader_tree()['is_editor'])

    def test_05_screen_help(self):
        Article = self.Article.with_user(self.user)
        self.assertEqual(Article.td_screen_count('res.partner'), 1)
        help_ = Article.td_screen_help('res.partner')
        self.assertEqual([a['id'] for a in help_['articles']], [self.article.id])
        self.assertEqual(help_['articles'][0]['path'], 'Sales')
        self.assertIn('VAT number', help_['articles'][0]['snippet'])
        self.assertEqual(help_['model_id'], self.env['ir.model']._get('res.partner').id)
        self.assertEqual(Article.td_screen_count('res.users'), 0)
        self.assertEqual(Article.td_screen_count(False, False), 0)

    def test_06_screen_help_by_application(self):
        menu = self.env.ref('base.menu_administration')
        self.article.menu_ids = [(6, 0, menu.ids)]
        self.assertEqual(self.Article.with_user(self.user).td_screen_count('res.users', menu.id), 1)

    def test_07_article_view(self):
        data = self.Article.with_user(self.user).td_reader_article(self.article.id)
        self.assertEqual(data['path'], [{'id': self.section.id, 'name': 'Sales'}])
        self.assertIn('VAT number', data['body'])
        section = self.Article.with_user(self.user).td_reader_article(self.section.id)
        self.assertEqual([c['id'] for c in section['children']], [self.article.id])
        with self.assertRaises(AccessError):
            self.Article.with_user(self.user).td_reader_article(self.secret.id)

    def test_07b_article_in_restricted_section(self):
        # an article open to everybody inside a section limited to administrators: the reader opens it, the section
        # is not shown in the path (A-14-5, A-11-fix2)
        inner = self.Article.create({'name': 'Open article', 'parent_id': self.secret.id, 'body': '<p>open</p>'})
        data = self.Article.with_user(self.user).td_reader_article(inner.id)
        self.assertEqual(data['path'], [])
        self.assertEqual(data['name'], 'Open article')

    def test_08_no_cycle(self):
        with self.assertRaises(UserError):  # ValidationError of the constraint or the recursion check of the ORM
            self.section.parent_id = self.article

    def test_09_body_sanitized(self):
        self.article.body = '<p>ok</p><script>alert(1)</script>'
        self.assertNotIn('<script', self.article.body)

    def test_10_starter_articles_and_admin_is_editor(self):
        start = self.env.ref('td_knowledge.article_start')
        self.assertTrue(start.is_package)
        self.assertIn(self.env.ref('td_knowledge.group_td_knowledge_editor'),
                      self.env.ref('base.group_system').all_implied_ids)


@tagged('post_install', '-at_install')
class TestKnowledgeTour(HttpCase):

    def test_knowledge_tour(self):
        self.env['td.knowledge.article'].create({
            'name': 'Tour: users',
            'body': '<p>How to invite a user</p>',
            'model_ids': [(6, 0, self.env['ir.model']._get('res.users').ids)],
        })
        self.start_tour('/odoo/action-base.action_res_users', 'td_knowledge_tour', login='admin')
