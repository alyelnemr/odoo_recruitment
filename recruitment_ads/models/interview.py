from odoo import models,fields,api


class Interview(models.Model):
    _name = 'calendar.event.interview'
    _inherit = 'calendar.event'

    @api.model
    def _default_partners(self):
        """ When active_model is res.partner, the current partners should be attendees """
        partners = self.env.user.partner_id
        active_id = self._context.get('active_id')
        if self._context.get('active_model') == 'res.partner' and active_id:
            if active_id not in partners.ids:
                partners |= self.env['res.partner'].browse(active_id)
        return partners

    name = fields.Char('Interview Subject')
    hr_applicant_id = fields.Many2one('hr.applicant','Applicant',compute='_get_applicant')

    #One2many and Many2Many
    categ_ids = fields.Many2many('calendar.event.type', 'interview_category_rel', 'interview_id', 'type_id', 'Tags')
    attendee_ids = fields.One2many('calendar.attendee', 'interview_id', 'Participant', ondelete='cascade')
    partner_ids = fields.Many2many('res.partner', 'interview_partner_rel', string='Assigned To',states={'done': [('readonly', True)]}, default=_default_partners)
    alarm_ids = fields.Many2many('calendar.alarm', 'interview_calendar_alarm_rel', string='Reminders',
                                 ondelete="restrict", copy=False)
    activity_ids = fields.One2many('mail.activity', 'interview_id', string='Activities')

    @api.depends('res_id','res_model_id')
    def _get_applicant(self):
        for r in self:
            if r.res_model_id.name == 'hr.applicant':
                r.hr_applicant_id = self.env['hr.applicant'].browse([r.res_id])

    @api.model
    def create(self, vals):
        res = super(Interview, self).create(vals)
        if res.hr_applicant_id:
            activity_val = {
                'res_id':res.res_id,
                'res_model_id':res.res_model_id.id,
                'activity_type_id':self.env.ref("recruitment_ads.mail_activity_type_data_interview"),
                'date_deadline':res.start_date,
            }
            res.activity_ids = [(0,0,activity_val)]
