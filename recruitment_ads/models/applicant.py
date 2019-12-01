import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Applicant(models.Model):
    _inherit = "hr.applicant"

    email_from = fields.Char(required=True)
    partner_phone = fields.Char(required=True)
    partner_mobile = fields.Char(required=True)
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
                'default_name': self.name + "'s interview",
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
            match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', self.email_from)
            if match == None:
                raise ValidationError('Not a valid E-mail ID')


class Stage(models.Model):
    _inherit = 'hr.recruitment.stage'

    @api.multi
    def unlink(self):
        """Prevent deleting offer stage"""
        real_ids, xml_ids = zip(*self.get_xml_id().items())
        if 'recruitment_ads.application_stage_offer_cycle_data' in xml_ids:
            raise ValidationError(_("You can't delete offer stage"))
        return super(Stage, self).unlink()
