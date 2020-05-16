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
        if self.recruiter_ids:
            domain += [('create_uid', 'in', self.recruiter_ids.ids)]
        else:
            if self.check_rec_manager == 'coordinator':
                recruiters = self.env['res.users'].search(
                    ['|','|','|', ('business_unit_id', '=', self.env.user.business_unit_id.id),
                     ('business_unit_id', 'in', self.env.user.multi_business_unit_id.ids),('multi_business_unit_id', 'in', self.env.user.business_unit_id.id),('multi_business_unit_id', 'in', self.env.user.multi_business_unit_id.ids)])
                domain += [('create_uid', 'in', recruiters.ids)]
        if self.job_ids:
            domain.append(('job_id', 'in', self.job_ids.ids))

        else:
            if self.bu_ids:
                bu_jobs = self.env['hr.job'].search([('business_unit_id', 'in', self.bu_ids.ids)])
                domain.append(('job_id', 'in', bu_jobs.ids))


        applications = self.env['hr.applicant'].search(domain, order='create_date desc')
        if applications:
            no_records = False
            self.application_ids = [(6, 0, applications.ids)]

        if no_records:
            raise ValidationError(_("No record to display"))

        report = self.env.ref('recruitment_ads.action_report_general_sheet_xlsx')
        return report.report_action(self)
