import logging
import re

from odoo import models, api, fields, tools, _
from odoo.addons.base.res.res_partner import Partner
from odoo.osv.expression import get_unaccent_wrapper
from odoo.exceptions import ValidationError

_schema = logging.getLogger('odoo.schema')


class PartnerInherit(models.Model):
    _inherit = 'res.partner'

    @api.constrains('mobile', 'name', 'phone')
    def constrain_partner_mobile(self):
        for applicant in self:
            if applicant.phone:
                if applicant.phone.isnumeric() == False or len(applicant.phone) > 15:
                    raise ValidationError(_('Mobile number must be digits only and not greater than 15 digit. '))
            if applicant.mobile:
                if applicant.mobile.isnumeric() == False or len(applicant.mobile) > 15:
                    raise ValidationError(_('Phone number must be digits only and not greater than 15 digit. '))
            if applicant.name:
                if all(x.isalpha() or x.isspace() for x in applicant.name):
                    pass
                else:
                    raise ValidationError(_('Applicant Name must be Characters only . '))

    short_display = fields.Char("Short display name", compute='_compute_short_display_name', store=True)
    applicant = fields.Boolean(string='Applicant')
    date_of_birth = fields.Date(string='Date of Birth')
    face_book = fields.Char(string='Facebook')
    linkedin = fields.Char(string='LinkedIn')
    applications_ids = fields.One2many('hr.applicant', 'partner_id', string="Applications")
    last_app_job_id = fields.Many2one('hr.job', string="Last Application Job", compute='_get_last_application')
    last_app_last_activity_id = fields.Many2one('mail.activity.type', string="Last Application Last Activity",
                                                compute='_get_last_application')
    last_app_last_activity_date = fields.Date(string="Last Application Last Activity Date",
                                              compute='_get_last_application')

    _sql_constraints = [
        ('mobile_uniq',
         'CHECK (1=1)',
         'Mobile has been entered before.'),
        ('email_uniq',
         'CHECK (1=1)',
         'Email has been entered before.')
    ]

    @api.multi
    def _get_last_application(self):
        for contact in self:
            if contact.applications_ids:
                last_application = \
                    [application for application in contact.applications_ids.sorted(lambda a: a.id)][-1]
                contact.last_app_job_id = last_application.job_id
                contact.last_app_last_activity_id = last_application.last_activity
                contact.last_app_last_activity_date = last_application.last_activity_date

    @api.model_cr_context
    def _auto_init(self):
        res = super(PartnerInherit, self)._auto_init()
        if not tools.index_exists(self._cr, 'res_partner_mobile_uniq_index'):
            self._cr.execute('CREATE UNIQUE INDEX "{}" ON "{}" {}'.format('res_partner_mobile_uniq_index', self._table,
                                                                          '(mobile) WHERE (applicant is TRUE)'))
            _schema.debug("Table %r: created index %r (%s)", self._table, 'res_partner_mobile_uniq_index',
                          '(mobile) WHERE (applicant is TRUE)')
        if not tools.index_exists(self._cr, 'res_partner_email_uniq_index'):
            self._cr.execute('CREATE UNIQUE INDEX "{}" ON "{}" {}'.format('res_partner_email_uniq_index', self._table,
                                                                          '(email) WHERE (applicant is TRUE)'))
            _schema.debug("Table %r: created index %r (%s)", self._table, 'res_partner_email_uniq_index',
                          '(email) WHERE (applicant is TRUE)')
        return res

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
        match_name_start = self._context.get('match_name_start', False)
        search_for_applicant = self._context.get('search_for_applicant', False)
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

    @api.onchange('email')
    def validate_mail(self):
        if self.email:
            # I add 'A-Z' to allow capital letters in email format
            match = re.match('^[_a-zA-Z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', self.email)
            if match == None:
                raise ValidationError('Not a valid E-mail ID')

    @api.constrains('email', 'mobile', 'phone', 'face_book', 'linkedin')
    def constrain_email_mobile(self):
        for applicant in self:
            if not applicant.email and not applicant.mobile and not applicant.phone and not applicant.face_book and \
                    not applicant.linkedin:
                raise ValidationError(_('Please insert at least one Applicant info.'))

    @api.multi
    def action_open_partner_merge(self):
        view = self.env.ref('base_partner_merge.base_partner_merge_automatic_wizard_form')
        # merge_contact_id = self.env['base.partner.merge.automatic.wizard'].create(
        #     {'state': 'option', 'dst_partner_id': res_id})
        self.ensure_one()
        action = {
            'name': _('merge'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'base.partner.merge.automatic.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': 14,
            'context': self._context,
        }
        return action

    @api.multi
    def write(self, vals):
        contact_obj = self.env['res.partner']
        duplicated_contact = []
        if self.email:
            duplicated_email = contact_obj.search([('email', '=', self.email)])
            duplicated_contact.append(duplicated_email) if duplicated_email not in duplicated_contact and len(
                duplicated_email) > 1 else False
        if self.mobile:
            duplicated_mobile = contact_obj.search([('mobile', '=', self.mobile)])
            duplicated_contact.append(duplicated_mobile) if duplicated_mobile not in duplicated_contact and len(
                duplicated_mobile) > 1 else False
        if self.phone:
            duplicated_phone = contact_obj.search([('phone', '=', self.phone)])
            duplicated_contact.append(duplicated_phone) if duplicated_phone not in duplicated_contact and len(
                duplicated_phone) > 1 else False
        if self.face_book:
            duplicated_face_book = contact_obj.search([('face_book', '=', self.face_book)])
            duplicated_contact.append(duplicated_face_book) if duplicated_face_book not in duplicated_contact and len(
                duplicated_face_book) > 1 else False
        if self.linkedin:
            duplicated_linkedin = contact_obj.search([('linkedin', '=', self.linkedin)])
            duplicated_contact.append(duplicated_linkedin) if duplicated_linkedin not in duplicated_contact and len(
                duplicated_linkedin) > 1 else False
        if duplicated_contact:
            raise ValidationError(_('There is a duplication in applicant contact, Please press "Check Duplication".'))
        # return self.action_open_partner_merge()
        res = super(PartnerInherit, self).write(vals)
        return res
