from odoo import models, _


class GenerateMonthlyTargetReportXslx(models.AbstractModel):
    _name = 'report.recruitment_ads.report_generate_monthly_target_xlsx'
    _inherit = 'report.recruitment_ads.abstract_report_xlsx'

    def _get_report_name(self):
        return _('Monthly target Report')

    def _get_report_sheets(self, report):
        if report.type_report == 'target':
            return [{
            'Monthly Target Report': {
                0: {'header': _('Recruiter'), 'field': 'recruiter_id', 'width': 20, 'type': 'many2one'},
                1: {'header': _('Date'), 'field': 'date', 'width': 20},
                2: {'header': _('Recruiter BU'), 'field': 'user_bu', 'width': 20, 'type': 'many2one'},
                3: {'header': _('BU'), 'field': 'bu_id', 'width': 20, 'type': 'many2one'},
                4: {'header': _('Department'), 'field': 'department_id', 'width': 20, 'type': 'many2one'},
                5: {'header': _('Section'), 'field': 'section_id', 'width': 20, 'type': 'many2one'},
                6: {'header': _('Position'), 'field': 'job_id', 'width': 20, 'type': 'many2one'},
                7: {'header': _('Level'), 'field': 'level_id', 'width': 20, 'type': 'many2one'},
                8: {'header': _('Position Type'), 'field': 'position_type', 'width': 20},
                9: {'header': _('Expecting Offer Date'), 'field': 'expected_offer_date', 'width': 20},
                10: {'header': _('Expecting Hire Date'), 'field': 'expected_hire_date', 'width': 20},
                11: {'header': _('MP'), 'field': 'mp', 'width': 20, 'type': 'amount'},
                12: {'header': _('Current'), 'field': 'current', 'width': 20, 'type': 'amount'},
                13: {'header': _('Replacement'), 'field': 'replacement', 'width': 20, 'type': 'amount'},
                14: {'header': _('Vacant'), 'field': 'vacant', 'width': 20, 'type': 'amount'},
                15: {'header': _('Total Need'), 'field': 'total_need', 'width': 20, 'type': 'amount'},
                16: {'header': _('Offer Target'), 'field': 'offer_target', 'width': 20, 'type': 'amount'},
                17: {'header': _('Offer Weight'), 'field': 'offer_weight', 'width': 20, 'type': 'amount'},
                18: {'header': _('Hire Target'), 'field': 'hire_target', 'width': 20, 'type': 'amount'},
                19: {'header': _('Hire Weight'), 'field': 'hire_weight', 'width': 20, 'type': 'amount'},
            }
        }]
        if report.type_report == 'actual':
            return [{
            'Monthly Target Report': {
                0: {'header': _('Recruiter'), 'field': 'recruiter_id', 'width': 20, 'type': 'many2one'},
                1: {'header': _('Date'), 'field': 'date', 'width': 20},
                2: {'header': _('Recruiter BU'), 'field': 'user_bu', 'width': 20, 'type': 'many2one'},
                3: {'header': _('BU'), 'field': 'bu_id', 'width': 20, 'type': 'many2one'},
                4: {'header': _('Department'), 'field': 'department_id', 'width': 20, 'type': 'many2one'},
                5: {'header': _('Section'), 'field': 'section_id', 'width': 20, 'type': 'many2one'},
                6: {'header': _('Position'), 'field': 'job_id', 'width': 20, 'type': 'many2one'},
                7: {'header': _('Level'), 'field': 'level_id', 'width': 20, 'type': 'many2one'},
                8: {'header': _('Position Type'), 'field': 'position_type', 'width': 20},
                9: {'header': _('Actual  Offer Date'), 'field': 'actual_offer_date', 'width': 20},
                10: {'header': _('Actual Hire Date'), 'field': 'actual_hire_date', 'width': 20},
                11: {'header': _('MP'), 'field': 'mp', 'width': 20, 'type': 'amount'},
                12: {'header': _('Current'), 'field': 'current', 'width': 20, 'type': 'amount'},
                13: {'header': _('Replacement'), 'field': 'replacement', 'width': 20, 'type': 'amount'},
                14: {'header': _('Vacant'), 'field': 'vacant', 'width': 20, 'type': 'amount'},
                15: {'header': _('Total Need'), 'field': 'total_need', 'width': 20, 'type': 'amount'},
                16: {'header': _('Actual Offer '), 'field': 'actual_offer', 'width': 20 },
                17: {'header': _('Actual Offer Weight'), 'field': 'actual_offer_weight', 'width': 20},
                18: {'header': _('Actual Hire'), 'field': 'hire_actual', 'width': 20 },
                19: {'header': _('Actual Hire Weight'), 'field': 'actual_hire_weight', 'width': 20},
            }
        }]
        if report.type_report == 'actual_vs_target':
            return [{
            'Monthly Target Report': {
                0: {'header': _('Recruiter'), 'field': 'recruiter_id', 'width': 20, 'type': 'many2one'},
                1: {'header': _('Date'), 'field': 'date', 'width': 20},
                2: {'header': _('Recruiter BU'), 'field': 'user_bu', 'width': 20, 'type': 'many2one'},
                3: {'header': _('BU'), 'field': 'bu_id', 'width': 20, 'type': 'many2one'},
                4: {'header': _('Department'), 'field': 'department_id', 'width': 20, 'type': 'many2one'},
                5: {'header': _('Section'), 'field': 'section_id', 'width': 20, 'type': 'many2one'},
                6: {'header': _('Position'), 'field': 'job_id', 'width': 20, 'type': 'many2one'},
                7: {'header': _('Level'), 'field': 'level_id', 'width': 20, 'type': 'many2one'},
                8: {'header': _('Position Type'), 'field': 'position_type', 'width': 20},
                9: {'header': _('Actual Offer Date'), 'field': 'actual_offer_date', 'width': 25},
                10: {'header': _('Expected Offer Date'), 'field': 'target_offer_date', 'width': 25},
                11: {'header': _('Actual Hire Date '), 'field': 'actual_hire_date', 'width': 25},
                12: {'header': _('Expected Hire Date '),
                     'field': 'target_hire_date', 'width': 25},
                13: {'header': _('MP'), 'field': 'mp', 'width': 20, 'type': 'amount'},
                14: {'header': _('Current'), 'field': 'current', 'width': 20, 'type': 'amount'},
                15: {'header': _('Replacement'), 'field': 'replacement', 'width': 20, 'type': 'amount'},
                16: {'header': _('Vacant'), 'field': 'vacant', 'width': 20, 'type': 'amount'},
                17: {'header': _('Total Need'), 'field': 'total_need', 'width': 20, 'type': 'amount'},
                18: {'header': _('Actual Offer '), 'field': 'actual_offer', 'width': 25 },
                19: {'header': _('Target Offer '), 'field': 'target_offer', 'width': 25},
                20: {'header': _('Actual Offer Weight'), 'field': 'actual_offer_weight', 'width': 25},
                21: {'header': _('Target Offer Weight'),
                     'field': 'target_offer_weight', 'width': 25},
                22: {'header': _('Actual Hire'), 'field': 'hire_actual', 'width': 25 },
                23: {'header': _('Target Hire'), 'field': 'target_hire', 'width': 25},
                24: {'header': _('Actual Hire Weight'), 'field': 'actual_hire_weight', 'width': 25},
                25: {'header': _('Target Hire Weight'),
                     'field': 'target_offer_weight', 'width': 25},
            }
        }]

    def _generate_report_content(self, workbook, report):
        self.write_array_header('Monthly Target Report')
        if report.type_report == 'target':
            for line in report.line_ids:
                self.write_line(MonthlyTargetWrapper(line), 'Monthly Target Report')
        if report.type_report == 'actual' or report.type_report == 'actual_vs_target' :
            for line in report.line_ids:
                offer = self.env['hr.offer'].search([('issue_date','>=',line.start_date),
                         ('create_uid','=',line.recruiter_id.id),('job_id','=',line.job_position_id.id)], order = 'issue_date asc')
                hired = self.env['hr.offer'].search(
                    [('hiring_date', '>=', line.start_date),
                     ('create_uid', '=', line.recruiter_id.id), ('job_id', '=',line.job_position_id.id),('state','=','hired')], order = 'hiring_date asc')
                if offer:
                     actual_offer_date = offer[0].issue_date
                     actual_offer = len(offer)
                else:
                    actual_offer_date = '0-0-0'
                    actual_offer = 0

                if hired :
                     actual_hire_date =  hired[0].hiring_date
                     actual_hire = len(hired)
                else:
                    actual_hire_date = '0-0-0'
                    actual_hire = 0

                actual_offer_weight = actual_offer * line.level_id.weight
                actual_hire_weight = actual_hire * line.level_id.weight

                if report.type_report == 'actual' :
                    self.write_line(MonthlyActualWrapper(line,actual_offer_date,actual_hire_date,actual_offer,actual_hire,actual_offer_weight,actual_hire_weight), 'Monthly Target Report')
                else:
                    self.write_line(
                        MonthlyActualVSTargetWrapper(line, actual_offer_date, actual_hire_date, actual_offer,
                                                     actual_hire, actual_offer_weight, actual_hire_weight),
                        'Monthly Target Report')

