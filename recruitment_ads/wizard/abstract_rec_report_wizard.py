from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AbstractRecruitmentReportWizard(models.AbstractModel):
    _name = 'abstract.rec.report.wizard'

    date_from = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_to = fields.Date(string='End Date', required=True, default=fields.Date.today)

    job_ids = fields.Many2many('hr.job', string='Job Position')
    bu_ids = fields.Many2many('business.unit', string='Business Unit',default = lambda self : self.env.user.business_unit_id)

    @api.model
    def _get_current_login_user(self):
     return [self.env.user.id]

    recruiter_ids = fields.Many2many('res.users', string='Recruiter Responsible',default=_get_current_login_user)


    @api.model
    def get_user(self):
        res_user = self.env.user
        if res_user.has_group ('hr_recruitment.group_hr_recruitment_manager'):
            return True
        else:
            return False

    check_rec_manager = fields.Boolean(string="check field",default = get_user)


    @api.constrains('date_from', 'date_to')
    def check_dates(self):
        for r in self:
            if r.date_to < r.date_from:
                raise ValidationError(_("You can't select start date greater than end date"))

    @api.onchange('bu_ids')
    def onchange_bu_ids(self):
        self.job_ids = False
        

    @api.onchange('date_from', 'date_to','bu_ids')
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
                if self.check_rec_manager:
                    bu_jobs = self.env['hr.job'].search([('business_unit_id', 'in', self.bu_ids.ids)])
                    recruiters = self.env['res.users'].search([('business_unit_id', 'in', self.bu_ids.ids)])
                    return {'domain': {'job_ids': [('id', 'in', jobs.ids), ('id', 'in', bu_jobs.ids)],'recruiter_ids':[('id', 'in', recruiters.ids)]}}

                else:
                    bu_jobs = self.env['hr.job'].search(
                        [('business_unit_id', 'in', self.bu_ids.ids), '|', ('user_id', '=', self.env.user.id),
                         ('other_recruiters_ids', 'in', self.env.user.id)])
                    return {'domain': {'job_ids': [('id', 'in', jobs.ids), ('id', 'in', bu_jobs.ids)]}}
            else:
                if self.check_rec_manager:
                    recruiters = self.env['res.users'].search([])
                    return {'domain': {'job_ids': [('id', 'in', jobs.ids)],'recruiter_ids':[('id', 'in', recruiters.ids)]}}

                else:
                    rec_jobs = self.env['hr.job'].search(
                        ['|', ('user_id', '=', self.env.user.id),('other_recruiters_ids', 'in', self.env.user.id)])
                    return {'domain': {'job_ids': [('id', 'in', jobs.ids), ('id', 'in', rec_jobs.ids)]}}