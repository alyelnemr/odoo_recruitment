from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class InterviewReportWizard(models.TransientModel):
    """Interview Report Wizard"""
    _name = "interview.report.wizard"
    _inherit = 'abstract.rec.report.wizard'

    _description = "Interview Report Wizard"

    interview_ids = fields.Many2many('mail.activity', 'interview_recruiter_report_rel', 'report_id', 'interview_id',
                                     domain=[('active', '=', False)])

    @api.multi
    def button_export_xlsx(self):
        self.ensure_one()
        no_records = True
        domain = [
            ('create_date', '>=', self.date_from + ' 00:00:00'),
            ('create_date', '<=', self.date_to + ' 23:59:59'),
        ]

        if self.job_ids:
            domain.append(('job_id', 'in', self.job_ids.ids))
            if self.recruiter_ids:
                domain += [('create_uid', 'in', self.recruiter_ids.ids)]
        else:
            if self.bu_ids:
                if self.check_rec_manager == 'manager' or self.check_rec_manager == 'coordinator':
                    if self.recruiter_ids:
                        domain += [('create_uid', 'in', self.recruiter_ids.ids),
                                   ('job_id.business_unit_id', 'in', self.bu_ids.ids)]
                    bu_jobs = self.env['hr.job'].search([('business_unit_id', 'in', self.bu_ids.ids)])
                else:
                    if self.recruiter_ids:
                        domain += ['|', '&', ('create_uid', 'in', self.recruiter_ids.ids),
                                   ('job_id.business_unit_id', 'in', self.bu_ids.ids)]
                    bu_jobs = self.env['hr.job'].search(
                        [('business_unit_id', 'in', self.bu_ids.ids), '|', ('user_id', '=', self.env.user.id),
                         ('other_recruiters_ids', 'in', self.env.user.id)])
                domain.append(('job_id', 'in', bu_jobs.ids))
            else:
                if self.check_rec_manager == 'coordinator':
                    if self.recruiter_ids:
                        domain += [('create_uid', 'in', self.recruiter_ids.ids)]
                    bu_jobs = self.env['hr.job'].search(
                        ['|', ('business_unit_id', '=', self.env.user.business_unit_id.id),
                         ('business_unit_id', 'in', self.env.user.multi_business_unit_id.ids)])
                    domain.append(('job_id', 'in', bu_jobs.ids))

                if self.check_rec_manager == 'officer':
                    if self.recruiter_ids:
                        domain += ['|', ('create_uid', 'in', self.recruiter_ids.ids)]
                    rec_jobs = self.env['hr.job'].search(
                        ['|', ('user_id', '=', self.env.user.id), ('other_recruiters_ids', 'in', self.env.user.id)])
                    domain += [('job_id', 'in', rec_jobs.ids)]

                if self.check_rec_manager == 'manager':
                    if self.recruiter_ids:
                        domain += [('create_uid', 'in', self.recruiter_ids.ids)]

        applications = self.env['hr.applicant'].search(domain, order='create_date desc')
        if applications:
            no_records = False
        self.application_ids = [(6, 0, applications.ids)]

        if no_records:
            raise ValidationError(_("No record to display"))

        report = self.env.ref('recruitment_ads.action_report_interview_report_xlsx')
        return report.report_action(self)
