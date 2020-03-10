# coding=utf-8
import re

# noinspection PyProtectedMember
from odoo import _, models

from .general_sheet_xlsx import GeneralSheetWrapper


# noinspection PyMethodMayBeStatic
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
                    1: {'header': _('Recruiter BU'), 'field': 'generated_by_bu_id', 'width': 20, 'type': 'many2one'},
                    2: {'header': _('Application Code'), 'field': 'application_code', 'width': 20},
                    3: {'header': _('Applicant Name'), 'field': 'partner_name', 'width': 20},
                    4: {'header': _('Email'), 'field': 'email_from', 'width': 20},
                    5: {'header': _('Phone'), 'field': 'partner_phone', 'width': 20},
                    6: {'header': _('Mobile'), 'field': 'partner_mobile', 'width': 20},
                    7: {'header': _('CV Source'), 'field': 'source_id', 'width': 10, 'type': 'many2one'},
                    8: {'header': _('Date'), 'field': 'create_date', 'width': 18, 'type': 'datetime'},
                    9: {'header': _('Business unit'), 'field': 'business_unit_id', 'width': 18, 'type': 'many2one'},
                    10: {'header': _('Department'), 'field': 'department_id', 'width': 20, 'type': 'many2one'},
                }
            })

            # getting the department_id of each job of the application.
            if report.job_ids:
                departments = list(set(report.job_ids.mapped('department_id')))
            else:
                departments = report.application_ids.sorted('create_date', reverse=True).mapped('department_id')
            max_sections_count = 0
            for department in departments:
                if department.parent_id:
                    department_list = []
                    while department:
                        department_list.append(department.id)
                        department = department.parent_id
                    if len(department_list) > max_sections_count:
                        max_sections_count = len(department_list)
            start = 10
            if max_sections_count >= 1:
                sheets[0]['CV Source'].update({
                    start + 1: {'header': _('Section'),
                                'field': 'section_id',
                                'width': 20,
                                'type': 'many2one', }})
                start = start + 1
                # start = 11
                # for i in range(max_sections_count):
                #     if i <= 1:
                #         continue
                #     sheets[0]['CV Source'].update({
                #         start + i: {'header': _('Section' + str(i)),
                #                     'field': 'section_id' + str(i),
                #                     'width': 20,
                #                     'type': 'many2one', }})
                # start = start + i

            sheets[0]['CV Source'].update({
                start + 1: {'header': _('Job Position'), 'field': 'job_id', 'width': 35, 'type': 'many2one'},
                start + 2: {'header': _('Expected Salary'), 'field': 'salary_expected', 'width': 18, 'type': 'amount'},
                start + 3: {'header': _('Current  Salary'), 'field': 'salary_current', 'width': 18, 'type': 'amount'},
                start + 4: {'header': _('Matched'), 'field': 'cv_matched', 'width': 10, 'type': 'bool'},
                start + 5: {'header': _('Reason of Rejection'), 'field': 'reason_of_rejection', 'width': 10, },
            })
        if report.calls:
            sheets.append({
                'Calls': {
                    0: {'header': _('Recruiter Responsible'), 'field': 'real_create_uid', 'width': 20,
                        'type': 'many2one'},
                    1: {'header': _('Recruiter BU'), 'field': 'generated_by_bu_id', 'width': 20, 'type': 'many2one'},
                    2: {'header': _('Application Code'), 'field': 'application_code', 'width': 20},
                    3: {'header': _('Applicant Name'), 'field': 'partner_name', 'width': 20},
                    4: {'header': _('Email'), 'field': 'email_from', 'width': 20},
                    5: {'header': _('Phone'), 'field': 'partner_phone', 'width': 20},
                    6: {'header': _('Mobile'), 'field': 'partner_mobile', 'width': 20},
                    7: {'header': _('Call Date'), 'field': 'write_date', 'width': 18, 'type': 'datetime'},
                    8: {'header': _('Called By'), 'field': 'user_id', 'width': 20, 'type': 'many2one'},
                    9: {'header': _('Call result'), 'field': 'call_result_id', 'width': 20, },
                    10: {'header': _('Comment'), 'field': 'feedback', 'width': 22},
                    11: {'header': _('Business unit'), 'field': 'business_unit_id', 'width': 18, 'type': 'many2one'},
                    12: {'header': _('Department'), 'field': 'department_id', 'width': 22, 'type': 'many2one'},
                }
            })

            # getting the department_id of each job of the application.
            if report.job_ids:
                departments = list(set(report.job_ids.mapped('department_id')))
            else:
                departments = report.application_ids.sorted('create_date', reverse=True).mapped('department_id')
            max_sections_count = 0
            for department in departments:
                if department.parent_id:
                    department_list = []
                    while department:
                        department_list.append(department.id)
                        department = department.parent_id
                    if len(department_list) > max_sections_count:
                        max_sections_count = len(department_list)
            start = 12
            if not report.cv_source:
                sheet= sheets[0]['Calls']
            else:
                sheet = sheets[1]['Calls']
            if max_sections_count >= 1:
                sheet.update({
                    start + 1: {'header': _('Section'),
                                'field': 'section_id',
                                'width': 20,
                                'type': 'many2one', }})
                start = start + 1
                # start = 11
                # for i in range(max_sections_count):
                #     if i <= 1:
                #         continue
                #     sheets[1]['Calls'].update({
                #         start + i: {'header': _('Section' + str(i)),
                #                     'field': 'section_id' + str(i),
                #                     'width': 20,
                #                     'type': 'many2one', }})
                # start = start + i
            sheet.update({
                start + 1: {'header': _('Job position'), 'field': 'job_id', 'width': 35, 'type': 'many2one'},
                start + 2: {'header': _('Expected Salary'), 'field': 'salary_expected', 'width': 18, 'type': 'amount'},
                start + 3: {'header': _('Current  Salary'), 'field': 'salary_current', 'width': 18, 'type': 'amount'},
                start + 4: {'header': _('Matched'), 'field': 'cv_matched', 'width': 10, 'type': 'bool'},
            })
        if report.interviews:
            applications = self.env['hr.applicant'].browse(list(set(report.interview_ids.mapped('res_id'))))
            sheets.append({
                'Interviews': {
                    0: {'header': _('Recruiter Responsible'), 'field': 'real_create_uid', 'width': 20,
                        'type': 'many2one'},
                    1: {'header': _('Recruiter BU'), 'field': 'generated_by_bu_id', 'width': 20, 'type': 'many2one'},
                    2: {'header': _('Application Code'), 'field': 'application_code', 'width': 20},
                    3: {'header': _('Applicant Name'), 'field': 'partner_name', 'width': 20},
                    4: {'header': _('Email'), 'field': 'email_from', 'width': 20},
                    5: {'header': _('Phone'), 'field': 'partner_phone', 'width': 20},
                    6: {'header': _('Mobile'), 'field': 'partner_mobile', 'width': 20},
                    7: {'header': _('Business unit'), 'field': 'business_unit_id', 'width': 18, 'type': 'many2one'},
                    8: {'header': _('Department'), 'field': 'department_id', 'width': 22, 'type': 'many2one'},
                }
            })

            # getting the department_id of each job of the application.
            if report.job_ids:
                departments = list(set(report.job_ids.mapped('department_id')))
            else:
                departments = report.application_ids.sorted('create_date', reverse=True).mapped('department_id')
            max_sections_count = 0
            for department in departments:
                if department.parent_id:
                    department_list = []
                    while department:
                        department_list.append(department.id)
                        department = department.parent_id
                    if len(department_list) > max_sections_count:
                        max_sections_count = len(department_list)
            start = 7
            if not report.calls and not report.cv_source:
                sheet= sheets[0]['Interviews']
            if (not report.calls and  report.cv_source) or (report.calls and  not report.cv_source):
                sheet= sheets[1]['Interviews']
            if  report.calls and  report.cv_source:
                sheet= sheets[2]['Interviews']

            if max_sections_count >= 1:
                sheet.update({
                    start + 1: {'header': _('Section'),
                                'field': 'section_id',
                                'width': 20,
                                'type': 'many2one', }})
                start = start + 1
                # start = 11
                # for i in range(max_sections_count):
                #     if i <= 1:
                #         continue
                #     sheets[2]['Interviews'].update({
                #         start + i: {'header': _('Section' + str(i)),
                #                     'field': 'section_id' + str(i),
                #                     'width': 20,
                #                     'type': 'many2one', }})
                # start = start + i
            sheet.update({
                    start + 1: {'header': _('Job position'), 'field': 'job_id', 'width': 35, 'type': 'many2one'},
                    start + 2: {'header': _('Expected Salary'), 'field': 'salary_expected', 'width': 18, 'type': 'amount'},
                    start + 3: {'header': _('Current  Salary'), 'field': 'salary_current', 'width': 18, 'type': 'amount'},
                    start + 4: {'header': _('Matched'), 'field': 'cv_matched', 'width': 10, 'type': 'bool'},
                    start + 5: {'header': _('Interview date 1'), 'field': 'interview_date', 'width': 18},
                    start + 6: {'header': _('Interviewers 1'), 'field': 'interviewers', 'width': 30, 'type': 'x2many'},
                    start + 7: {'header': _('Interviewer type 1'), 'field': 'interview_type_id', 'width': 30,
                         'type': 'many2one'},
                    start + 8: {'header': _('Interview result 1'), 'field': 'interview_result', 'width': 20, },
                    start + 9: {'header': _('Comment 1'), 'field': 'interview_comment', 'width': 22},
            })
            if applications:
                max_interviews_count = max(
                    applications.with_context({'active_test': False}).mapped('count_done_interviews')) - 1
                if max_interviews_count > 0:
                    if max_sections_count:
                        start = 18
                    else:
                        start = 17
                    for i in range(max_interviews_count):
                        sheets[-1]['Interviews'].update(
                            {
                                start: {'header': _('Interview date ' + str(i + 2)),
                                        'field': 'interview_date' + str(i + 1),
                                        'width': 18},
                                start + 1: {'header': _('Interviewers ' + str(i + 2)),
                                            'field': 'interviewers' + str(i + 1),
                                            'width': 30,
                                            'type': 'x2many'},
                                start + 2: {'header': _('Interview type ' + str(i + 2)),
                                            'field': 'interview_type_id' + str(i + 1),
                                            'width': 20, 'type': 'many2one'},
                                start + 3: {'header': _('Interview result ' + str(i + 2)),
                                            'field': 'interview_result' + str(i + 1),
                                            'width': 20, },
                                start + 4: {'header': _('Comment ' + str(i + 2)),
                                            'field': 'interview_comment' + str(i + 1),
                                            'width': 22},
                            }
                        )
                        start = start + 5
        if report.offer:
            sheets.append({
                'Offers and Hired': {
                    0: {'header': _('Application Code'), 'field': 'application_code', 'width': 20},
                    1: {'header': _('Candidate Name'), 'field': 'applicant_name', 'width': 20},
                    2: {'header': _('Email'), 'field': 'email_from', 'width': 20},
                    3: {'header': _('Mobile'), 'field': 'partner_mobile', 'width': 20},
                    4: {'header': _('Recruiter'), 'field': 'create_uid', 'width': 20, 'type': 'many2one'},
                    5: {'header': _('Business unit'), 'field': 'business_unit_id', 'width': 20, 'type': 'many2one'},
                    6: {'header': _('Department'), 'field': 'department_id', 'width': 20, 'type': 'many2one'},
                }
            })

            # getting the department_id of each job of the application.
            if report.job_ids:
                departments = list(set(report.job_ids.mapped('department_id')))
            else:
                departments = report.application_ids.sorted('create_date', reverse=True).mapped('department_id')
            max_sections_count = 0
            for department in departments:
                if department.parent_id:
                    department_list = []
                    while department:
                        department_list.append(department.id)
                        department = department.parent_id
                    if len(department_list) > max_sections_count:
                        max_sections_count = len(department_list)
            start = 6
            if not report.calls and not report.cv_source and not report.interviews:
                sheet= sheets[0]['Offers and Hired']

            if  report.calls and  report.cv_source and report.interviews:
                sheet= sheets[3]['Offers and Hired']

            if (not report.calls and  report.cv_source and report.interviews) or(report.calls and not report.cv_source and report.interviews) or (report.calls and report.cv_source and not report.interviews):
                sheet= sheets[2]['Offers and Hired']
            if (not report.calls and not report.cv_source and report.interviews) or (report.calls and not report.cv_source and not report.interviews) or(not report.calls and  report.cv_source and not report.interviews):
                sheet = sheets[1]['Offers and Hired']

            if max_sections_count >= 1:
                sheet.update({
                    start + 1: {'header': _('Section'),
                                'field': 'section_id',
                                'width': 20,
                                'type': 'many2one', }})
                start = start + 1
                # start = 11
                # for i in range(max_sections_count):
                #     if i <= 1:
                #         continue
                #     sheets[3]['Offers and Hired'].update({
                #         start + i: {'header': _('Section' + str(i)),
                #                     'field': 'section_id' + str(i),
                #                     'width': 20,
                #                     'type': 'many2one', }})
                # start = start + i
            sheet.update({
                    start + 1: {'header': _('Job position'), 'field': 'job_id', 'width': 20, 'type': 'many2one'},
                    start + 2: {'header': _('Issue Date'), 'field': 'issue_date', 'width': 20},
                    start + 3: {'header': _('Total Salary'), 'field': 'total_salary', 'width': 20, 'type': 'amount'},
                    start + 4: {'header': _('Total Package'), 'field': 'total_package', 'width': 20, 'type': 'amount'},
                    start + 5: {'header': _('Hiring Status  '), 'field': 'state', 'width': 20},
                    start + 6: {'header': _('Hiring Date'), 'field': 'hiring_date', 'width': 20},
                    start + 7: {'header': _('Comments'), 'field': 'comment', 'width': 40},
                    start + 8: {'header': _('Offer Type'), 'field': 'offer_type', 'width': 40},
                    start + 9: {'header': _('Generated By'), 'field': 'generated_by_bu_id', 'width': 40, 'type': 'many2one'}
            })
        return sheets

    def _generate_report_content(self, workbook, report):
        if report.cv_source:
            self.write_array_header('CV Source')
            for app_line in report.application_ids.sorted('create_date', reverse=True):
                self.write_line(CVSourceLineWrapper(app_line), 'CV Source')

        if report.calls:
            self.write_array_header('Calls')
            for call in report.call_ids.sorted('write_date', reverse=True):
                self.write_line(CallLineWrapper(call), 'Calls')

        if report.interviews:
            self.write_array_header('Interviews')
            applications = self.env['hr.applicant'].browse(list(set(report.interview_ids.mapped('res_id'))))
            for application in applications.sorted('write_date', reverse=True):
                self.write_line(InterviewsPerApplicationWrapper(application), 'Interviews')

        if report.offer:
            self.write_array_header('Offers and Hired')
            for offer in report.offer_ids.sorted(lambda o: (o.issue_date, o.create_date), reverse=True):
                self.write_line(offerLineWrapper(offer), 'Offers and Hired')


