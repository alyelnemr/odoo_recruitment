import base64

import pytz
from odoo import models, fields, api, _
from odoo.addons.calendar.models.calendar import Meeting, is_calendar_id, calendar_id2real_id
from odoo.exceptions import ValidationError


class Interview(models.Model):
    _inherit = 'calendar.event'

    hr_applicant_id = fields.Many2one('hr.applicant', 'Applicant', compute='_get_applicant')
    job_id = fields.Many2one('hr.job', 'Job Position', compute='_get_applicant', store=True)
    type = fields.Selection([('normal', 'Normal'), ('interview', 'Interview')], string="Type", default='normal')
    extra_followers_ids = fields.Many2many('res.partner', string="Followers",
                                           relation='interview_followers_interview_rel', column1='interview_id',
                                           column2='follower_id')

    partner_ids = fields.Many2many('res.partner', string='Interviewers')
    display_partners = fields.Html(string='Interviewers', compute='_display_partners')
    last_stage_activity = fields.Char('Last stage activity')
    last_stage_result = fields.Char('Last stage result')
    department_id = fields.Many2one('hr.department', string='Department', compute='_get_applicant', store=True)
    is_interview_done = fields.Boolean('Is interview done?', default=False)

    @api.constrains('partner_ids', 'start', 'stop')
    def check_overlapping_interviews(self):
        for interview in self.filtered(lambda m: m.type == 'interview'):
            domain = [
                ('partner_ids', 'in', interview.partner_ids.ids),
                ('is_interview_done', '=', False),
                ('type', '=', 'interview'),
                ('start', '<', interview.stop),
                ('stop', '>', interview.start),
                ('id', '!=', interview.id),
            ]
            overlapped_interviews = self.search(domain)
            if overlapped_interviews:
                error_message = ""
                tz = pytz.timezone(self.env.user.tz) if self.env.user.tz else pytz.utc
                for overlapped_interview in overlapped_interviews:
                    startdate = fields.Datetime.from_string(overlapped_interview.start)
                    startdate = pytz.utc.localize(startdate)  # Add "+00:00" timezone
                    startdate = startdate.astimezone(tz)  # Convert to user timezone
                    startdate = fields.Datetime.to_string(startdate)
                    enddate = fields.Datetime.from_string(overlapped_interview.stop)
                    enddate = pytz.utc.localize(enddate)
                    enddate = enddate.astimezone(tz)
                    enddate = fields.Datetime.to_string(enddate)
                    conflicted_partners = interview.partner_ids & overlapped_interview.partner_ids
                    error_message += ', '.join(conflicted_partners.mapped(
                        'name')) + ' has interview from ' + startdate + ' to ' + enddate + '\n'
                raise ValidationError(error_message)

    @api.depends('partner_ids')
    def _display_partners(self):
        for rec in self:
            if rec.partner_ids:
                res = self.env.ref('recruitment_ads.display_interviewers').render(
                    {"interviewers": rec.partner_ids.mapped('name')}
                )
                rec.display_partners = res

    @api.depends('res_id', 'res_model_id')
    def _get_applicant(self):
        for r in self:
            if r.res_model_id.model == 'hr.applicant':
                r.hr_applicant_id = self.env['hr.applicant'].browse([r.res_id])
                r.job_id = self.env['hr.applicant'].browse([r.res_id]).job_id
                r.department_id = self.env['hr.applicant'].browse([r.res_id]).department_id

    @api.constrains('duration', 'allday')
    def check_duration(self):
        for meeting in self:
            if not meeting.allday and meeting.duration <= 0:
                raise ValidationError(_("Duration Can't be less than or equal to zero"))

    @api.multi
    def write(self, values):
        """Override the write function to trigger create attendee function where there is a change in
        extra_followers_ids field"""

        # compute duration, only if start and stop are modified
        if not 'duration' in values and 'start' in values and 'stop' in values:
            values['duration'] = self._get_duration(values['start'], values['stop'])

        self._sync_activities(values)

        # process events one by one
        for meeting in self:
            # special write of complex IDS
            real_ids = []
            new_ids = []
            if not is_calendar_id(meeting.id):
                real_ids = [int(meeting.id)]
            else:
                real_event_id = calendar_id2real_id(meeting.id)

                # if we are setting the recurrency flag to False or if we are only changing fields that
                # should be only updated on the real ID and not on the virtual (like message_follower_ids):
                # then set real ids to be updated.
                blacklisted = any(key in values for key in ('start', 'stop', 'active'))
                if not values.get('recurrency', True) or not blacklisted:
                    real_ids = [real_event_id]
                else:
                    data = meeting.read(['start', 'stop', 'rrule', 'duration'])[0]
                    if data.get('rrule'):
                        new_ids = meeting.with_context(dont_notify=True).detach_recurring_event(
                            values).ids  # to prevent multiple notify_next_alarm

            new_meetings = self.browse(new_ids)
            real_meetings = self.browse(real_ids)
            all_meetings = real_meetings + new_meetings
            super(Meeting, real_meetings).write(values)

            # set end_date for calendar searching
            if any(field in values for field in ['recurrency', 'end_type', 'count', 'rrule_type', 'start', 'stop']):
                for real_meeting in real_meetings:
                    if real_meeting.recurrency and real_meeting.end_type == u'count':
                        final_date = real_meeting._get_recurrency_end_date()
                        super(Meeting, real_meeting).write({'final_date': final_date})

            attendees_create = False
            if values.get('partner_ids', False) or values.get('extra_followers_ids',
                                                              False):  # here is the adding trigger
                attendees_create = all_meetings.with_context(
                    dont_notify=True,
                    send_inviation_mail=True).create_attendees()  # to prevent multiple notify_next_alarm

            # Notify attendees if there is an alarm on the modified event, or if there was an alarm
            # that has just been removed, as it might have changed their next event notification
            if not self._context.get('dont_notify'):
                if len(meeting.alarm_ids) > 0 or values.get('alarm_ids'):
                    partners_to_notify = meeting.partner_ids.ids
                    event_attendees_changes = attendees_create and real_ids and attendees_create[real_ids[0]]
                    if event_attendees_changes:
                        partners_to_notify.extend(event_attendees_changes['removed_partners'].ids)
                    self.env['calendar.alarm_manager'].notify_next_alarm(partners_to_notify)

            if (values.get('start_date') or values.get('start_datetime') or
                (values.get('start') and self.env.context.get('from_ui'))) and values.get('active', True):
                for current_meeting in all_meetings:
                    if attendees_create:
                        attendees_create = attendees_create[current_meeting.id]
                        attendee_to_email = attendees_create['old_attendees'] - attendees_create['removed_attendees']
                    else:
                        attendee_to_email = current_meeting.attendee_ids

                    if attendee_to_email:
                        attendee_to_email._send_mail_to_attendees('calendar.calendar_template_meeting_changedate')
        return True

    @api.model
    def create(self, values):
        if self.env.context.get('default_type', False) == 'interview':
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

            # Update last stage activity and and result if found
            done_activites = meeting.hr_applicant_id.with_context({'active_test': False}).activity_ids.filtered(
                lambda a: not a.active).sorted('write_date', reverse=True)
            if done_activites:
                meeting.update({
                    'last_stage_activity': done_activites[0].activity_type_id.name,
                    'last_stage_result': done_activites[0].call_result_id or done_activites[0].interview_result,
                })
            return meeting
        else:
            return super(Interview, self).create(values)

    @api.multi
    def create_attendees(self):
        result = super(Interview, self.filtered(lambda meeting: meeting.type == 'normal')).create_attendees()
        current_user = self.env.user
        for meeting in self.filtered(lambda meeting: meeting.type == 'interview'):
            alreay_meeting_partners = meeting.attendee_ids.mapped('partner_id')
            meeting_attendees = self.env['calendar.attendee']
            meeting_partners = self.env['res.partner']
            extra_followers_ids = meeting.extra_followers_ids

            # create attendee for the applicant
            if meeting.hr_applicant_id.email_from not in meeting.attendee_ids.mapped('email'):
                applicant_vals = {
                    'email': meeting.hr_applicant_id.email_from,
                    'event_id': meeting.id,
                    'applicant_name': meeting.hr_applicant_id.partner_name,
                    'is_applicant': True,
                }
                meeting_attendees |= self.env['calendar.attendee'].create(applicant_vals)

            for partner in meeting.partner_ids.filtered(
                    lambda partner: partner not in alreay_meeting_partners) | extra_followers_ids.filtered(
                lambda partner: partner not in alreay_meeting_partners):
                values = {
                    'partner_id': partner.id,
                    'email': partner.email,
                    'event_id': meeting.id,
                }

                # current user don't have to accept his own meeting
                if partner == self.env.user.partner_id:
                    values['state'] = 'accepted'

                attendee = self.env['calendar.attendee'].create(values)

                meeting_attendees |= attendee
                meeting_partners |= partner

            if meeting_attendees:
                if self._context.get('send_invitation_mail', False):
                    to_notify = meeting_attendees.filtered(
                        lambda a: a.email and current_user.email and a.email.lower() != current_user.email.lower())
                    to_notify._send_mail_to_attendees('calendar.calendar_template_meeting_invitation')

                meeting.write(
                    {'attendee_ids': [(4, meeting_attendee.id) for meeting_attendee in meeting_attendees]})
            if meeting_partners:
                meeting.message_subscribe(partner_ids=meeting_partners.ids)

            # We remove old attendees who are not in partner_ids now.
            all_partners = meeting.partner_ids | extra_followers_ids
            all_partner_attendees = meeting.attendee_ids.mapped('partner_id')
            old_attendees = meeting.attendee_ids
            partners_to_remove = all_partner_attendees + meeting_partners - all_partners

            attendees_to_remove = self.env["calendar.attendee"]
            if partners_to_remove:
                attendees_to_remove = self.env["calendar.attendee"].search(
                    [('partner_id', 'in', partners_to_remove.ids), ('event_id', '=', meeting.id)])
                attendees_to_remove.unlink()

            result[meeting.id] = {
                'new_attendees': meeting_attendees,
                'old_attendees': old_attendees,
                'removed_attendees': attendees_to_remove,
                'removed_partners': partners_to_remove
            }
        return result

    @api.multi
    def action_mail_compose_message(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('recruitment_ads', 'calendar_template_interview_invitation')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'calendar.event',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'force_email': True
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }


