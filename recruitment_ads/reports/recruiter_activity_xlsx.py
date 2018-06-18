from odoo import _, models

class GeneralLedgerXslx(models.AbstractModel):
    _name = 'report.recruitment_ads.report_recruiter_activity_xlsx'
    _inherit = 'report.recruitment_ads.abstract_report_xlsx'

    def _get_report_name(self):
        return _('Recruiter Activity')

    def _get_report_columns(self, report):
        return {
            0: {'header': _('Recruiter Responsible'), 'field': 'user_id', 'width': 11},
            1: {'header': _('Applicant Name'), 'field': 'partner_name', 'width': 18},
            2: {'header': _('Date'), 'field': 'create_date', 'width': 8},
            3: {'header': _('CV Source'), 'field': 'source_id', 'width': 9},
            4: {'header': _('Department'), 'field': 'department_id', 'width': 25},
            5: {'header': _('Job Position'), 'field': 'job_id', 'width': 40},
        }

    def _generate_report_content(self, workbook, report):
        self.write_array_header()
        self.write_array_title('Calls')
