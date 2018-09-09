from odoo import models, fields, api
from datetime import datetime


class Offer(models.Model):
    _name = 'hr.offer'
    _inherit = ['mail.thread']

    @api.depends('application_id', 'application_id.job_id', 'application_id.partner_id')
    def _offer_name(self):
        for offer in self:
            name = []
            if offer.application_id.department_id.name: name.append(offer.application_id.department_id.name)
            if offer.application_id.job_id.name: name.append(offer.application_id.job_id.name)
            if offer.application_id.partner_id.name: name.append(offer.application_id.partner_id.name)
            name = ' / '.join(name)
            offer.name = name
            offer.offer_name = "Create Offer / " + name

    @api.depends('fixed_salary', 'variable_salary', 'housing_allowance', 'travel_allowance', 'mobile_allowance')
    def _compute_total_package(self):
        for offer in self:
            total_package = offer.fixed_salary + offer.variable_salary + \
                            offer.housing_allowance + offer.travel_allowance + offer.mobile_allowance
            offer.total_package = total_package

    name = fields.Char(compute=_offer_name, string='Name')
    offer_name = fields.Char(compute=_offer_name)
    application_id = fields.Many2one('hr.applicant')
    fixed_salary = fields.Float(string='Fixed Salary', track_visibility='onchange')
    variable_salary = fields.Float(string='Variable Salary', track_visibility='onchange')
    housing_allowance = fields.Float(string='Housing Allowance', track_visibility='onchange')
    travel_allowance = fields.Float(string='Travel Allowance', track_visibility='onchange')
    mobile_allowance = fields.Float(string='Mobile Allowance', track_visibility='onchange')
    issue_date = fields.Date(string='Issue Date', default=fields.Date.today)
    hiring_date = fields.Date(string="Hiring Date", track_visibility='onchange')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.user.company_id.currency_id)
    total_package = fields.Float(string='Total Package', compute=_compute_total_package, store=True)
    state = fields.Selection(
        [('offer', 'Offer'),
         ('hold', 'Hold'),
         ('pipeline', 'Pipeline'),
         ('hired', 'Hired'),
         ('not_join', 'Not Join'),
         ('reject', 'Reject Offer')], default='offer', string="Hiring Status", track_visibility='onchange',
        required=True)
    comment = fields.Text(string='Notes')
    reject_reason = fields.Many2one('reject.reason', string='Rejection Reason')


class RejectionReason(models.Model):
    _name = 'reject.reason'

    name = fields.Char(string='Name', required=True)