# noinspection PyProtectedMember
class CVSourceLineWrapper:
    def __init__(self, cv_source):
        self.create_uid = cv_source.create_uid
        self.generated_by_bu_id = cv_source.create_uid.business_unit_id
        self.application_code = cv_source.name
        self.partner_name = cv_source.partner_name
        self.email_from = cv_source.email_from
        self.partner_phone = cv_source.partner_phone
        self.partner_mobile = cv_source.partner_mobile
        self.source_id = cv_source.source_id
        self.create_date = cv_source.create_date
        self.business_unit_id = cv_source.department_id.business_unit_id
        if cv_source.job_id.department_id.parent_id:
            department = cv_source.job_id.department_id
            department_list = []
            while department:
                department_list.append(department)
                department = department.parent_id
            department_list.reverse()
            # self.department_list = list(filter(None, department_list))
            self.department_id = department_list[0]
            self.section_id = department_list[1]
            setattr(self, 'section_id' , department_list[1])
            # if len(department_list) > 2:
            #     for i in range(len(department_list)):
            #         if i <= 1:
            #             continue
            #         setattr(self, 'section_id' + str(i), department_list[i])

        else:
            self.department_id = cv_source.job_id.department_id

        self.job_id = cv_source.job_id
        self.salary_expected = cv_source.salary_expected
        self.salary_current = cv_source.salary_current
        self.cv_matched = cv_source.cv_matched
        self.reason_of_rejection = cv_source.reason_of_rejection
        self._context = cv_source._context
        self.env = cv_source.env


