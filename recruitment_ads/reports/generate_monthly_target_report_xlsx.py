from odoo import models, _


class GenerateMonthlyTargetReportXslx(models.AbstractModel):
    _name = 'report.recruitment_ads.report_generate_monthly_target_xlsx'
    _inherit = 'report.recruitment_ads.abstract_report_xlsx'

    def _get_report_name(self):
        return _('Monthly target Report')

    def _get_report_sheets(self, report):
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
                15: {'header': _('Offer Target'), 'field': 'offer_target', 'width': 20, 'type': 'amount'},
                16: {'header': _('Offer Weight'), 'field': 'offer_weight', 'width': 20, 'type': 'amount'},
                17: {'header': _('Hire Target'), 'field': 'hire_target', 'width': 20, 'type': 'amount'},
                18: {'header': _('Hire Weight'), 'field': 'hire_weight', 'width': 20, 'type': 'amount'},
            }
        }]

    def _generate_report_content(self, workbook, report):
        self.write_array_header('Monthly Target Report')
        for line in report.line_ids:
            self.write_line(MonthlyTargetWrapper(line), 'Monthly Target Report')


class MonthlyTargetWrapper:
    def __init__(self, line):
        self.recruiter_id = line.recruiter_id
        self.user_bu = line.recruiter_bu_id
        self.date = line.start_date
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
        self.offer_target = line.offer_target
        self.offer_weight = line.offer_weight
        self.hire_target = line.hire_target
        self.hire_weight = line.hire_weight
