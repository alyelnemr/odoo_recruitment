from odoo import _, models
from odoo.exceptions import ValidationError


class RecActivityXslx(models.AbstractModel):
    _name = 'report.recruitment_ads.report_recruiter_activity_xlsx'
    _inherit = 'report.recruitment_ads.abstract_report_xlsx'

    def _get_report_name(self):
        return _('Recruiter Activity')

    def _get_report_sheets(self, report):
        sheets = []
        if report.cv_source:
            sheets.append({
                'CV Source': {
                    0: {'header': _('Recruiter Responsible'), 'field': 'create_uid', 'width': 20, 'type': 'many2one'},
                    1: {'header': _('Applicant Name'), 'field': 'partner_name', 'width': 20},
                    2: {'header': _('Date'), 'field': 'create_date', 'width': 18, 'type': 'datetime'},
                    3: {'header': _('CV Source'), 'field': 'source_id', 'width': 10, 'type': 'many2one'},
                    4: {'header': _('Department'), 'field': 'department_id', 'width': 20, 'type': 'many2one'},
                    5: {'header': _('Job Position'), 'field': 'job_id', 'width': 22, 'type': 'many2one'},
                }
            })
        if report.calls:
            sheets.append({
                'Calls': {
                    0: {'header': _('Recruiter Responsible'), 'field': 'real_create_uid', 'width': 20, 'type': 'many2one'},
                    1: {'header': _('Applicant Name'), 'field': 'partner_name', 'width': 20},
                    2: {'header': _('Call Date'), 'field': 'write_date', 'width': 18, 'type': 'datetime'},
                    3: {'header': _('Called By'), 'field': 'user_id', 'width': 10, 'type': 'many2one'},
                    4: {'header': _('Call result'), 'field': 'call_result_id', 'width': 20, },
                    5: {'header': _('Comment'), 'field': 'feedback', 'width': 22},
                    6: {'header': _('Department'), 'field': 'department_id', 'width': 22, 'type': 'many2one'},
                    7: {'header': _('Job Description'), 'field': 'job_id', 'width': 22, 'type': 'many2one'},
                }
            })
        if report.interviews:
            sheets.append({
                'Interviews': {
                    0: {'header': _('Recruiter Responsible'), 'field': 'real_create_uid', 'width': 20, 'type': 'many2one'},
                    1: {'header': _('Applicant Name'), 'field': 'partner_name', 'width': 20},
                    2: {'header': _('Interview Date'), 'field': 'start_date', 'width': 18, 'type': 'datetime'},
                    3: {'header': _('Interviewers'), 'field': 'partner_ids', 'width': 30, 'type': 'x2many'},
                    4: {'header': _('Interview result'), 'field': 'interview_result', 'width': 20, },
                    5: {'header': _('Comment'), 'field': 'feedback', 'width': 22},
                    6: {'header': _('Department'), 'field': 'department_id', 'width': 22, 'type': 'many2one'},
                    7: {'header': _('Job Description'), 'field': 'job_id', 'width': 22, 'type': 'many2one'},
                }
            })
        return sheets

    def _generate_report_content(self, workbook, report):
        if report.cv_source:
            self.write_array_header('CV Source')
            for app_line in report.application_ids.sorted('create_date',reverse=True):
                self.write_line(app_line, 'CV Source')

        if report.calls:
            self.write_array_header('Calls')
            for call in report.call_ids.sorted('write_date',reverse=True):
                self.write_line(CallLineWrapper(call), 'Calls')

        if report.interviews:
            self.write_array_header('Interviews')
            for interview in report.interview_ids.sorted('write_date',reverse=True):
                self.write_line(InterviewLineWrapper(interview), 'Interviews')

class CallLineWrapper:
    def __init__(self, call):
        applicant = call.env[call.res_model].browse(call.res_id)
        self.real_create_uid = call.real_create_uid
        self.partner_name = applicant.partner_name
        self.write_date = call.write_date
        self.user_id = call.user_id
        self.call_result_id = call.call_result_id
        self.feedback = call.feedback
        self.department_id = applicant.department_id
        self.job_id = applicant.job_id
        self._context = call._context
        self.env = call.env


class InterviewLineWrapper:
    def __init__(self, interview):
        applicant = interview.env[interview.res_model].browse(interview.res_id)
        self.real_create_uid = interview.real_create_uid
        self.partner_name = applicant.partner_name
        self.start_date = interview.calendar_event_id.start
        self.partner_ids = interview.calendar_event_id.partner_ids
        self.interview_result = interview.interview_result
        self.feedback = interview.feedback
        self.department_id = applicant.department_id
        self.job_id = applicant.job_id
        self._context = interview._context
        self.env = interview.env
