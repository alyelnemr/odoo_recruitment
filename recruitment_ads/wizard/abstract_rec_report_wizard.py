from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AbstractRecruitmentReportWizard(models.AbstractModel):
    _name = 'abstract.rec.report.wizard'

    date_from = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_to = fields.Date(string='End Date', required=True, default=fields.Date.today)

    job_ids = fields.Many2many('hr.job', string='Job Position')

    @api.constrains('date_from', 'date_to')
    def check_dates(self):
        for r in self:
            if r.date_to < r.date_from:
                raise ValidationError(_("You can't select start date greater than end date"))

    @api.onchange('date_from', 'date_to')
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

            return {'domain': {'job_ids': [('id', 'in', jobs.ids)]}}
