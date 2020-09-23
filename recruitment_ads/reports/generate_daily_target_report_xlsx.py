from odoo import models, _


class GenerateDailyTargetReportXslx(models.AbstractModel):
    _name = 'report.recruitment_ads.report_generate_daily_target_xlsx'
    _inherit = 'report.recruitment_ads.abstract_report_xlsx'

    def _get_report_name(self):
        return _('Daily target Report')

    def _get_report_sheets(self, report):
        if report.type_report == 'target':
          return [{
            'Daily Target Report': {
                0: {'header': _('Date'), 'field': 'date', 'width': 20},
                1: {'header': _('Recruiter BU'), 'field': 'user_bu', 'width': 20, 'type': 'many2one'},
                2: {'header': _('Recruiter'), 'field': 'recruiter_id', 'width': 20, 'type': 'many2one'},
                3: {'header': _('BU'), 'field': 'bu_id', 'width': 20, 'type': 'many2one'},
                4: {'header': _('Department'), 'field': 'department_id', 'width': 20, 'type': 'many2one'},
                5: {'header': _('Section'), 'field': 'section_id', 'width': 20, 'type': 'many2one'},
                6: {'header': _('Position'), 'field': 'job_id', 'width': 20, 'type': 'many2one'},
                7: {'header': _('Level'), 'field': 'level_id', 'width': 20, 'type': 'many2one'},
                8: {'header': _('Weight'), 'field': 'weight', 'width': 20, 'type': 'amount'},
                9: {'header': _('Target Screening'), 'field': 'target_screening', 'width': 20, 'type': 'amount'},
                10: {'header': _('Target Calls'), 'field': 'target_calls', 'width': 20, 'type': 'amount'},
                11: {'header': _('Target Invitation'), 'field': 'target_invitation', 'width': 20, 'type': 'amount'},
                12: {'header': _('Target HR Accepted'), 'field': 'target_hr_accepted', 'width': 20, 'type': 'amount'},
                13: {'header': _('Target Final Accepted'), 'field': 'target_final_accepted', 'width': 20,
                     'type': 'amount'},
            }
        }]
        if report.type_report == 'actual':
            return [{
                'Daily Target Report': {
                    0: {'header': _('Date'), 'field': 'date', 'width': 20},
                    1: {'header': _('Recruiter BU'), 'field': 'user_bu', 'width': 20, 'type': 'many2one'},
                    2: {'header': _('Recruiter'), 'field': 'recruiter_id', 'width': 20, 'type': 'many2one'},
                    3: {'header': _('BU'), 'field': 'bu_id', 'width': 20, 'type': 'many2one'},
                    4: {'header': _('Department'), 'field': 'department_id', 'width': 20, 'type': 'many2one'},
                    5: {'header': _('Section'), 'field': 'section_id', 'width': 20, 'type': 'many2one'},
                    6: {'header': _('Position'), 'field': 'job_id', 'width': 20, 'type': 'many2one'},
                    7: {'header': _('Level'), 'field': 'level_id', 'width': 20, 'type': 'many2one'},
                    8: {'header': _('Weight'), 'field': 'weight', 'width': 20, 'type': 'amount'},
                    9: {'header': _('Actual Screening'), 'field': 'actual_screening', 'width': 20},
                    10: {'header': _('Actual Calls'), 'field': 'actual_calls', 'width': 20},
                    11: {'header': _('Actual Invitation'), 'field': 'actual_invitation', 'width': 20},
                    12: {'header': _('Actual HR Accepted'), 'field': 'actual_hr_accepted', 'width': 20},
                    13: {'header': _('Actual Final Accepted'), 'field': 'actual_final_accepted', 'width': 20},
                }
            }]
        if report.type_report == 'actual_vs_target':
            return [{
                'Daily Target Report': {
                    0: {'header': _('Date'), 'field': 'date', 'width': 20},
                    1: {'header': _('Recruiter BU'), 'field': 'user_bu', 'width': 20, 'type': 'many2one'},
                    2: {'header': _('Recruiter'), 'field': 'recruiter_id', 'width': 20, 'type': 'many2one'},
                    3: {'header': _('BU'), 'field': 'bu_id', 'width': 20, 'type': 'many2one'},
                    4: {'header': _('Department'), 'field': 'department_id', 'width': 20, 'type': 'many2one'},
                    5: {'header': _('Section'), 'field': 'section_id', 'width': 20, 'type': 'many2one'},
                    6: {'header': _('Position'), 'field': 'job_id', 'width': 20, 'type': 'many2one'},
                    7: {'header': _('Level'), 'field': 'level_id', 'width': 20, 'type': 'many2one'},
                    8: {'header': _('Weight'), 'field': 'weight', 'width': 20, 'type': 'amount'},
                    9: {'header': _('Target Screening'), 'field': 'target_screening', 'width': 25},
                    10: {'header': _('Actual Screening'), 'field': 'actual_screening', 'width': 25},
                    11: {'header': _('Target Calls'), 'field': 'target_calls', 'width': 25},
                    12: {'header': _('Actual calls'), 'field': 'actual_calls', 'width': 25},
                    13: {'header': _('Target Invitation '), 'field': 'target_invitation',
                         'width': 25},
                    14: {'header': _('Actual invitation'), 'field': 'actual_invitation', 'width': 25},
                    15: {'header': _('Target HR accepted'), 'field': 'target_hr_accepted',
                         'width': 25},
                    16: {'header': _('Actual HR Accepted'), 'field': 'actual_hr_accepted', 'width': 25},
                    17: {'header': _('Target Final Accepted '), 'field': 'target_final_accepted', 'width': 25},
                    18: {'header': _('Actual Final Accepted'),
                         'field': 'actual_final_accepted', 'width': 25},
                }
            }]

    def _generate_report_content(self, workbook, report):
        self.write_array_header('Daily Target Report')
        if report.type_report == 'target':
            for line in report.line_ids:
                self.write_line(DailyTargetWrapper(line), 'Daily Target Report')
        if report.type_report == 'actual' or report.type_report == 'actual_vs_target' :
            for line in report.line_ids:
                count_actual_invitation = 0
                cvs = self.env['hr.applicant'].search([('create_uid','=',line.recruiter_id.id),('create_date','>=',report.date_from ),
                                                       ('create_date','<=',report.date_to ),('job_id','=',line.job_position_id.id)
                                                       ])
                if cvs:
                    # get done calls on cvs
                    actual_calls = self.env['mail.activity'].search(
                        [('real_create_uid', '=', line.recruiter_id.id), ('create_date', '>=', report.date_from),
                         ('create_date', '<=', report.date_to),
                         ('res_id', 'in', cvs.ids), ('activity_type_id', 'in', (2, 6, 7)),('active','=',False)])
                    actual_calls = len(actual_calls)
                    for cv in cvs:
                        # get first interview for each cv
                        actual_invitation = self.env['mail.activity'].search(
                            [('real_create_uid', '=', line.recruiter_id.id),('res_id', '=', cv.id),
                             ('create_date', '>=', report.date_from),('create_date', '<=', report.date_to),
                             ('res_model','=','hr.applicant'),('interview_result','!=',False),('active','=',False),
                             ('activity_type_id','=',5)],limit=1)
                        count_actual_invitation += len(actual_invitation)
                    # get done hr interviews  for cvs
                    hr_accepted = self.env['calendar.event'].search(
                        [('create_uid', '=', line.recruiter_id.id),
                         ('create_date', '>=', report.date_from), ('create_date', '<=', report.date_to),
                         ('res_model', '=', 'hr.applicant'),('res_id','in',cvs.ids),
                         ('interview_type_id', '=', 1),('is_interview_done','=',True)])

                    result= self.env['mail.activity'].search([('calendar_event_id','in',hr_accepted.ids),('active','=',False)],order ='write_date desc',limit = 1)
                    if result.interview_result == "Accepted":
                        hr_accepted = 1
                    else:
                        hr_accepted = 0
                    # get done final interviews for cvs
                    final_accepted = self.env['calendar.event'].search(
                        [('create_uid', '=', line.recruiter_id.id),
                         ('create_date', '>=', report.date_from), ('create_date', '<=', report.date_to),
                         ('res_model', '=', 'hr.applicant'),('res_id','in',cvs.ids),
                         ('interview_type_id', '=', 3),('is_interview_done','=',True)])
                    final_accepted = len(final_accepted)
                else:
                    actual_calls = 0
                    count_actual_invitation = 0
                    hr_accepted = 0
                    final_accepted = 0
                if report.type_report == 'actual':
                    self.write_line(ActualTargetWrapper(line,cvs,actual_calls,count_actual_invitation,hr_accepted,final_accepted), 'Daily Target Report')
                else:
                    self.write_line(Actual_Vs_TargetWrapper(line, cvs ,actual_calls,count_actual_invitation,hr_accepted,final_accepted), 'Daily Target Report')


