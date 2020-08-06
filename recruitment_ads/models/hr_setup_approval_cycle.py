# -*- coding: utf-8 -*-
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import ValidationError


class HRSetupApprovalCycle(models.Model):
    _name = "hr.setup.approval.cycle"
    _description = 'Setup Approval Cycle'
    _inherit = ['mail.thread']
    _order = "name"

    name = fields.Char(string='Approval Cycle Code')
    recruiter_bu = fields.Selection([('equal', 'Equal'), ('not_equal', 'Not Equal')], string='Recruiter BU',
                                    default='equal', required=True)
    position_grade_id = fields.Many2many('position.grade', string='Position Grade', required=True)
    salary_scale_id = fields.Many2one('salary.scale', string='Salary Scale', required=True)
    offer_type = fields.Selection([('normal_offer', 'Normal Offer'),
                                   ('nursing_offer', 'Nursing Offer'), ],
                                  string="Offer Type", default="normal_offer", required=True)
    no_of_approval = fields.Integer('No Of Approval', compute='_compute_no_of_approval')
    approval_list_ids = fields.One2many('hr.setup.approval.cycle.users', 'approval_cycle_id', 'Approval List')

    @api.one
    def _compute_no_of_approval(self):
        self.no_of_approval = len([pl for pl in self.approval_list_ids if pl.stage_id.name == 'Users'])

    @api.model
    def create(self, vals):
        is_exist = self.search([
            ('recruiter_bu', '=', vals.get('recruiter_bu', False)),
            ('position_grade_id', 'in',
             vals.get('position_grade_id')[0][2] if vals.get('position_grade_id', False) else False),
            ('salary_scale_id', '=', vals.get('salary_scale_id', False)),
            ('offer_type', '=', vals.get('offer_type', False))
        ], limit=1)
        if is_exist:
            raise ValidationError(
                _('There is another Approval cycle exits (%s) with the same Filtration Criteria') % is_exist.name)
        approval_list = []
        stage_id = self.env['hr.master.approval.group.state'].search([], limit=1)
        for approval_user in self.env['hr.master.approval.group'].search([]):
            approval_list.append((0, 0, {
                'name': approval_user.name,
                'stage_id': stage_id.id,
            }))
        vals['approval_list_ids'] = approval_list
        vals['name'] = self.env.ref('recruitment_ads.sequence_approval_cycle').next_by_id()
        return super(HRSetupApprovalCycle, self).create(vals)

    @api.multi
    def write(self, vals):
        for approval_cycle in self:
            is_exist = approval_cycle.search([
                ('recruiter_bu', '=', vals.get('recruiter_bu', False) or approval_cycle.recruiter_bu),
                ('position_grade_id', 'in',
                 vals.get('position_grade_id')[0][2] if vals.get('position_grade_id',
                                                                 False) else approval_cycle.position_grade_id.ids),
                ('salary_scale_id', '=', vals.get('salary_scale_id', False) or approval_cycle.salary_scale_id.id),
                ('offer_type', '=', vals.get('offer_type', False) or approval_cycle.offer_type)
            ], limit=1)
            if is_exist:
                raise ValidationError(
                    _('There is another Approval cycle exits (%s) with the same Filtration Criteria.') % is_exist.name)
        return super(HRSetupApprovalCycle, self).write(vals)


class HRSetupApprovalCycleUsers(models.Model):
    _name = "hr.setup.approval.cycle.users"
    _description = 'Setup Approval User'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _order = 'id asc'

    def _get_default_stage_id(self):
        """ Gives default stage_id """
        return self.env['hr.master.approval.group.state'].search([], limit=1).id

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = stages._search([], order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    name = fields.Char(string='name', required=True)
    stage_id = fields.Many2one('hr.master.approval.group.state', string="state", track_visibility='onchange',
                               default=_get_default_stage_id, group_expand='_read_group_stage_ids', copy=False,
                               index=True, required=True)
    approval_cycle_id = fields.Many2one('hr.setup.approval.cycle', 'Approval Cycle')
    kanban_state = fields.Selection([
        ('normal', 'Grey'),
        ('user', 'Green')], string='Kanban State',
        copy=False, default='normal', required=True)


class HRMasterApprovalGroup(models.Model):
    _name = "hr.master.approval.group"
    _description = 'Master Approval Group'
    _inherit = ['mail.thread']
    _order = 'sequence asc'

    name = fields.Char(String='name', required=True)
    sequence = fields.Integer(default=10)


class HRMasterApprovalGroupState(models.Model):
    _name = "hr.master.approval.group.state"
    _description = 'Master Approval State'
    _inherit = ['mail.thread']
    _order = 'sequence asc'

    name = fields.Char(String='name', required=True)
    sequence = fields.Integer(default=10)
