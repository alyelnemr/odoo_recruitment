from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HRPolicyCEOApproval(models.Model):
    _name = 'hr.policy.ceo.approval'

    approval_group = fields.Many2one('hr.master.approval.group', string='Approval Group', ondelete='cascade')
    hr_policy = fields.Many2one('hr.policy', string='HR Policy')


class HRPolicyOfferAndHire(models.Model):
    _name = 'hr.policy.offer.and.hire.level'

    level = fields.Many2one('job.level', string='Job Level', ondelete='cascade')
    offer = fields.Char('Offer', required=True, default=0)
    hire = fields.Char('Hire', required=True, default=0)
    total = fields.Integer('Total', readonly=True, compute="_compute_total")
    hr_policy = fields.Many2one('hr.policy', string='HR Policy')

    @api.depends('offer', 'hire')
    @api.one
    def _compute_total(self):
        if self.offer.isdigit() and self.hire.isdigit():
            self.total = int(self.hire) + int(self.offer)

    @api.onchange('offer')
    def _on_change_check_offer_numbers_only(self):
        if not self.offer.isdigit():
            raise ValidationError(_('Offer must be numbers only!'))

    @api.onchange('hire')
    def _on_change_check_hire_numbers_only(self):
        if not self.hire.isdigit():
            raise ValidationError(_('Hire must be numbers only!'))

class HRPolicy(models.Model):
    _name = 'hr.policy'

    name = fields.Char(string="Policy Name")
    day = fields.Integer(string="Days")
    month = fields.Integer(string="Months")
    year = fields.Integer(string="Years")
    ceo_approval_amount = fields.Integer(string="Max Offer Amount", default=15000)
    ceo_approval_group = fields.One2many('hr.policy.ceo.approval', 'hr_policy', string='Approval Group')
    hr_policy_type = fields.Selection([('application_period', 'Application Period'),
                                       ('offer_and_hire', 'Offer and Hire'),
                                       ('ceo_approval_amount', 'CEO Approval Amount')], string='Policy Type',
                                      default='application_period', required=True)
    offer_and_hire_level = fields.One2many('hr.policy.offer.and.hire.level', 'hr_policy', string='Levels')

    @api.multi
    def unlink(self):
        for line in self:
            raise ValidationError(_('Cannot Delete HR Policy.'))
        return super(HRPolicy, self).unlink()
