from odoo import _, models
import re

class ComplianceReportXslx(models.AbstractModel):
    _name = 'report.recruitment_ads.compliance_report_xlsx'
    _inherit = 'report.recruitment_ads.abstract_report_xlsx'

    def _get_report_name(self):
        return _('Compliance Report')

    def _get_report_sheets(self,report):
        sheets = []
        sheets.append({
            'Compliance Report': {
                0: {'header': _('Recruiter Responsible'), 'field': 'user_id', 'width': 20, 'type': 'many2one'},
                1: {'header': _('Recruiter BU'), 'field': 'generated_by_bu_id', 'width': 20, 'type': 'many2one'},
                2: {'header': _('Total applications'), 'field': 'total_application', 'width': 20},
                3: {'header': _('Total calls'), 'field': 'no_calls', 'width': 20},
                4: {'header': _('Done calls'), 'field': 'done_call', 'width': 20},
                5: {'header': _('Total Interviews'), 'field': 'total_interview', 'width': 20},
                6: {'header': _('Done Interviews'), 'field': 'done_interview', 'width': 20},
                7: {'header': _('Total Offers'), 'field': 'total_offers', 'width': 20},
                8: {'header': _('Hired'), 'field': 'no_hire', 'width': 20},

            }
        })
        return sheets

    def _generate_report_content(self, workbook, report):
        if report:
            self.write_array_header('Compliance Report')
            domain = [('create_date', '>=', report.date_from + ' 00:00:00'),
                      ('create_date', '<=', report.date_to + ' 23:59:59'),
                      ]
            for rec in set(report.application_ids.mapped('create_uid')):
                total_app = report.application_ids.filtered(lambda x: x.create_uid == rec).mapped(id)
                call_domain =[
                    ('active', '=', False),
                    ('res_model', '=', 'hr.applicant'),
                    ('real_create_uid', '=', rec.id),
                    ('activity_type_id', 'in', (2, 6, 7),)
                ]
                interviews_domain = [
                    ('active', '=', False),
                    ('res_model', '=', 'hr.applicant'),
                    ('real_create_uid', '=', rec.id),
                    ('activity_type_id', '=', 5),]

                offers_domain = [('create_uid', '=', rec.id),]
                if report.bu_ids:
                    offers_domain.append(('business_unit_id','in',report.bu_ids.ids))
                    # interviews_domain.append(('res_id.job_id.business_unit_id', 'in', report.bu_ids.ids))
                    # call_domain.append(('res_id.job_id', 'in', report.bu_ids.ids),)

                call_domain.extend(domain)
                total_calls = self.env['mail.activity'].search(call_domain)
                no_done_calls=total_calls.filtered(lambda x: x.call_result_id != False)


                interviews_domain.extend(domain)
                interviews = self.env['mail.activity'].search(interviews_domain)
                done_interviews = interviews.filtered(lambda x: x.interview_result != False)


                offers_domain.extend(domain)
                offers = self.env['hr.offer'].search(offers_domain)
                hired = offers.filtered(lambda x: x.state == 'hired')

                total_app=str(len(total_app))
                total_calls=str(len(total_calls))
                no_done_calls=str(len(no_done_calls))
                interviews=str(len(interviews))
                done_interviews=str(len(done_interviews))
                offers=str(len(offers))
                hired=str(len(hired))


                self.write_line(ComplianceWrapper(total_app,rec,total_calls,no_done_calls,interviews,done_interviews,
                                                  offers,hired), 'Compliance Report')



class ComplianceWrapper:
    def __init__(self,total_app,recruiter,total_calls,done_calls,no_interviews,done_interviews,offers,hired):
        self.user_id = recruiter
        self.generated_by_bu_id = recruiter.business_unit_id
        self.total_application= total_app
        self.no_calls = total_calls
        self.done_call=done_calls
        self.total_interview = no_interviews
        self.done_interview = done_interviews
        self.total_offers = offers
        self.no_hire = hired