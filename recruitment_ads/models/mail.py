from odoo import fields, models, api


class MailActivityType(models.Model):
    _inherit = "mail.activity.type"

    category = fields.Selection(selection_add=[('interview', 'Interview'), ('online_call', 'Online Call/Message')])


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    call_result_id = fields.Char(string="Call result")
    interview_result = fields.Char(string="Interview result")
    active = fields.Boolean(string='Active', default=True)
    real_create_uid = fields.Many2one('res.users', string='Real Create User',
                                      help='Store the real create user as odoo always overwrite create_uid with admin',
                                      default=lambda self: self.env.user)
    real_write_uid = fields.Many2one('res.users', string='Real Write User',
                                     help='Store the real write user as odoo always overwrite write_uid with admin',
                                     default=lambda self: self.env.user)

    @api.multi
    def write(self, vals):
        vals['real_write_uid'] = self.env.user.id
        activity = super(MailActivity, self).write(vals)
        return activity

    @api.multi
    def update_calendar_event(self, result=False):
        for activity in self:
            if activity.res_model == 'hr.applicant':
                hr_applicant_id = self.env['hr.applicant'].browse([activity.res_id])
                not_done_interviews = hr_applicant_id.activity_ids.filtered(
                    lambda a: a.activity_category == 'interview' and a.id != activity.id)
                not_done_interviews.mapped('calendar_event_id').write(
                    {'last_stage_activity': activity.activity_type_id.name,
                     'last_stage_result': result})

    def action_interview_result(self, feedback=False, interview_result=False):
        message = self.env['mail.message']

        self.write(dict(interview_result=interview_result, feedback=feedback))
        for activity in self:
            record = self.env[activity.res_model].browse(activity.res_id)
            interviewers = activity.calendar_event_id.partner_ids.mapped('name')
            record.message_post_with_view(
                'mail.message_activity_done',
                values={'activity': activity, 'interviewers': ','.join(interviewers) if interviewers else False},
                subtype_id=self.env.ref('mail.mt_activities').id,
                mail_activity_type_id=activity.activity_type_id.id,
            )
            message |= record.message_ids[0]

        self.write({'active': False})
        self.mapped('calendar_event_id').write({'is_interview_done': True})
        self.update_calendar_event(interview_result)
        return message.ids and message.ids[0] or False

    def action_call_result(self, feedback=False, call_result_id=False):
        message = self.env['mail.message']

        self.write(dict(call_result_id=call_result_id, feedback=feedback))

        for activity in self:
            record = self.env[activity.res_model].browse(activity.res_id)
            record.message_post_with_view(
                'mail.message_activity_done',
                values={'activity': activity},
                subtype_id=self.env.ref('mail.mt_activities').id,
                mail_activity_type_id=activity.activity_type_id.id,
            )
            message |= record.message_ids[0]

        self.write({'active': False})
        self.update_calendar_event(call_result_id)
        return message.ids and message.ids[0] or False

    def action_feedback(self, feedback=False):
        message = self.env['mail.message']
        if feedback:
            self.write(dict(feedback=feedback))
        for activity in self:
            record = self.env[activity.res_model].browse(activity.res_id)
            record.message_post_with_view(
                'mail.message_activity_done',
                values={'activity': activity},
                subtype_id=self.env.ref('mail.mt_activities').id,
                mail_activity_type_id=activity.activity_type_id.id,
            )
            message |= record.message_ids[0]

        self.write({'active': False})
        self.update_calendar_event()
        return message.ids and message.ids[0] or False


class CallResult(models.Model):
    _name = 'call.result'

    name = fields.Char(string="Name")
