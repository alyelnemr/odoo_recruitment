from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ResUsers(models.Model):
    _inherit = 'res.users'

    business_unit_id = fields.Many2one('business.unit', string="Business Unit")
    multi_business_unit_id = fields.Many2many('business.unit', string="Other Business Unit")

    @api.onchange('business_unit_id')
    def onchange_bu_ids(self):
        self.multi_business_unit_id = False

    @api.model
    def create(self, vals):
        res = super(ResUsers, self).create(vals)
        res.partner_id.email = res.login
        if res.has_group('hr_recruitment.group_hr_recruitment_user') \
                and res.has_group('recruitment_ads.group_view_setup_approval_cycle') \
                and not (res.has_group('recruitment_ads.group_hr_recruitment_coordinator') or
                         res.has_group('hr_recruitment.group_hr_recruitment_manager')):
            raise ValidationError(_('Officer is not allowed to access Approval Cycles.'))
        return res

    @api.multi
    def write(self, vals):
        res = super(ResUsers, self).write(vals)
        if self.has_group('hr_recruitment.group_hr_recruitment_user') \
                and self.has_group('recruitment_ads.group_view_setup_approval_cycle') \
                and not (self.has_group('recruitment_ads.group_hr_recruitment_coordinator') or
                         self.has_group('hr_recruitment.group_hr_recruitment_manager')):
            raise ValidationError(_('Officer is not allowed to access Approval Cycles.'))
        return res

    @api.multi
    def unlink(self):
        if self.env.ref('recruitment_ads.website_user_root', False).id in self.ids:
            raise UserError(_(
                'You can not remove the website admin user as it is used internally for resources created by Odoo (updates, module installation, ...)'))
        return super(ResUsers, self).unlink()
