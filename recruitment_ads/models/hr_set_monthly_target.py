from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import datetime as datetime_now


class HRSetMonthlyTarget(models.Model):
    _name = 'hr.set.monthly.target'
    _description = 'Set Monthly Target'
    _rec_name = 'date_from'

    def _get_bu_domain(self):
        domain = []
        if self.env.user.has_group('recruitment_ads.group_hr_recruitment_coordinator') and not self.env.user.has_group(
                'hr_recruitment.group_hr_recruitment_manager'):
            domain = ['|', ('id', '=', self.env.user.business_unit_id.id),
                      ('id', 'in', self.env.user.multi_business_unit_id.ids),
                      ('name','not in',('AHQ','Careers'))
                      ]
        elif self.env.user.has_group('hr_recruitment.group_hr_recruitment_manager'):
            domain = [('name','not in',['AHQ','Careers'])]
        return domain


    date_from = fields.Date(required=True, default=fields.Date.today, track_visibility='always',string = 'Date From')
    date_to = fields.Date(required=True,default=datetime.today()+ relativedelta(months=1), track_visibility='always')
    bu_ids = fields.Many2many('business.unit', 'set_monthly_target_bu_rel', 'monthly_target_id', 'bu_id',
                              string='Business Units', domain=lambda self: self._get_bu_domain())
    job_ids = fields.Many2many('hr.job', string='Job Position')
    user_ids = fields.Many2many('res.users', 'set_monthly_target_users_rel', 'monthly_target_id', 'user_id',
                                string='Recruiter Responsible')
    line_ids = fields.One2many('hr.set.monthly.target.line', 'target_id', string='Lines')
    lines_count = fields.Integer(compute='_compute_lines_count')

    @api.one
    def _compute_lines_count(self):
        self.lines_count = len(self.line_ids)

    @api.onchange('bu_ids','job_ids')
    def  _get_job_user_domain(self):
        # JOB DOMAIN
        if self.bu_ids:
            job_domain = [('business_unit_id', 'in', self.bu_ids.ids), ('state', '=', 'recruit')]
        else:
            if self.env.user.has_group('hr_recruitment.group_hr_recruitment_manager'):
                job_domain = [('state', '=', 'recruit')]
            else:
                job_domain = [('business_unit_id', 'in',
                               self.env.user.business_unit_id.ids + self.env.user.multi_business_unit_id.ids),
                              ('state', '=', 'recruit')]
        # USER DOMAIN
        jobs = False
        bus = self.env.user.business_unit_id.ids + self.env.user.multi_business_unit_id.ids
        user_domain = [('active', '=', True)]
        if self.bu_ids:
            user_domain += [
                '|', ('business_unit_id', 'in', self.bu_ids.ids),
                ('multi_business_unit_id', 'in', self.bu_ids.ids),
            ]
            jobs = self.env['hr.job'].search(job_domain)
        elif bus and not self.bu_ids and self.env.user.has_group(
                'recruitment_ads.group_hr_recruitment_coordinator') and not self.env.user.has_group(
            'hr_recruitment.group_hr_recruitment_manager'):
            user_domain += ['|', ('business_unit_id', 'in', bus),
                            ('multi_business_unit_id', 'in', bus)]
        if self.job_ids:
            user_domain += [('id', 'in', self.job_ids.mapped('user_id').ids + self.job_ids.mapped(
                'other_recruiters_ids').ids)]
        elif jobs:
            user_domain += [('id', 'in', jobs.mapped('user_id').ids + jobs.mapped('other_recruiters_ids').ids)]

        if self.env.user.has_group('recruitment_ads.group_hr_recruitment_coordinator') and not self.env.user.has_group(
                'hr_recruitment.group_hr_recruitment_manager') and self.job_ids and not self._context.get(
            'get_domain', False):
            if len(self.env['res.users'].search(user_domain)) == 0:
                raise ValidationError(_('The Selected Job positions have no recruiters under your BU'))
        return {'domain': {'job_ids': job_domain ,'user_ids': user_domain}}


    @api.multi
    def search_filter(self):
        self.ensure_one()
        for r in self:
            if r.date_to < r.date_from:
                raise ValidationError(_("You can't select start date greater than end date"))
        self.line_ids.unlink()
        if self.job_ids:
            job_domain = [('id', 'in', self.job_ids.ids)]
        else:
            job_domain = self.with_context({'get_domain': True})._get_job_user_domain().get('domain', False).get('job_ids',
                                                                                                             False)
        if self.user_ids:
            user_domain = [('id', 'in', self.user_ids.ids)]
        else:
            user_domain = self.with_context({'get_domain': True})._get_job_user_domain().get('domain', False).get(
                'user_ids', False)

        job_report = self.env['hr.job'].search(job_domain)
        user_report = self.env['res.users'].search(user_domain)
        for job in job_report:
            for user in job.mapped('user_id') + job.mapped('other_recruiters_ids'):
                if user in user_report:
                    self.env['hr.set.monthly.target.line'].create({
                        'recruiter_id': user.id,
                        'recruiter_bu_id': user.business_unit_id.id,
                        'start_date': self.date_from,
                        'bu_id': job.business_unit_id.id,
                        'department_id': job.department_id.id,
                        'section_id': job.section_id.id,
                        'job_id': job.job_title_id.id,
                        'job_position_id': job.id,
                        'level_id': job.job_level_id.id,
                        'target_id': self.id,
                    })

        if len(self.line_ids) == 0:
            raise ValidationError('Please Set Monthly Target first before saving')

        return True

    @api.model
    def create(self, vals):
        users=[]
        if vals.get('job_ids')[0][2]:
            job_domain = [('id', 'in', vals.get('job_ids')[0][2])]
        else:
            job_domain = self.with_context({'get_domain': True})._get_job_user_domain().get('domain', False).get('job_ids',
                                                                                                             False)
        if vals.get('user_ids')[0][2]:
            user_domain = [('id', 'in', vals.get('user_ids')[0][2])]
        else:
            user_domain = self.with_context({'get_domain': True})._get_job_user_domain().get('domain', False).get(
                'user_ids', False)

        job_report = self.env['hr.job'].search(job_domain)
        user_report = self.env['res.users'].search(user_domain)

        for job in job_report:
            for user in job.mapped('user_id') + job.mapped('other_recruiters_ids'):
                if user in user_report:
                    users.append(user)
        if not users:
          raise ValidationError('The Selected Job positions have no recruiters under your BU')

        if not (self.env.user.has_group('recruitment_ads.group_hr_recruitment_coordinator') or self.env.user.has_group(
                'hr_recruitment.group_hr_recruitment_manager')):
            raise ValidationError(_('You are not allowed to set targets'))
        res = super(HRSetMonthlyTarget, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        if not (self.env.user.has_group('recruitment_ads.group_hr_recruitment_coordinator') or self.env.user.has_group(
                'hr_recruitment.group_hr_recruitment_manager')):
            raise ValidationError(_('You are not allowed to set targets'))
        return super(HRSetMonthlyTarget, self).write(vals)


class HRSetMonthlyTargetLine(models.Model):
    _name = 'hr.set.monthly.target.line'
    _description = 'Set Monthly Target Lines'
    _rec_name = 'start_date'

    start_date = fields.Date( track_visibility='always')
    recruiter_bu_id = fields.Many2one('business.unit', string='Recruiter BU',
                                      track_visibility='always',readonly=True)
    recruiter_id = fields.Many2one('res.users',   string='Recruiter Responsible',
                                   track_visibility='always',readonly=True)
    bu_id = fields.Many2one('business.unit', string='BU',  track_visibility='always',readonly=True)
    department_id = fields.Many2one('hr.department', string='Department',
                                    track_visibility='always',readonly=True)
    section_id = fields.Many2one('hr.department', string='Section',
                                 track_visibility='always',readonly=True)
    job_id = fields.Many2one('job.title', string='Position',  track_visibility='always',readonly=True)
    job_position_id = fields.Many2one('hr.job', string='Position from target',
                                      track_visibility='always')
    level_id = fields.Many2one('job.level', string='Level', track_visibility='always')

    offer_target = fields.Integer(string="Offer Target", track_visibility='always', default=0)
    hire_target = fields.Integer(string="Hire Target", track_visibility='always', default=0)
    vacant = fields.Integer(string="Vacant", track_visibility='always', default=0,readonly=True,compute='_compute_vacant')
    replacement_emp = fields.Integer(string="Replacement", track_visibility='always', default=0)
    man_power = fields.Integer(string="MP", track_visibility='always', default=0)
    current_emp = fields.Integer(string="Current", track_visibility='always', default=0)
    expecting_offer_date = fields.Date( track_visibility='always',string='Expecting Offer Date',readonly=True,compute ='compute_offer_hire_expecting_date')
    expecting_hire_date = fields.Date( track_visibility='always',string='Expecting Hire Date',readonly=True ,compute ='compute_offer_hire_expecting_date')
    offer_weight = fields.Float( track_visibility='always',string='Offer Weight',readonly=True)
    hire_weight = fields.Float(track_visibility='always', string='Hire Weight',readonly=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    target_id = fields.Many2one('hr.set.monthly.target', string='Set Monthly Target', track_visibility='always')
    position_type = fields.Selection(
        [('normal', 'Normal'),
         ('critical', 'Critical'), ], string='Position Type',
        default='normal', )

    @api.onchange('level_id')
    def _compute_level(self):
        for record in self:
          record.hire_weight = record.offer_weight = record.level_id.weight

    @api.onchange('start_date')
    def _validation_start_date(self):
        for record in self:
           if record.start_date > record.target_id.date_to or record.start_date < record.target_id.date_from :
               raise ValidationError('Cannot accept date before Start Date of the Target OR after the Target date .')

    @api.depends('man_power','current_emp')
    def _compute_vacant(self):
        for record in self:
            record.vacant = record.man_power - record.current_emp

    @api.depends('start_date','level_id')
    def compute_offer_hire_expecting_date(self):
        hr_policy = self.env['hr.policy'].search([('hr_policy_type','=', 'offer_and_hire')], limit=1)
        if hr_policy:
            for policy in hr_policy.offer_and_hire_level:
                for record in self:
                    if policy.level == record.level_id:
                        offer_days = int(policy.offer)
                        hire_days = int(policy.hire)
                        date_1 = datetime_now.datetime.strptime(record.start_date, "%Y-%m-%d")
                        record.expecting_offer_date = date_1 + datetime_now.timedelta(days = offer_days)
                        offer_date = datetime_now.datetime.strptime(record.expecting_offer_date, "%Y-%m-%d")
                        record.expecting_hire_date = offer_date + datetime_now.timedelta(days=hire_days)

    @api.model
    def create(self, vals):
        res = super(HRSetMonthlyTargetLine, self).create(vals)
        res.send_monthly_target_mail(vals)
        return res

    @api.multi
    def write(self, vals):
        res = super(HRSetMonthlyTargetLine, self).write(vals)
        self.send_monthly_target_mail(vals)
        return res

    def send_monthly_target_mail(self, data):
        if data:
            self.send_mail_set_monthly_target()

    @api.multi
    def send_mail_set_monthly_target(self):
        template = self.env.ref('recruitment_ads.set_monthly_target_line_email_template')
        self.env['mail.template'].browse(template.id).send_mail(self.id)

    def get_mail_url(self):
        self.ensure_one()
        res = self.env['generate.monthly.target.report.wizard'].with_env(self.env(user=self.recruiter_id)).create({
            'date_from': self.start_date,
            'date_to': self.start_date,
            'job_ids': [(6, 0, [self.job_position_id.id] or [])] if self.job_position_id else False,
            'recruiter_ids': [(6, 0, [self.recruiter_id.id] or [])] if self.recruiter_id else False,
        })
        action = self.env['ir.actions.act_window'].for_xml_id('recruitment_ads',
                                                              'generate_monthly_target_report_wizard_action')
        return 'web#action=' + str(action.get('id')) + '&id=' + str(res.id)
