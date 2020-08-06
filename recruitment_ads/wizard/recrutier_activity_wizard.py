from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RecruiterActivityReportWizard(models.TransientModel):
    """Recruiter Activity Report Wizard"""
    _name = "recruiter.activity.report.wizard"
    _inherit = 'abstract.rec.report.wizard'

    _description = "Recruiter Activity Report Wizard"
    # @api.model
    # def _get_current_login_user(self):
    #  return [self.env.user.id]

    # recruiter_ids = fields.Many2many('res.users', string='Recruiter Responsible')

    cv_source = fields.Boolean('Cv Source')
    calls = fields.Boolean('Calls')
    interviews = fields.Boolean('Interviews')
    offer = fields.Boolean('Offered')
    hired = fields.Boolean('Hired')

    # application_ids = fields.Many2many('hr.applicant')
    call_ids = fields.Many2many('mail.activity', 'call_recruiter_report_rel', 'report_id', 'call_id',
                                domain=[('active', '=', False)])
    interview_ids = fields.Many2many('mail.activity', 'interview_recruiter_report_rel', 'report_id', 'interview_id',
                                     domain=[('active', '=', False)])
    offer_ids = fields.Many2many('hr.offer', 'offer_recruiter_report_rel', 'report_id', 'offer_id')
    hired_ids = fields.Many2many('hr.offer', 'hired_recruiter_report_rel', 'report_id', 'offer_id')

    @api.multi
    def button_export_xlsx(self):
        self.ensure_one()
        if not (self.calls or self.cv_source or self.interviews or self.offer or self.hired):
            raise ValidationError(_("Please Select at least one activity to export"))
        no_records = True
        if self.cv_source:
            if self.cv_source:
                domain = [
                    ('create_date', '>=', self.date_from + ' 00:00:00'),
                    ('create_date', '<=', self.date_to + ' 23:59:59'),
                ]
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

                if applications:
                    no_records = False
                self.application_ids = [(6, 0, applications.ids)]

        if self.calls:
            domain = [
                ('write_date', '>=', self.date_from + ' 00:00:00'),
                ('write_date', '<=', self.date_to + ' 23:59:59'),
                ('active', '=', False),
                ('call_result_id', '!=', False),
                ('res_model', '=', 'hr.applicant'),
            ]
            if self.check_rec_manager == 'coordinator':
                bu_jobs = self.env['hr.job'].search(
                    ['|', ('business_unit_id', '=', self.env.user.business_unit_id.id),
                     ('business_unit_id', 'in', self.env.user.multi_business_unit_id.ids)])
                applications_id = self.env['hr.applicant'].search([('job_id', 'in', bu_jobs.ids)])
                domain.append(('res_id', 'in', applications_id.ids), )
            if self.recruiter_ids:
                domain.append(('real_create_uid', 'in', self.recruiter_ids.ids))
            else:
                if self.check_rec_manager == 'coordinator':
                    recruiters = self.env['res.users'].search(
                        ['|', '|', '|', ('business_unit_id', '=', self.env.user.business_unit_id.id),
                         ('business_unit_id', 'in', self.env.user.multi_business_unit_id.ids),
                         ('multi_business_unit_id', 'in', self.env.user.business_unit_id.id),
                         ('multi_business_unit_id', 'in', self.env.user.multi_business_unit_id.ids)])
                    domain += [('real_create_uid', 'in', recruiters.ids)]
            calls = self.env['mail.activity'].search(domain, order='write_date desc')

            applications_on_jobs = self.env['hr.applicant'].search([
                ('id', 'in', calls.mapped('res_id')),
                ('job_id', '!=', False),
            ])
            applications_ids = list(set(calls.mapped('res_id')) & set(applications_on_jobs.ids))
            calls = self.env['mail.activity'].search(domain + [('res_id', 'in', applications_ids)],
                                                     order='write_date desc')

            if self.job_ids:
                calls = calls.filtered(lambda c: self.env['hr.applicant'].browse(c.res_id).job_id in self.job_ids)
            else:
                if self.bu_ids:
                    bu_jobs = self.env['hr.job'].search([('business_unit_id', 'in', self.bu_ids.ids)])
                    calls = calls.filtered(lambda c: self.env['hr.applicant'].browse(c.res_id).job_id in bu_jobs)
                else:
                    if self.check_rec_manager == 'coordinator':
                        # bu_jobs = self.env['hr.job'].search(
                        #     ['|', ('business_unit_id', '=', self.env.user.business_unit_id.id),
                        #      ('business_unit_id', 'in', self.env.user.multi_business_unit_id.ids)])
                        calls = calls.filtered(lambda c: self.env['hr.applicant'].browse(c.res_id).job_id in bu_jobs)

            if calls:
                no_records = False
            self.call_ids = [(6, 0, calls.ids)]

        if self.interviews:
            domain = [
                ('write_date', '>=', self.date_from + ' 00:00:00'),
                ('write_date', '<=', self.date_to + ' 23:59:59'),
                ('active', '=', False),
                ('activity_category', '=', 'interview'),
                ('res_model', '=', 'hr.applicant')
            ]
            if self.check_rec_manager == 'coordinator':
                bu_jobs = self.env['hr.job'].search(
                    ['|', ('business_unit_id', '=', self.env.user.business_unit_id.id),
                     ('business_unit_id', 'in', self.env.user.multi_business_unit_id.ids)])
                applications_id = self.env['hr.applicant'].search([('job_id', 'in', bu_jobs.ids)])
                domain.append(('res_id', 'in', applications_id.ids), )
            if self.recruiter_ids:
                domain.append(('real_create_uid', 'in', self.recruiter_ids.ids))
            else:
                if self.check_rec_manager == 'coordinator':
                    recruiters = self.env['res.users'].search(
                        ['|', '|', '|', ('business_unit_id', '=', self.env.user.business_unit_id.id),
                         ('business_unit_id', 'in', self.env.user.multi_business_unit_id.ids),
                         ('multi_business_unit_id', 'in', self.env.user.business_unit_id.id),
                         ('multi_business_unit_id', 'in', self.env.user.multi_business_unit_id.ids)])
                    domain += [('real_create_uid', 'in', recruiters.ids)]
            interviews = self.env['mail.activity'].search(domain, order='write_date desc')
            if self.job_ids:
                interviews = interviews.filtered(lambda c: c.calendar_event_id.hr_applicant_id.job_id in self.job_ids)
            else:
                if self.bu_ids:
                    bu_jobs = self.env['hr.job'].search([('business_unit_id', 'in', self.bu_ids.ids)])
                    interviews = interviews.filtered(lambda c: c.calendar_event_id.hr_applicant_id.job_id in bu_jobs)
                else:
                    if self.check_rec_manager == 'coordinator':
                        # bu_jobs = self.env['hr.job'].search(
                        #     ['|', ('business_unit_id', '=', self.env.user.business_unit_id.id),
                        #      ('business_unit_id', 'in', self.env.user.multi_business_unit_id.ids)])
                        interviews = interviews.filtered(
                            lambda c: c.calendar_event_id.hr_applicant_id.job_id in bu_jobs)
            if interviews:
                no_records = False
            self.interview_ids = [(6, 0, interviews.ids)]

        if self.offer:
            domain = [
                ('issue_date', '>=', self.date_from),
                ('issue_date', '<=', self.date_to),
            ]
            if self.recruiter_ids:
                domain.append(('create_uid', 'in', self.recruiter_ids.ids))
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

            offer = self.env['hr.offer'].search(domain, order='issue_date desc')
            if offer:
                no_records = False
            self.offer_ids = [(6, 0, offer.ids)]

        if self.hired:
            domain = [
                ('hiring_date', '>=', self.date_from),
                ('hiring_date', '<=', self.date_to),
            ]
            if self.recruiter_ids:
                domain.append(('create_uid', 'in', self.recruiter_ids.ids))
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

            domain.append(('state', '=', 'hired'))
            hired = self.env['hr.offer'].search(domain, order='issue_date desc')
            if hired:
                no_records = False
            self.hired_ids = [(6, 0, hired.ids)]

        if no_records:
            raise ValidationError(_("No record to display"))

        report = self.env.ref('recruitment_ads.action_report_recruiter_activity_xlsx')
        return report.report_action(self)
