from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ComplianceReportWizard(models.TransientModel):
    _name = "compliance.report.wizard"

    date_from = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_to = fields.Date(string='End Date', required=True, default=fields.Date.today)
    recruiter_ids = fields.Many2many('res.users', string='Recruiter Responsible')
    bu_ids = fields.Many2many('business.unit', string='Business Unit')
    application_ids = fields.Many2many('hr.applicant')

    @api.constrains('date_from', 'date_to')
    def check_dates(self):
        for r in self:
            if r.date_to < r.date_from:
                raise ValidationError(_("You can't select start date greater than end date"))

    @api.onchange('bu_ids')
    def onchange_bu_ids(self):
        self.recruiter_ids = False
        if not self.bu_ids:
            recruiters = self.env['res.users'].search([])
        else:
            recruiters = self.env['res.users'].search([('business_unit_id', 'in', self.bu_ids.ids)])
        return {'domain': {'recruiter_ids': [('id', 'in', recruiters.ids)]}}

    @api.multi
    def button_export_xlsx(self):
        self.ensure_one()
        no_records = True
        domain = [
            ('create_date', '>=', self.date_from + ' 00:00:00'),
            ('create_date', '<=', self.date_to + ' 23:59:59'),
        ]
        if self.recruiter_ids:
            domain.append(('create_uid', 'in', self.recruiter_ids.ids))
        if self.bu_ids:
            bu_jobs = self.env['hr.job'].search([('business_unit_id', 'in', self.bu_ids.ids)])
            domain.append(('job_id', 'in', bu_jobs.ids))

        applications = self.env['hr.applicant'].search(domain, order='create_date desc')
        if applications:
            no_records = False
            self.application_ids =[(6, 0, applications.ids)]

        if no_records:
            raise ValidationError(_("No record to display"))



        report = self.env.ref('recruitment_ads.action_compliance_report_xlsx')
        return report.report_action(self)
