from odoo import api, fields, models,_
from odoo.exceptions import ValidationError

class RecruiterActivityReportWizard(models.TransientModel):
    """Recruiter Activity Report Wizard"""
    _name = "recruiter.activity.report.wizard"
    _inherit = 'abstract.rec.report.wizard'

    _description = "Recruiter Activity Report Wizard"
    @api.model
    def _get_current_login_user(self):
     return [self.env.user.id]

    recruiter_ids = fields.Many2many('res.users', string='Recruiter Responsible',default=_get_current_login_user  )

    cv_source = fields.Boolean('Cv Source')
    calls = fields.Boolean('Calls')
    interviews = fields.Boolean('Interviews')
    offer = fields.Boolean('Offered and Hired')

    application_ids = fields.Many2many('hr.applicant')
    call_ids = fields.Many2many('mail.activity','call_recruiter_report_rel','report_id','call_id',domain=[('active','=',False)])
    interview_ids = fields.Many2many('mail.activity','interview_recruiter_report_rel','report_id','interview_id',domain=[('active','=',False)])
    offer_ids = fields.Many2many('hr.offer', 'offer_recruiter_report_rel', 'report_id', 'offer_id')


    @api.multi
    def button_export_xlsx(self):
        self.ensure_one()
        if not (self.calls or self.cv_source or self.interviews or self.offer):
            raise ValidationError(_("Please Select at least one activity to export"))
        no_records = True
        if self.cv_source:
            domain = [
                ('create_date', '>=', self.date_from + ' 00:00:00'),
                ('create_date', '<=', self.date_to + ' 23:59:59'),
            ]
            if self.recruiter_ids:
                domain.append(('create_uid', 'in', self.recruiter_ids.ids))
            if self.job_ids:
                domain.append(('job_id', 'in', self.job_ids.ids))
            applications = self.env['hr.applicant'].search(domain, order='create_date desc')
            if applications:
                no_records = False
            self.application_ids = [(6,0,applications.ids)]

        if self.calls:
            domain = [
                ('write_date', '>=', self.date_from + ' 00:00:00'),
                ('write_date', '<=', self.date_to + ' 23:59:59'),
                ('active', '=', False),
                ('call_result_id', '!=', False),
                ('res_model', '=', 'hr.applicant'),
            ]
            if self.recruiter_ids:
                domain.append(('real_create_uid', 'in', self.recruiter_ids.ids))
            calls = self.env['mail.activity'].search(domain, order='write_date desc')
            if self.job_ids:
                calls = calls.filtered(lambda c: self.env['hr.applicant'].browse(c.res_id).job_id in self.job_ids)
            if calls:
                no_records = False
            self.call_ids = [(6,0,calls.ids)]

        if self.interviews:
            domain = [
                ('write_date', '>=', self.date_from + ' 00:00:00'),
                ('write_date', '<=', self.date_to + ' 23:59:59'),
                ('active', '=', False),
                ('activity_category', '=', 'interview'),
                ('res_model', '=', 'hr.applicant')
            ]
            if self.recruiter_ids:
                domain.append(('real_create_uid', 'in', self.recruiter_ids.ids))
            interviews = self.env['mail.activity'].search(domain, order='write_date desc')
            if self.job_ids:
                interviews = interviews.filtered(lambda c: c.calendar_event_id.hr_applicant_id.job_id in self.job_ids)
            if interviews:
                no_records = False
            self.interview_ids = [(6,0,interviews.ids)]

        if self.offer:
            domain = [
                ('issue_date', '>=', self.date_from),
                ('issue_date', '<=', self.date_to),
            ]
            if self.recruiter_ids:
                domain.append(('create_uid', 'in', self.recruiter_ids.ids))
            if self.job_ids:
                domain.append(('job_id', 'in', self.job_ids.ids))
            offer = self.env['hr.offer'].search(domain, order='issue_date desc')
            if offer:
                no_records = False
            self.offer_ids = [(6, 0, offer.ids)]

        if no_records:
            raise ValidationError(_("No record to display"))

        report = self.env.ref('recruitment_ads.action_report_recruiter_activity_xlsx')
        return report.report_action(self)
