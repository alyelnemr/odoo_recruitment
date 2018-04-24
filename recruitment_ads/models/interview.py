from odoo import models, fields, api


class Interview(models.Model):
    _inherit = 'calendar.event'

    hr_applicant_id = fields.Many2one('hr.applicant', 'Applicant', compute='_get_applicant')
    type = fields.Selection([('normal', 'Normal'), ('interview', 'Interview')], string="Type", default='normal')
    extra_followers_ids = fields.Many2many('res.partner', 'interview_followers_rel', 'interview_id', 'partner_id',string="Followers")
    @api.one
    @api.depends('partner_ids','message_follower_ids')
    def _get_extra_followers(self):
        self.extra_followers_ids = self.message_follower_ids.mapped('partner_id') - self.partner_ids

    def _set_extra_followers(self):
        self.message_subscribe((self.extra_followers_ids-self.message_follower_ids.mapped('partner_id')).ids)
        self._message_auto_subscribe_notify((self.extra_followers_ids-self.message_follower_ids.mapped('partner_id')).ids)


    @api.depends('res_id', 'res_model_id')
    def _get_applicant(self):
        for r in self:
            if r.res_model_id.model == 'hr.applicant':
                r.hr_applicant_id = self.env['hr.applicant'].browse([r.res_id])
