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

    @api.depends('application_id')
    def _offer_name(self):
        department_name = ""
        job_name = ""
        if self.application_id.department_id:
            department_name = self.application_id.department_id.name + " / "
        if self.application_id.job_id.name:
            job_name = self.application_id.job_id.name + " / "
        offer_name = "Create Offer / " + department_name + job_name + self.application_id.partner_id.name
        self.offer_name = offer_name
        self.name = department_name + job_name + self.application_id.partner_id.name + " Offer"

    @api.depends('fixed_salary', 'variable_salary', 'housing_allowance', 'travel_allowance', 'mobile_allowance')
    def _compute_total_package(self):
        total_package = self.fixed_salary + self.variable_salary + self.housing_allowance + self.travel_allowance \
                        + self.mobile_allowance
        self.total_package = total_package

    name = fields.Char(string="Name", compute='_offer_name')
    offer_name = fields.Char(compute=_offer_name)
    total_package = fields.Float(string='Total Package', compute=_compute_total_package, store=True)
