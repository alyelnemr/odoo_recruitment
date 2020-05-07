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

            activity_calls = [('active', '=', False),
                               ('res_model', '=', 'hr.applicant'),
                              ('activity_type_id', 'in' , (2, 6, 7))
                               ]

            activity_interviews = [('active', '=', False),
                                   ('res_model', '=', 'hr.applicant'),
                                   ('activity_type_id', '=' , 5),
                               ]
            app_domain = []
            offers_domain = []
            if report.bu_ids:
                jobs=self.env['hr.job'].search([('business_unit_id', 'in', report.bu_ids.ids)])
                applications = self.env['hr.applicant'].search([('job_id', 'in', jobs.ids)])
                app_domain.append(('job_id','in',jobs.ids),)
                offers_domain.append(('business_unit_id','in',report.bu_ids.ids),)
                activity_interviews.append(('res_id','in',applications.ids),)
                activity_calls.append(('res_id','in',applications.ids),)

            app_domain.extend(domain)
            activity_calls.extend(domain)
            activity_interviews.extend(domain)
            offers_domain.extend(domain)
            for recruiter in report.recruiter_ids.ids:
                app_domain.append(('create_uid','=',recruiter),)
                activity_calls.append(('real_create_uid', '=', recruiter), )
                activity_interviews.append(('real_create_uid', '=', recruiter), )
                offers_domain.append(('create_uid', '=', recruiter), )
                total_app = self.env['hr.applicant'].search(app_domain)
                attachments = self.env['ir.attachment'].search([('res_model', '=', 'hr.applicant'), ('res_id', 'in', total_app.ids)])
                cvs = attachments.filtered(lambda x: x.attachment_type == 'cv')
                asses = attachments.filtered(lambda x: x.attachment_type == 'assessment')
                total_calls = self.env['mail.activity'].search(activity_calls)
                no_done_calls = total_calls.filtered(lambda x: x.call_result_id != False)
                interviews = self.env['mail.activity'].search(activity_interviews)
                done_interviews = interviews.filtered(lambda x: x.interview_result != False)
                offers = self.env['hr.offer'].search(offers_domain)
                hired = offers.filtered(lambda x: x.state == 'hired')
                del app_domain[-1]
                del activity_calls[-1]
                del activity_interviews[-1]
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