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
                    0: {'header': _('Recruiter Responsible'), 'field': 'user_id', 'width': 20},
                    1: {'header': _('Recruiter BU'), 'field': 'generated_by_bu_id', 'width': 20},
                    2: {'header': _('Application Code'), 'field': 'application_code', 'width': 20},
                    3: {'header': _('Applicant Name'), 'field': 'partner_name', 'width': 20},
                    4: {'header': _('Have CV'), 'field': 'have_cv', 'width': 20, 'type': 'bool'},
                    5: {'header': _('Have Assessment'), 'field': 'have_assessment', 'width': 20, 'type': 'bool'},
                    6: {'header': _('Email'), 'field': 'email_from', 'width': 20},
                    7: {'header': _('Phone'), 'field': 'partner_phone', 'width': 20},
                    8: {'header': _('Mobile'), 'field': 'partner_mobile', 'width': 20},
                    9: {'header': _('FaceBook'), 'field': 'face_book', 'width': 20},
                    10: {'header': _('LinkedIn'), 'field': 'linkedin', 'width': 20},
                    11: {'header': _('CV Source'), 'field': 'source_id', 'width': 10},
                    12: {'header': _('Source Responsible'), 'field': 'source_resp', 'width': 20},
                    13: {'header': _('Creation Date'), 'field': 'create_date', 'width': 18},
                    14: {'header': _('Business unit'), 'field': 'business_unit_id', 'width': 18},
                    15: {'header': _('Department'), 'field': 'department_id', 'width': 20},
                }
            })

            last_row = max(sheets[0]['CV Source'])
            # if report.job_ids:
            #     departments_query = 'select hr_department.id  from hr_department inner join hr_job on hr_department.id = hr_job.department_id where hr_department.parent_id is not null and hr_job.id in %s'
            #     self.env.cr.execute(departments_query, (tuple(report.job_ids.ids),))
            #     departments = self.env.cr.dictfetchall()
            # else:
            if report.application_ids.ids :
                # departments_query = 'select hr_applicant.id  from hr_applicant inner join hr_department on hr_department.id = hr_applicant.department_id where hr_applicant.id in %s and hr_department.parent_id is not null '
                departments_query = 'select section_id  from hr_applicant  where id in %s and section_id is not null  '
                self.env.cr.execute(departments_query, (tuple(report.application_ids.ids),))
                departments = self.env.cr.dictfetchall()
            else:
                departments = False
            if departments:
                sheets[0]['CV Source'].update({
                    last_row + 1: {'header': _('Section'),
                                   'field': 'section_id',
                                   'width': 20,
                                   }})
                last_row = last_row + 1
            sheets[0]['CV Source'].update({
                last_row + 1: {'header': _('Job Position'), 'field': 'job_id', 'width': 35},
                last_row + 2: {'header': _('Expected Salary'), 'field': 'salary_expected', 'width': 18,
                               'type': 'amount'},
                last_row + 3: {'header': _('Current  Salary'), 'field': 'salary_current', 'width': 18,
                               'type': 'amount'},
                last_row + 4: {'header': _('Matched'), 'field': 'cv_matched', 'width': 10, 'type': 'bool'},
                last_row + 5: {'header': _('Reason of Rejection'), 'field': 'reason_of_rejection', 'width': 35, },
            })

        if report.calls:
            sheets.append({
                'Calls': {
                    0: {'header': _('Recruiter Responsible'), 'field': 'user_id', 'width': 20,
                        },
                    1: {'header': _('Recruiter BU'), 'field': 'generated_by_bu_id', 'width': 20},
                    2: {'header': _('Application Code'), 'field': 'application_code', 'width': 20},
                    3: {'header': _('Applicant Name'), 'field': 'partner_name', 'width': 20},
                    4: {'header': _('Email'), 'field': 'email_from', 'width': 20},
                    5: {'header': _('Phone'), 'field': 'partner_phone', 'width': 20},
                    6: {'header': _('Mobile'), 'field': 'partner_mobile', 'width': 20},
                    7: {'header': _('FaceBook'), 'field': 'face_book', 'width': 20},
                    8: {'header': _('LinkedIn'), 'field': 'linkedin', 'width': 20},
                    9: {'header': _('Call Type'), 'field': 'call_type', 'width': 18},
                    10: {'header': _('Call Date'), 'field': 'write_date', 'width': 18},
                    11: {'header': _('Done Date'), 'field': 'call_result_date', 'width': 18},
                    12: {'header': _('Called By'), 'field': 'user_id', 'width': 20},
                    13: {'header': _('Call result'), 'field': 'call_result_id', 'width': 20, },
                    14: {'header': _('Comment'), 'field': 'feedback', 'width': 22},
                    15: {'header': _('Business unit'), 'field': 'business_unit_id', 'width': 18},
                    16: {'header': _('Department'), 'field': 'department_id', 'width': 22},
                }
            })

            tap_count = -1
            for tap in sheets:
                for k, v in tap.items():
                    tap_count += 1
                    if k == 'Calls':
                        break
            last_row = max(sheets[tap_count]['Calls'])

            x = 0
            if report.cv_source:
                x += 1
            sheet = sheets[x]['Calls']
            # if report.job_ids:
            #     departments_query = 'select hr_department.id  from hr_department inner join hr_job on hr_department.id = hr_job.department_id where hr_department.parent_id is not null and hr_job.id in %s'
            #     self.env.cr.execute(departments_query, (tuple(report.job_ids.ids),))
            #     departments = self.env.cr.dictfetchall()
            # else:
            if report.call_ids.ids :
                departments_query = '''select hr_applicant.section_id  from hr_applicant 
                inner join mail_activity on  mail_activity.res_id = hr_applicant.id
                 where mail_activity.id in %s and hr_applicant.section_id is not null '''
                self.env.cr.execute(departments_query, (tuple(report.call_ids.ids),))
                departments = self.env.cr.dictfetchall()
            else:
                departments = False
            if departments:
                sheet.update({
                    last_row + 1: {'header': _('Section'),
                                   'field': 'section_id',
                                   'width': 20,
                                   }})
                last_row = last_row + 1
            sheet.update({
                last_row + 1: {'header': _('Job position'), 'field': 'job_id', 'width': 35},
                last_row + 2: {'header': _('Expected Salary'), 'field': 'salary_expected', 'width': 18},
                last_row + 3: {'header': _('Current  Salary'), 'field': 'salary_current', 'width': 18},
                last_row + 4: {'header': _('Matched'), 'field': 'cv_matched', 'width': 10, 'type': 'bool'},
                last_row + 5: {'header': _('Source Responsible'), 'field': 'source_resp', 'width': 20,
                               },
                #
            })

        if report.interviews:

            sheets.append({
                'Interviews': {
                    0: {'header': _('Recruiter Responsible'), 'field': 'user_id', 'width': 20
                        },
                    1: {'header': _('Recruiter BU'), 'field': 'generated_by_bu_id', 'width': 20},
                    2: {'header': _('Application Code'), 'field': 'application_code', 'width': 20},
                    3: {'header': _('Applicant Name'), 'field': 'partner_name', 'width': 20},
                    4: {'header': _('Email'), 'field': 'email_from', 'width': 20},
                    5: {'header': _('Phone'), 'field': 'partner_phone', 'width': 20},
                    6: {'header': _('Mobile'), 'field': 'partner_mobile', 'width': 20},
                    7: {'header': _('FaceBook'), 'field': 'face_book', 'width': 20},
                    8: {'header': _('LinkedIn'), 'field': 'linkedin', 'width': 20},
                    9: {'header': _('Business unit'), 'field': 'business_unit_id', 'width': 18},
                    10: {'header': _('Department'), 'field': 'department_id', 'width': 22},
                }
            })
            tap_count = -1
            for tap in sheets:
                for k, v in tap.items():
                    tap_count += 1
                    if k == 'Interviews':
                        break
            last_row = max(sheets[tap_count]['Interviews'])

            x = 0
            if report.cv_source:
                x += 1
            if report.calls:
                x += 1
            sheet = sheets[x]['Interviews']
            # if report.job_ids:
            #     departments_query = 'select hr_department.id  from hr_department inner join hr_job on hr_department.id = hr_job.department_id where hr_department.parent_id is not null and hr_job.id in %s'
            #     self.env.cr.execute(departments_query, (tuple(report.job_ids.ids),))
            #     departments = self.env.cr.dictfetchall()
            # else:
            if report.interview_ids.ids:
                # departments_query = '''select hr_applicant.id  from hr_applicant
                # inner join hr_department on hr_department.id = hr_applicant.department_id
                # inner join mail_activity on  mail_activity.res_id = hr_applicant.id
                #  where mail_activity.id in %s and hr_department.parent_id is not null '''

                departments_query = '''select hr_applicant.section_id  from hr_applicant 
                   inner join mail_activity on  mail_activity.res_id = hr_applicant.id
                    where mail_activity.id in %s and hr_applicant.section_id is not null '''
                self.env.cr.execute(departments_query, (tuple(report.interview_ids.ids),))
                departments = self.env.cr.dictfetchall()
            else:departments = False
            if departments:
                sheet.update({
                    last_row + 1: {'header': _('Section'),
                                   'field': 'section_id',
                                   'width': 20,
                                   }})
                last_row = last_row + 1
            sheet.update({
                last_row + 1: {'header': _('Job position'), 'field': 'job_id', 'width': 35},
                last_row + 2: {'header': _('Expected Salary'), 'field': 'salary_expected', 'width': 18
                               },
                last_row + 3: {'header': _('Current  Salary'), 'field': 'salary_current', 'width': 18
                               },
                last_row + 4: {'header': _('Matched'), 'field': 'cv_matched', 'width': 10, 'type': 'bool'},
                last_row + 5: {'header': _('Have Assessment'), 'field': 'have_assessment', 'width': 20, 'type': 'bool'},
                last_row + 6: {'header': _('Source Responsible'), 'field': 'source_resp', 'width': 20
                               },
                last_row + 7: {'header': _('Created on'), 'field': 'interview_create_date', 'width': 18},
                last_row + 8: {'header': _('Interview date 1'), 'field': 'interview_date', 'width': 18},
                last_row + 9: {'header': _('Interviewers 1'), 'field': 'interviewers', 'width': 30},
                last_row + 10: {'header': _('Interviewer type 1'), 'field': 'interview_type_id', 'width': 30
                                },
                last_row + 11: {'header': _('Interview result 1'), 'field': 'interview_result', 'width': 20},
                last_row + 12: {'header': _('Interview Done Date 1'), 'field': 'interview_result_date', 'width': 20},
                last_row + 13: {'header': _('Comment 1'), 'field': 'interview_comment', 'width': 22},
            })
            last_row = max(sheets[tap_count]['Interviews'])
            max_interviews_count = False
            if report.interview_ids.ids:
                max_interviews_count_query = 'select max(x.count) from( select count(res_id) from mail_activity where id in %s and activity_type_id = %s and active = %s group by res_id) x'
                self.env.cr.execute(max_interviews_count_query, (tuple(report.interview_ids.ids), 5, False))
                max_interviews_count = self.env.cr.dictfetchall()
                max_interviews_count = max_interviews_count[0]['max'] - 1
            if max_interviews_count:
                tap_count = -1
                for tap in sheets:
                    for k, v in tap.items():
                        tap_count += 1
                        if k == 'Interviews':
                            break
                for i in range(max_interviews_count):
                    sheets[-1]['Interviews'].update(
                        {
                            last_row: {'header': _('Created on' + str(i + 2)),
                                       'field': 'interview_create_date'+ str(i + 1),
                                       'width': 18},
                            last_row + 1: {'header': _('Interview date ' + str(i + 2)),
                                           'field': 'interview_date' + str(i + 1),
                                           'width': 18},
                            last_row + 2: {'header': _('Interviewers ' + str(i + 2)),
                                           'field': 'interviewers' + str(i + 1),
                                           'width': 30,
                                           },
                            last_row + 3: {'header': _('Interview type ' + str(i + 2)),
                                           'field': 'interview_type_id' + str(i + 1),
                                           'width': 20},
                            last_row + 4: {'header': _('Interview result ' + str(i + 2)),
                                           'field': 'interview_result' + str(i + 1),
                                           'width': 20, },
                            last_row + 5: {'header': _('Interview Done Date ' + str(i + 2)),
                                           'field': 'interview_result_date' + str(i + 1),
                                           'width': 20, },
                            last_row + 6: {'header': _('Comment ' + str(i + 2)),
                                           'field': 'interview_comment' + str(i + 1),
                                           'width': 22},
                        }
                    )
                    last_row = last_row + 7

        if report.offer:
            sheets.append({
                'Offers': {
                    0: {'header': _('Application Code'), 'field': 'application_code', 'width': 20},
                    1: {'header': _('Candidate Name'), 'field': 'applicant_name', 'width': 20},
                    2: {'header': _('Email'), 'field': 'email_from', 'width': 20},
                    3: {'header': _('Mobile'), 'field': 'partner_mobile', 'width': 20},
                    4: {'header': _('FaceBook'), 'field': 'face_book', 'width': 20},
                    5: {'header': _('LinkedIn'), 'field': 'linkedin', 'width': 20},
                    6: {'header': _('Have Assessment'), 'field': 'have_assessment', 'width': 20, 'type': 'bool'},
                    7: {'header': _('Recruiter'), 'field': 'create_uid', 'width': 20},
                    8: {'header': _('Business unit'), 'field': 'business_unit_id', 'width': 20},
                    9: {'header': _('Department'), 'field': 'department_id', 'width': 20},
                }
            })
            tap_count = -1
            for tap in sheets:
                for k, v in tap.items():
                    tap_count += 1
                    if k == 'Offers':
                        break
            last_row = max(sheets[tap_count]['Offers'])

            x = 0
            if report.cv_source:
                x += 1
            if report.calls:
                x += 1
            if report.interviews:
                x += 1
            sheet = sheets[x]['Offers']
            # if report.job_ids:
            #     departments_query = 'select hr_department.id  from hr_department inner join hr_job on hr_department.id = hr_job.department_id where hr_department.parent_id is not null and hr_job.id in %s'
            #     self.env.cr.execute(departments_query, (tuple(report.job_ids.ids),))
            #     departments = self.env.cr.dictfetchall()
            # else:
            if report.offer_ids.ids:

                departments_query = '''select hr_applicant.section_id  from hr_applicant 
                   inner join hr_offer on  hr_offer.application_id= hr_applicant.id
                    where hr_offer.id in %s and hr_applicant.section_id is not null '''

                # departments_query = '''select hr_applicant.id  from hr_applicant
                # inner join hr_department on hr_department.id = hr_applicant.department_id
                # inner join hr_offer on  hr_offer.application_id= hr_applicant.id
                #  where hr_offer.id in %s and hr_department.parent_id is not null '''
                self.env.cr.execute(departments_query, (tuple(report.offer_ids.ids),))
                departments = self.env.cr.dictfetchall()
            else:
                departments = False
            if departments:
                sheet.update({
                    last_row + 1: {'header': _('Section'),
                                   'field': 'section_id',
                                   'width': 20,
                                   }})
                last_row = last_row + 1
            sheet.update({
                last_row + 1: {'header': _('Job position'), 'field': 'job_id', 'width': 20},
                last_row + 2: {'header': _('Issue Date'), 'field': 'issue_date', 'width': 20},
                last_row + 3: {'header': _('Total Salary'), 'field': 'total_salary', 'width': 20, 'type': 'amount'},
                last_row + 4: {'header': _('Have Offer'), 'field': 'have_offer', 'width': 20, 'type': 'bool'},
                last_row + 5: {'header': _('Total Package'), 'field': 'total_package', 'width': 20, 'type': 'amount'},
                last_row + 6: {'header': _('Hiring Status  '), 'field': 'state', 'width': 20},
                last_row + 7: {'header': _('Hiring Date'), 'field': 'hiring_date', 'width': 20},
                last_row + 8: {'header': _('Comments'), 'field': 'comment', 'width': 40},
                last_row + 9: {'header': _('Offer Type'), 'field': 'offer_type', 'width': 40},
                last_row + 10: {'header': _('Generated By'), 'field': 'generated_by_bu_id', 'width': 40,
                                },
                last_row + 11: {'header': _('Source Responsible'), 'field': 'source_resp', 'width': 20,
                                },
            })

        if report.hired:
            sheets.append({
                'Hired': {
                    0: {'header': _('Application Code'), 'field': 'application_code', 'width': 20},
                    1: {'header': _('Candidate Name'), 'field': 'applicant_name', 'width': 20},
                    2: {'header': _('Email'), 'field': 'email_from', 'width': 20},
                    3: {'header': _('Mobile'), 'field': 'partner_mobile', 'width': 20},
                    4: {'header': _('FaceBook'), 'field': 'face_book', 'width': 20},
                    5: {'header': _('LinkedIn'), 'field': 'linkedin', 'width': 20},
                    6: {'header': _('Recruiter'), 'field': 'create_uid', 'width': 20},
                    7: {'header': _('Business unit'), 'field': 'business_unit_id', 'width': 20},
                    8: {'header': _('Department'), 'field': 'department_id', 'width': 20, },
                }
            })
            tap_count = -1
            for tap in sheets:
                for k, v in tap.items():
                    tap_count += 1
                    if k == 'Hired':
                        break
            last_row = max(sheets[tap_count]['Hired'])
            x = 0
            if report.cv_source:
                x += 1
            if report.calls:
                x += 1
            if report.interviews:
                x += 1
            if report.offer:
                x += 1
            sheet = sheets[x]['Hired']
            if report.job_ids:
                departments_query = 'select hr_department.id  from hr_department inner join hr_job on hr_department.id = hr_job.department_id where hr_department.parent_id is not null and hr_job.id in %s'
                self.env.cr.execute(departments_query, (tuple(report.job_ids.ids),))
                departments = self.env.cr.dictfetchall()
            else:
                if report.hired_ids.ids:
                    # departments_query = '''select hr_applicant.id  from hr_applicant
                    # inner join hr_department on hr_department.id = hr_applicant.department_id
                    # inner join hr_offer on  hr_offer.application_id= hr_applicant.id
                    #  where hr_offer.id in %s and hr_department.parent_id is not null '''
                    departments_query = '''select hr_applicant.section_id  from hr_applicant 
                       inner join hr_offer on  hr_offer.application_id= hr_applicant.id
                        where hr_offer.id in %s and hr_applicant.section_id is not null '''
                    self.env.cr.execute(departments_query, (tuple(report.hired_ids.ids),))
                    departments = self.env.cr.dictfetchall()
                else:
                    departments = False

            if departments:
                sheet.update({
                    last_row + 1: {'header': _('Section'),
                                   'field': 'section_id',
                                   'width': 20,
                                   }})
                last_row = last_row + 1
            sheet.update({
                last_row + 1: {'header': _('Job position'), 'field': 'job_id', 'width': 20},
                last_row + 2: {'header': _('Issue Date'), 'field': 'issue_date', 'width': 20},
                last_row + 3: {'header': _('Total Salary'), 'field': 'total_salary', 'width': 20, 'type': 'amount'},
                last_row + 4: {'header': _('Total Package'), 'field': 'total_package', 'width': 20, 'type': 'amount'},
                last_row + 5: {'header': _('Hiring Status  '), 'field': 'state', 'width': 20},
                last_row + 6: {'header': _('Hiring Date'), 'field': 'hiring_date', 'width': 20},
                last_row + 7: {'header': _('Comments'), 'field': 'comment', 'width': 40},
                last_row + 8: {'header': _('Offer Type'), 'field': 'offer_type', 'width': 40},
                last_row + 9: {'header': _('Generated By'), 'field': 'generated_by_bu_id', 'width': 40,
                               },
                last_row + 10: {'header': _('Source Responsible'), 'field': 'source_resp', 'width': 20,
                                },
            })

        return sheets

    def _generate_report_content(self, workbook, report):
        if report.cv_source:
            self.write_array_header('CV Source')
            cvs = '''select prt_user.name user_id , prt_creater.name source_resp , creater_bu.name creater_bu ,
            app.name app_name , app_partner.mobile, app_partner.phone , app.email_from , app.have_assessment,
            app.have_cv ,app.partner_name , app_partner.face_book , app_partner.linkedin, app.create_date,
            source.name source , app.cv_matched , app.salary_expected , app.salary_current ,app.reason_of_rejection,
            job.name job_name , job_bu.name bu_name ,department.name department ,section.name section
            from hr_applicant app
            inner join res_partner app_partner
             on app.partner_id = app_partner.id
             left join  res_users usr on app.user_id = usr.id
             left join res_partner  prt_user on usr.partner_id = prt_user.id
             left join res_users creater on creater.id = app.create_uid
             left join res_partner prt_creater on creater.partner_id = prt_creater.id
             left join business_unit creater_bu on creater.business_unit_id = creater_bu.id
             left join utm_source source on app.source_id = source.id
             left join hr_job job on app.job_id = job.id 
             left join  business_unit job_bu on job.business_unit_id = job_bu.id

             left join hr_department department on app.department_id = department.id 
             left join hr_department section on app.section_id = section.id 
             
             where app.id in %s order by  create_date desc'''
            if report.application_ids.ids:
                self._cr.execute(cvs, (tuple(report.application_ids.ids),))
                cvs = self.env.cr.dictfetchall()

                for cv in cvs:
                    self.write_line(CVSourceLineWrapper(cv), 'CV Source')

        if report.calls:
            self.write_array_header('Calls')
            calls = 'select * from mail_activity where id in %s order by  write_date desc'
            if report.call_ids.ids:
                self._cr.execute(calls, (tuple(report.call_ids.ids),))
                calls = self.env.cr.dictfetchall()
                for i in range(len(calls)):
                    call_activity_query = '''
                        select app.name app_name ,app_partner.phone,app_partner.mobile ,
                         app.email_from,app_partner.face_book,app.partner_name,
                        app_partner.linkedin ,app.cv_matched , app.salary_expected , app.salary_current,cr_bu.name cr_bu,
                        job.name job_name,job_bu.name job_bu , department.name department ,section.name section, prt_uid_name.name source_resp ,
                         MAT.name , MA.write_date , MA.call_result_id ,MA.call_result_date,MA.feedback ,prt.name create_uid
                        from mail_activity MA

                        inner join mail_activity_type MAT
                        on MAT.id = MA.activity_type_id 
                        inner join res_users uid 
                        on  MA.user_id = uid.id
                        inner join res_partner prt 
                        on  uid.partner_id = prt.id
                        left join  business_unit cr_bu
                        on uid.business_unit_id = cr_bu.id
                        left join hr_applicant app
                        left join res_partner app_partner
                        on app.partner_id = app_partner.id
                        on app.id = MA.res_id
                        left join hr_job job on app.job_id = job.id 
                        left join  business_unit job_bu on job.business_unit_id = job_bu.id

                        left join hr_department department on app.department_id = department.id 
                        left join hr_department section on app.section_id = section.id 
                        
                        left join res_users source_resp on source_resp.id = app.create_uid
                        left join res_partner prt_uid_name on source_resp.partner_id = prt_uid_name.id
                        where MA.call_result_id is not null  and MA.id = %s
                    '''
                    self._cr.execute(call_activity_query, (calls[i]['id'],))
                    call_data = self.env.cr.dictfetchall()
                    self.write_line(CallLineWrapper(call_data), 'Calls')

        if report.interviews:
            self.write_array_header('Interviews')
            # applications = self.env['hr.applicant'].browse(list(set(report.interview_ids.mapped('res_id'))))
            # x=len(applications)
            applications = '''select distinct app.id ,app.write_date 
                            from mail_activity ma 
                           inner join hr_applicant app on app.id = ma.res_id where ma.id in %s 
                           order by  app.write_date desc'''
            if report.interview_ids.ids:
                self._cr.execute(applications, (tuple(report.interview_ids.ids),))
                applications = self.env.cr.dictfetchall()
                # y = len(applications)
                for i in range(len(applications)):
                    interviews_activity_query = '''
                    select  app.name app_name, app.partner_name, app_partner.mobile , app.email_from,app_partner.face_book, app_partner.linkedin ,
                    app.have_cv ,app.have_assessment ,app_partner.phone , prt_uid_name.name creater ,job_bu.name job_bu,app.write_date,
                    department.name department, section.name section , job.name job_name , cr_bu.name cr_bu , res_partner.name prt_name , 
                    app.salary_expected , app.salary_current ,  MA.create_date create_on, MA.write_date , MA.interview_result ,MA.interview_result_date,MA.feedback ,
                    it.name, CE.display_corrected_start_date ,CE.start_datetime,CE.start_date,STRING_AGG ( res.name, '•'  )  ,app.cv_matched
                    from mail_activity MA

    
                    inner join calendar_event CE on MA.calendar_event_id = CE.id
    
    
                    inner join interview_type it  on  CE.interview_type_id = it.id  
    
    
                    left join calendar_event_res_partner_rel CR on CE.id = CR.calendar_event_id
    
    
                    left join res_partner res on  CR.res_partner_id = res.id
    
    
                    inner join hr_applicant app on app.id = MA.res_id
                    
                    inner join res_partner app_partner
                     on app.partner_id = app_partner.id
    
                    left join  res_users usr on app.user_id = usr.id
    
    
                    inner join res_partner  on usr.partner_id = res_partner.id
    
    
                    left join res_users uid on uid.id = app.create_uid
    
                    left join res_partner prt_uid_name on uid.partner_id = prt_uid_name.id
    
                     left join business_unit cr_bu on uid.business_unit_id = cr_bu.id
    
                    left join hr_job job on app.job_id = job.id 
    
                    left join  business_unit job_bu on job.business_unit_id = job_bu.id
                    
                    left join hr_department department on app.department_id = department.id 
                    left join hr_department section on app.section_id = section.id 
    
                    where MA.res_id = %s
    
                    group by MA.id, MA.write_date , MA.interview_result ,MA.interview_result_date,MA.feedback ,
                    CE.display_corrected_start_date, it.name ,
                    app.name ,app.partner_name, app_partner.mobile , app.email_from,app_partner.face_book, app_partner.linkedin ,
                    app.have_cv ,app.have_assessment ,app_partner.phone , prt_uid_name.name,job_bu.name ,
                    department.name ,section.name, job.name, cr_bu.name , res_partner.name , 
                    app.salary_expected , app.salary_current ,app.write_date, MA.create_date,app.cv_matched,CE.start_datetime,CE.start_date
                    order by  MA.write_date asc
                    '''
                    self._cr.execute(interviews_activity_query, (applications[i]['id'],))
                    interviews_data = self.env.cr.dictfetchall()
                    if interviews_data:
                        self.write_line(InterviewsPerApplicationWrapper(interviews_data), 'Interviews')
        if report.offer or report.hired:
            offer_query = '''
                            select  app.name app_name , app.partner_name,app.email_from, 
                            app_partner.mobile, app_partner.face_book , app_partner.linkedin ,app.have_assessment,
                            prt_creater.name create_uid , offer_bu.name bu_name,source_prt.name source_resp ,
                            job.name job_name, section.name section ,department.name department,
                            offer.issue_date, offer.total_package , offer.have_offer,
                            offer.total_salary ,offer.offer_type , offer.hiring_date ,
                            offer.state , offer.comment ,offer_gen_bu.name gen_bu_name
                            from hr_offer offer

                            left join hr_applicant app on app.id = offer.application_id 
                            inner join res_partner app_partner
                            on app.partner_id = app_partner.id
                            left join res_users source_usr on source_usr.id = app.create_uid
            		        left join res_partner source_prt on source_usr.partner_id = source_prt.id

                            left join res_users creater on creater.id = offer.create_uid
            		        left join res_partner prt_creater on creater.partner_id = prt_creater.id
            		        left join  business_unit offer_bu on offer.business_unit_id  = offer_bu.id
            		        left join  business_unit offer_gen_bu on offer.generated_by_bu_id = offer_gen_bu.id
            		        left join hr_job job on offer.job_id = job.id
                            left join hr_department department on app.department_id = department.id 
                            left join hr_department section on app.section_id = section.id 
                            where offer.id in %s order by issue_date desc
                        '''
        if report.offer:
            self.write_array_header('Offers')
            if report.offer_ids.ids:
                self.env.cr.execute(offer_query, (tuple(report.offer_ids.ids),))
                offers = self.env.cr.dictfetchall()
                for offer in offers:
                    self.write_line(offerLineWrapper(offer), 'Offers')

        if report.hired:
            self.write_array_header('Hired')
            if report.hired_ids.ids:
                self.env.cr.execute(offer_query, (tuple(report.hired_ids.ids),))
                offers = self.env.cr.dictfetchall()
                for hired in offers:
                    self.write_line(offerLineWrapper(hired), 'Hired')


