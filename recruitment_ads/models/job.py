from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class JobPosition(models.Model):
    _name = 'job.title'
    name = fields.Char(required=True)
    department_ids = fields.Many2many('hr.department', 'hr_dep_job_rel', 'job_id', 'dep_id')


class BusinessUnit(models.Model):
    _name = 'business.unit'
    name = fields.Char(required=True)


class Department(models.Model):
    _inherit = "hr.department"
    business_unit_id = fields.Many2one('business.unit', required=True)
    job_title_ids = fields.Many2many('job.title', 'hr_dep_job_rel', 'dep_id', 'job_id', string='Job Titles')

    @api.constrains('business_unit_id', 'parent_id')
    def check_business_unit(self):
        for dep in self:
            if dep.parent_id.business_unit_id:
                if dep.business_unit_id != dep.parent_id.business_unit_id:
                    raise ValidationError(_("You can't create department with BU different from its parent department "))


class Job(models.Model):
    _inherit = ['hr.job']
    business_unit_id = fields.Many2one('business.unit', required=True)
    department_id = fields.Many2one('hr.department', string='Department', required=True)
    job_title_id = fields.Many2one('job.title', string='Job Title', required=True)

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
