from odoo import models, fields, api
from odoo.addons.calendar.models.calendar import Meeting


class Interview(models.Model):
    _inherit = 'calendar.event'

    hr_applicant_id = fields.Many2one('hr.applicant', 'Applicant', compute='_get_applicant')
    type = fields.Selection([('normal', 'Normal'), ('interview', 'Interview')], string="Type", default='normal')
    extra_followers_ids = fields.Many2many('res.partner', string="Followers", compute='_get_extra_followers',
                                           inverse='_set_extra_followers')

    @api.model
    def create(self, values):
        if not 'user_id' in values:  # Else bug with quick_create when we are filter on an other user
            values['user_id'] = self.env.user.id

        # compute duration, if not given
        if not 'duration' in values:
            values['duration'] = self._get_duration(values['start'], values['stop'])

        # created from calendar: try to create an activity on the related record
        if not values.get('activity_ids'):
            defaults = self.default_get(['activity_ids', 'res_model_id', 'res_id', 'user_id'])
            res_model_id = values.get('res_model_id', defaults.get('res_model_id'))
            res_id = values.get('res_id', defaults.get('res_id'))
            user_id = values.get('user_id', defaults.get('user_id'))
            if not defaults.get('activity_ids') and res_model_id and res_id:
                if hasattr(self.env[self.env['ir.model'].sudo().browse(res_model_id).model], 'activity_ids'):
                    meeting_activity_type = self.env['mail.activity.type'].search([('category', '=', 'interview')],
                                                                                  limit=1)
                    if meeting_activity_type:
                        activity_vals = {
                            'res_model_id': res_model_id,
                            'res_id': res_id,
                            'activity_type_id': meeting_activity_type.id,
                        }
                        if user_id:
                            activity_vals['user_id'] = user_id
                        values['activity_ids'] = [(0, 0, activity_vals)]

        meeting = super(Meeting, self).create(values)
        meeting._sync_activities(values)

        final_date = meeting._get_recurrency_end_date()
        # `dont_notify=True` in context to prevent multiple notify_next_alarm
        meeting.with_context(dont_notify=True).write({'final_date': final_date})
        meeting.with_context(dont_notify=True).create_attendees()

        # Notify attendees if there is an alarm on the created event, as it might have changed their
        # next event notification
        if not self._context.get('dont_notify'):
            if len(meeting.alarm_ids) > 0:
                self.env['calendar.alarm_manager'].notify_next_alarm(meeting.partner_ids.ids)
        return meeting

    @api.multi
    @api.depends('partner_ids', 'message_follower_ids')
    def _get_extra_followers(self):
        for r in self:
            extra_followers = (r.message_follower_ids.mapped('partner_id') - r.partner_ids).ids
            r.extra_followers_ids = extra_followers if extra_followers else False

    def _set_extra_followers(self):
        for r in self:
            extra_followers_ids = r.extra_followers_ids
            self.message_unsubscribe(
                (r.message_follower_ids.mapped('partner_id') - (extra_followers_ids + r.partner_ids)).ids)
            self.message_subscribe((extra_followers_ids - r.message_follower_ids.mapped('partner_id')).ids)
            self._message_auto_subscribe_notify(
                (extra_followers_ids - r.message_follower_ids.mapped('partner_id')).ids)

    @api.depends('res_id', 'res_model_id')
    def _get_applicant(self):
        for r in self:
            if r.res_model_id.model == 'hr.applicant':
                r.hr_applicant_id = self.env['hr.applicant'].browse([r.res_id])