# noinspection PyProtectedMember
class CallLineWrapper:
    def __init__(self, call):
        applicant = call.env[call.res_model].browse(call.res_id)
        self.real_create_uid = call.real_create_uid
        self.generated_by_bu_id = call.real_create_uid.business_unit_id
        self.application_code = applicant.name
        self.partner_name = applicant.partner_name
        self.email_from = applicant.email_from
        self.partner_phone = applicant.partner_phone
        self.partner_mobile = applicant.partner_mobile
        self.write_date = call.write_date
        self.user_id = call.user_id
        self.call_result_id = call.call_result_id
        self.feedback = re.sub(r"<.*?>", '', call.feedback)
        self.business_unit_id = applicant.department_id.business_unit_id
        if applicant.job_id.department_id.parent_id:
            department = applicant.job_id.department_id
            department_list = []
            while department:
                department_list.append(department)
                department = department.parent_id
            department_list.reverse()
            # self.department_list = list(filter(None, department_list))
            self.department_id = department_list[0]
            self.section_id = department_list[1]
            setattr(self, 'section_id' , department_list[1])

            # if len(department_list) > 2:
            #     for i in range(len(department_list)):
            #         if i <= 1:
            #             continue
            #         setattr(self, 'section_id' + str(i), department_list[i])

        else:
            self.department_id = applicant.job_id.department_id

        self.job_id = applicant.job_id
        self.salary_expected = applicant.salary_expected
        self.salary_current = applicant.salary_current
        self.cv_matched = applicant.cv_matched
        self._context = call._context
        self.env = call.env


