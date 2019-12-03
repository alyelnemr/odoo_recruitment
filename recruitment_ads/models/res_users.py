from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    business_unit_id = fields.Many2one('business.unit', string="Business Unit")