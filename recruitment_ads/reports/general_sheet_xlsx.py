from odoo import _, models
import re


class GeneralSheetXslx(models.AbstractModel):
    _name = 'report.recruitment_ads.report_general_sheet_xlsx'
    _inherit = 'report.recruitment_ads.abstract_report_xlsx'

    def _get_report_name(self):
        return _('General Sheet')

    def _get_report_sheets(self, report):
        sheets = []
        max_interviews_count = 0
        max_interviews_count_query ='select max(x.count) from( select count(res_id) from mail_activity where res_id in %s and activity_type_id = %s and active = %s group by res_id) x'
        self.env.cr.execute(max_interviews_count_query, (tuple(report.application_ids.ids),5,False))
        interviews_count = self.env.cr.dictfetchall()
        if interviews_count[0]['max'] :
            max_interviews_count = interviews_count[0]['max'] -1
        sheets.append({
            'General Sheet': {
                0: {'header': _('Recruiter Responsible'), 'field': 'user_id', 'width': 20},
                1: {'header': _('Recruiter BU'), 'field': 'generated_by_bu_id', 'width': 20},
                2: {'header': _('Applicant Code'), 'field': 'application_code', 'width': 20},
                3: {'header': _('Applicant Name'), 'field': 'partner_name', 'width': 20},
                4: {'header': _('Have CV'), 'field': 'have_cv', 'width': 20, 'type': 'bool'},
                5: {'header': _('Have Assessment'), 'field': 'have_assessment', 'width': 20, 'type': 'bool'},
                6: {'header': _('Mobile'), 'field': 'partner_mobile', 'width': 20},
                7: {'header': _('Email'), 'field': 'email_from', 'width': 20},
                8: {'header': _('Facebook'), 'field': 'facebook_link', 'width': 20},
                9: {'header': _('Linkedin'), 'field': 'linkedin_link', 'width': 20},
                10: {'header': _('Yes/No'), 'field': 'cv_matched', 'width': 10, 'type': 'bool'},
                11: {'header': _('Expected salary'), 'field': 'salary_expected','width': 20},
                12: {'header': _('Current salary'), 'field': 'salary_current','width': 20},
                13: {'header': _('CV Source'), 'field': 'source_id', 'width': 10},
                14: {'header': _('Source Responsible'), 'field': 'source_resp', 'width': 20},
                15: {'header': _('Business unit'), 'field': 'business_unit_id', 'width': 18},
                16: {'header': _('Department'), 'field': 'department_id', 'width': 20},

            }
        })

        if report.job_ids:
            departments_query = 'select hr_department.id  from hr_department inner join hr_job on hr_department.id = hr_job.department_id where hr_department.parent_id is not null and hr_job.id in %s'
            self.env.cr.execute(departments_query, (tuple(report.job_ids.ids),))
            departments = self.env.cr.dictfetchall()
        else:
            departments_query = 'select hr_applicant.id  from hr_applicant inner join hr_department on hr_department.id = hr_applicant.department_id where hr_applicant.id in %s and hr_department.parent_id is not null '
            self.env.cr.execute(departments_query, (tuple(report.application_ids.ids),))
            departments = self.env.cr.dictfetchall()
        last_row = max(sheets[0]['General Sheet'])
        if departments:
            sheets[0]['General Sheet'].update({
                last_row + 1: {'header': _('Section'),
                               'field': 'section_id',
                               'width': 20,
                                }})
            last_row = last_row + 1
        #
        sheets[0]['General Sheet'].update(
            {
                last_row + 1: {'header': _('Job Position'), 'field': 'job_id', 'width': 35},
        #
                last_row + 2: {'header': _('Call Type'), 'field': 'call_type', 'width': 18},
                last_row + 3: {'header': _('Call Date'), 'field': 'call_date', 'width': 18},
                last_row + 4: {'header': _('Called by'), 'field': 'called_by', 'width': 18},
                last_row + 5: {'header': _('Call Result'), 'field': 'call_result', 'width': 18},
                last_row + 6: {'header': _('Call Done Date '), 'field': 'call_result_date', 'width': 18},
                last_row + 7: {'header': _('Call Comment'), 'field': 'call_comment', 'width': 18},
                last_row + 8: {'header': _('Interview Creation Date 1'), 'field': 'interview_create_date', 'width': 22},
                last_row + 9: {'header': _('Interview Date 1'), 'field': 'interview_date', 'width': 18},
                last_row + 10: {'header': _('Interviewers 1'), 'field': 'interviewers', 'width': 30},
                last_row + 11: {'header': _('Interview result 1'), 'field': 'interview_result', 'width': 20, },
                last_row + 12: {'header': _('Interview Done Date'), 'field': 'interview_result_date', 'width': 20, },
                last_row + 13: {'header': _('Interview type 1'), 'field': 'interview_type_id', 'width': 20
                                },
                last_row + 14: {'header': _('Interview Comment 1'), 'field': 'interview_comment', 'width': 22},
             })
        last_row = max(sheets[0]['General Sheet']) + 1
        if max_interviews_count > 0:
            for i in range(max_interviews_count):
                sheets[0]['General Sheet'].update(
                    {
                        last_row : {'header': _('Interview Creation Date ' + str(i + 2)), 'field': 'interview_create_date' + str(i + 1),
                                       'width': 22},
                        last_row + 1: {'header': _('Interview Date ' + str(i + 2)), 'field': 'interview_date' + str(i + 1),
                                   'width': 18},
                        last_row + 2: {'header': _('Interviewers ' + str(i + 2)), 'field': 'interviewers' + str(i + 1),
                                       'width': 30,
                        },
                        last_row + 3: {'header': _('Interview result ' + str(i + 2)),
                                       'field': 'interview_result' + str(i + 1),
                                       'width': 20, },
                        last_row + 4: {'header': _('Interview Done Date ' + str(i + 2)),
                                       'field': 'interview_result_date' + str(i + 1),
                                       'width': 20, },

                        last_row + 5: {'header': _('Interview type ' + str(i + 2)),
                                       'field': 'interview_type_id' + str(i + 1),
                                       'width': 20},
                        last_row + 6: {'header': _('Interview Comment ' + str(i + 2)),
                                       'field': 'interview_comment' + str(i + 1), 'width': 22},
                    }
                )
                last_row = last_row + 7
        last_row = max(sheets[0]['General Sheet'])
        sheets[0]['General Sheet'].update(
            {
                last_row + 1: {'header': _('Offer Status'), 'field': 'offer_status', 'width': 22},
                last_row + 2: {'header': _('Offer Date'), 'field': 'offer_date', 'width': 22},
                last_row + 3: {'header': _('Hiring Date'), 'field': 'hiring_date', 'width': 22},
                last_row + 4: {'header': _('Offer Type'), 'field': 'offer_type', 'width': 22},
                last_row + 5: {'header': _('Total Salary'), 'field': 'total_salary', 'width': 20, 'type': 'amount'},
                last_row + 6: {'header': _('Total Package'), 'field': 'total_package', 'width': 20, 'type': 'amount'},
                last_row + 7: {'header': _('Have Offer'), 'field': 'have_offer', 'width': 20, 'type': 'bool'},
                last_row + 8: {'header': _('Generated By'), 'field': 'offer_generated_by_bu_id', 'width': 40,
                               }
            }

         )
        return sheets

    def _generate_report_content(self, workbook, report):
        if report:
            self.write_array_header('General Sheet')
            applications = self.env['hr.applicant'].search([('id','in',report.application_ids.ids)], order='create_date desc')
            for app_line in applications:
                app_datas_query = '''
                select  app.name,app.partner_name,app.have_cv ,app.have_assessment ,app.partner_mobile ,
                 app.email_from,app.face_book,
                app.linkedin ,app.cv_matched , app.salary_expected , app.salary_current , res_partner.name prt_name ,
                prt_uid_name.name creater , cr_bu.name cr_bu , utm_source.name source_name , job.name job_name ,
                job_bu.name job_bu , dep.name dept ,parent_dep.name parent_dept,
                offer.state , offer.issue_date , offer.hiring_date ,offer.offer_type , 
                offer.total_package , offer.have_offer , offer.total_salary ,
                offer_bu.name offer_bu
                from hr_applicant app 
                left join  res_users usr
                on app.user_id = usr.id
                left join res_partner  
                on usr.partner_id = res_partner.id
                left join res_users uid on uid.id = app.create_uid
                left join res_partner prt_uid_name on uid.partner_id = prt_uid_name.id
                left join business_unit cr_bu on uid.business_unit_id =   cr_bu.id
                left join utm_source on app.source_id = utm_source.id
                left join hr_job job on app.job_id = job.id 
		        left join  business_unit job_bu on job.business_unit_id = job_bu.id
                left join hr_department dep on job.department_id = dep.id 
		        left join hr_department parent_dep on dep.parent_id = parent_dep.id 
                left join hr_offer offer on app.offer_id = offer.id
		        left join  business_unit offer_bu on offer.generated_by_bu_id = offer_bu.id
                where app.id = %s  
                
                '''
                self._cr.execute(app_datas_query, (app_line.id,))
                app_data= self.env.cr.dictfetchall()

                call_activity_query ='''
                    select MAT.name , MA.write_date , MA.call_result_id ,MA.call_result_date,MA.feedback ,prt.name create_uid
                    from mail_activity MA
                    inner join mail_activity_type MAT
                    on MAT.id = MA.activity_type_id 
                    inner join res_users uid 
                    on  MA.user_id = uid.id
                    inner join res_partner prt 
                    on  uid.partner_id = prt.id
                    where MA.call_result_id is not null  and MA.res_id = %s
                    order by  MA.write_date desc limit 1
                '''
                self._cr.execute(call_activity_query, (app_line.id,))
                call_data= self.env.cr.dictfetchall()

                interviews_activity_query = '''
                select MA.create_date , MA.write_date , MA.interview_result ,MA.interview_result_date,MA.feedback ,
                 it.name, CE.display_corrected_start_date ,STRING_AGG ( res.name, '•'  )  
                 from mail_activity MA
                inner join calendar_event CE
                on MA.calendar_event_id = CE.id
                inner join interview_type it 
                on  CE.interview_type_id = it.id                 
                inner join calendar_event_res_partner_rel CR
                on CE.id = CR.calendar_event_id
                inner join res_partner res 
                on  CR.res_partner_id = res.id
                where MA.interview_result is not null and MA.res_id = %s
                group by  MA.id, MA.write_date , MA.interview_result ,MA.interview_result_date,MA.feedback ,
                CE.display_corrected_start_date, it.name 
                order by  MA.write_date asc 
                '''
                self._cr.execute(interviews_activity_query, (app_line.id,))
                interviews_data= self.env.cr.dictfetchall()
                self.write_line(GeneralSheetWrapper(app_data,call_data ,interviews_data), 'General Sheet')



