from odoo import models, _


class GenerateDailyTargetReportXslx(models.AbstractModel):
    _name = 'report.recruitment_ads.report_generate_daily_target_xlsx'
    _inherit = 'report.recruitment_ads.abstract_report_xlsx'

    def _get_report_name(self):
        return _('Daily target Report')

    def _get_report_sheets(self, report):
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

    def _generate_report_content(self, workbook, report):
        self.write_array_header('Daily Target Report')
        for line in report.line_ids:
            self.write_line(DailyTargetWrapper(line), 'Daily Target Report')


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
        self.target_calls = self.target_screening * .8
        self.target_invitation = self.target_calls * .3
        self.target_hr_accepted = self.target_invitation * .35
        self.target_final_accepted = self.target_hr_accepted * .5
