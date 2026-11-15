from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.orm.domains import Domain
from odoo.tools import html2plaintext

from . import stemmer

SEARCH_LIMIT = 50
SNIPPET_CHARS = 160


class TdKnowledgeArticle(models.Model):
    _name = 'td.knowledge.article'
    _description = 'Knowledge article'
    _inherit = ['mail.thread']
    _parent_store = True
    _order = 'sequence, name, id'

    name = fields.Char('Title', required=True, tracking=True)
    icon = fields.Char('Icon', size=8, help='One emoji shown before the title in the tree.')
    body = fields.Html('Content', sanitize=True)
    sequence = fields.Integer('Sequence', default=10)
    active = fields.Boolean('Active', default=True, tracking=True)
    parent_id = fields.Many2one('td.knowledge.article', 'Section', index=True, ondelete='restrict', tracking=True)
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many('td.knowledge.article', 'parent_id', 'Articles of the section')
    model_ids = fields.Many2many('ir.model', string='Screens (models)', ondelete='cascade',
                                 help='The article is shown by «Help» on the lists and forms of these models.')
    menu_ids = fields.Many2many('ir.ui.menu', string='Applications and menus',
                                help='The article is shown by «Help» everywhere in these applications.')
    group_ids = fields.Many2many('res.groups', string='Readers',
                                 help='Empty: every internal user reads the article. Otherwise only these groups '
                                      '(the editors always see it).')
    search_terms = fields.Text('Search index', compute='_compute_search_terms', store=True,
                               help='Stems of the words of the title and the content (word forms in the search).')
    text_search = fields.Char('Text', compute='_compute_text_search', search='_search_text_search',
                              help='Search in the title and the content with word forms: «монтажу» finds «монтаж».')
    is_package = fields.Boolean('From the package', readonly=True,
                                help='Shipped by a ToDo module. An update of the package does not overwrite changes.')

    @api.depends('name', 'body')
    def _compute_search_terms(self):
        for article in self:
            terms = stemmer.stems(f'{article.name or ""} {html2plaintext(article.body or "")}')
            article.search_terms = f' {" ".join(sorted(terms))} ' if terms else False

    def _compute_text_search(self):
        self.text_search = False

    def _search_text_search(self, operator, value):
        if operator not in ('ilike', 'like', '=') or not isinstance(value, str):
            return NotImplemented
        domains = []
        for word in stemmer.words(value):
            domains.append(Domain.OR([
                [('name', 'ilike', word)],
                [('body', 'ilike', word)],
                # the stem of the search word starts a stem of the article
                [('search_terms', 'ilike', f' {stemmer.stem(word)}')],
            ]))
        return Domain.AND(domains) if domains else Domain.TRUE

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if self._has_cycle():
            raise ValidationError(_('A section cannot be inside its own article.'))

    # ------------------------------------------------------------------
    # Reader (client action td_knowledge.reader)
    # ------------------------------------------------------------------
    @api.model
    def td_reader_tree(self, query=''):
        """Articles the user may read, as a flat list for the tree; with a query only the matches and their
        sections. Access rules apply (no sudo)."""
        articles = self.search([])
        matches = None
        query = (query or '').strip()
        if query:
            matches = self.search([('text_search', 'ilike', query)], limit=SEARCH_LIMIT)
            keep = set()
            for article in matches:
                keep.update(int(i) for i in article.parent_path.split('/') if i)
            articles = articles.filtered(lambda a: a.id in keep)
        visible = set(articles.ids)
        return {
            'articles': [{
                'id': a.id,
                'name': a.name,
                'icon': a.icon or '',
                'parent_id': a.parent_id.id if a.parent_id.id in visible else False,
                'match': matches is not None and a in matches,
            } for a in articles],
            'is_editor': self.env.user.has_group('td_knowledge.group_td_knowledge_editor'),
        }

    @api.model
    def td_reader_article(self, article_id):
        article = self.browse(article_id).exists()
        if not article:
            return False
        article.check_access('read')
        return {
            'id': article.id,
            'name': article.name,
            'icon': article.icon or '',
            'body': article.body or '',
            'path': [{'id': a.id, 'name': a.name} for a in article._td_ancestors()],
            'children': [{'id': c.id, 'name': c.name, 'icon': c.icon or ''} for c in article.child_ids],
            'attachments': [{'id': att.id, 'name': att.name} for att in self.env['ir.attachment'].search(
                [('res_model', '=', self._name), ('res_id', '=', article.id)])],
            'write_date': fields.Datetime.to_string(article.write_date),
            'author': article.write_uid.name,
        }

    def _td_ancestors(self):
        self.ensure_one()
        ids = [int(i) for i in self.parent_path.split('/') if i][:-1]
        # a section limited to other groups is skipped: its title must not be read (AccessError) or shown
        return self.browse(ids).exists()._filtered_access('read')

    # ------------------------------------------------------------------
    # Help for the current screen (systray)
    # ------------------------------------------------------------------
    @api.model
    def _td_screen_domain(self, model=None, menu_id=None):
        domain = []
        # ir.model is not readable by internal users: resolve the id with the ORM helper (sudo, cached)
        model_id = self.env['ir.model']._get_id(model) if model else False
        if model_id:
            domain.append(('model_ids', 'in', [model_id]))
        if menu_id:
            menus = self.env['ir.ui.menu'].browse(int(menu_id)).exists()
            if menus:
                domain.append(('menu_ids', 'in', menus.ids))
        if not domain:
            return [('id', '=', 0)]
        return ['|', *domain] if len(domain) == 2 else domain

    @api.model
    def td_screen_count(self, model=None, menu_id=None):
        return self.search_count(self._td_screen_domain(model, menu_id))

    @api.model
    def td_screen_help(self, model=None, menu_id=None):
        """Articles of the current screen: linked to its model first, then to its application."""
        articles = self.search(self._td_screen_domain(model, menu_id))
        ir_model = self.env['ir.model']._get(model) if model else self.env['ir.model']
        if ir_model:
            articles = articles.sorted(lambda a: (ir_model.id not in a.sudo().model_ids.ids, a.sequence, a.name))
        return {
            'articles': [{
                'id': a.id,
                'name': a.name,
                'icon': a.icon or '',
                'snippet': self._td_snippet(a.body),
                'path': ' / '.join(a._td_ancestors().mapped('name')),
            } for a in articles],
            'model_id': ir_model.id or False,
            'model_name': ir_model.name or '',
            'is_editor': self.env.user.has_group('td_knowledge.group_td_knowledge_editor'),
        }

    @api.model
    def _td_snippet(self, body):
        text = ' '.join(html2plaintext(body or '').split())
        return text if len(text) <= SNIPPET_CHARS else text[:SNIPPET_CHARS].rsplit(' ', 1)[0] + '…'