class GeneralSheetWrapper:
    def __init__(self,app_data , call_data , interviews_data):
        self.user_id = app_data[0]['prt_name']
        self.generated_by_bu_id =  app_data[0]['cr_bu']
        self.application_code = app_data[0]['name']
        self.partner_name =app_data[0]['partner_name']
        self.have_cv = app_data[0]['have_cv']
        self.have_assessment = app_data[0]['have_assessment']
        self.partner_mobile = app_data[0]['partner_mobile']
        self.email_from = app_data[0]['email_from']
        self.facebook_link = app_data[0]['face_book']
        self.linkedin_link = app_data[0]['linkedin']
        self.cv_matched = app_data[0]['cv_matched']
        self.salary_expected = str(app_data[0]['salary_expected'])
        self.salary_current = str(app_data[0]['salary_current'])
        self.source_id = app_data[0]['source_name']
        self.source_resp = app_data[0]['creater']
        self.business_unit_id = app_data[0]['job_bu']
        if not app_data[0]['parent_dept'] :
            self.department_id = app_data[0]['dept']
        else:
            self.section_id = app_data[0]['dept']
            self.department_id = app_data[0]['parent_dept']
        self.job_id =  app_data[0]['job_name']

        if call_data:
            self.call_type = call_data[0]['name'] if call_data[0]['name']  else False
            self.call_date = call_data[0]['write_date'] if call_data[0]['write_date'] else False
            self.called_by = call_data[0]['create_uid'] if call_data[0]['create_uid'] else False
            self.call_result = call_data[0]['call_result_id'] if call_data[0]['call_result_id'] else False
            self.call_result_date = call_data[0]['call_result_date'] if call_data[0]['call_result_date'] else False
            self.call_comment = re.sub(r"<.*?>", '', call_data[0]['feedback']) if call_data[0]['feedback'] else False

        if interviews_data:
            self.interview_type_id = interviews_data[0]['name'] if interviews_data[0]['name']  else False
            self.interviewers = interviews_data[0]['string_agg']if interviews_data[0]['string_agg'] else False
            self.interview_create_date = interviews_data[0]['create_date'] if interviews_data[0]['create_date'] else False
            self.interview_date = interviews_data[0]['display_corrected_start_date'] if interviews_data[0]['display_corrected_start_date'] else False
            self.interview_result = interviews_data[0]['interview_result'] if interviews_data[0]['interview_result'] else False
            self.interview_result_date = interviews_data[0]['interview_result_date'] if interviews_data[0]['interview_result_date'] else False
            self.interview_result_date = interviews_data[0]['interview_result_date'] if interviews_data[0][
                'interview_result_date'] else False
            self.interview_comment = re.sub(r"<.*?>", '', interviews_data[0]['feedback']) if interviews_data[0]['feedback'] else False

        for i in range(len(interviews_data)):
            if i == 0:
                continue
            setattr(self, 'interview_create_date' + str(i), interviews_data[i]['create_date'])
            setattr(self, 'interview_date' + str(i), interviews_data[i]['display_corrected_start_date'])
            setattr(self, 'interviewers' + str(i), interviews_data[i]['string_agg'])
            setattr(self, 'interview_result' + str(i),interviews_data[i]['interview_result'])
            setattr(self, 'interview_result_date' + str(i), interviews_data[i]['interview_result_date'])
            setattr(self, 'interview_type_id' + str(i), interviews_data[i]['name'])
            setattr(self, 'interview_comment' + str(i),
                            re.sub(r"<.*?>", '', interviews_data[i]['feedback'] if interviews_data[i]['feedback'] else ''))

        self.offer_status = app_data[0]['state']
        self.offer_date = app_data[0]['issue_date']
        self.hiring_date = app_data[0]['hiring_date']
        if app_data[0]['offer_type'] == 'normal_offer' :
            self.offer_type =  'Normal Offer'
        if app_data[0]['offer_type'] == 'nursing_offer' :
            self.offer_type =  'Nursing Offer'
        self.total_package = app_data[0]['total_package']
        self.have_offer = app_data[0]['have_offer']
        self.total_salary = app_data[0]['total_salary']
        self.offer_generated_by_bu_id = app_data[0]['offer_bu']

