# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrApprovalCycle(models.Model):
    _name = 'hr.approval.cycle'
    _description = 'Approval Cycle'
    _inherit = ['mail.thread']
    _order = 'id DESC'

    @api.onchange('users_list_ids.state', 'users_list_ids.sent')
    @api.depends('users_list_ids.state', 'users_list_ids.sent')
    def _compute_state(self):
        for approval in self:
            if any(x.state == 'no_action' and x.sent for x in approval.users_list_ids):
                approval.state = 'pending'
            elif all(x.state == 'approved' for x in approval.users_list_ids):
                approval.state = 'approved'
            elif any(x.state == 'rejected' for x in approval.users_list_ids):
                approval.state = 'rejected'
            else:
                approval.state = 'created'

    name = fields.Char(string='Name')
    offer_id = fields.Many2one('hr.offer', string='Offer')
    application_id = fields.Many2one('hr.applicant', related='offer_id.application_id',store=True)
    applicant_name = fields.Char(string='Candidate Name', related='application_id.partner_name')
    job_id = fields.Many2one('hr.job', string='Job position', related='application_id.job_id', store=True)
    department_id = fields.Many2one('hr.department', string='Department', related='application_id.department_id')
    section_id = fields.Many2one('hr.department', string='Section', related='application_id.section_id')
    business_unit_id = fields.Many2one('business.unit', string='Business Unit', related='job_id.business_unit_id',
                                       store=True)

    create_uid = fields.Many2one('res.users', string='Recruiter Responsible', readonly=True)
    generated_by_bu_id = fields.Many2one('business.unit', string="Recruiter BU ", related='create_uid.business_unit_id',
                                         store=True)
    total_package = fields.Float(string='Offer Total Package', related='offer_id.total_package', store=True)
    salary_scale_id = fields.Many2one('salary.scale', string="Salary Scale", related='offer_id.salary_scale_id',
                                      store=True)
    position_grade_id = fields.Many2one('position.grade', string="Position Grade", related='offer_id.position_grade_id',
                                        store=True)
    setup_approval_cycle_id = fields.Many2one('hr.setup.approval.cycle', string='Setup Approval Cycle')
    state = fields.Selection(
        [('created', 'Created'),
         ('pending', 'Pending'),
         ('approved', 'Approved'),
         ('rejected', 'Rejected')
         ], default='created', string="Approval Status", track_visibility='onchange', compute=_compute_state,
        required=True, store=True)
    comment = fields.Text(string='Comments')
    users_list_ids = fields.One2many('hr.approval.cycle.users', 'approval_cycle_id', 'Users', auto_join=True)

    @api.multi
    def action_send(self):
        self.ensure_one()
        return True


class HrApprovalCycleUsers(models.Model):
    _name = 'hr.approval.cycle.users'
    _description = 'Approval Cycle Users'

    approval_position_id = fields.Many2one('hr.setup.approval.cycle.users', 'Approval Position', required=True,
                                           copy=False)
    approval_user_id = fields.Many2one('res.partner', 'Approval User', domain=[('GUID', '!=', False)], required=True,
                                       copy=False)
    approval_cycle_id = fields.Many2one('hr.approval.cycle', string='Approval Cycle Wizard', required=True,
                                        ondelete='cascade',
                                        index=True, copy=False)
    state = fields.Selection([
        ('no_action', 'No Action'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='no_action', required=True, copy=False)
    sent = fields.Boolean('Send Email', default=False, copy=False)
    notes = fields.Text(string='Notes')
