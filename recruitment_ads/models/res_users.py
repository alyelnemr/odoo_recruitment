from odoo import models, fields ,api


class ResUsers(models.Model):
    _inherit = 'res.users'

    business_unit_id = fields.Many2one('business.unit', string="Business Unit")
    multi_business_unit_id = fields.Many2many('business.unit', string="Other Business Unit")

    @api.onchange('business_unit_id')
    def onchange_bu_ids(self):
       self.multi_business_unit_id = False