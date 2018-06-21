from odoo import api, fields, models,_
from odoo.exceptions import ValidationError

class RecruiterActivityReportWizard(models.TransientModel):
    """Recruiter Activity Report Wizard"""

    _name = "recruiter.activity.report.wizard"
    _description = "Recruiter Activity Report Wizard"

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)

    recruiter_ids = fields.Many2many('res.users', string='Recruiter Responsible')
    job_ids = fields.Many2many('hr.job', string='Job Position')

    cv_source = fields.Boolean('Cv Source')
    calls = fields.Boolean('Calls')
    interviews = fields.Boolean('Interviews')

    @api.multi
    def button_export_xlsx(self):
        self.ensure_one()
        if not (self.calls or self.cv_source or self.interviews):
            raise ValidationError(_("Please Select at least one activity to export"))
        report = self.env.ref('recruitment_ads.action_report_recruiter_activity_xlsx')
        return report.report_action(self)
