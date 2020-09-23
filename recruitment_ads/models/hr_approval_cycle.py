# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import base64
from odoo.tools import osutil, config
from datetime import datetime
import os

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

    # @api.multi
    # def action_send(self):
    #     self.ensure_one()
    #     template = self.env.ref('recruitment_ads.approval_cycle_mail_template', False)
    #     if template:
    #         if self.users_list_ids[0].approval_user_id.email:
    #             template.email_to = self.users_list_ids[0].approval_user_id.email
    #             self.env['mail.template'].browse(template.id).send_mail(self.users_list_ids[0].id)
    #             self.state = 'pending'
    #             self.users_list_ids[0].sent = True
    #     return True

    @api.multi
    def action_send(self):
        self.ensure_one()

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
        offer = self.offer_id
        from docxtpl import DocxTemplate
        paths = config['addons_path'].split(',')
        c_p = ''
        for path in paths:
            c_p = path + '/recruitment_ads/static/src/docx/'
            if os.path.isdir(c_p):
                break
        if not c_p:
            raise ValidationError('Check addon paths on configuration file')
        if self.offer_id.bu_location != 'egypt':
            doc = DocxTemplate(c_p + "KSA_Offer_template.docx")
            context = {
                'partner_name': offer.application_id.partner_id.name,
                'job': offer.job_id.name,
                'dep': offer.department_id.name,
                'basic_salary': str(
                    offer.fixed_salary) + ' ' + offer.currency_id.symbol if offer.offer_type in ('normal_offer' , 'exceeding_salary_scale' , 'cont_renewal' ) else str(
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
                    offer.fixed_salary) + ' ' + offer.currency_id.symbol if offer.offer_type in ('normal_offer' , 'exceeding_salary_scale' , 'cont_renewal' ) else str(
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
        attach = self.env['ir.attachment'].search([('res_model','=','hr.applicant'),('res_id','=',self.application_id.id),('attachment_type','in',('cv','assessment'))])
        attach = res.ids + attach.ids
        ctx = {
            'default_model': 'hr.approval.cycle.users',
            'default_res_id': self.users_list_ids[0].id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'default_approval_user': self.users_list_ids[0].approval_user_id.id,
            'default_recruiter_id': self.create_uid.partner_id.id,
            'default_attachment_ids': [(6, 0, attach)],
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
    token = fields.Char()
    sequence = fields.Char()
    email_id = fields.Many2one('mail.mail',store=True)
