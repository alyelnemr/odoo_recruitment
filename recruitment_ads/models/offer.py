from odoo import models, fields, api


class Offer(models.Model):
    _name = 'hr.offer'
    _inherit = ['mail.thread']

    @api.depends('application_id', 'application_id.job_id', 'application_id.partner_id')
    def _offer_name(self):
        for offer in self:
            name = (offer.application_id.job_id.name or '') + " / " + (offer.application_id.partner_id.name or '')
            offer.name = name
            offer_name = "Create Offer / " + name
            offer.offer_name = offer_name

    @api.depends('fixed_salary', 'variable_salary', 'housing_allowance', 'travel_allowance', 'mobile_allowance')
    def _compute_total_package(self):
        for offer in self:
            total_package = offer.fixed_salary + offer.variable_salary + \
                            offer.housing_allowance + offer.travel_allowance + offer.mobile_allowance
            offer.total_package = total_package

    name = fields.Char(compute=_offer_name, string='Name')
    offer_name = fields.Char(compute=_offer_name)
    application_id = fields.Many2one('hr.applicant')
    application_name = fields.Char(related='application_id.partner_name')
    job_id = fields.Many2one('hr.job', string='Applied Job', related='application_id.job_id')
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
    reject_reason = fields.Selection([('1', 'r1')], string='Rejection Reason')