# noinspection PyProtectedMember
class CVSourceLineWrapper:
    def __init__(self, cv_source):
        self.user_id = cv_source['user_id']
        self.generated_by_bu_id = cv_source['creater_bu']
        self.application_code = cv_source['app_name']
        self.partner_name = cv_source['partner_name']
        self.have_cv = cv_source['have_cv']
        self.have_assessment = cv_source['have_assessment']
        self.email_from = cv_source['email_from']
        self.partner_phone = cv_source['phone']
        self.partner_mobile = cv_source['mobile']
        self.face_book = cv_source['face_book']
        self.linkedin = cv_source['linkedin']
        self.source_id = cv_source['source']
        self.source_resp = cv_source['source_resp']
        self.create_date = cv_source['create_date']
        self.business_unit_id = cv_source['bu_name']
        # if not cv_source['parent_dept']:
        #     self.department_id = cv_source['dept']
        # else:
        #     self.section_id = cv_source['dept']
        #     self.department_id = cv_source['parent_dept']
        self.department_id = cv_source['department']
        # else:
        self.section_id = cv_source['section']
        self.job_id = cv_source['job_name']
        if cv_source['salary_expected']:
            self.salary_expected = cv_source['salary_expected']
        else:
            self.salary_expected = '0.0'

        if cv_source['salary_current']:
            self.salary_current = cv_source['salary_current']
        else:
            self.salary_current = '0.0'
        self.cv_matched = cv_source['cv_matched']
        self.reason_of_rejection = cv_source['reason_of_rejection']


