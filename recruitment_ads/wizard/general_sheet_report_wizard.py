from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class GeneralSheetReportWizard(models.TransientModel):
    """General Sheet Report Wizard"""
    _name = "general.sheet.report.wizard"
    _inherit = 'abstract.rec.report.wizard'

    _description = "General Sheet Report Wizard"

    application_ids = fields.Many2many('hr.applicant')

    @api.multi
    def button_export_xlsx(self):
        self.ensure_one()

        no_records = True
        domain = [
            ('create_date', '>=', self.date_from + ' 00:00:00'),
            ('create_date', '<=', self.date_to + ' 23:59:59'),
        ]

        if self.job_ids:
            domain.append(('job_id','in',self.job_ids.ids))
        else:
            if self.bu_ids:
                if self.check_rec_manager:
                    bu_jobs = self.env['hr.job'].search([('business_unit_id', 'in', self.bu_ids.ids)])
                    domain.append(('job_id', 'in', bu_jobs.ids))

                else:
                    bu_jobs = self.env['hr.job'].search(
                        [('business_unit_id', 'in', self.bu_ids.ids), '|', ('user_id', '=', self.env.user.id),
                         ('other_recruiters_ids', 'in', self.env.user.id)])
                    domain.append(('job_id', 'in', bu_jobs.ids))
            else:
                if not self.check_rec_manager:
                #     rec_jobs = self.env['hr.job'].search([])
                #     domain.append(('job_id', 'in', rec_jobs))
                # else:
                    rec_jobs = self.env['hr.job'].search(
                        ['|', ('user_id', '=', self.env.user.id), ('other_recruiters_ids', 'in', self.env.user.id)])
                    domain.append(('job_id', 'in', rec_jobs.ids))
        applications = self.env['hr.applicant'].search(domain , order='create_date desc')
        if applications:
            no_records = False
            self.application_ids = [(6, 0, applications.ids)]

        if no_records:
            raise ValidationError(_("No record to display"))

        report = self.env.ref('recruitment_ads.action_report_general_sheet_xlsx')
        return report.report_action(self)
