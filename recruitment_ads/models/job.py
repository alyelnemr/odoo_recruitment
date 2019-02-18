from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class JobPosition(models.Model):
    _name = 'job.title'
    name = fields.Char(required=True)
    department_ids = fields.Many2many('hr.department', 'hr_dep_job_rel', 'job_id', 'dep_id')
    job_code = fields.Char(string="Job Code", required=True)
    has_application = fields.Boolean(string='Has Application', compute='_compute_has_application')

    def _compute_has_application(self):
        title_id = self.id
        if self.env['hr.applicant'].search([('job_id.job_title_id.id', '=', title_id)], limit=1):
            self.has_application = True

    _sql_constraints = [
        ('job_title_uniq',
         'unique(name)',
         'Job title entered before, Job title must be unique.'),
        ('job_code_uniq',
         'unique(job_code)',
         'Job Code entered before, Job Code must be unique.'),
    ]


class BusinessUnit(models.Model):
    _name = 'business.unit'
    name = fields.Char(required=True)


class Department(models.Model):
    _inherit = "hr.department"

    def _get_default_bu(self):
        return self.env.ref('recruitment_ads.main_andalusia_bu',raise_if_not_found=False)

    business_unit_id = fields.Many2one('business.unit', required=True, default=_get_default_bu)
    job_title_ids = fields.Many2many('job.title', 'hr_dep_job_rel', 'dep_id', 'job_id', string='Job Titles')

    @api.constrains('business_unit_id', 'parent_id')
    def check_business_unit(self):
        for dep in self:
            if dep.parent_id.business_unit_id:
                if dep.business_unit_id != dep.parent_id.business_unit_id:
                    raise ValidationError(
                        _("You can't create department with BU different from its parent department "))

    _sql_constraints = [('name_business_unit_id_unique',
                         'unique(name,business_unit_id)',
                         'The name of the department be unique per business unit!'),]


class Job(models.Model):
    _inherit = ['hr.job']

    def _get_default_bu(self):
        return self.env.ref('recruitment_ads.main_andalusia_bu',raise_if_not_found=False)

    business_unit_id = fields.Many2one('business.unit', required=True, default=_get_default_bu)
    department_id = fields.Many2one('hr.department', string='Department', required=True)
    job_title_id = fields.Many2one('job.title', string='Job Title', required=True)
    user_id = fields.Many2one('res.users', default=lambda self:self.env.user)

    other_recruiters_ids = fields.Many2many('res.users',string="Other Recruiters")

    @api.onchange('job_title_id')
    def onchange_job_title_id(self):
        self.name = self.job_title_id.name

    @api.onchange('business_unit_id')
    def onchange_business_unit(self):
        self.department_id = False
        self.job_title_id = False

    @api.onchange('department_id')
    def onchange_department_id(self):
        self.job_title_id = False
