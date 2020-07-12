from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


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
                        'name': self.date_from,
                        'recruiter_id': user.id,
                        'recruiter_bu_id': user.business_unit_id.id,
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


class HRSetMonthlyTargetLine(models.Model):
    _name = 'hr.set.monthly.target.line'
    _description = 'Set Monthly Target Lines'

    name = fields.Date(required=True, track_visibility='always')
    recruiter_bu_id = fields.Many2one('business.unit', string='Recruiter BU',
                                      track_visibility='always')
    recruiter_id = fields.Many2one('res.users', required=True,  string='Recruiter Responsible',
                                   track_visibility='always')
    bu_id = fields.Many2one('business.unit', string='BU', required=True,  track_visibility='always')
    department_id = fields.Many2one('hr.department', string='Department', required=True,
                                    track_visibility='always')
    section_id = fields.Many2one('hr.department', string='Section',
                                 track_visibility='always')
    job_id = fields.Many2one('job.title', string='Position', required=True,  track_visibility='always')
    job_position_id = fields.Many2one('hr.job', string='Position from target',
                                      track_visibility='always')
    level_id = fields.Many2one('job.level', string='Level', track_visibility='always')

    offer_target = fields.Integer(string="Offer Target", track_visibility='always', default=0)
    hire_target = fields.Integer(string="Hire Target", track_visibility='always', default=0)
    vacant = fields.Integer(string="Vacant", track_visibility='always', default=0)
    replacement_emp = fields.Integer(string="Replacement", track_visibility='always', default=0)
    man_power = fields.Integer(string="MP", track_visibility='always', default=0)
    current_emp = fields.Integer(string="Current", track_visibility='always', default=0)
    expecting_offer_date = fields.Date( track_visibility='always',string='Expecting Offer Date')
    expecting_hire_date = fields.Date( track_visibility='always',string='Expecting Hire Date')


    target_id = fields.Many2one('hr.set.monthly.target', string='Set Monthly Target', track_visibility='always')
    position_type = fields.Selection(
        [('normal', 'Normal'),
         ('critical', 'Critical'), ], string='Position Type',
        default='normal', )

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
            'date_from': self.name,
            'date_to': self.name,
            'job_ids': [(6, 0, [self.job_position_id.id] or [])] if self.job_position_id else False,
            'recruiter_ids': [(6, 0, [self.recruiter_id.id] or [])] if self.recruiter_id else False,
        })
        action = self.env['ir.actions.act_window'].for_xml_id('recruitment_ads',
                                                              'generate_monthly_target_report_wizard_action')
        return 'web#action=' + str(action.get('id')) + '&id=' + str(res.id)
