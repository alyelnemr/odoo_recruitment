from odoo import models, fields, api, _

class HrRequest(models.Model):
    _name = 'hr.request'
    _inherit = ['mail.thread']
    _description = 'Hr Request'
    _rec_name = 'applicant_code'

    applicant_name = fields.Char(string='Applicant Name', required=True)
    applicant_code = fields.Char(string='Applicant Code', required=True)
    business_unit_id = fields.Many2one('business.unit', string='Business Unit', required=True)
    job_id = fields.Many2one('hr.job', string='Job Position', required=True)
    department_id = fields.Many2one('hr.department', string='Department', required=True)
    section_id = fields.Many2one('hr.department', string='Section', required=True)
    recruiter_responsible = fields.Many2one('res.users', string='Recruiter Responsible', readonly=True)
    hr_responsible = fields.Many2one('res.partner', string='Hr Responsible', readonly=True)
    hiring_status = fields.Char()
    hiring_date = fields.Date()