# noinspection PyProtectedMember
class InterviewLineWrapper:
    def __init__(self, interview):
        applicant = interview.env[interview.res_model].browse(interview.res_id)
        self.real_create_uid = interview.real_create_uid
        self.application_code = applicant.name
        self.partner_name = applicant.partner_name
        self.email_from = applicant.email_from
        self.partner_phone = applicant.partner_phone
        self.partner_mobile = applicant.partner_mobile
        self.start_date = interview.calendar_event_id.start
        self.partner_ids = interview.calendar_event_id.partner_ids
        self.interview_type_id = interview.calendar_event_id.interview_type_id
        self.interview_result = interview.interview_result
        self.feedback = re.sub(r"<.*?>", '', interview.feedback)
        self.business_unit_id = applicant.department_id.business_unit_id

        if applicant.job_id.department_id.parent_id:
            department = applicant.job_id.department_id
            department_list = []
            while department:
                department_list.append(department)
                department = department.parent_id
            department_list.reverse()
            # self.department_list = list(filter(None, department_list))
            self.department_id = department_list[0]
            self.section_id = department_list[1]
            setattr(self, 'section_id' , department_list[1])
            # if len(department_list) > 2:
            #     for i in range(len(department_list)):
            #         if i <= 1:
            #             continue
            #         setattr(self, 'section_id' + str(i), department_list[i])

        else:
            self.department_id = applicant.job_id.department_id

        self.job_id = applicant.job_id
        self.salary_expected = applicant.salary_expected
        self.salary_current = applicant.salary_current
        self.cv_matched = applicant.cv_matched
        self._context = interview._context
        self.env = interview.env


