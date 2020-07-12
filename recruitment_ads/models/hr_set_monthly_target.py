from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HRSetMonthlyTarget(models.Model):
    _name = 'hr.set.monthly.target'
    _description = 'Set Monthly Target'

    name = fields.Date(required=True, default=fields.Date.today, track_visibility='always')
    date_to = fields.Date(required=True, default=fields.Date.today, track_visibility='always')
    bu_ids = fields.Many2many('business.unit', 'set_monthly_target_bu_rel', 'monthly_target_id', 'bu_id',
                              string='Business Units')
    job_ids = fields.Many2many('hr.job', string='Job Position')
    user_ids = fields.Many2many('res.users', 'set_monthly_target_users_rel', 'monthly_target_id', 'user_id',
                                string='Recruiter Responsible')
    line_ids = fields.One2many('hr.set.monthly.target.line', 'target_id', string='Lines')


class HRSetMonthlyTargetLine(models.Model):
    _name = 'hr.set.monthly.target.line'
    _description = 'Set Monthly Target Lines'

    name = fields.Date(required=True, track_visibility='always')
    recruiter_bu_id = fields.Many2one('business.unit', string='Recruiter BU',
                                      track_visibility='always')
    recruiter_id = fields.Many2one('res.users', required=True, string='Recruiter Responsible',
                                   track_visibility='always')
    bu_id = fields.Many2one('business.unit', string='BU', required=True, track_visibility='always')
    department_id = fields.Many2one('hr.department', string='Department', required=True,
                                    track_visibility='always')
    section_id = fields.Many2one('hr.department', string='Section',
                                 track_visibility='always')
    job_id = fields.Many2one('job.title', string='Position', required=True, track_visibility='always')
    job_position_id = fields.Many2one('hr.job', string='Position from target',
                                      track_visibility='always')
    level_id = fields.Many2one('job.level', string='Level', track_visibility='always')

    offer_target = fields.Integer(string="Offer Target", track_visibility='always', default=0)
    hire_target = fields.Integer(string="Hire Target", track_visibility='always', default=0)
    vacant = fields.Integer(string="Vacant", track_visibility='always', default=0)
    replacement_emp = fields.Integer(string="Replacement", track_visibility='always', default=0)
    man_power = fields.Integer(string="MP", track_visibility='always', default=0)
    current_emp = fields.Integer(string="Current", track_visibility='always', default=0)
    expecting_offer_date = fields.Date(required=True, track_visibility='always', string='Expecting Offer Date')
    expecting_hire_date = fields.Date(required=True, track_visibility='always', string='Expecting Hire Date')

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