# noinspection PyProtectedMember
class CallLineWrapper:
    def __init__(self, call):
        self.user_id = call[0]['create_uid']
        self.generated_by_bu_id = call[0]['cr_bu']
        self.application_code = call[0]['app_name']
        self.partner_name = call[0]['partner_name']
        self.email_from = call[0]['email_from']
        self.partner_phone = call[0]['phone']
        self.partner_mobile = call[0]['mobile']
        self.face_book = call[0]['face_book']
        self.linkedin = call[0]['linkedin']
        self.call_type = call[0]['name']
        self.write_date = call[0]['write_date']
        self.call_result_date = call[0]['call_result_date']
        self.user_id = call[0]['create_uid']
        self.call_result_id = call[0]['call_result_id']
        self.feedback = re.sub(r"<.*?>", '', call[0]['feedback'])
        self.business_unit_id = call[0]['job_bu']
        # if not call[0]['parent_dept']:
        self.department_id = call[0]['department']
        # else:
        self.section_id = call[0]['section']
            # self.department_id = call[0]['parent_dept']

        self.job_id = call[0]['job_name']
        if call[0]['salary_expected']:
            self.salary_expected = str(call[0]['salary_expected'])
        else:
            self.salary_expected = '0.0'
        if call[0]['salary_current']:
            self.salary_current = str(call[0]['salary_current'])
        else:
            self.salary_current = '0.0'

        self.cv_matched = call[0]['cv_matched']
        self.source_resp = call[0]['source_resp']


