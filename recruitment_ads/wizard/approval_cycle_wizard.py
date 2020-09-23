from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import uuid
import os
import base64
from odoo.tools import osutil, config
from datetime import datetime


class HRApprovalCycleWizard(models.TransientModel):
    _name = "hr.approval.cycle.wizard"
    _description = 'Approval Cycle Wizard'

    @api.multi
    def action_save(self):
        self.ensure_one()
        if any(not user.approval_user_id for user in self.users_list_ids):
            raise ValidationError(_('Approval User is required.'))
        user_list = []
        sequence = self.env.ref('recruitment_ads.sequence_approval_cycle_users')
        for user in self.users_list_ids:
            user_list.append((0, 0, {
                'approval_position_id': user.approval_position_id.id,
                'approval_user_id': user.approval_user_id.id,
                'token': str(uuid.uuid4()),
                'sequence': sequence.next_by_id()
            }))
        self.env['hr.approval.cycle'].create({
            'name': self.name,
            'offer_id': self.offer_id.id,
            'users_list_ids': user_list,
            'comment': self.comment,

        })
        self.offer_id.application_id.stage_id = self.env.ref('recruitment_ads.application_stage_approval_cycle_data').id
        return {'type': 'ir.actions.act_window_close'}

    #
    # @api.multi
    # def action_save_send(self):
    #     self.ensure_one()
    #     if any(not user.approval_user_id for user in self.users_list_ids):
    #         raise ValidationError(_('Approval User is required.'))
    #     user_list = []
    #     sequence = self.env.ref('recruitment_ads.sequence_approval_cycle_users')
    #     for user in self.users_list_ids:
    #         user_list.append((0, 0, {
    #             'approval_position_id': user.approval_position_id.id,
    #             'approval_user_id': user.approval_user_id.id,
    #             'token' : str(uuid.uuid4()),
    #             'sequence' : sequence.next_by_id()
    #
    #         }))
    #     approval_cycle=self.env['hr.approval.cycle'].create({
    #         'name': self.name,
    #         'offer_id': self.offer_id.id,
    #         'users_list_ids': user_list,
    #         'comment': self.comment,
    #     })
    #     self.offer_id.application_id.stage_id = self.env.ref('recruitment_ads.application_stage_approval_cycle_data').id
    #     template = self.env.ref('recruitment_ads.approval_cycle_mail_template', False)
    #     if template:
    #         if self.users_list_ids[0].approval_user_id.email:
    #             template.email_to = self.users_list_ids[0].approval_user_id.email
    #             token = approval_cycle.users_list_ids[0].token
    #             self.env['mail.template'].browse(template.id).send_mail(approval_cycle.users_list_ids[0].id)
    #             approval_cycle.state = 'pending'
    #             approval_cycle.users_list_ids[0].sent = True
    #     return {'type': 'ir.actions.act_window_close'}

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

    @api.multi
    def action_mail_compose_message(self):
        self.ensure_one()
        if any(not user.approval_user_id for user in self.users_list_ids):
            raise ValidationError(_('Approval User is required.'))
        user_list = []
        sequence = self.env.ref('recruitment_ads.sequence_approval_cycle_users')
        for user in self.users_list_ids:
            user_list.append((0, 0, {
                'approval_position_id': user.approval_position_id.id,
                'approval_user_id': user.approval_user_id.id,
                'token' : str(uuid.uuid4()),
                'sequence' : sequence.next_by_id()

            }))
        approval_cycle=self.env['hr.approval.cycle'].create({
            'name': self.name,
            'offer_id': self.offer_id.id,
            'users_list_ids': user_list,
            'comment': self.comment,
        })
        self.offer_id.application_id.stage_id = self.env.ref('recruitment_ads.application_stage_approval_cycle_data').id

        ir_model_data = self.env['ir.model.data']
        try:
            template_id = \
                ir_model_data.get_object_reference('recruitment_ads',
                                                   'approval_cycle_mail_template')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = \
                ir_model_data.get_object_reference('recruitment_ads',
                                                   'view_approval_cycle_mail_compose_message_wizard_from')[1]
        except ValueError:
            compose_form_id = False
        offer = approval_cycle.offer_id
        from docxtpl import DocxTemplate
        paths = config['addons_path'].split(',')
        c_p = ''
        for path in paths:
            c_p = path + '/recruitment_ads/static/src/docx/'
            if os.path.isdir(c_p):
                break
        if not c_p:
            raise ValidationError('Check addon paths on configuration file')
        if approval_cycle.offer_id.bu_location != 'egypt':
            doc = DocxTemplate(c_p + "KSA_Offer_template.docx")
            context = {
                'partner_name': offer.application_id.partner_id.name,
                'job': offer.job_id.name,
                'dep': offer.department_id.name,
                'basic_salary': str(
                    offer.fixed_salary) + ' ' + offer.currency_id.symbol if offer.offer_type in ('normal_offer' , 'exceeding_salary_scale' , 'cont_renewal') else str(
                    offer.total_salary) + ' ' + offer.currency_id.symbol,
                'total_salary': str(offer.total_salary) + ' ' + offer.currency_id.symbol,
                'package_salary': str(offer.total_package) + ' ' + offer.currency_id.symbol,
                'house_allowance': str(offer.housing_allowance) + ' ' + offer.currency_id.symbol,
                'travel_allowance': str(offer.travel_allowance) + ' ' + offer.currency_id.symbol,
            }
            doc.render(context)
            sequence = self.env.ref('recruitment_ads.sequence_offer_ksa')
            number = sequence.next_by_id()
            file_number = "KSA_Offer_%s.docx" % number
        else:
            doc = DocxTemplate(c_p + "egypt-offer.docx")
            context = {
                'name_en': offer.application_id.partner_id.name,
                'job': offer.job_id.job_title_id.name,
                'level': offer.job_id.job_level_id.name or '',
                'department': offer.department_id.name,
                'business_unit': offer.business_unit_id.name,
                'fixed_salary': str(
                    offer.fixed_salary) + ' ' + offer.currency_id.symbol if offer.offer_type in ('normal_offer' , 'exceeding_salary_scale' , 'cont_renewal') else str(
                    offer.total_salary) + ' ' + offer.currency_id.symbol,
                'variable_salary': str(offer.variable_salary) + ' ' + offer.currency_id.symbol,
                'total_package': str(offer.total_package) + ' ' + offer.currency_id.symbol,
                'date': datetime.strptime(offer.issue_date, '%Y-%m-%d').strftime('%d-%b-%Y')
            }
            doc.render(context)
            sequence = self.env.ref('recruitment_ads.sequence_offer_egypt')
            number = sequence.next_by_id()
            file_number = "EGYPT_Offer_%s.docx" % number

        with osutil.tempdir() as dump_dir:
            file_name = dump_dir
        doc.save(file_name)
        if hasattr(file_name, 'read'):
            buf = file_name.read()
        else:
            with open(file_name, 'rb') as fh:
                buf = fh.read()

        b64_pdf = base64.encodestring(buf)
        res = self.env['ir.attachment'].create({
            'name': file_number,
            'datas': b64_pdf,
            'datas_fname': file_number})
        temp=self.env['mail.template'].browse(template_id)
        ctx = {
            'default_model': 'hr.approval.cycle.users',
            'default_res_id': approval_cycle.users_list_ids[0].id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'default_approval_user': approval_cycle.users_list_ids[0].approval_user_id.id,
            'default_recruiter_id': approval_cycle.create_uid.id,
            'default_attachment_ids': [(6, 0, res.ids)],
            'time_format': '%I:%M %p',
            'force_email': True
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'approval.cycle.mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }


class HrApprovalCycleUsersWizard(models.TransientModel):
    _name = 'hr.approval.cycle.users.wizard'
    _description = 'Approval Cycle Users Wizard'

    approval_position_id = fields.Many2one('hr.setup.approval.cycle.users', 'Approval Position')
    approval_user_id = fields.Many2one('res.partner', 'Approval User', domain=[('GUID', '!=', False)])
    approval_cycle_id = fields.Many2one('hr.approval.cycle.wizard', string='Approval Cycle Wizard', required=True,
                                        ondelete='cascade',
                                        index=True, copy=False)
