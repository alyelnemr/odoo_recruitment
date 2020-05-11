from odoo import _, models
import re

class ComplianceReportXslx(models.AbstractModel):
    _name = 'report.recruitment_ads.compliance_report_xlsx'
    _inherit = 'report.recruitment_ads.abstract_report_xlsx'

    def _get_report_name(self):
        return _('Compliance Report')

    def _get_report_sheets(self,report):
        sheets = []
        sheets.append({
            'Compliance Report': {
                0: {'header': _('Recruiter Responsible'), 'field': 'user_id', 'width': 20},
                1: {'header': _('Recruiter BU'), 'field': 'user_bu', 'width': 20, 'type': 'many2one'},
                2: {'header': _('Total Applications'), 'field': 'total_application', 'width': 20},
                3: {'header': _('App/Cvs'), 'field': 'no_cv', 'width': 20},
                4: {'header': _('App/Assessment'), 'field': 'no_assess', 'width': 20},
                5: {'header': _('Total Calls'), 'field': 'no_calls', 'width': 20},
                6: {'header': _('Done Calls'), 'field': 'done_call', 'width': 20},
                7: {'header': _('Total Interviews'), 'field': 'total_interview', 'width': 20},
                8: {'header': _('Done Interviews'), 'field': 'done_interview', 'width': 20},
                9: {'header': _('Total Offers'), 'field': 'total_offers', 'width': 20},
                10: {'header': _('Hired'), 'field': 'no_hire', 'width': 20}

            }
        })
        return sheets

    def _generate_report_content(self, workbook, report):
        if report:
            self.write_array_header('Compliance Report')
            domain = [('create_date', '>=', report.date_from + ' 00:00:00'),
                      ('create_date', '<=', report.date_to + ' 23:59:59'),
                      ]

            app_domain = []
            offers_domain = []
            if report.bu_ids:
                jobs=self.env['hr.job'].search([('business_unit_id', 'in', report.bu_ids.ids)])
                applications = self.env['hr.applicant'].search([('job_id', 'in', jobs.ids)])
                app_domain.append(('job_id','in',jobs.ids),)
                offers_domain.append(('business_unit_id','in',report.bu_ids.ids),)

            app_domain.extend(domain)
            offers_domain.extend(domain)
            for recruiter in report.recruiter_ids.ids:
                app_domain.append(('create_uid','=',recruiter),)
                offers_domain.append(('create_uid', '=', recruiter), )
                total_app = self.env['hr.applicant'].search(app_domain)
                attachments = self.env['ir.attachment'].search([('res_model', '=', 'hr.applicant'), ('res_id', 'in', total_app.ids)])
                cvs = attachments.filtered(lambda x: x.attachment_type == 'cv')
                asses = attachments.filtered(lambda x: x.attachment_type == 'assessment')
                if report.bu_ids:
                    query_total_calls = 'select * from mail_activity where create_date >= %s and create_date <= %s and res_model = %s and  activity_type_id in (%s, %s, %s) and real_create_uid = %s and res_id in %s'
                    self.env.cr.execute(query_total_calls,( report.date_from + ' 00:00:00', report.date_to + ' 23:59:59','hr.applicant',2, 6, 7,recruiter, tuple(applications.ids)))
                    total_calls = self.env.cr.dictfetchall()
                    query_done_calls = 'select * from mail_activity where create_date >= %s and create_date <= %s and res_model = %s and  activity_type_id in (%s, %s, %s) and real_create_uid = %s and  call_result_id is not null and res_id in %s'
                    self.env.cr.execute(query_done_calls,(report.date_from + ' 00:00:00', report.date_to + ' 23:59:59', 'hr.applicant', 2, 6, 7, recruiter,tuple(applications.ids)))
                    no_done_calls = self.env.cr.dictfetchall()
                    query_total_interviews = 'select * from mail_activity where create_date >= %s and create_date <= %s and res_model = %s and  activity_type_id = %s and real_create_uid = %s and res_id in %s'
                    self.env.cr.execute(query_total_interviews, (
                    report.date_from + ' 00:00:00', report.date_to + ' 23:59:59', 'hr.applicant',5, recruiter,tuple(applications.ids)))
                    interviews = self.env.cr.dictfetchall()
                    query_done_interviews = 'select * from mail_activity where create_date >= %s and create_date <= %s and res_model = %s and  activity_type_id = %s and real_create_uid = %s and  interview_result is not null and res_id in %s'
                    self.env.cr.execute(query_done_interviews, (
                    report.date_from + ' 00:00:00', report.date_to + ' 23:59:59', 'hr.applicant',5, recruiter,tuple(applications.ids)))
                    done_interviews = self.env.cr.dictfetchall()
                else:
                    query_total_calls = 'select * from mail_activity where create_date >= %s and create_date <= %s and res_model = %s and  activity_type_id in (%s, %s, %s) and real_create_uid = %s'
                    self.env.cr.execute(query_total_calls,( report.date_from + ' 00:00:00', report.date_to + ' 23:59:59','hr.applicant',2, 6, 7,recruiter))
                    total_calls = self.env.cr.dictfetchall()
                    query_done_calls = 'select * from mail_activity where create_date >= %s and create_date <= %s and res_model = %s and  activity_type_id in (%s, %s, %s) and real_create_uid = %s and  call_result_id is not null'
                    self.env.cr.execute(query_done_calls,(report.date_from + ' 00:00:00', report.date_to + ' 23:59:59', 'hr.applicant', 2, 6, 7, recruiter))
                    no_done_calls = self.env.cr.dictfetchall()
                    query_total_interviews = 'select * from mail_activity where create_date >= %s and create_date <= %s and res_model = %s and  activity_type_id = %s and real_create_uid = %s'
                    self.env.cr.execute(query_total_interviews, (
                    report.date_from + ' 00:00:00', report.date_to + ' 23:59:59', 'hr.applicant',5, recruiter))
                    interviews = self.env.cr.dictfetchall()
                    query_done_interviews = 'select * from mail_activity where create_date >= %s and create_date <= %s and res_model = %s and  activity_type_id = %s and real_create_uid = %s and  interview_result is not null'
                    self.env.cr.execute(query_done_interviews, (
                    report.date_from + ' 00:00:00', report.date_to + ' 23:59:59', 'hr.applicant',5, recruiter))
                    done_interviews = self.env.cr.dictfetchall()
                offers = self.env['hr.offer'].search(offers_domain)
                hired = offers.filtered(lambda x: x.state == 'hired')
                del app_domain[-1]
                del offers_domain[-1]
                total_app = str(len(total_app))
                cvs_no = str(len(cvs))
                ass_no = str(len(asses))
                total_calls = str(len(total_calls))
                no_done_calls = str(len(no_done_calls))
                interviews = str(len(interviews))
                done_interviews = str(len(done_interviews))
                offers = str(len(offers))
                hired = str(len(hired))
                recruiter_obj = self.env['res.users'].browse(recruiter)
                self.write_line(
                    ComplianceWrapper(total_app, cvs_no, ass_no, recruiter_obj, total_calls, no_done_calls, interviews,done_interviews,offers, hired),'Compliance Report')
            report.recruiter_ids = False





class ComplianceWrapper:
    def __init__(self,total_app,cvs_no,ass_no,recruiter,total_calls,done_calls,no_interviews,done_interviews,offers,hired):
        self.user_id = recruiter.name
        self.user_bu = recruiter.business_unit_id
        self.total_application= total_app
        self.no_cv=cvs_no
        self.no_assess=ass_no
        self.no_calls = total_calls
        self.done_call=done_calls
        self.total_interview = no_interviews
        self.done_interview = done_interviews
        self.total_offers = offers
        self.no_hire = hired