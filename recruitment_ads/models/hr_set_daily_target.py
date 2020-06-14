from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, date


class HRSetDailyTarget(models.Model):
    _name = 'hr.set.daily.target'
    _inherit = ['mail.thread']
    _description = 'Set Daily Target'

    def _get_bu_domain(self):
        domain = []
        if self.env.user.has_group('recruitment_ads.group_hr_recruitment_coordinator') and not self.env.user.has_group(
                'hr_recruitment.group_hr_recruitment_manager'):
            domain = ['|', ('id', '=', self.env.user.business_unit_id.id),
                      ('id', 'in', self.env.user.multi_business_unit_id.ids)
                      ]
        elif self.env.user.has_group('hr_recruitment.group_hr_recruitment_manager'):
            domain = []
        return domain

    @api.model
    def default_get(self, fields):
        res = super(HRSetDailyTarget, self).default_get(fields)
        if self._context.get('params', False).get('model', False) == 'hr.set.daily.target':
            if self.env.user.has_group(
                    'recruitment_ads.group_hr_recruitment_coordinator') and not self.env.user.has_group(
                'hr_recruitment.group_hr_recruitment_manager'):
                res['user_ids'] = [(6, 0, [self.env.user.id])]
        return res

    name = fields.Date(required=True, default=fields.Date.today, track_visibility='always')
    bu_ids = fields.Many2many('business.unit', 'set_daily_target_bu_rel', 'daily_target_id', 'bu_id',
                              string='Business Units', domain=lambda self: self._get_bu_domain())
    job_ids = fields.Many2many('hr.job', string='Job Position')
    user_ids = fields.Many2many('res.users', 'set_daily_target_users_rel', 'daily_target_id', 'user_id',
                                string='Recruiter Responsible')
    line_ids = fields.One2many('hr.set.daily.target.line', 'target_id', string='Lines')
    lines_count = fields.Integer(compute='_compute_lines_count')

    @api.one
    def _compute_lines_count(self):
        self.lines_count = len(self.line_ids)

    @api.onchange('name')
    def onchange_date(self):
        if self.name < fields.Date.today():
            raise ValidationError(_('Date must be greater than or equal today'))

    @api.onchange('bu_ids')
    def _get_jobs_domain(self):
        if not self._context.get('get_domain', False):
            self.job_ids = False
        if self.bu_ids:
            job_domain = [('business_unit_id', 'in', self.bu_ids.ids), ('state', '=', 'recruit')]
        else:
            if self.env.user.has_group('hr_recruitment.group_hr_recruitment_manager'):
                job_domain = [('state', '=', 'recruit')]
            else:
                job_domain = [('business_unit_id', 'in',
                               self.env.user.business_unit_id.ids + self.env.user.multi_business_unit_id.ids),
                              ('state', '=', 'recruit')]
        return {'domain': {'job_ids': job_domain}}

    @api.onchange('job_ids')
    def _get_recruiters_domain(self):
        # self.user_ids = False
        flag = False
        bus = self.env.user.business_unit_id.ids + self.env.user.multi_business_unit_id.ids
        if self.job_ids:
            if self.env.user.has_group('hr_recruitment.group_hr_recruitment_manager'):
                user_domain = [('id', 'in', self.job_ids.mapped('user_id').ids + self.job_ids.mapped(
                    'other_recruiters_ids').ids), ('active', '=', True)]
            else:
                flag = True
                if bus:
                    user_domain = [
                        ('id', 'in',
                         self.job_ids.mapped('user_id').ids + self.job_ids.mapped('other_recruiters_ids').ids),
                        '|', ('business_unit_id', 'in', bus), ('multi_business_unit_id', 'in', bus),
                        ('active', '=', True)]
                else:
                    user_domain = [
                        ('id', 'in',
                         self.job_ids.mapped('user_id').ids + self.job_ids.mapped('other_recruiters_ids').ids),
                        ('active', '=', True)]
        else:
            if bus:
                user_domain = [('business_unit_id', 'in', bus),
                               ('active', '=', True)]
            else:
                user_domain = [('active', '=', True)]

        if flag and not self._context.get('get_domain', False):
            if len(self.env['res.users'].search(user_domain)) == 0:
                raise ValidationError(_('The Selected Job positions have no recruiters under your BU'))
        return {'domain': {'user_ids': user_domain}}

    @api.multi
    def search_filter(self):
        self.ensure_one()
        self.line_ids.unlink()
        # if self.bu_ids:
        #     bu_domain = [('id', 'in', self.bu_ids.ids)]
        # else:
        #     bu_domain = self._get_bu_domain()
        if self.job_ids:
            job_domain = [('id', 'in', self.job_ids.ids)]
        else:
            job_domain = self.with_context({'get_domain': True})._get_jobs_domain().get('domain', False).get('job_ids',
                                                                                                             False)
        if self.user_ids:
            user_domain = [('id', 'in', self.user_ids.ids)]
        else:
            user_domain = self.with_context({'get_domain': True})._get_recruiters_domain().get('domain', False).get(
                'user_ids', False)

        job_report = self.env['hr.job'].search(job_domain)
        user_report = self.env['res.users'].search(user_domain)
        for user in user_report:
            for job in job_report:
                self.env['hr.set.daily.target.line'].create({
                    'name': self.name,
                    'recruiter_id': user.id,
                    'recruiter_bu_id': user.business_unit_id.id,
                    'bu_id': job.business_unit_id.id,
                    'department_id': job.department_id.id,
                    'section_id': job.section_id.id,
                    'job_id': job.job_title_id.id,
                    'level_id': job.job_level_id.id,
                    'weight': job.job_level_id.weight or 0,
                    'cvs': job.job_level_id.cv or 0,
                    'target_id': self.id,
                })
        return True

    @api.model
    def create(self, vals):
        if not (self.env.user.has_group('recruitment_ads.group_hr_recruitment_coordinator') or self.env.user.has_group(
                'hr_recruitment.group_hr_recruitment_manager')):
            raise ValidationError(_('You are not allowed to set targets'))
        return super(HRSetDailyTarget, self).create(vals)

    @api.multi
    def write(self, vals):
        if not (self.env.user.has_group('recruitment_ads.group_hr_recruitment_coordinator') or self.env.user.has_group(
                'hr_recruitment.group_hr_recruitment_manager')):
            raise ValidationError(_('You are not allowed to set targets'))
        return super(HRSetDailyTarget, self).write(vals)


