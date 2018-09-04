from odoo import models, fields, api
from datetime import datetime


class Offer(models.Model):
    _name = 'hr.offer'

    application_id = fields.Many2one('hr.applicant')
    application_name = fields.Char(related='application_id.partner_name')
    job_id = fields.Many2one('hr.job', string='Applied Job', related='application_id.job_id')
    fixed_salary = fields.Float(string='Fixed Salary')
    variable_salary = fields.Float(string='Variable Salary')
    housing_allowance = fields.Float(string='Housing Allowance')
    travel_allowance = fields.Float(string='Travel Allowance')
    mobile_allowance = fields.Float(string='Mobile Allowance')
    issue_date = fields.Date(string='Issue Date', default=fields.Date.today)
    currency_id = fields.Many2one('res.currency',default=lambda self:self.env.user.company_id.currency_id)

    @api.depends('application_id')
    def _offer_name(self):
        offer_name = "Create Offer / " + self.application_id.department_id.name + " / " \
                     + self.application_id.job_id.name + " / " + self.application_id.partner_id.name
        self.offer_name = offer_name

    @api.depends('fixed_salary', 'variable_salary', 'housing_allowance', 'travel_allowance', 'mobile_allowance')
    def _compute_total_package(self):
        total_package = self.fixed_salary + self.variable_salary + self.housing_allowance + self.travel_allowance \
                        + self.mobile_allowance
        self.total_package = total_package

    offer_name = fields.Char(compute=_offer_name)
    total_package = fields.Float(string='Total Package', compute=_compute_total_package, store=True)
