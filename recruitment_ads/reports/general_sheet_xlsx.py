from odoo import _, models
import re


class GeneralSheetXslx(models.AbstractModel):
    _name = 'report.recruitment_ads.report_general_sheet_xlsx'
    _inherit = 'report.recruitment_ads.abstract_report_xlsx'

    def _get_report_name(self):
        return _('General Sheet')

    def _get_report_sheets(self, report):
        sheets = []
        max_interviews_count = max(
            report.with_context({'active_test': False}).application_ids.mapped('count_done_interviews')) - 1
        sheets.append({
            'General Sheet': {
                0: {'header': _('Applicant Name'), 'field': 'partner_name', 'width': 20},
                1: {'header': _('Mobile'), 'field': 'partner_mobile', 'width': 20},
                2: {'header': _('Email'), 'field': 'email_from', 'width': 20},
                3: {'header': _('Yes/No'), 'field': 'cv_matched', 'width': 10, 'type': 'bool'},
                4: {'header': _('Source'), 'field': 'source_id', 'width': 10, 'type': 'many2one'},
                5: {'header': _('Business unit'), 'field': 'business_unit_id', 'width': 18, 'type': 'many2one'},
                6: {'header': _('Department'), 'field': 'department_id', 'width': 20, 'type': 'many2one'},
                7: {'header': _('Job Position'), 'field': 'job_id', 'width': 35, 'type': 'many2one'},

                8: {'header': _('Call Date'), 'field': 'call_date', 'width': 18, 'type': 'datetime'},
                9: {'header': _('Called by'), 'field': 'called_by', 'width': 18, 'type': 'many2one'},
                10: {'header': _('Call Result'), 'field': 'call_result', 'width': 18},
                11: {'header': _('Comment'), 'field': 'call_comment', 'width': 18},

                12: {'header': _('Interview Date 1'), 'field': 'interview_date', 'width': 18},
                13: {'header': _('Interviewers 1'), 'field': 'interviewers', 'width': 30, 'type': 'x2many'},
                14: {'header': _('Interview result 1'), 'field': 'interview_result', 'width': 20, },
                15: {'header': _('Comment 1'), 'field': 'interview_comment', 'width': 22},
            }
        })
        if max_interviews_count > 0:
            start = 16
            for i in range(max_interviews_count):
                sheets[0]['General Sheet'].update(
                    {
                        start: {'header': _('Interview Date ' + str(i + 2)), 'field': 'interview_date' + str(i + 1),
                                'width': 18},
                        start + 1: {'header': _('Interviewers ' + str(i + 2)), 'field': 'interviewers' + str(i + 1),
                                    'width': 30,
                                    'type': 'x2many'},
                        start + 2: {'header': _('Interview result ' + str(i + 2)),
                                    'field': 'interview_result' + str(i + 1),
                                    'width': 20, },
                        start + 3: {'header': _('Comment ' + str(i + 2)), 'field': 'interview_comment' + str(i + 1),
                                    'width': 22},
                    }
                )
                start = start + 4
        last_row = max(sheets[0]['General Sheet'])
        sheets[0]['General Sheet'].update(
            {
                last_row + 1: {'header': _('Offer Status'), 'field': 'offer_status', 'width': 22},
                last_row + 2: {'header': _('Offer Date'), 'field': 'offer_date', 'width': 22},
                last_row + 3: {'header': _('Hiring Date'), 'field': 'hiring_date', 'width': 22},
            }
        )
        return sheets

    def _generate_report_content(self, workbook, report):
        if report:
            self.write_array_header('General Sheet')
            for app_line in report.application_ids.sorted('create_date', reverse=True):
                self.write_line(GeneralSheetWrapper(app_line), 'General Sheet')


class GeneralSheetWrapper:
    def __init__(self, application):
        self.partner_name = application.partner_name
        self.partner_mobile = application.partner_mobile
        self.email_from = application.email_from
        self.cv_matched = application.cv_matched
        self.source_id = application.source_id
        self.business_unit_id = application.department_id.business_unit_id
        self.department_id = application.department_id
        self.job_id = application.job_id

        calls = self._get_activity('call', application).sorted('write_date', reverse=False)
        first_call = calls[0] if calls else False
        call_feedback = first_call.feedback if first_call else False
        self.call_date = first_call.write_date if first_call else False
        self.called_by = first_call.user_id if first_call else False
        self.call_result = first_call.call_result_id if first_call else False
        self.call_comment = re.sub(r"<.*?>", '', call_feedback if call_feedback else '')

        interviews = self._get_activity('interview', application).sorted('write_date', reverse=False)
        first_interview = interviews[0] if interviews else False
        interview_feedback = first_interview.feedback if first_interview else False
        self.interview_date = first_interview.calendar_event_id.display_corrected_start_date if first_interview else False
        self.interviewers = first_interview.calendar_event_id.partner_ids if first_interview else False
        self.interview_result = first_interview.interview_result if first_interview else False
        self.interview_comment = re.sub(r"<.*?>", '', interview_feedback if interview_feedback else '')
        for i in range(len(interviews)):
            if i == 0:
                continue
            setattr(self, 'interview_date' + str(i), interviews[i].calendar_event_id.display_corrected_start_date)
            setattr(self, 'interviewers' + str(i), interviews[i].calendar_event_id.partner_ids)
            setattr(self, 'interview_result' + str(i), interviews[i].interview_result)
            setattr(self, 'interview_comment' + str(i),
                    re.sub(r"<.*?>", '', interviews[i].feedback if interviews[i].feedback else ''))

        self.offer_status = application.offer_id.state
        self.offer_date = application.offer_id.issue_date
        self.hiring_date = application.offer_id.hiring_date

        self.env = application.env
        self._context = application._context

    def _get_activity(self, activity, data):
        """
        This function get all the activity lines from the mail.activity model
        :param activity: 'call', 'interview'
        :param data:
        :return:
        """
        if activity == 'call':
            activity_type = data.env.ref('mail.mail_activity_data_call')
        if activity == 'interview':
            activity_type = data.env.ref('recruitment_ads.mail_activity_type_data_interview')
        return data.with_context({'active_test': False}).activity_ids.filtered(
            lambda a: a.activity_type_id == activity_type and not a.active)