from odoo import api, fields, models


class RecruiterActivityReportWizard(models.TransientModel):
    """Recruiter Activity Report Wizard"""

    _name = "recruiter.activity.report.wizard"
    _description = "Recruiter Activity Report Wizard"

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)

    recruiter_ids = fields.Many2many('res.users', string='Recruiter Responsible')
    job_ids = fields.Many2many('hr.job', string='Job Position')

    @api.multi
    def button_export_xlsx(self):
        self.ensure_one()
        report = self.env.ref('recruitment_ads.action_report_recruiter_activity_xlsx')
        return report.report_action([])
