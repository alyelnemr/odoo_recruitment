from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HRPolicyOfferAndHire(models.Model):
    _name = 'hr.policy.offer.and.hire.level'

    level = fields.Many2one('job.level', string='Job Level', readonly=True)
    offer = fields.Integer('Offer', required=True, default=0)
    hire = fields.Integer('Hire', required=True, default=0)
    total = fields.Integer('Total', readonly=True, compute="_compute_total")
    hr_policy = fields.Many2one('hr.policy', string='HR Policy')

    @api.depends('offer', 'hire')
    @api.one
    def _compute_total(self):
        self.total = self.hire + self.offer


class HRPolicy(models.Model):
    _name = 'hr.policy'

    name = fields.Char(string="Policy Name")
    day = fields.Integer(string="Days")
    month = fields.Integer(string="Months")
    year = fields.Integer(string="Years")
    hr_policy_type = fields.Selection([('application_period', 'Application Period'),
         ('offer_and_hire', 'Offer and Hire')], string='Policy Type', default='application_period', track_visibility='onchange', required=True)
    offer_and_hire_level = fields.One2many('hr.policy.offer.and.hire.level', 'hr_policy', string='Levels')

    @api.multi
    def unlink(self):
        for line in self:
            raise ValidationError(_('Cannot Delete HR Policy.'))
        return super(HRPolicy, self).unlink()
