from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AbstractRecruitmentReportWizard(models.AbstractModel):
    _name = 'abstract.rec.report.wizard'

    def _get_bu_domain(self):
        if self.env.user.has_group('recruitment_ads.group_hr_recruitment_coordinator') and not self.env.user.has_group(
                'hr_recruitment.group_hr_recruitment_manager'):
            domain = ['|', ('id', '=', self.env.user.business_unit_id.id),
                      ('id', 'in', self.env.user.multi_business_unit_id.ids)]
        else:
            domain = []
        return domain

    def _get_bu_default(self):
        if self.env.user.has_group('recruitment_ads.group_hr_recruitment_coordinator') and not self.env.user.has_group(
                'hr_recruitment.group_hr_recruitment_manager'):
            bu = self.env['business.unit'].search(['|', ('id', '=', self.env.user.business_unit_id.id),
                                                   ('id', 'in', self.env.user.multi_business_unit_id.ids)])
        else:
            bu = self.env.user.business_unit_id
        return bu

    @api.model
    def _get_current_login_user(self):
        return [self.env.user.id]

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

    date_from = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_to = fields.Date(string='End Date', required=True, default=fields.Date.today)

    job_ids = fields.Many2many('hr.job', string='Job Position')
    bu_ids = fields.Many2many('business.unit', string='Business Unit', default=lambda self: self._get_bu_default(),
                              domain=lambda self: self._get_bu_domain())
    recruiter_ids = fields.Many2many('res.users', string='Recruiter Responsible', default=_get_current_login_user)
    check_rec_manager = fields.Char(string="check field", default=get_user)

    @api.constrains('date_from', 'date_to')
    def check_dates(self):
        for r in self:
            if r.date_to < r.date_from:
                raise ValidationError(_("You can't select start date greater than end date"))

    @api.onchange('bu_ids')
    def onchange_bu_ids(self):
        self.job_ids = False

    @api.onchange('date_from', 'date_to', 'bu_ids')
    def onchange_job_ids(self):
        if self.date_from and self.date_to:
            changed_domain = [
                '|',
                '&',
                ('create_date', '>=', self.date_from + ' 00:00:00'),
                ('create_date', '<=', self.date_to + ' 23:59:59'),
                '&',
                ('write_date', '>=', self.date_from + ' 00:00:00'),
                ('write_date', '<=', self.date_to + ' 23:59:59'),
            ]
            changed_applicants = self.env['hr.applicant'].search(changed_domain)
            jobs = changed_applicants.mapped('job_id')
            changed_activity_domain = ['&'] + changed_domain + [('res_model', '=', 'hr.applicant')]
            changed_activity = self.env['mail.activity'].search(changed_activity_domain)
            jobs |= self.env['hr.applicant'].browse(changed_activity.mapped('res_id')).mapped('job_id')

            if self.bu_ids:
                if self.check_rec_manager == 'coordinator' or self.check_rec_manager == 'manager':
                    bu_jobs = self.env['hr.job'].search([('business_unit_id', 'in', self.bu_ids.ids)])
                    recruiters = self.env['res.users'].search([('business_unit_id', 'in', self.bu_ids.ids)])
                    return {'domain': {'job_ids': [('id', 'in', jobs.ids), ('id', 'in', bu_jobs.ids)],
                                       'recruiter_ids': [('id', 'in', recruiters.ids)]}}

                else:
                    bu_jobs = self.env['hr.job'].search(
                        [('business_unit_id', 'in', self.bu_ids.ids), '|', ('user_id', '=', self.env.user.id),
                         ('other_recruiters_ids', 'in', self.env.user.id)])
                    return {'domain': {'job_ids': [('id', 'in', jobs.ids), ('id', 'in', bu_jobs.ids)]}}
            else:
                if self.check_rec_manager == 'manager':
                    recruiters = self.env['res.users'].search([])
                    return {'domain': {'job_ids': [('id', 'in', jobs.ids)],
                                       'recruiter_ids': [('id', 'in', recruiters.ids)]}}

                elif self.check_rec_manager == 'coordinator':
                    recruiters = self.env['res.users'].search(
                        ['|', ('business_unit_id', '=', self.env.user.business_unit_id.id),
                         ('business_unit_id', 'in', self.env.user.multi_business_unit_id.ids)])
                    bu_jobs = self.env['hr.job'].search(
                        ['|', ('business_unit_id', '=', self.env.user.business_unit_id.id),
                         ('business_unit_id', 'in', self.env.user.multi_business_unit_id.ids)])
                    return {'domain': {'job_ids': [('id', 'in', jobs.ids), ('id', 'in', bu_jobs.ids)],
                                       'recruiter_ids': [('id', 'in', recruiters.ids)]}}
                else:
                    rec_jobs = self.env['hr.job'].search(
                        ['|', ('user_id', '=', self.env.user.id), ('other_recruiters_ids', 'in', self.env.user.id)])
                    return {'domain': {'job_ids': [('id', 'in', jobs.ids), ('id', 'in', rec_jobs.ids)]}}