# noinspection PyUnresolvedReferences,PyMissingConstructor,PyProtectedMember
class InterviewsPerApplicationWrapper(GeneralSheetWrapper):
    def __init__(self, application):
        self.real_create_uid = application.create_uid
        self.generated_by_bu_id = application.create_uid.business_unit_id
        self.application_code = application.name
        self.partner_name = application.partner_name
        self.email_from = application.email_from
        self.partner_phone = application.partner_phone
        self.partner_mobile = application.partner_mobile
        interviews = self._get_activity('interview', application).sorted('write_date', reverse=False)
        first_interview = interviews[0] if interviews else False
        interview_feedback = first_interview.feedback if first_interview else False
        self.interview_date = first_interview.calendar_event_id.display_corrected_start_date if first_interview else False
        self.interviewers = first_interview.calendar_event_id.partner_ids if first_interview else False
        self.interview_result = first_interview.interview_result if first_interview else False
        self.interview_type_id = first_interview.calendar_event_id.interview_type_id if first_interview else False
        self.interview_comment = re.sub(r"<.*?>", '', interview_feedback if interview_feedback else '')
        for i in range(len(interviews)):
            if i == 0:
                continue
            setattr(self, 'interview_date' + str(i), interviews[i].calendar_event_id.display_corrected_start_date)
            setattr(self, 'interviewers' + str(i), interviews[i].calendar_event_id.partner_ids)
            setattr(self, 'interview_result' + str(i), interviews[i].interview_result)
            setattr(self, 'interview_type_id' + str(i), interviews[i].calendar_event_id.interview_type_id)
            setattr(self, 'interview_comment' + str(i),
                    re.sub(r"<.*?>", '', interviews[i].feedback if interviews[i].feedback else ''))
        self.business_unit_id = application.department_id.business_unit_id

        if application.job_id.department_id.parent_id:
            department = application.job_id.department_id
            department_list = []
            while department:
                department_list.append(department)
                department = department.parent_id
            department_list.reverse()
            # self.department_list = list(filter(None, department_list))
            self.department_id = department_list[0]
            self.section_id = department_list[1]
            setattr(self, 'section_id' , department_list[1])
            # if len(department_list) > 2:
            #     for i in range(len(department_list)):
            #         if i <= 1:
            #             continue
            #         setattr(self, 'section_id' + str(i), department_list[i])

        else:
            self.department_id = application.job_id.department_id

        self.job_id = application.job_id
        self.salary_expected = application.salary_expected
        self.salary_current = application.salary_current
        self.cv_matched = application.cv_matched
        self._context = application._context
        self.env = application.env