class MonthlyTargetWrapper:
    def __init__(self, line):
        self.recruiter_id = line.recruiter_id
        self.user_bu = line.recruiter_bu_id
        self.date = line.start_date9
        self.bu_id = line.bu_id
        self.department_id = line.department_id
        self.section_id = line.section_id
        self.job_id = line.job_id
        self.level_id = line.level_id
        self.position_type = line.position_type
        self.expected_offer_date = line.expecting_offer_date
        self.expected_hire_date = line.expecting_hire_date
        self.mp = line.man_power
        self.current = line.current_emp
        self.replacement = line.replacement_emp
        self.vacant = line.vacant
        self.total_need = line.total_need
        self.offer_target = line.offer_target
        self.offer_weight = line.offer_weight
        self.hire_target = line.hire_target
        self.hire_weight = line.hire_weight

class MonthlyActualWrapper:
    def __init__(self, line,actual_offer_date,actual_hire_date,actual_offer,actual_hire,actual_offer_weight,actual_hire_weight):
        self.recruiter_id = line.recruiter_id
        self.user_bu = line.recruiter_bu_id
        self.date = line.start_date
        self.bu_id = line.bu_id
        self.department_id = line.department_id
        self.section_id = line.section_id
        self.job_id = line.job_id
        self.level_id = line.level_id
        self.position_type = line.position_type
        self.actual_offer_date = actual_offer_date
        self.actual_hire_date = actual_hire_date
        self.mp = line.man_power
        self.current = line.current_emp
        self.replacement = line.replacement_emp
        self.vacant = line.vacant
        self.total_need = line.total_need
        self.actual_offer = str(actual_offer)
        self.actual_offer_weight = str(actual_offer_weight)
        self.hire_actual = str(actual_hire)
        self.actual_hire_weight = str(actual_hire_weight)

