from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ComplianceReportWizard(models.TransientModel):
    _name = "compliance.report.wizard"

    date_from = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_to = fields.Date(string='End Date', required=True, default=fields.Date.today)
    recruiter_ids = fields.Many2many('res.users', string='Recruiter Responsible')
    bu_ids = fields.Many2many('business.unit', string='Business Unit')

    @api.constrains('date_from', 'date_to')
    def check_dates(self):
        for r in self:
            if r.date_to < r.date_from:
                raise ValidationError(_("You can't select start date greater than end date"))

    @api.onchange('bu_ids')
    def onchange_bu_ids(self):
        self.recruiter_ids = False
        if  self.bu_ids:
            recruiters = self.env['res.users'].search(
                ['|', ('business_unit_id', 'in', self.bu_ids.ids), ('multi_business_unit_id', 'in', self.bu_ids.ids)])
        else:
            recruiters = self.env['res.users'].search([])
        return {'domain': {'recruiter_ids': [('id', 'in', recruiters.ids)]}}

    @api.multi
    def button_export_xlsx(self):
        self.ensure_one()
        if self.bu_ids:
            if not self.recruiter_ids:
                self.recruiter_ids = self.env['res.users'].search(['|',('business_unit_id', 'in', self.bu_ids.ids),('multi_business_unit_id','in',self.bu_ids.ids)])
        else:
            if not self.recruiter_ids:
                self.recruiter_ids = self.env['res.users'].search([])


        report = self.env.ref('recruitment_ads.action_compliance_report_xlsx')
        return report.report_action(self)