class Attendee(models.Model):
    _inherit = 'calendar.attendee'

    applicant_name = fields.Char(string='Applicant Name')
    is_applicant = fields.Boolean(string='Is Applicant?', default=False)

    @api.depends('partner_id', 'partner_id.name', 'email')
    def _compute_common_name(self):
        for attendee in self:
            attendee.common_name = attendee.applicant_name or attendee.partner_id.name or attendee.email

    @api.multi
    def _send_mail_to_attendees(self, template_xmlid, force_send=False):
        """ Send mail for event invitation to event attendees.
            :param template_xmlid: xml id of the email template to use to send the invitation
            :param force_send: if set to True, the mail(s) will be sent immediately (instead of the next queue processing)
        """
        res_interview = True
        res_meeting = True
        if self.env['ir.config_parameter'].sudo().get_param('calendar.block_mail') or self._context.get(
                "no_mail_to_attendees"):
            return False

        meetings = self.filtered(lambda m: m.event_id.type == 'normal')
        interviews = self.filtered(lambda m: m.event_id.type == 'interview')
        if meetings:
            res_meeting = super(Attendee, meetings)._send_mail_to_attendees(template_xmlid, force_send)

        if interviews:
            map_meeting_interview_template = {
                'calendar.calendar_template_meeting_invitation': 'recruitment_ads.calendar_template_interview_invitation',
                'calendar.calendar_template_meeting_changedate': 'recruitment_ads.calendar_template_interview_changedate',
                'calendar.calendar_template_meeting_reminder': 'recruitment_ads.calendar_template_interview_reminder',
            }

            if template_xmlid == 'calendar.calendar_template_meeting_invitation':

                calendar_view = self.env.ref('calendar.view_calendar_event_calendar')
                invitation_template = self.env.ref(map_meeting_interview_template.get(template_xmlid, template_xmlid))

                # prepare rendering context for mail template

                rendering_context = dict(self._context)
                applicants = self.filtered(lambda a: a.is_applicant and a.email)
                if applicants:
                    rendering_context.update({
                        'email_to': ','.join(applicants.mapped('email')),
                        'email_cc': ','.join((self - applicants).mapped('email')),
                    })
                else:
                    rendering_context.update({
                        'email_to': ','.join(self.filtered(lambda a: a.email != False).mapped('email')),
                    })
                invitation_template = invitation_template.with_context(rendering_context)

                # send email with attachments
                mails_to_send = self.env['mail.mail']
                for interview in interviews.mapped('event_id'):
                    mail_id = invitation_template.send_mail(calendar_id2real_id(interview.id))
                    vals = {}
                    ics_files = interview.get_ics_file()
                    ics_file = ics_files.get(interview.id)
                    if ics_file:
                        vals['attachment_ids'] = [(0, 0, {'name': 'invitation.ics',
                                                          'mimetype': 'text/calendar',
                                                          'datas_fname': 'invitation.ics',
                                                          'datas': base64.b64encode(ics_file)})]
                    vals['model'] = None  # We don't want to have the mail in the tchatter while in queue!
                    vals['res_id'] = False
                    current_mail = self.env['mail.mail'].browse(mail_id)
                    current_mail.mail_message_id.write(vals)
                    mails_to_send |= current_mail

                if force_send and mails_to_send:
                    res_interview = mails_to_send.send()


            elif template_xmlid != 'calendar.calendar_template_meeting_invitation':
                res_interview = super(Attendee, interviews)._send_mail_to_attendees(
                    map_meeting_interview_template.get(template_xmlid, template_xmlid), force_send)
        return res_interview and res_meeting
