from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class Offer(models.TransientModel):
    _name = "hr.offer.wizard"
    _inherits = {'hr.offer':'offer_id'}

    offer_id = fields.Many2one('hr.offer',string="Offer",auto_join=True)

    @api.multi
    def action_save(self):
        self.ensure_one()
        self.application_id.offer_id = self.offer_id
        return {'type': 'ir.actions.act_window_close'}

    @api.depends('application_id.department_id.business_unit_id', 'application_id', 'application_id.job_id', 'application_id.partner_id')
    def _offer_name(self):
        for offer in self:
            name = []
            if offer.application_id.department_id.business_unit_id.name:
                name.append(offer.application_id.department_id.business_unit_id.name)
            if offer.application_id.department_id.name: name.append(offer.application_id.department_id.name)
            if offer.application_id.job_id.name: name.append(offer.application_id.job_id.name)
            if offer.application_id.partner_id.name: name.append(offer.application_id.partner_id.name)
            name = ' / '.join(name)
            offer.name = name
            offer.offer_name = "Create Offer / " + name

    @api.depends('fixed_salary', 'variable_salary', 'housing_allowance', 'travel_allowance', 'mobile_allowance',
                 'shifts_no', 'hour_rate', 'offer_type')
    def _compute_total_package(self):
        for offer in self:
            if offer.offer_type == "normal_offer":
                total_package = offer.fixed_salary + offer.variable_salary + \
                                offer.housing_allowance + offer.travel_allowance + offer.mobile_allowance
                offer.total_package = total_package
            elif offer.offer_type == "nursing_offer":
                total_package = offer.hour_rate * offer.shifts_no * offer.shift_hours + \
                                offer.housing_allowance + offer.travel_allowance + offer.mobile_allowance
                offer.total_package = total_package

    name = fields.Char(string="Name", compute='_offer_name')
    offer_name = fields.Char(compute=_offer_name)
    total_package = fields.Float(string='Total Package', compute=_compute_total_package, store=True)

    @api.onchange('shifts_no')
    def onchange_shifts_no(self):
        self.hour_rate = False

    @api.onchange('offer_type')
    def onchange_offer_type(self):
        self.hour_rate = False
        self.fixed_salary = False
        self.variable_salary = False
        self.housing_allowance = False
        self.travel_allowance = False
        self.mobile_allowance = False
        self.shifts_no = False
