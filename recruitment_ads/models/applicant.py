import re
import json
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class Applicant(models.Model):
    _inherit = "hr.applicant"

    @api.multi
    def _compute_approval_cycles_number(self):
        for applicant in self:
            applicant.approval_cycles_number = len(applicant.approval_cycle_ids)
            applicant.approved_approval_cycles_number = len(applicant.approved_approval_cycle_ids)

    email_from = fields.Char()
    partner_phone = fields.Char(related="partner_id.phone", size=256)
    partner_mobile = fields.Char(related="partner_id.mobile", size=256)
    face_book = fields.Char(string='Facebook Link ', readonly=False, related="partner_id.face_book")
    linkedin = fields.Char(string='LinkedIn Link', readonly=False, related="partner_id.linkedin")
    department_id = fields.Many2one('hr.department', "Department", domain=[('parent_id', '=', False)])
    section_id = fields.Many2one('hr.department', "Section", domain=[('parent_id', '!=', False)])

    partner_name = fields.Char(required=True)
    job_id = fields.Many2one('hr.job', "Applied Job", ondelete='restrict',required= True)

    partner_id = fields.Many2one('res.partner', "Applicant", required=True)
    # applicant_history_ids = fields.Many2many('hr.applicant', 'applicant_history_rel', 'applicant_id', 'history_id',
    #                                          string='History', readonly=False)
    applicant_history_ids = fields.Many2many('hr.applicant.history', 'applicant_history_relation', 'applicant_id',
                                             'history_id',
                                             string='History', compute='onchange_hr_applicant')
    last_activity = fields.Many2one('mail.activity.type', compute='_get_activity', store=True)
    last_activity_date = fields.Date(compute='_get_activity', store=True)
    result = fields.Char(compute='_get_activity', store=True)
    source_id = fields.Many2one('utm.source', required=True)
    offer_id = fields.Many2one('hr.offer', string='Offer', readonly=True)
    cv_matched = fields.Boolean('Matched', default=False)
    reason_of_rejection = fields.Char('Reason of Rejection', help="Reason why this is applicant not matched")
    count_done_interviews = fields.Integer('Done Interviews Count', compute='_get_count_done_interviews')
    count_not_done_interviews = fields.Integer('Not Done Interviews Count', compute='_get_count_done_interviews')
    salary_current = fields.Float("Current Salary", help="Current Salary of Applicant")
    name = fields.Char("Application Code", readonly=True, required=False, compute='_compute_get_application_code',
                       store=True)
    serial = fields.Char('serial', copy=False)
    allow_call = fields.Boolean(string="Allow Online Call", compute='_get_allow_call', store=True)
    # face_book = fields.Char(string='Facebook Link ', related="partner_id.face_book", readonly=False)
    # linkedin = fields.Char(string='LinkedIn Link', related="partner_id.linkedin", readonly=False)
    have_cv = fields.Boolean(srting='Have CV', compute='_get_attachment', default=False, store=True)
    have_assessment = fields.Boolean(compute='_get_attachment', default=False, store=True)
    user_id = fields.Many2one('res.users', "Responsible", track_visibility="onchange", default=False)
    source_resp = fields.Many2one('res.users', "Source Responsible", track_visibility="onchange",
                                  default=lambda self: self.env.user.id)
    old_data = fields.Text('Last Updated Data')
    tooltip_icon = fields.Char(string='Info.')
    calendar_event_ids = fields.One2many('calendar.event', 'hr_applicant_id', string='Events')
    cv_counter = fields.Integer('CV Counter', default=0, compute='_get_attachment', store=True)
    assessment_counter = fields.Integer('Assessment Counter', default=0, compute='_get_attachment', store=True)
    approval_cycle_ids = fields.One2many('hr.approval.cycle', 'application_id', string='Approval Cycles', readonly=True,
                                         related='offer_id.approval_cycle_ids', store=True)
    approved_approval_cycle_ids = fields.One2many('hr.approval.cycle', 'application_id', string='Approval Cycles',
                                                  readonly=True, store=True,
                                                  related='offer_id.approval_cycle_ids',
                                                  domain=[('state', '=', 'approved')])
    approval_cycles_number = fields.Integer('Number of Approval Cycles',
                                            compute=_compute_approval_cycles_number)

    approved_approval_cycles_number = fields.Integer('Number of Approved Approval Cycles',
                                                     compute=_compute_approval_cycles_number)
    last_approval_cycle_state= fields.Char(compute='_get_approval_cycles_state')

    def _get_approval_cycles_state(self):
        for rec in self:
             approval_cycle = self.env['hr.approval.cycle'].search([('offer_id','=',rec.offer_id.id)],order= 'create_date desc',limit=1)
             if approval_cycle:
                 rec.last_approval_cycle_state = approval_cycle.state

    def get_last_activity(self):
        activity = {}
        self._cr.execute(
            "select MAT.name , to_char(MA.date_deadline, 'DD-MM-YYYY') , MA.call_result_id, MA.interview_result , MAT.id  from mail_activity MA INNER JOIN mail_activity_type MAT ON MA.activity_type_id = MAT.id"
            " where MA.res_model =  %s and  MA.res_id =  %s AND (MAT.id not in (%s ,%s ,%s))  order by MA.create_date desc limit 1 ",
            ('hr.applicant', self.id, 1, 3, 4))
        results = self.env.cr.fetchone()

        if results:
            if not results[2] and not results[3]:
                activity = {
                    'Activity_Result': 'No result added.'}
            else:
                if results[4] != 5:
                    activity = {
                        'Activity_type': 'Type = ' + results[0],
                        'Activity_Date': 'Date = ' + results[1],
                        'Activity_Result': 'Result = ' + results[2]}
                else:
                    activity = {
                        'Activity_type': 'Type = ' + results[0],
                        'Activity_Date': 'Date = ' + results[1],
                        'Activity_Result': 'Result = ' + results[3]}
            return activity
        else:
            activity = {
                'Activity_Result': 'There is no activity added.'}
            return activity

    @api.multi
    def write(self, vals):
        ctx = self._context.copy()
        if not ctx.get('write_counter', False):
            for applicant in self:
                if not ctx.get('edit_contact', False):
                    old_dict = {}
                    for key, val in vals.items():
                        if key in ('email_form', 'partner_mobile', 'partner_phone', 'face_book', 'linkedin'):
                            old_dict[key] = applicant[key]
                    if old_dict:
                        vals['old_data'] = json.dumps(old_dict)

        for applicant in self:
            if vals.get('job_id', False):
                applicant.calculate_application_period_policy(vals, action="write")
            if vals.get('stage_id', False) and \
                    applicant.stage_id.id == self.env.ref(
                'recruitment_ads.application_stage_approval_cycle_data').id and self.last_approval_cycle_state != 'approved' and vals.get('stage_id') != self.stage_id.id :
                raise ValidationError(
                    'You can not move application to other stage until the approval cycle is approved.')

        res = super(Applicant, self).write(vals)
        for applicant in self:
            if applicant.stage_id.id == self.env.ref('recruitment_ads.application_stage_approval_cycle_data').id \
                    and len(applicant.offer_id.approval_cycle_ids) == 0:
                raise ValidationError(
                    'You can not add application to approval cycle stage until create Approval cycle on application.')

        return res

    def get_current_user_group(self):
        res_user = self.env.user
        if res_user.has_group('hr_recruitment.group_hr_recruitment_manager'):
            return 'manager'
        else:
            return "not manager"

    @api.multi
    @api.depends('attachment_ids.res_id', 'attachment_ids.attachment_type')
    def _get_attachment(self):
        for record in self:
            cv = self.env['ir.attachment'].search(
                [('res_id', '=', record.id), ('attachment_type', '=', 'cv'), ('res_model', '=', 'hr.applicant')])
            assessment = self.env['ir.attachment'].search(
                [('res_id', '=', record.id), ('attachment_type', '=', 'assessment'),
                 ('res_model', '=', 'hr.applicant')])
            if cv:
                record.have_cv = True
            else:
                record.have_cv = False
            if assessment:
                record.have_assessment = True
            else:
                record.have_assessment = False
            record.cv_counter = len(cv)
            record.assessment_counter = len(assessment)

    @api.one
    @api.depends('job_id.job_title_id.job_code', 'partner_mobile', 'partner_name', 'serial')
    def _compute_get_application_code(self):
        job_code = self.job_id.job_title_id.job_code
        applicant_mobile = self.partner_mobile[-3:] if self.partner_mobile else "N/A"
        initials = ''.join(
            initial[:2].upper() for initial in self.partner_name.split())[:4] if self.partner_name else False
        applicant_name = initials
        serial = self.serial
        self.name = '-'.join(filter(lambda i: i, [applicant_name, job_code, applicant_mobile, serial]))

    def calculate_application_period_policy(self, vals, action):
        """
        This function checks if the applicant has applied on the same job before within the period in the policy
        :param vals:
        :return: raise a validation error, and stop the user from creating the application, if the applicant has applied
        before within the policy period.
        """
        if vals.get('job_id', False):
            parent_id = ""
            if action == "create":
                parent_id = vals['partner_id']
            elif action == "write":
                parent_id = self.partner_id.id
            policy = self.env['hr.policy'].search([], limit=1)
            domain = [('partner_id', '=', parent_id), ('job_id', '=', vals['job_id'])]
            old_applications = self.env['hr.applicant'].search(domain)
            if old_applications:
                for old_app in old_applications:
                    app_date = fields.Datetime.from_string(old_app.create_date)
                    added_date = app_date + relativedelta(days=policy.day, months=policy.month, years=policy.year)
                    if added_date > datetime.today():
                        remaining_time = added_date - datetime.today()
                        period = []
                        period.append(str(policy.day) + " day(s)") if policy.day > 0 else False
                        period.append(str(policy.month) + " month(s)") if policy.month else False
                        period.append(str(policy.year) + " year(s)") if policy.year else False
                        raise ValidationError(
                            _("This Applicant is applied before on this Job: '%s.'\n"
                              "Please wait %s and then apply again.\n"
                              "Maximum Period: %s") % (
                                old_app.job_id.name if old_app.job_id.name else "",
                                str(remaining_time.days) + " day(s)", " ".join(period)))

    @api.model
    def create(self, vals):
        self.calculate_application_period_policy(vals, action="create")
        res = super(Applicant, self).create(vals)
        if not res.source_resp:
            res.source_resp = self.env.user.id
        sequence = self.env.ref('recruitment_ads.sequence_application')
        number = sequence.next_by_id()
        res.serial = number
        return res

    @api.one
    def _get_count_done_interviews(self):
        activity_type = self.env.ref('recruitment_ads.mail_activity_type_data_interview')
        self.count_done_interviews = len(
            self.activity_ids.filtered(lambda a: a.activity_type_id == activity_type and not a.active)
        )
        self.count_not_done_interviews = len(
            self.activity_ids.filtered(lambda a: a.activity_type_id == activity_type and a.active)
        )

    @api.multi
    def unlink(self):
        if self.with_context({'active_test': False}).activity_ids:
            raise ValidationError(_("Can't delete application that has activities"))
        return super(Applicant, self).unlink()

    def _get_activity(self, update=False):
        for applicant in self:
            activities = applicant.with_context({'active_test': False}).activity_ids
            if activities:
                #
                last_activity = activities.sorted('create_date')[-1]

                # if applicant.last_activity or applicant.last_activity_date:
                if update:
                    applicant._write({'last_activity': last_activity.activity_type_id.id,
                                      'last_activity_date': last_activity.date_deadline,

                                      })
                else:
                    applicant.last_activity = last_activity.activity_type_id
                    applicant.last_activity_date = last_activity.date_deadline

                if last_activity.activity_category == 'interview':
                    if update:
                        applicant._write({'result': last_activity.interview_result
                                          })
                    else:
                        applicant.result = last_activity.interview_result
                else:
                    if update:
                        applicant._write({'result': last_activity.call_result_id
                                          })
                    else:
                        applicant.result = last_activity.call_result_id

    def _onchange_job_id_internal(self, job_id):
        department_id = False
        section_id = False
        user_id = False
        stage_id = self.stage_id.id
        if job_id:
            job = self.env['hr.job'].browse(job_id)
            department_id = job.department_id.id
            section_id = job.section_id.id
            # user_id = job.user_id.id
            if not self.stage_id:
                stage_ids = self.env['hr.recruitment.stage'].search([
                    '|',
                    ('job_id', '=', False),
                    ('job_id', '=', job.id),
                    ('fold', '=', False)
                ], order='sequence asc', limit=1).ids
                stage_id = stage_ids[0] if stage_ids else False

        return {'value': {
            'department_id': department_id,
            'section_id': section_id,
            'stage_id': stage_id,
            'user_id': user_id
        }}

    @api.onchange('job_id')
    def onchange_job_id(self):
        vals = self._onchange_job_id_internal(self.job_id.id)
        self.department_id = vals['value']['department_id']
        self.section_id = vals['value']['section_id']
        if not self._origin.id:
            self.user_id = False
        self.stage_id = vals['value']['stage_id']

    @api.onchange('department_id')
    def onchange_department_id(self):
        if self.department_id != self.section_id.parent_id:
            self.section_id = False

    def _get_history_data(self, applicant_id):
        if applicant_id == False:
            return self.env['hr.applicant.history']
        domain = [('partner_id', '=', applicant_id), ('id', 'not in', self.ids)]
        apps = self.env['hr.applicant'].search(domain)
        for app in apps:
            if app:
                app._get_activity(update=True)

        return self.env['hr.applicant.history'].search(domain)

    @api.onchange('partner_id')
    def onchange_hr_applicant(self):

        history = self._get_history_data(self.partner_id.id)
        self.applicant_history_ids = [(6, 0, history.ids)]

    @api.multi
    @api.onchange('department_id.allow_call', 'section_id.allow_call')
    @api.depends('department_id.allow_call', 'section_id.allow_call')
    def _get_allow_call(self):
        for applicant in self:
            if applicant.section_id:
                applicant.allow_call = applicant.section_id.allow_call
            elif applicant.department_id:
                applicant.allow_call = applicant.department_id.allow_call
            else:
                applicant.allow_call = False

    @api.onchange('cv_matched')
    def onchange_cv_matched(self):
        self.reason_of_rejection = False

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.partner_phone = self.partner_id.phone
        self.partner_mobile = self.partner_id.mobile
        self.email_from = self.partner_id.email
        self.partner_name = self.partner_id.name
        self.face_book = self.partner_id.face_book
        self.linkedin = self.partner_id.linkedin
        # self.linkedin = self.partner_id.linkedin

    @api.multi
    def action_makeMeeting(self):
        self.ensure_one()
        activity_result = self.env['mail.activity'].search([('res_id', '=', self.id)])
        if activity_result:
            for activity in activity_result:
                if not activity.call_result_id and not activity.interview_result:
                    raise ValidationError('Please insert Activity Result in order to be transferred to another stage')
        if self.user_id.id != self.env.user.id and not self.env.user.has_group(
                'hr_recruitment.group_hr_recruitment_manager'):
            raise ValidationError(
                'This Application is Owned by another Recruiter , you are not allowed to take any action on.')
        if not self.partner_phone or not self.partner_mobile or not self.email_from:
            raise ValidationError('Please insert Applicant Mobile /Email /Phone in order to schedule activity .')
        else:
            calendar_view_id = self.env.ref('recruitment_ads.view_calendar_event_interview_calender').id
            form_view_id = self.env.ref('recruitment_ads.view_calendar_event_interview_form').id
            if self.job_id.name and self.partner_name:
                name = self.job_id.name + "-" + self.partner_name + "'s interview"
            else:
                name = ''
            action = {
                'type': 'ir.actions.act_window',
                'name': 'Schedule Interview',
                'res_model': 'calendar.event',
                'view_mode': 'calendar,form',
                'view_type': 'form',
                'view_id': form_view_id,
                'views': [[calendar_view_id, 'calendar'], [form_view_id, 'form']],
                'target': 'current',
                'domain': [['type', '=', 'interview']],
                'context': {
                    'default_name': name,
                    'default_res_id': self.id,
                    'default_res_model': self._name,
                    'default_type': 'interview',
                },
            }
            return action

    @api.multi
    @api.returns('ir.attachment')
    def get_resume(self):
        """Get Resume(s) of applicant"""
        self.ensure_one()
        return self.env['ir.attachment'].search([('res_model', '=', 'hr.applicant'), ('res_id', 'in', self.ids)])

    @api.multi
    def action_generate_offer(self):
        self.ensure_one()
        allowed_users = self.job_id.user_id | self.job_id.hr_responsible_id | self.job_id.other_recruiters_ids
        if self.env.user.has_group('hr_recruitment.group_hr_recruitment_manager') or \
                self.env.user in allowed_users:
            form_view_id = self.env.ref('recruitment_ads.job_offer_form_wizard_view').id
            action = {
                'type': 'ir.actions.act_window',
                'name': 'Offers',
                'res_model': 'hr.offer.wizard',
                'view_mode': 'form',
                'view_type': 'form',
                'view_id': form_view_id,
                'target': 'new',
            }
        else:
            raise ValidationError(_(
                "You cannot create offer to this applicant, you are't the recruitment/hr/other responsible for this job nor a manager"))
        return action

    @api.onchange('email_from')
    def validate_mail(self):
        if self.email_from:
            # I add 'A-Z' to allow capital letters in email format
            # match = re.match('^[_a-zA-Z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$',
            #                  self.email_from)
            match = re.match('^[_a-zA-Z0-9-]+(\.[_a-zA-Z0-9-]+)*@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*(\.[a-zA-Z]{2,4})$',
                             self.email_from)
            if match == None:
                raise ValidationError('Not a valid E-mail ID')

    @api.constrains('email_form', 'partner_mobile', 'partner_phone', 'face_book', 'linkedin')
    def constrain_email_mobile(self):
        for applicant in self:
            if not applicant.email_from and not applicant.partner_mobile and not applicant.partner_phone and \
                    not applicant.face_book and not applicant.linkedin:
                raise ValidationError(_('Please insert at least one Applicant info.'))

    @api.constrains('partner_mobile', 'partner_name', 'partner_phone')
    def constrain_partner_mobile(self):
        # pattern =re.compile("[0-9]")
        # pattern = re.compile("[@_!#$%^&*()<>?/\|}{~:]")
        # match= pattern.match(self.partner_mobile)
        # if match == None:
        for applicant in self:
            if applicant.partner_mobile:
                if applicant.partner_mobile.isnumeric() == False or len(applicant.partner_mobile) > 15:
                    raise ValidationError(_('Mobile number must be digits only and not greater than 15 digit. '))
            if applicant.partner_phone:
                if applicant.partner_phone.isnumeric() == False or len(applicant.partner_phone) > 15:
                    raise ValidationError(_('Phone number must be digits only and not greater than 15 digit. '))
            if applicant.partner_name:
                # pattern = re.compile("[0-9]")
                # pattern = ('^([^~+&@!#$%]*)$')
                # match = re.search('^([{}\[\]\^~+&@!#)=\'"/|$%(*!+_\-]*)$',applicant.partner_name)
                if all(x.isalpha() or x.isspace() for x in applicant.partner_name):
                    pass
                else:
                    # if applicant.partner_name.isalpha() == False :
                    raise ValidationError(_('Applicant Name must be Characters only . '))

    # oveeride  method to prevent current user to change state if is not recruiter responsible for application
    @api.onchange('stage_id')
    def onchange_stage_id(self):
        # res=super(Applicant, self).onchange_stage_id
        activity_result = self.env['mail.activity'].search([('res_id', '=', self._origin.id)])
        if activity_result:
            for activity in activity_result:
                if not activity.call_result_id and not activity.interview_result:
                    raise ValidationError('Please insert Activity Result in order to be transferred to another stage')
        if self.env.user.id != self.user_id.id and not self.env.user.has_group(
                'hr_recruitment.group_hr_recruitment_manager') and self._origin.id:
            raise ValidationError(
                'This Application is Owned by another Recruiter , you are not allowed to take any action on.')
        else:
            vals = self._onchange_stage_id_internal(self.stage_id.id)
            if vals['value'].get('date_closed'):
                self.date_closed = vals['value']['date_closed']
        return super(Applicant, self).onchange_stage_id()

    def check_application_duplication(self):
        contact_obj = self.env['res.partner']
        duplicated_contact = []
        if self.partner_mobile:
            duplicated_partner_mobiles = contact_obj.search([('mobile', '=', self.partner_mobile)]).ids
            if len(duplicated_partner_mobiles) > 1:
                for dup_partner_mobile in duplicated_partner_mobiles:
                    if dup_partner_mobile not in duplicated_contact:
                        duplicated_contact.append(dup_partner_mobile)
        if self.partner_phone:
            duplicated_partner_phones = contact_obj.search([('phone', '=', self.partner_phone)]).ids
            if len(duplicated_partner_phones) > 1:
                for dup_partner_phone in duplicated_partner_phones:
                    if dup_partner_phone not in duplicated_contact:
                        duplicated_contact.append(dup_partner_phone)
        if self.linkedin:
            duplicated_linkedins = contact_obj.search([('linkedin', '=', self.linkedin)]).ids
            if len(duplicated_linkedins) > 1:
                for dup_linkedin in duplicated_linkedins:
                    if dup_linkedin not in duplicated_contact:
                        duplicated_contact.append(dup_linkedin)
        if self.face_book:
            duplicated_face_books = contact_obj.search([('face_book', '=', self.face_book)]).ids
            if len(duplicated_face_books) > 1:
                for dup_face_book in duplicated_face_books:
                    if dup_face_book not in duplicated_contact:
                        duplicated_contact.append(dup_face_book)

        if duplicated_contact:
            return duplicated_contact


