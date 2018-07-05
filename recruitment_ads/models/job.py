from odoo import models, fields, api


class JobPosition(models.Model):
    _name = 'job.position'
    name = fields.Char(required=True)
    department_ids = fields.Many2many('hr.department', 'hr_dep_job_rel', 'job_id', 'dep_id')


class BusinessUnit(models.Model):
    _name = 'business.unit'
    name = fields.Char(required=True)


class Department(models.Model):
    _inherit = "hr.department"
    business_unit_id = fields.Many2one('business.unit', required=True)
    job_position = fields.Many2many('job.position', 'hr_dep_job_rel', 'dep_id', 'job_id', string='Job Position')


class Job(models.Model):
    _inherit = ['hr.job']
    business_unit_id = fields.Many2one('business.unit', required=True)
    department_id = fields.Many2one('hr.department', string='Department', required=True)
    job_position = fields.Many2one('job.position', string='Job Position', required=True)

    @api.onchange('job_position')
    def onchange_job_position(self):
        self.name = self.job_position.name

    @api.onchange('business_unit_id')
    def onchange_business_unit(self):
        self.department_id = False
        self.job_position = False

    @api.onchange('department_id')
    def onchange_department_id(self):
        self.job_position = False