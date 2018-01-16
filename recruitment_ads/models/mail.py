from datetime import date, datetime, timedelta
from odoo import api, exceptions, fields, models, _
from odoo.exceptions import UserError, AccessError


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    call_result_id = fields.Char(string="Call result")



    def action_call_result(self, call_result_id=False):
        message = self.env['mail.message']

        if call_result_id:
            self.write(dict(call_result_id=call_result_id))

            for activity in self:
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

        elif not call_result_id  and self.activity_type_id.name == 'Call':
            raise UserError(_("Please select call result"))


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
    _name='call.result'

    name = fields.Char(string="Name")