# noinspection PyProtectedMember
class offerLineWrapper:
    def __init__(self, offer):
        self.application_code = offer.application_id.name
        self.applicant_name = offer.applicant_name
        self.email_from = offer.application_id.email_from
        self.partner_mobile = offer.application_id.partner_mobile
        self.create_uid = offer.create_uid
        self.business_unit_id = offer.business_unit_id

        if offer.job_id.department_id.parent_id:
            department = offer.job_id.department_id
            department_list = []
            while department:
                department_list.append(department)
                department = department.parent_id
            department_list.reverse()
            # self.department_list = list(filter(None, department_list))
            self.department_id = department_list[0]
            self.section_id = department_list[1]
            setattr(self, 'section_id' , department_list[1])
            # if len(department_list) > 2:
            #     for i in range(len(department_list)):
            #         if i <= 1:
            #             continue
            #         setattr(self, 'section_id' + str(i), department_list[i])

        else:
            self.department_id = offer.job_id.department_id

        self.job_id = offer.job_id
        self.issue_date = offer.issue_date
        self.total_package = offer.total_package
        self.total_salary = offer.total_salary
        self.generated_by_bu_id = offer.generated_by_bu_id
        self.state = offer.state
        self.hiring_date = offer.hiring_date
        self.comment = offer.comment
        offer_dict = {'normal_offer': 'Normal Offer', 'nursing_offer': 'Nursing Offer'}
        self.offer_type = offer_dict.get(offer.offer_type, '')
        self._context = offer._context
        self.env = offer.env
