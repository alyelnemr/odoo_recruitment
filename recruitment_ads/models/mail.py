from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import date, datetime, timedelta


class MailActivityType(models.Model):
    _inherit = "mail.activity.type"

    category = fields.Selection(selection_add=[('interview', 'Interview'), ('facebook_call', 'Facebook Call'),
                                               ('linkedIn_call', 'LinkedIn Call')])


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
    call_result_date = fields.Date()
    interview_result_date = fields.Date()
    call_not_interested_date = fields.Date()

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
            record.write({'result': interview_result})
        self.write({'active': False,
                    'interview_result_date': fields.Date.today()})
        self.mapped('calendar_event_id').write({'is_interview_done': True})
        self.update_calendar_event(interview_result)
        return message.ids and message.ids[0] or False

    def action_call_result(self, feedback=False, call_result_id=False, not_interested_date=False):
        message = self.env['mail.message']

        try:
            d = datetime.strptime(not_interested_date, "%Y-%m-%d")
        except ValueError:
            d = None

        self.write(dict(call_result_id=call_result_id,
                        feedback=feedback, call_not_interested_date=d))

        for activity in self:
            record = self.env[activity.res_model].browse(activity.res_id)
            record.message_post_with_view(
                'mail.message_activity_done',
                values={'activity': activity},
                subtype_id=self.env.ref('mail.mt_activities').id,
                mail_activity_type_id=activity.activity_type_id.id,
            )
            message |= record.message_ids[0]
            record.write({'result': call_result_id})
        self.write({'active': False,
                    'call_result_date': fields.Date.today()})
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

    @api.model
    def create(self, values):
        if self._context.get('default_res_model', False) == 'hr.applicant':
            hr_applicant_id = self.env['hr.applicant'].browse([values.get('res_id', False)])
            if values.get('activity_type_id', False) == 2:
                if not hr_applicant_id.partner_phone and not hr_applicant_id.partner_mobile:
                    raise ValidationError(_("Please insert Applicant Mobile /Phone in order to schedule Call?"))
            if values.get('activity_type_id', False) == 6:
                if not hr_applicant_id.face_book:
                    raise ValidationError(_("Please insert Applicant Facebook in order to schedule Facebook Call?"))
            if values.get('activity_type_id', False) == 7:
                if not hr_applicant_id.linkedin:
                    raise ValidationError(_("Please insert Applicant LinkedIn in order to schedule LinkedIn Call?"))
            hr_applicant_id.write({'last_activity': values['activity_type_id'],
                                   'last_activity_date': values['date_deadline'],
                                   'result': False,
                                   })
            if not hr_applicant_id.user_id:
                hr_applicant_id.write({'user_id': self.env.user.id,
                                       })
            if values.get('activity_type_id', False) == 7 or values.get('activity_type_id', False) == 6 or values.get(
                    'activity_type_id', False) == 2:
                activity = self.env['hr.recruitment.stage'].search([('name', '=', 'Call')], limit=1)
                if activity:
                    hr_applicant_id.write({'stage_id': activity.id})

        return super(MailActivity, self).create(values)

    # override the method to change due date when select call take the current date not after two days
    @api.onchange('activity_type_id')
    def _onchange_activity_type_id(self):
        res = super(MailActivity, self)._onchange_activity_type_id()
        if self.activity_type_id:
            self.summary = self.activity_type_id.summary
            self.date_deadline = datetime.now()
        return res

    # override method to close wizard and refresh page
    def action_close_dialog(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'reload', }

    def send_rejection_mail(self, feedback=False, interview_result=False):
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
            record.write({'result': interview_result})
        self.write({'active': False,
                    'interview_result_date': fields.Date.today()})
        self.mapped('calendar_event_id').write({'is_interview_done': True})
        self.update_calendar_event(interview_result)
        return message.ids and message.ids[0] or False
        # self.ensure_one()
        # ir_model_data = self.env['ir.model.data']
        # try:
        #     template_id = \
        #         ir_model_data.get_object_reference('recruitment_ads',
        #                                            'rejected_applicant_email_template')[1]
        # except ValueError:
        #     template_id = False
        # try:
        #     compose_form_id = \
        #         ir_model_data.get_object_reference('recruitment_ads',
        #                                            'view_rejection_mail_compose_message_wizard_from')[1]
        # except ValueError:
        #     compose_form_id = False
        # ctx = {
        #     'default_model': 'calendar.event',
        #     'default_res_id': self.calendar_event_id.id,
        #     'default_use_template': bool(template_id),
        #     'default_template_id': template_id,
        #     'default_composition_mode': 'comment',
        #     'default_candidate_id': self.calendar_event_id.hr_applicant_id.partner_id.id,
        #     'default_application_id': self.calendar_event_id.hr_applicant_id.id,
        #     'default_partner_ids': [(6, 0, self.calendar_event_id.partner_ids.ids)],
        #     'time_format': '%I:%M %p',
        #     'force_email': True
        # }
        # return {
        #     'type': 'ir.actions.act_window',
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'res_model': 'rejection.mail.compose.message',
        #     'views': [(compose_form_id, 'form')],
        #     'view_id': compose_form_id,
        #     'target': 'new',
        #     'context': ctx,
        # }


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    # method inherited to stop the old odoo behavior from sending mails to the recruiter responsible.
    @api.multi
    def _message_auto_subscribe_notify(self, partner_ids):
        """ Notify newly subscribed followers of the last posted message.
            :param partner_ids : the list of partner to add as needaction partner of the last message
                                 (This excludes the current partner)
        """
        if not partner_ids:
            return

        if self.env.context.get('mail_auto_subscribe_no_notify'):
            return

        # send the email only to the current record and not all the ids matching active_domain !
        # by default, send_mail for mass_mail use the active_domain instead of active_ids.
        if 'active_domain' in self.env.context:
            ctx = dict(self.env.context)
            ctx.pop('active_domain')
            self = self.with_context(ctx)

        # the following part is removed to prevent the old odoo behavior from sending mails to the recruiter responsible

        # for record in self:
        #     record.message_post_with_view(
        #         'mail.message_user_assigned',
        #         composition_mode='mass_mail',
        #         partner_ids=[(4, pid) for pid in partner_ids],
        #         auto_delete=True,
        #         auto_delete_message=True,
        #         parent_id=False, # override accidental context defaults
        #         subtype_id=self.env.ref('mail.mt_note').id)


class CallResult(models.Model):
    _name = 'call.result'

    name = fields.Char(string="Name")
