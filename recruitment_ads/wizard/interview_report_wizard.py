from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class InterviewReportWizard(models.TransientModel):
    """Interview Report Wizard"""
    _name = "interview.report.wizard"
    _inherit = 'abstract.rec.report.wizard'

    _description = "Interview Report Wizard"

    interview_ids = fields.Many2many('mail.activity', 'interview_report_rel', 'report_id', 'interview_id')

    @api.multi
    def button_export_xlsx(self):
        self.ensure_one()
        no_records = True
        domain = []

        if self.recruiter_ids:
            domain += [('create_uid', 'in', self.recruiter_ids.ids)]
        else:
            if self.check_rec_manager == 'coordinator':
                recruiters = self.env['res.users'].search(
                    ['|', '|', '|', ('business_unit_id', '=', self.env.user.business_unit_id.id),
                     ('business_unit_id', 'in', self.env.user.multi_business_unit_id.ids),
                     ('multi_business_unit_id', 'in', self.env.user.business_unit_id.id),
                     ('multi_business_unit_id', 'in', self.env.user.multi_business_unit_id.ids)])
                domain += [('create_uid', 'in', recruiters.ids)]
        if self.job_ids:
            domain.append(('job_id', 'in', self.job_ids.ids))
        else:
            if self.bu_ids:
                bu_jobs = self.env['hr.job'].search([('business_unit_id', 'in', self.bu_ids.ids)])
                domain.append(('job_id', 'in', bu_jobs.ids))
            else:
                if self.check_rec_manager == 'coordinator':
                    bu_jobs = self.env['hr.job'].search(
                        ['|', ('business_unit_id', '=', self.env.user.business_unit_id.id),
                         ('business_unit_id', 'in', self.env.user.multi_business_unit_id.ids)])
                    domain.append(('job_id', 'in', bu_jobs.ids))

        applications = self.env['hr.applicant'].search(domain, order='create_date desc')

        ma_domain = [
            ('calendar_event_id.display_start', '>=', self.date_from + ' 00:00:00'),
            ('calendar_event_id.display_start', '<=', self.date_to + ' 23:59:59'),
            ('calendar_event_id.is_interview_done', '=', False),
            ('res_id', 'in', applications.ids),
            ('res_model', '=', 'hr.applicant')
        ]
        interviews = self.env['mail.activity'].search(ma_domain, order='write_date desc')
        if interviews:
            no_records = False
        self.interview_ids = [(6, 0, interviews.ids)]
        self.application_ids = [(6, 0, interviews.mapped('res_id'))]

        if no_records:
            raise ValidationError(_("No record to display"))

        report = self.env.ref('recruitment_ads.action_report_interview_report_xlsx')
        return report.report_action(self)
