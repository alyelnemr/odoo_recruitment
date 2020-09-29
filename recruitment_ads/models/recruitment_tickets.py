from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from lxml import etree


class RecruitmentTickets(models.Model):
    _name = 'recruitment.tickets'
    _inherit = ['mail.thread']
    _description = 'Recruitment Tickets'
    _order = 'business_unit_id,create_date'
    _rec_name = 'applicant_code'

    applicant_name = fields.Char(string='Applicant Name', required=True)
    applicant_code = fields.Char(string='Applicant Code', required=True)
    business_unit_id = fields.Many2one('business.unit', string='Business Unit', required=True)
    job_id = fields.Many2one('hr.job', string='Job Position', required=True)
    department_id = fields.Many2one('hr.department', string='Department', required=True)
    section_id = fields.Many2one('hr.department', string='Section')
    create_uid = fields.Many2one('res.users', string='Requester', readonly=True)