class HRSetDailyTargetLine(models.Model):
    _name = 'hr.set.daily.target.line'
    _inherit = ['mail.thread']
    _description = 'Set Daily Target Lines'

    name = fields.Date(required=True, readonly=True, track_visibility='always')
    recruiter_bu_id = fields.Many2one('business.unit', string='Recruiter BU', readonly=True,
                                      track_visibility='always')
    recruiter_id = fields.Many2one('res.users', required=True, readonly=True, string='Recruiter Responsible',
                                   track_visibility='always')
    bu_id = fields.Many2one('business.unit', string='BU', required=True, readonly=True, track_visibility='always')
    department_id = fields.Many2one('hr.department', string='Department', required=True, readonly=True,
                                    track_visibility='always')
    section_id = fields.Many2one('hr.department', string='Section', readonly=True,
                                 track_visibility='always')
    job_id = fields.Many2one('job.title', string='Position', required=True, readonly=True, track_visibility='always')
    level_id = fields.Many2one('job.level', string='Level', track_visibility='always')
    weight = fields.Integer(string="Weight", track_visibility='always', default=0)
    cvs = fields.Integer(string="Target Application", track_visibility='always', default=0)
    target_id = fields.Many2one('hr.set.daily.target', string='Set Daily Target', track_visibility='always')

    @api.onchange('level_id')
    def _compute_level(self):
        # for line in self:
        self.weight = self.level_id.weight
        self.cvs = self.level_id.cv