from odoo import models, api, fields
from odoo.addons.base.res.res_partner import Partner
from odoo.osv.expression import get_unaccent_wrapper


class PartnerInherit(models.Model):
    _inherit = 'res.partner'

    short_display = fields.Char("Short display name", compute='_compute_short_display_name', store=True)
    applicant = fields.Boolean(string='Applicant')

    @api.depends('name')
    def _compute_short_display_name(self):
        for partner in self:
            partner.short_display = ''.join([part[0] for part in partner.name.split(maxsplit=1)])

    @api.multi
    def name_get(self):
        res = []
        if 'display_pos' in self._context:
            for rec in self:
                res.append((rec.id, rec.name + ' - ' + (rec.function or '')))
        else:
            return super(PartnerInherit, self).name_get()
        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        match_name_start = self._context.get('match_name_start',False)
        search_for_applicant = self._context.get('search_for_applicant',False)
        unaccent = get_unaccent_wrapper(self.env.cr)
        if match_name_start:
            like_search_name = '%s%%' % name
            query_sql = """SELECT id
                             FROM res_partner
                          {where} ({display_name} {operator} {percent}
                               OR {name} {operator} {percent})
                               -- don't panic, trust postgres bitmap
                         ORDER BY {name}
                        """
            query_data = {
                'display_name': unaccent('display_name'),
                'name': unaccent('name'),
            }
        elif search_for_applicant:
            like_search_name = '%%%s%%' % name
            query_sql = """SELECT id
                             FROM res_partner
                          {where} ({display_name} {operator} {percent}
                               OR {name} {operator} {percent}
                               OR {mobile} {operator} {percent}
                               OR {phone} {operator} {percent}
                               OR {email} {operator} {percent})
                               -- don't panic, trust postgres bitmap
                         ORDER BY {name}
                        """
            query_data = {
                'display_name': unaccent('display_name'),
                'name': unaccent('name'),
                'mobile': unaccent('mobile'),
                'phone': unaccent('phone'),
                'email': unaccent('email')
            }

        if match_name_start or search_for_applicant:
            if args is None:
                args = []
            if name and operator in ('=', 'ilike', '=ilike', 'like', '=like'):
                self.check_access_rights('read')
                where_query = self._where_calc(args)
                self._apply_ir_rules(where_query, 'read')
                from_clause, where_clause, where_clause_params = where_query.get_sql()
                where_str = where_clause and (" WHERE %s AND " % where_clause) or ' WHERE '

                # search on the name of the contacts and of its company
                search_name = name
                if operator in ('ilike', 'like'):
                    search_name = like_search_name
                if operator in ('=ilike', '=like'):
                    operator = operator[1:]
                query = query_sql.format(where=where_str,
                                   operator=operator,
                                   percent=unaccent('%s'),
                                         **query_data)
                where_clause_params += [search_name] * len(query_data)
                if limit:
                    query += ' limit %s'
                    where_clause_params.append(limit)
                self.env.cr.execute(query, where_clause_params)
                partner_ids = [row[0] for row in self.env.cr.fetchall()]

                if partner_ids:
                    return self.browse(partner_ids).name_get()
                else:
                    return []
            return super(Partner, self).name_search(name, args, operator=operator, limit=limit)

        return super(PartnerInherit, self).name_search(name=name, args=args, operator=operator, limit=limit)

    _sql_constraints = [
        ('mobile_uniq',
         'UNIQUE (mobile)',
         'Data entered before.'),
        ('email_uniq',
         'UNIQUE (email)',
         'Data entered before.')
    ]