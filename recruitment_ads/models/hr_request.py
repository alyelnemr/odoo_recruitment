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

    @api.multi
    def create_user_account(self):
        self.ensure_one()

        ir_model_data = self.env['ir.model.data']
        try:
            template_id = \
                ir_model_data.get_object_reference('recruitment_ads',
                                                   'create_user_account_mail_template')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = \
                ir_model_data.get_object_reference('recruitment_ads',
                                                   'view_create_user_account_mail_compose_message_wizard_from')[1]
        except ValueError:
            compose_form_id = False

        ctx = {
            'default_model':'hr.request',
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'time_format': '%I:%M %p',
            'force_email': True,
        }

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'create.user.account.mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