# noinspection PyUnresolvedReferences,PyMissingConstructor,PyProtectedMember
class InterviewsPerApplicationWrapper(GeneralSheetWrapper):
    def __init__(self, interviews_data):
        self.user_id = interviews_data[0]['prt_name']
        self.generated_by_bu_id = interviews_data[0]['cr_bu']
        self.application_code = interviews_data[0]['app_name']
        self.partner_name = interviews_data[0]['partner_name']
        self.email_from = interviews_data[0]['email_from']
        self.partner_phone = interviews_data[0]['phone']
        self.partner_mobile = interviews_data[0]['mobile']
        self.face_book = interviews_data[0]['face_book']
        self.linkedin = interviews_data[0]['linkedin']

        self.interview_type_id = interviews_data[0]['name'] if interviews_data[0]['name'] else False
        self.interviewers = interviews_data[0]['string_agg'] if interviews_data[0]['string_agg'] else False
        self.interview_create_date = interviews_data[0]['create_on'] if interviews_data[0]['create_on'] else False
        if interviews_data[0]['display_corrected_start_date']:
            self.interview_date = interviews_data[0]['display_corrected_start_date']
        elif interviews_data[0]['start_datetime']:
            self.interview_date = interviews_data[0]['start_datetime']
        elif interviews_data[0]['start_date']:
            self.interview_date = interviews_data[0]['start_date']
        else:
            False
        self.interview_result = interviews_data[0]['interview_result'] if interviews_data[0][
            'interview_result'] else False
        self.interview_result_date = interviews_data[0]['interview_result_date'] if interviews_data[0][
            'interview_result_date']\
            else False

        self.interview_comment = re.sub(r"<.*?>", '', interviews_data[0]['feedback']) if interviews_data[0][
            'feedback'] else False

        for i in range(len(interviews_data)):
            if i == 0:
                continue
            setattr(self, 'interview_create_date' + str(i), interviews_data[i]['create_on'])
            if interviews_data[i]['display_corrected_start_date']:
                setattr(self, 'interview_date' + str(i), interviews_data[i]['display_corrected_start_date'])
            elif interviews_data[i]['start_datetime']:
                setattr(self, 'interview_date' + str(i), interviews_data[i]['start_datetime'])
            elif interviews_data[i]['start_date']:
                setattr(self, 'interview_date' + str(i), interviews_data[i]['start_date'])
            else:
                False
            # setattr(self, 'interview_date' + str(i), interviews_data[i]['display_corrected_start_date'])
            setattr(self, 'interviewers' + str(i), interviews_data[i]['string_agg'])
            setattr(self, 'interview_result' + str(i), interviews_data[i]['interview_result'])
            setattr(self, 'interview_result_date' + str(i), interviews_data[i]['interview_result_date'])
            setattr(self, 'interview_type_id' + str(i), interviews_data[i]['name'])
            setattr(self, 'interview_comment' + str(i),
                    re.sub(r"<.*?>", '', interviews_data[i]['feedback'] if interviews_data[i]['feedback'] else ''))

        self.business_unit_id = interviews_data[0]['job_bu']
        # if not interviews_data[0]['parent_dept']:
        self.department_id = interviews_data[0]['department']
        # else:
        self.section_id = interviews_data[0]['section']
            # self.department_id = interviews_data[0]['parent_dept']
        self.job_id = interviews_data[0]['job_name']
        self.salary_expected = str(interviews_data[0]['salary_expected'])
        self.salary_current = str(interviews_data[0]['salary_current'])
        self.cv_matched = interviews_data[0]['cv_matched']
        self.have_assessment = interviews_data[0]['have_assessment']
        self.source_resp = interviews_data[0]['creater']

    # def _get_activity(self, activity, data):
    #     """
    #     This function get all the activity lines from the mail.activity model
    #     :param activity: 'call', 'interview'
    #     :param data:
    #     :return:
    #     """
    #     activity_type = ""
    #     if activity == 'call':
    #         if data.with_context({'active_test': False}).activity_ids.filtered(
    #                 lambda r: r.activity_type_id.name == "Call"):
    #             activity_type = data.env.ref('mail.mail_activity_data_call')
    #         if data.with_context({'active_test': False}).activity_ids.filtered(
    #                 lambda r: r.activity_type_id.name == "LinkedIn Call"):
    #             activity_type = data.env.ref('recruitment_ads.mail_activity_type_data_linkedIn_call')
    #         if data.with_context({'active_test': False}).activity_ids.filtered(
    #                 lambda r: r.activity_type_id.name == "Facebook Call"):
    #             activity_type = data.env.ref('recruitment_ads.mail_activity_type_data_facebook_call')
    #     if activity == 'interview':
    #         activity_type = data.env.ref('recruitment_ads.mail_activity_type_data_interview')
    #     return data.with_context({'active_test': False}).activity_ids.filtered(
    #         lambda a: a.activity_type_id == activity_type and not a.active)


