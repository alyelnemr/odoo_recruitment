from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class GenerateDailyTargetReportWizard(models.TransientModel):
    _name = "generate.daily.target.report.wizard"

    def _get_bu_domain(self):
        if not self.env.user.has_group(
                'hr_recruitment.group_hr_recruitment_manager'):
            domain = ['|', ('id', '=', self.env.user.business_unit_id.id),
                      ('id', 'in', self.env.user.multi_business_unit_id.ids)
                      ]
        else:
            domain = []
        return domain

    @api.model
    def default_get(self, fields):
        res = super(GenerateDailyTargetReportWizard, self).default_get(fields)
        if not self.env.user.has_group('hr_recruitment.group_hr_recruitment_manager'):
            res['recruiter_ids'] = [(6, 0, [self.env.user.id])]
        return res

    @api.model
    def get_user(self):
        res_user = self.env.user
        if res_user.has_group('hr_recruitment.group_hr_recruitment_manager'):
            return "manager"
        elif self.env.user.has_group(
                'recruitment_ads.group_hr_recruitment_coordinator') and not self.env.user.has_group(
            'hr_recruitment.group_hr_recruitment_manager'):
            return "coordinator"
        else:
            return "officer"

    check_rec_manager = fields.Char(string="check field", default=get_user)
    date_from = fields.Date(string='From', required=True, default=fields.Date.today)
    date_to = fields.Date(string='To', required=True, default=fields.Date.today)
    bu_ids = fields.Many2many('business.unit', string='Business Unit', domain=lambda self: self._get_bu_domain())
    job_ids = fields.Many2many('hr.job', string='Job Position')
    recruiter_ids = fields.Many2many('res.users', string='Recruiter Responsible')
    line_ids = fields.Many2many('hr.set.daily.target.line', 'generate_daily_target_lines', 'wizard_id', 'set_line_id',
                                string='Lines')
    type_report = fields.Selection([('target', 'Target'), ('actual', 'Actual'), ('actual_vs_target', 'Actual vs Target')],
                              required=True, default='target',string='Type')

    @api.constrains('date_from', 'date_to')
    def check_dates(self):
        for r in self:
            if r.date_to < r.date_from:
                raise ValidationError(_("You can't select start date greater than end date"))

    @api.onchange('bu_ids')
    def _get_jobs_domain(self):
        return self._get_job_user_domain()

    @api.onchange('job_ids')
    def _get_recruiters_domain(self):
        return self._get_job_user_domain()

    def _get_job_user_domain(self):
        # JOB DOMAIN
        job_domain = [('state', '=', 'recruit')]
        if self.bu_ids:
            job_domain += [('business_unit_id', 'in', self.bu_ids.ids)]
        else:
            if not self.env.user.has_group('hr_recruitment.group_hr_recruitment_manager') and (
                    self.env.user.business_unit_id or self.env.user.multi_business_unit_id):
                job_domain += ['|', ('business_unit_id', 'in',
                                     self.env.user.business_unit_id.ids + self.env.user.multi_business_unit_id.ids),
                               '|', ('user_id', '=', self.env.user.id), ('other_recruiters_ids', '=', self.env.user.id)]
            elif self.env.user.has_group('hr_recruitment.group_hr_recruitment_user') and not self.env.user.has_group(
                    'hr_recruitment.group_hr_recruitment_manager'):
                job_domain += ['|', ('user_id', '=', self.env.user.id), ('other_recruiters_ids', '=', self.env.user.id)]

        # USER DOMAIN
        jobs = False
        bus = self.env.user.business_unit_id.ids + self.env.user.multi_business_unit_id.ids
        user_domain = [('active', '=', True)]
        if self.bu_ids:
            user_domain += [
                '|', ('business_unit_id', 'in', self.bu_ids.ids),
                ('multi_business_unit_id', 'in', self.bu_ids.ids),
            ]
            jobs = self.env['hr.job'].search(job_domain)
        elif bus and not self.bu_ids and self.env.user.has_group(
                'recruitment_ads.group_hr_recruitment_coordinator') and not self.env.user.has_group(
            'hr_recruitment.group_hr_recruitment_manager'):
            user_domain += ['|', ('business_unit_id', 'in', bus),
                            ('multi_business_unit_id', 'in', bus)]
        if self.job_ids:
            user_domain += [('id', 'in', self.job_ids.mapped('user_id').ids + self.job_ids.mapped(
                'other_recruiters_ids').ids)]
        elif jobs:
            user_domain += [('id', 'in', jobs.mapped('user_id').ids + jobs.mapped('other_recruiters_ids').ids)]

        if self.env.user.has_group('recruitment_ads.group_hr_recruitment_coordinator') and not self.env.user.has_group(
                'hr_recruitment.group_hr_recruitment_manager') and self.job_ids and not self._context.get(
            'get_domain', False):
            if len(self.env['res.users'].search(user_domain)) == 0:
                raise ValidationError(_('The Selected Job positions have no recruiters under your BU'))
        return {'domain': {'job_ids': job_domain, 'recruiter_ids': user_domain}}

    @api.multi
    def button_generate_daily_report(self):
        self.ensure_one()
        if self.job_ids:
            job_domain = [('id', 'in', self.job_ids.ids)]
        else:
            job_domain = self.with_context({'get_domain': True})._get_jobs_domain().get('domain', False).get('job_ids',
                                                                                                             False)
        if self.recruiter_ids:
            user_domain = [('id', 'in', self.recruiter_ids.ids)]
        else:
            user_domain = self.with_context({'get_domain': True})._get_recruiters_domain().get('domain', False).get(
                'recruiter_ids', False)

        job_report = self.env['hr.job'].search(job_domain)
        user_report = self.env['res.users'].search(user_domain)
        if job_report and user_report:
            lines = self.env['hr.set.daily.target.line'].search([
                ('recruiter_id', 'in', user_report.ids),
                ('job_id', 'in', job_report.mapped('job_title_id').ids),
                ('name', '>=', self.date_from),
                ('name', '<=', self.date_to),
                ('active', '=', True),
            ])
            if not lines:
                raise ValidationError('No Daily Target is set for the selected range')
            else:
                self.line_ids = lines
        else:
            raise ValidationError('No Daily Target is set for the selected range')

        report = self.env.ref('recruitment_ads.action_report_generate_daily_target_xlsx')
        return report.report_action(self)