class MonthlyActualVSTargetWrapper:
    def __init__(self, line,actual_offer_date,actual_hire_date,actual_offer,actual_hire,actual_offer_weight,actual_hire_weight):
        self.recruiter_id = line.recruiter_id
        self.user_bu = line.recruiter_bu_id
        self.date = line.start_date
        self.bu_id = line.bu_id
        self.department_id = line.department_id
        self.section_id = line.section_id
        self.job_id = line.job_id
        self.level_id = line.level_id
        self.position_type = line.position_type
        self.actual_offer_date = actual_offer_date
        self.target_offer_date = line.expecting_offer_date
        self.actual_hire_date = actual_hire_date
        self.target_hire_date = line.expecting_hire_date
        self.mp = line.man_power
        self.current = line.current_emp
        self.replacement = line.replacement_emp
        self.vacant = line.vacant
        self.total_need = line.total_need
        self.actual_offer = str(actual_offer)
        self.target_offer = str(line.offer_target)
        self.actual_offer_weight = str(actual_offer_weight)
        self.target_offer_weight = str(line.offer_weight)
        self.hire_actual = str(actual_hire)
        self.target_hire = str(line.hire_target)
        self.actual_hire_weight = str(actual_hire_weight)
        self.target_offer_weight = str(line.hire_weight)