# noinspection PyProtectedMember
class offerLineWrapper:
    def __init__(self, offer):
        self.application_code = offer['app_name']
        self.applicant_name = offer['partner_name']
        self.email_from = offer['email_from']
        self.partner_mobile = offer['mobile']
        self.face_book = offer['face_book']
        self.linkedin = offer['linkedin']
        self.have_assessment = offer['have_assessment']
        self.create_uid = offer['create_uid']
        self.business_unit_id = offer['bu_name']
        # if not offer['parent_dept']:
        self.department_id = offer['department']
        # else:
        self.section_id = offer['section']
            # self.department_id = offer['parent_dept']

        self.job_id = offer['job_name']

        self.issue_date = offer['issue_date']

        if offer['total_package']:
            self.total_package = offer['total_package']
        else:
            self.total_package = '0.0'

        if offer['total_salary']:
            self.total_salary = offer['total_salary']
        else:
            self.total_salary = '0.0'
        self.have_offer = offer['have_offer']
        self.generated_by_bu_id = offer['gen_bu_name']
        self.state = offer['state']
        self.hiring_date = offer['hiring_date']
        self.comment = offer['comment']
        offer_dict = {'normal_offer': 'Normal Offer', 'nursing_offer': 'Nursing Offer'}
        if offer['offer_type'] == 'normal_offer':
            self.offer_type = 'Normal Offer'
        else:
            self.offer_type = 'Nursing Offer'
        self.source_resp = offer['source_resp']