class Stage(models.Model):
    _inherit = 'hr.recruitment.stage'

    @api.multi
    def unlink(self):
        """Prevent deleting offer call cv_source hired interview  stage"""
        real_ids, xml_ids = zip(*self.get_xml_id().items())
        if ('recruitment_ads.application_stage_offer_cycle_data') in xml_ids or (
                'recruitment_ads.application_stage_cvsource_cycle_data') in xml_ids \
                or ('recruitment_ads.application_stage_call_cycle_data') in xml_ids or (
                'recruitment_ads.application_stage_interview_cycle_data') in xml_ids \
                or ('recruitment_ads.application_stage_hired_cycle_data') in xml_ids:
            raise ValidationError(_("You are not allowed to delete this Stage"))

        return super(Stage, self).unlink()

    @api.multi
    def write(self, vals):
        """Prevent edit  offer call cv_source hired interview  stage"""
        real_ids, xml_ids = zip(*self.get_xml_id().items())
        if ('recruitment_ads.application_stage_offer_cycle_data') in xml_ids or (
                'recruitment_ads.application_stage_cvsource_cycle_data') in xml_ids \
                or ('recruitment_ads.application_stage_call_cycle_data') in xml_ids or (
                'recruitment_ads.application_stage_interview_cycle_data') in xml_ids \
                or ('recruitment_ads.application_stage_hired_cycle_data') in xml_ids:
            raise ValidationError(_("You are not allowed to edit this Stage"))

        return super(Stage, self).write(vals)
