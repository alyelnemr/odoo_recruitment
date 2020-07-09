from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HRPolicyOfferAndHire(models.Model):
    _name = 'hr.policy.offer.and.hire.level'

    level = fields.Many2one('job.level', string='Job Level', readonly=True)


class HRPolicy(models.Model):
    _name = 'hr.policy'

    name = fields.Char(string="Policy Name")
    day = fields.Integer(string="Days")
    month = fields.Integer(string="Months")
    year = fields.Integer(string="Years")

    @api.multi
    def unlink(self):
        for line in self:
            raise ValidationError(_('Cannot Delete HR Policy.'))
        return super(HRPolicy, self).unlink()
