from odoo import fields, models


class MailActivityType(models.Model):
    _inherit = "mail.activity.type"

    category = fields.Selection(selection_add=[('interview', 'Interview')])


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    call_result_id = fields.Char(string="Call result")
    interview_result = fields.Char(string="Interview result")
    active = fields.Boolean(string='Active',default=True)

    def action_interview_result(self, feedback=False, interview_result=False):
        message = self.env['mail.message']

        self.write(dict(interview_result=interview_result, feedback=feedback))
        for activity in self:
            record = self.env[activity.res_model].browse(activity.res_id)
            interviewers = activity.calendar_event_id.partner_ids.mapped('name')
            activity.calendar_event_id.last_stage_result = interview_result
            record.message_post_with_view(
                'mail.message_activity_done',
                values={'activity': activity,'interviewers':','.join(interviewers) if interviewers else False},
                subtype_id=self.env.ref('mail.mt_activities').id,
                mail_activity_type_id=activity.activity_type_id.id,
            )
            message |= record.message_ids[0]

        self.write({'active':False})
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
        return message.ids and message.ids[0] or False

    def action_feedback(self, feedback=False):
        message = self.env['mail.message']

        if feedback:
            self.write(dict(feedback=feedback))

        for activity in self:
            if activity.activity_type_id.name != 'Call':
                record = self.env[activity.res_model].browse(activity.res_id)
                record.message_post_with_view(
                    'mail.message_activity_done',
                    values={'activity': activity},
                    subtype_id=self.env.ref('mail.mt_activities').id,
                    mail_activity_type_id=activity.activity_type_id.id,
                )
                message |= record.message_ids[0]
            self.unlink()
            return message.ids and message.ids[0] or False


class CallResult(models.Model):
    _name = 'call.result'

    name = fields.Char(string="Name")
