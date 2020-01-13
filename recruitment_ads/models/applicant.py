import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class IrAttachmentInherit(models.Model):
    _inherit = 'ir.attachment'
    # attach_name_seq = fields.Char()
    file_name_seq = fields.Char()

    @api.onchange('datas_fname')
    def _get_attach_name(self):
        if self.datas_fname and self.res_model == 'hr.applicant':
            no_attach= self.env['ir.attachment'].search([('res_id', '=', self.res_id)],order='create_date asc')
            extension= self.datas_fname.split(".")
            if extension:
                last_item = len(extension) - 1
                extension = extension[last_item]

                if no_attach:
                    last_attach_index = len(no_attach) - 1
                    last_attach_obj = no_attach[last_attach_index]
                    self.file_name_seq = int(last_attach_obj.file_name_seq) + 1
                else:
                    self.file_name_seq = str(1)
                if self.name:
                    self.datas_fname = self.name + '(' + self.file_name_seq + ')' + '.' + extension
                    self.name = self.name + '(' + self.file_name_seq  + ')'
    @api.depends('res_model', 'res_id')
    def _compute_res_name(self):
        res = super(IrAttachmentInherit, self). _compute_res_name()
        for attachment in self:
            if attachment.res_model and attachment.res_id:
                if attachment.res_model == 'hr.applicant':
                    record = self.env[attachment.res_model].browse(attachment.res_id)
                    attachment.res_name = record.display_name
                    attachment.name = record.display_name
        return res

class Applicant(models.Model):
    _inherit = "hr.applicant"

    email_from = fields.Char(required=False)
    partner_phone = fields.Char()
    partner_mobile = fields.Char()

    partner_name = fields.Char(required=True)
    job_id = fields.Many2one('hr.job', "Applied Job", ondelete='restrict')

    partner_id = fields.Many2one('res.partner', "Applicant", required=True)
    applicant_history_ids = fields.Many2many('hr.applicant', 'applicant_history_rel', 'applicant_id', 'history_id',
                                             string='History', readonly=False)
    last_activity = fields.Many2one('mail.activity.type', compute='_get_activity')
    last_activity_date = fields.Date(compute='_get_activity')
    result = fields.Char(compute='_get_activity')
    source_id = fields.Many2one('utm.source', required=True)
    offer_id = fields.Many2one('hr.offer', string='Offer', readonly=True)
    cv_matched = fields.Boolean('Matched', default=False)
    reason_of_rejection = fields.Char('Reason of Rejection',help="Reason why this is applicant not matched")
    count_done_interviews = fields.Integer('Done Interviews Count', compute='_get_count_done_interviews')
    salary_current = fields.Float("Current Salary", help="Current Salary of Applicant")
    name = fields.Char("Application Code", readonly=True, required=False, compute='_compute_get_application_code',
                       store=True)
    serial = fields.Char('serial',copy=False)

    @api.one
    @api.depends('job_id.job_title_id.job_code', 'partner_id.date_of_birth', 'partner_name', 'serial')
    def _compute_get_application_code(self):
        job_code = self.job_id.job_title_id.job_code
        date_of_birth = self.partner_id.date_of_birth if self.partner_id.date_of_birth else "0000"
        initials = ''.join(
            initial[0].upper() for initial in self.partner_name.split())[:4] if self.partner_name else False
        applicant_name = initials
        serial = self.serial
        self.name = '-'.join(filter(lambda i: i, [job_code, date_of_birth, applicant_name, serial]))

    @api.model
    def create(self, vals):
        res = super(Applicant, self).create(vals)
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

    @api.multi
    def unlink(self):
        if self.with_context({'active_test': False}).activity_ids:
            raise ValidationError(_("Can't delete application that has activities"))
        return super(Applicant, self).unlink()

    @api.depends('activity_ids')
    def _get_activity(self):
        for applicant in self:
            activities = applicant.with_context({'active_test': False}).activity_ids
            if activities:
                last_activity = activities.sorted('create_date')[-1]
                applicant.last_activity = last_activity.activity_type_id
                applicant.last_activity_date = last_activity.date_deadline
                if last_activity.activity_category == 'interview':
                    applicant.result = last_activity.interview_result
                else:
                    applicant.result = last_activity.call_result_id

    def _get_history_data(self, applicant_id):
        if applicant_id == False:
            return self.env['hr.applicant']
        domain = [('partner_id', '=', applicant_id)]
        return self.search(domain)

    @api.onchange('partner_id')
    def onchange_hr_applicant(self):
        history = self._get_history_data(self.partner_id.id)
        self.applicant_history_ids = [(6, 0, history.ids)]

    @api.onchange('cv_matched')
    def onchange_cv_matched(self):
        self.reason_of_rejection = False

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.partner_phone = self.partner_id.phone
        self.partner_mobile = self.partner_id.mobile
        self.email_from = self.partner_id.email
        self.partner_name = self.partner_id.name

    @api.multi
    def action_makeMeeting(self):
        self.ensure_one()
        calendar_view_id = self.env.ref('recruitment_ads.view_calendar_event_interview_calender').id
        form_view_id = self.env.ref('recruitment_ads.view_calendar_event_interview_form').id
        if  self.job_id.name and self.partner_name:
            name= self.job_id.name+"-"+self.partner_name + "'s interview"
        else:
            name=''
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
            match = re.match('^[_a-zA-Z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', self.email_from)
            if match == None:
                raise ValidationError('Not a valid E-mail ID')

    @api.constrains('email_form','partner_mobile')
    def constrain_email_mobile(self):
        for applicant in self:
            if not applicant.email_from and not applicant.partner_mobile:
                raise ValidationError (_('Please insert Applicant Mobile or Email '))

    @api.constrains('partner_mobile','partner_name','partner_phone')
    def constrain_partner_mobile(self):
        # pattern =re.compile("[0-9]")
        # pattern = re.compile("[@_!#$%^&*()<>?/\|}{~:]")
        # match= pattern.match(self.partner_mobile)
        # if match == None:
        for applicant in self:
            if applicant.partner_mobile:
                if applicant.partner_mobile.isnumeric() == False or len(applicant.partner_mobile) > 15 :
                    raise ValidationError (_('Mobile number must be digits only and not greater than 15 digit. '))
            if applicant.partner_phone:
                if applicant.partner_phone.isnumeric() == False or len(applicant.partner_phone) > 15:
                    raise ValidationError(_('Phone number must be digits only and not greater than 15 digit. '))
            if applicant.partner_name:
                # pattern = re.compile("[0-9]")
                # pattern = ('^([^~+&@!#$%]*)$')
                # match = re.search('^([{}\[\]\^~+&@!#)=\'"/|$%(*!+_\-]*)$',applicant.partner_name)
                if all(x.isalpha() or x.isspace() for x in applicant.partner_name ):
                    pass
                else:
                # if applicant.partner_name.isalpha() == False :
                    raise ValidationError(_('Applicant Name must be Characters only . '))

class Stage(models.Model):
    _inherit = 'hr.recruitment.stage'

    @api.multi
    def unlink(self):
        """Prevent deleting offer stage"""
        real_ids, xml_ids = zip(*self.get_xml_id().items())
        if 'recruitment_ads.application_stage_offer_cycle_data' in xml_ids:
            raise ValidationError(_("You can't delete offer stage"))
        return super(Stage, self).unlink()
