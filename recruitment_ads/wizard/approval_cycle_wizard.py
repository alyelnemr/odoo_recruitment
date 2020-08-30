from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HRApprovalCycleWizard(models.TransientModel):
    _name = "hr.approval.cycle.wizard"
    _description = 'Approval Cycle Wizard'

    @api.multi
    def action_save(self):
        self.ensure_one()
        if any(not user.approval_user_id for user in self.users_list_ids):
            raise ValidationError(_('Approval User is required.'))
        user_list = []
        for user in self.users_list_ids:
            user_list.append((0, 0, {
                'approval_position_id': user.approval_position_id.id,
                'approval_user_id': user.approval_user_id.id
            }))
        self.env['hr.approval.cycle'].create({
            'name': self.name,
            'offer_id': self.offer_id.id,
            'users_list_ids': user_list,
            'comment': self.comment,
        })
        self.offer_id.application_id.stage_id = self.env.ref('recruitment_ads.application_stage_approval_cycle_data').id
        return {'type': 'ir.actions.act_window_close'}


    @api.multi
    def action_save_send(self):
        self.ensure_one()
        if any(not user.approval_user_id for user in self.users_list_ids):
            raise ValidationError(_('Approval User is required.'))
        user_list = []
        for user in self.users_list_ids:
            user_list.append((0, 0, {
                'approval_position_id': user.approval_position_id.id,
                'approval_user_id': user.approval_user_id.id
            }))
        approval_cycle=self.env['hr.approval.cycle'].create({
            'name': self.name,
            'offer_id': self.offer_id.id,
            'users_list_ids': user_list,
            'comment': self.comment,
        })
        self.offer_id.application_id.stage_id = self.env.ref('recruitment_ads.application_stage_approval_cycle_data').id
        template = self.env.ref('recruitment_ads.approval_cycle_mail_template', False)
        if template:
            if self.users_list_ids[0].approval_user_id.email:
                template.email_to = self.users_list_ids[0].approval_user_id.email
                self.env['mail.template'].browse(template.id).send_mail(approval_cycle.id)
                approval_cycle.state = 'pending'
                approval_cycle.users_list_ids[0].sent = True
        return {'type': 'ir.actions.act_window_close'}

    name = fields.Char(string='Name')
    application_id = fields.Many2one('hr.applicant')
    offer_id = fields.Many2one('hr.offer', string='Offer')
    salary_scale_id = fields.Many2one('salary.scale', string="Salary Scale", related='offer_id.salary_scale_id',
                                      store=True)
    position_grade_id = fields.Many2one('position.grade', string="Position Grade", related='offer_id.position_grade_id',
                                        store=True)
    setup_approval_cycle_id = fields.Many2one('hr.setup.approval.cycle', string='Setup Approval Cycle')

    comment = fields.Text(string='Comments')
    users_list_ids = fields.One2many('hr.approval.cycle.users.wizard', 'approval_cycle_id', 'Users', auto_join=True)
    Next_user = fields.Many2one('res.users')

class HrApprovalCycleUsersWizard(models.TransientModel):
    _name = 'hr.approval.cycle.users.wizard'
    _description = 'Approval Cycle Users Wizard'

    approval_position_id = fields.Many2one('hr.setup.approval.cycle.users', 'Approval Position')
    approval_user_id = fields.Many2one('res.partner', 'Approval User', domain=[('GUID', '!=', False)])
    approval_cycle_id = fields.Many2one('hr.approval.cycle.wizard', string='Approval Cycle Wizard', required=True,
                                        ondelete='cascade',
                                        index=True, copy=False)