class DailyTargetWrapper:
    def __init__(self, line):
        self.date = line.name
        self.user_bu = line.recruiter_bu_id
        self.recruiter_id = line.recruiter_id
        self.bu_id = line.bu_id
        self.department_id = line.department_id
        self.section_id = line.section_id
        self.job_id = line.job_id
        self.level_id = line.level_id
        self.weight = line.weight or 0.0
        self.target_screening = line.cvs or 0.0
        self.target_calls = round(self.target_screening * .8,2)
        self.target_invitation = round(self.target_calls * .3,2)
        self.target_hr_accepted = round(self.target_invitation * .35,2)
        self.target_final_accepted = round(self.target_hr_accepted * .5,2)

class ActualTargetWrapper:
    def __init__(self, line,cvs,actual_calls,count_actual_invitation,hr_accepted,final_accepted):
        self.date = line.name
        self.user_bu = line.recruiter_bu_id
        self.recruiter_id = line.recruiter_id
        self.bu_id = line.bu_id
        self.department_id = line.department_id
        self.section_id = line.section_id
        self.job_id = line.job_id
        self.level_id = line.level_id
        self.weight = line.weight or 0.0
        self.actual_screening = str(len(cvs))
        self.actual_calls = str(actual_calls)
        self.actual_invitation = str(count_actual_invitation)
        self.actual_hr_accepted = str(hr_accepted)
        self.actual_final_accepted = str(final_accepted)

class Actual_Vs_TargetWrapper:
    def __init__(self, line,cvs,actual_calls,count_actual_invitation,hr_accepted,final_accepted):
        self.date = line.name
        self.user_bu = line.recruiter_bu_id
        self.recruiter_id = line.recruiter_id
        self.bu_id = line.bu_id
        self.department_id = line.department_id
        self.section_id = line.section_id
        self.job_id = line.job_id
        self.level_id = line.level_id
        self.weight = line.weight or 0.0
        self.target_screening = str(line.cvs)
        self.actual_screening = str(len(cvs))
        self.target_calls = str(round(float(self.target_screening) * .8,2))
        self.actual_calls = str(actual_calls)
        self.target_invitation = str(round(float(self.target_calls) * .3,2))
        self.actual_invitation = str(count_actual_invitation)
        self.target_hr_accepted = str(round(float(self.target_invitation) * .35,2))
        self.actual_hr_accepted = str(hr_accepted)
        self.target_final_accepted = str(round(float(self.target_hr_accepted) * .5,2))
        self.actual_final_accepted = str(final_accepted)
