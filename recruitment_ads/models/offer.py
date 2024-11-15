# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.tools import osutil, config
from odoo.exceptions import ValidationError
from datetime import date, datetime
import os
import base64


class Offer(models.Model):
    _name = 'hr.offer'
    _description = 'Offers'
    _inherit = ['mail.thread']

    @api.depends('application_id.department_id.business_unit_id', 'application_id', 'application_id.job_id',
                 'application_id.partner_name', 'application_id.department_id')
    def _offer_name(self):
        for offer in self:
            name = []
            if offer.application_id.department_id.business_unit_id.name:
                name.append(offer.application_id.department_id.business_unit_id.name)
            if offer.application_id.department_id.name:
                name.append(offer.application_id.department_id.name)
            if offer.application_id.job_id.name:
                name.append(offer.application_id.job_id.name)
            if offer.application_id.partner_name:
                name.append(offer.application_id.partner_name)
            name = ' / '.join(name)
            offer.name = name
            offer.offer_name = "Create Offer / " + name

    @api.depends('fixed_salary', 'variable_salary', 'housing_allowance', 'medical_insurance', 'travel_allowance',
                 'mobile_allowance', 'shifts_no', 'hour_rate', 'offer_type', 'years_of_exp', 'amount_per_year')
    def _compute_total_package(self):
        for offer in self:
            if offer.offer_type in ("normal_offer", 'exceeding_salary_scale', 'cont_renewal'):
                total_salary = offer.fixed_salary + offer.variable_salary
                total_package = total_salary + offer.housing_allowance + offer.medical_insurance + \
                                offer.travel_allowance + offer.mobile_allowance
                offer.total_salary = total_salary
                offer.total_package = total_package
            elif offer.offer_type == "nursing_offer":
                total_amount = offer.years_of_exp * offer.amount_per_year
                total_salary = (offer.hour_rate * offer.shifts_no * offer.shift_hours) + total_amount
                total_package = total_salary + offer.housing_allowance + \
                                offer.medical_insurance + offer.travel_allowance + offer.mobile_allowance
                offer.total_amount = total_amount
                offer.total_salary = total_salary
                offer.total_package = total_package

    name = fields.Char(compute=_offer_name, string='Name')
    offer_name = fields.Char(compute=_offer_name)
    application_id = fields.Many2one('hr.applicant')
    approval_cycle_ids = fields.One2many('hr.approval.cycle', 'offer_id', string='Approval Cycles', readonly=True)
    applicant_name = fields.Char(string='Applicant Name', related='application_id.partner_name')
    job_id = fields.Many2one('hr.job', string='Job position', related='application_id.job_id', store=True)
    department_id = fields.Many2one('hr.department', string='Department', related='application_id.department_id')

    fixed_salary = fields.Float(string='Fixed Salary', track_visibility='onchange',
                                digits=dp.get_precision('Offer Salary'))
    variable_salary = fields.Float(string='Variable Salary', track_visibility='onchange',
                                   digits=dp.get_precision('Offer Salary'))
    housing_allowance = fields.Float(string='Housing Allowance', track_visibility='onchange',
                                     digits=dp.get_precision('Offer Salary'))
    medical_insurance = fields.Float(string='Medical Insurance', track_visibility='onchange',
                                     digits=dp.get_precision('Offer Salary'))
    travel_allowance = fields.Float(string='Travel Allowance', track_visibility='onchange',
                                    digits=dp.get_precision('Offer Salary'))
    mobile_allowance = fields.Float(string='Mobile Allowance', track_visibility='onchange',
                                    digits=dp.get_precision('Offer Salary'))
    total_package = fields.Float(string='Total Package', compute='_compute_total_package', store=True,
                                 digits=dp.get_precision('Offer Salary'))
    total_salary = fields.Float(string='Total Salary', compute='_compute_total_package', store=True,
                                digits=dp.get_precision('Offer Salary'))

    years_of_exp = fields.Float(string='Years of Experience', track_visibility='onchange',
                                digits=dp.get_precision('Offer Salary'))
    amount_per_year = fields.Float(string='Amount/Year', track_visibility='onchange',
                                   digits=dp.get_precision('Offer Salary'))
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_package', store=True,
                                digits=dp.get_precision('Offer Salary'))

    business_unit_id = fields.Many2one('business.unit', string='Business Unit',
                                       related='application_id.job_id.business_unit_id', store=True)
    bu_location = fields.Selection(string='Location',
                                   related='application_id.job_id.business_unit_id.bu_location')
    user_id = fields.Many2one('res.users', string="Recruiter Responsible", related='application_id.user_id')
    last_activity = fields.Many2one('mail.activity.type', string='Last Stage', related='application_id.last_activity')
    last_activity_date = fields.Date(string='Last Stage Date', related='application_id.last_activity_date')
    availability = fields.Date("Availability", related='application_id.availability',
                               help="The date at which the applicant will be available to start working")

    issue_date = fields.Date(string='Issue Date', default=fields.Date.today)
    hiring_date = fields.Date(string="Hiring Date", track_visibility='onchange')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.user.company_id.currency_id)
    state = fields.Selection(
        [('offer', 'Offer'),
         ('hold', 'Hold'),
         ('pipeline', 'Pipeline'),
         ('hired', 'Hired'),
         ('not_join', 'Not Join'),
         ('reject', 'Reject Offer')], default='offer', string="Hiring Status", track_visibility='onchange',
        required=True)
    button_visible = fields.Boolean(compute='_compute_button_visible')
    lock_hired_date = fields.Boolean(compute='_compute_lock_hired_date',
                                     help="Technical field to lock the hired_date field if the user update it or "
                                          "the user is not manager")
    comment = fields.Text(string='Notes')
    reject_reason = fields.Many2one('reject.reason', string='Rejection Reason')
    offer_type = fields.Selection([('normal_offer', 'Normal Offer'),
                                   ('nursing_offer', 'Medical/Nursing Offer'), ('cont_renewal', 'Contract Renewal'),
                                   ('exceeding_salary_scale', 'Offer exceeding salary scale')],
                                  string="Offer Type", default="normal_offer", required=True)
    shifts_no = fields.Integer('No. of Shifts/Month', required=False)
    shift_hours = fields.Float('No. of hours/Shift', required=False, default=12)
    hour_rate = fields.Float('Hour Rate', required=False)
    generated_by_bu_id = fields.Many2one('business.unit', string="Generated by", related='create_uid.business_unit_id',
                                         store=True)
    have_offer = fields.Boolean(default=False, store=True)
    have_approval_cycle = fields.Boolean(default=False, store=True, compute='_have_approval_cycle')
    salary_scale_id = fields.Many2one('salary.scale', string="Salary Scale", ondelete='restrict', required=True)
    position_grade_id = fields.Many2one('position.grade', string="Position Grade", ondelete='restrict', required=True)
    last_approval_cycle_state = fields.Boolean(compute='_get_last_approval_cycle_state')
    approval_cycle_state = fields.Char(compute='_get_last_approval_cycle_state')
    send_hr_mail_flag = fields.Boolean(default=False)

    @api.multi
    @api.depends('approval_cycle_ids')
    @api.onchange('approval_cycle_ids')
    def _have_approval_cycle(self):
        for offer in self:
            if offer.approval_cycle_ids:
                offer.have_approval_cycle = True
            else:
                offer.have_approval_cycle = False

    def _get_last_approval_cycle_state(self):
        if not self.approval_cycle_ids:
            self.last_approval_cycle_state = True
        if self.approval_cycle_ids:
            approval_cycles = self.env['hr.approval.cycle'].search([('id', 'in', self.approval_cycle_ids.ids)],
                                                                   order='create_date desc', limit=1)
            if approval_cycles:
                self.approval_cycle_state = approval_cycles.state
                if approval_cycles.state == 'rejected':
                    self.last_approval_cycle_state = True

    def _compute_button_visible(self):
        for rec in self:
            allowed_users = self.job_id.user_id | self.job_id.hr_responsible_id | self.job_id.other_recruiters_ids
            if self.env.user.has_group('hr_recruitment.group_hr_recruitment_manager') or \
                    self.env.user in allowed_users:
                rec.button_visible = True
            else:
                rec.button_visible = False

    def _compute_lock_hired_date(self):
        for rec in self:
            if rec.hiring_date and rec.state == 'hired':
                if self.env.user.has_group('hr_recruitment.group_hr_recruitment_manager'):
                    rec.lock_hired_date = False
                else:
                    rec.lock_hired_date = True

    @api.constrains('hiring_date', 'state')
    def check_hiring_date(self):
        for offer in self:
            if offer.state == 'pipeline':
                today = date.today()
                if offer.hiring_date < str(today):
                    raise ValidationError(_("Hire date mustn't be less than today Date."))

    @api.constrains('hiring_date', 'issue_date')
    def check_business_unit(self):
        for offer in self:
            if offer.issue_date and offer.hiring_date:
                if offer.issue_date > offer.hiring_date:
                    raise ValidationError(_("Hire date must be more than the Issue Date."))

    @api.constrains('offer_type', 'shifts_no', 'hour_rate')
    def check_shifts_no_hour_rate(self):
        for offer in self:
            if offer.offer_type == 'nursing_offer':
                if offer.shifts_no < 1:
                    raise ValidationError(_("No. of Shifts/Month must be more than 0."))
                if offer.hour_rate < 1:
                    raise ValidationError(_("Hour Rate must be more than 0."))

    @api.onchange('shifts_no')
    def onchange_shifts_no(self):
        self.hour_rate = False

    @api.onchange('offer_type')
    def onchange_offer_type(self):
        self.hour_rate = False
        self.fixed_salary = False
        self.variable_salary = False
        self.housing_allowance = False
        self.travel_allowance = False
        self.mobile_allowance = False
        self.years_of_exp = False
        self.amount_per_year = False
        self.shifts_no = False

    @api.multi
    def action_open_application(self):
        self.ensure_one()

        action = {
            'type': 'ir.actions.act_window',
            'name': 'application',
            'res_model': 'hr.applicant',
            'res_id': self.application_id.id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'current',
        }
        return action

    @api.multi
    def write(self, vals):
        if vals.get('state') == 'hired':
            activity = self.env['hr.recruitment.stage'].search([('name', '=', 'Hired')], limit=1)
            if activity:
                self.application_id.write({'stage_id': activity.id})
        res = super(Offer, self).write(vals)
        if self.state == 'hired' and self.env['hr.approval.cycle'].search([
            ('offer_id', '=', self.id),
            ('state', '!=', 'approved'),
        ], limit=1):
            raise ValidationError('You can not change offer state to be hired until the approval cycle is accepted.')

        return res

    @api.multi
    def print_offer_egypt(self):
        from docxtpl import DocxTemplate
        paths = config['addons_path'].split(',')
        c_p = ''
        for path in paths:
            # c_p = path + '\\recruitment_ads\\static\\src\\docx\\'
            c_p = path + '/recruitment_ads/static/src/docx/'
            if os.path.isdir(c_p):
                break
        if not c_p:
            raise ValidationError('Check addon paths on configuration file')
        doc = DocxTemplate(c_p + "egypt-offer.docx")

        context = {
            'name_en': self.application_id.partner_id.name,
            'job': self.job_id.job_title_id.name,
            'level': self.job_id.job_level_id.name or '',
            'department': self.department_id.name,
            'business_unit': self.business_unit_id.name,
            'fixed_salary': str(
                self.fixed_salary) + ' ' + self.currency_id.symbol if self.offer_type in (
                'normal_offer', 'exceeding_salary_scale', 'cont_renewal') else str(
                self.total_salary) + ' ' + self.currency_id.symbol,
            'variable_salary': str(self.variable_salary) + ' ' + self.currency_id.symbol,
            'total_package': str(self.total_package) + ' ' + self.currency_id.symbol,
            'date': datetime.strptime(self.issue_date, '%Y-%m-%d').strftime('%d-%b-%Y')
        }
        doc.render(context)

        # save pdf as attachment
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
        url = '/web/content/%s?download=true' % res.id
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    @api.multi
    def print_ksa_offer_docx(self):

        from docxtpl import DocxTemplate
        paths = config['addons_path'].split(',')
        c_p = ''
        for path in paths:
            # c_p = path + '\\recruitment_ads\\static\\src\\docx\\'
            c_p = path + '/recruitment_ads/static/src/docx/'
            if os.path.isdir(c_p):
                break
        if not c_p:
            raise ValidationError('Check addon paths on configuration file')
        # c_p = config['addons_path'].split(',')[-1] + '\\recruitment_ads\\static\\src\\docx\\'
        doc = DocxTemplate(c_p + "KSA_Offer_template.docx")

        context = {
            'partner_name': self.application_id.partner_id.name,
            'job': self.job_id.name,
            'dep': self.department_id.name,
            'basic_salary': str(
                self.fixed_salary) + ' ' + self.currency_id.symbol if self.offer_type in (
                'normal_offer', 'exceeding_salary_scale', 'cont_renewal') else str(
                self.total_salary) + ' ' + self.currency_id.symbol,
            'total_salary': str(self.total_salary) + ' ' + self.currency_id.symbol,
            'package_salary': str(self.total_package) + ' ' + self.currency_id.symbol,
            'house_allowance': str(self.housing_allowance) + ' ' + self.currency_id.symbol,
            'travel_allowance': str(self.travel_allowance) + ' ' + self.currency_id.symbol,
        }
        doc.render(context)

        sequence = self.env.ref('recruitment_ads.sequence_offer_ksa')
        number = sequence.next_by_id()
        file_number = "KSA_Offer_%s.docx" % number
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
        url = '/web/content/%s?download=true' % res.id
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    @api.multi
    def action_generate_approval_cycle(self):
        self.ensure_one()
        offer_id = self._context.get('default_offer_id', False)
        application_id = self._context.get('default_application_id', False)
        offer = False
        if offer_id and application_id:
            offer = self.env['hr.offer'].browse(offer_id)
            application = self.env['hr.applicant'].browse(application_id)
            bu_relation = 'equal'
            if offer.job_id.business_unit_id.id != self.env.user.business_unit_id.id:
                bu_relation = 'not_equal'

            setup_approval_cycle = self.env['hr.setup.approval.cycle'].search([
                ('recruiter_bu', '=', bu_relation),
                ('position_grade_id', '=', offer.position_grade_id.id),
                ('salary_scale_id', '=', offer.salary_scale_id.id),
                ('offer_type', '=', offer.offer_type),
            ], limit=1)
            if setup_approval_cycle:
                setup_approval_cycle_id = setup_approval_cycle.id
            else:
                raise ValidationError(_('There is not exist approval cycle with this offer criteria.'))
            name = []
            if setup_approval_cycle.name:
                name.append(setup_approval_cycle.name)
            if offer.job_id.name:
                name.append(offer.job_id.name)
            if offer.department_id.name:
                name.append(offer.department_id.name)
            if offer.job_id.business_unit_id.name:
                name.append(offer.job_id.business_unit_id.name)
            if application.partner_name:
                name.append(application.partner_name)
            name = ' / '.join(name)  # Approval Cycle /Job position/department/BU/Candidate Name
            # salary_scale_id = offer.salary_scale_id.id
            # position_grade_id = offer.position_grade_id.id
            users_list_ids = []
            unduplicated_user_list = []
            for user in self.env['hr.setup.approval.cycle.users'].search(
                    [
                        ('id', 'in', setup_approval_cycle.approval_list_ids.ids),
                        ('stage_id.name', '=', 'Users'),
                    ]):
                unduplicated_user_list.append(user.id)
                users_list_ids.append((0, 0, {
                    'approval_position_id': user.id,
                    'state': 'no_action'
                }))

            hr_policy = self.env['hr.policy'].search([('hr_policy_type', '=', 'ceo_approval_amount')], limit=1)
            if hr_policy:
                if offer.total_package >= hr_policy.ceo_approval_amount:
                    for user in hr_policy.ceo_approval_group:
                        approval_user_ceo = self.env['hr.setup.approval.cycle.users'].search(
                            [('name', '=', user.approval_group.name),
                             ('approval_cycle_id', '=', setup_approval_cycle.id)], limit=1)
                        if approval_user_ceo.id not in unduplicated_user_list:
                            users_list_ids.append((0, 0, {
                                'approval_position_id': approval_user_ceo.id,
                                'state': 'no_action'
                            }))

            wizard = self.env['hr.approval.cycle.wizard'].create({
                'users_list_ids': users_list_ids,
                # 'position_grade_id': position_grade_id,
                # 'salary_scale_id': salary_scale_id,
                'name': name,
                'setup_approval_cycle_id': setup_approval_cycle_id,

            })
            form_view_id = self.env.ref('recruitment_ads.approval_cycle_form_wizard_view').id
            action = {
                'type': 'ir.actions.act_window',
                'name': 'Create Approval Cycle',
                'res_model': 'hr.approval.cycle.wizard',
                'res_id': wizard.id,
                'view_mode': 'form',
                'view_type': 'form',
                'view_id': form_view_id,
                'target': 'new',
            }
            return action
        else:
            return False

    def get_approval_cycle_url(self):
        self.ensure_one()
        # action = self.env['ir.actions.act_window'].for_xml_id('recruitment_ads', 'action_hr_approval_cycle')
        approval_cycle_id = self.env['hr.approval.cycle'].search(
            [('id', 'in', self.approval_cycle_ids.ids), ('state', '!=', 'rejected')],
            order='create_date desc', limit=1)
        # return 'web#id=' + str(approval_cycle_id.id) + '&view_type=form&model=hr.approval.cycle&action=' + str(
        #     action.get('id'))
        return approval_cycle_id

    @api.multi
    def action_send_hr_mail(self):
        self.ensure_one()

        ir_model_data = self.env['ir.model.data']
        try:
            template_id = \
                ir_model_data.get_object_reference('recruitment_ads',
                                                   'send_hr_mail_template')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = \
                ir_model_data.get_object_reference('recruitment_ads',
                                                   'view_send_hr_mail_compose_message_wizard_from')[1]
        except ValueError:
            compose_form_id = False
        offer = self
        from docxtpl import DocxTemplate
        paths = config['addons_path'].split(',')
        c_p = ''
        for path in paths:
            c_p = path + '/recruitment_ads/static/src/docx/'
            if os.path.isdir(c_p):
                break
        if not c_p:
            raise ValidationError('Check addon paths on configuration file')
        if offer.bu_location != 'egypt':
            doc = DocxTemplate(c_p + "KSA_Offer_template.docx")
            context = {
                'partner_name': offer.application_id.partner_id.name,
                'job': offer.job_id.name,
                'dep': offer.department_id.name,
                'basic_salary': str(
                    offer.fixed_salary) + ' ' + offer.currency_id.symbol if offer.offer_type in (
                    'normal_offer', 'exceeding_salary_scale', 'cont_renewal') else str(
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
                    offer.fixed_salary) + ' ' + offer.currency_id.symbol if offer.offer_type in (
                    'normal_offer', 'exceeding_salary_scale', 'cont_renewal') else str(
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
        attach = self.env['ir.attachment'].search(
            [('res_model', '=', 'hr.applicant'), ('res_id', '=', self.application_id.id),
             ('attachment_type', 'in', ('cv', 'assessment'))])
        attach = res.ids + attach.ids
        ctx = {
            'default_model': 'hr.offer',
            'default_offer_id': offer.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'default_attachment_ids': [(6, 0, attach)],
            'time_format': '%I:%M %p',
            'force_email': True,
            'default_hr_offer_id': offer.id,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'send.hr.mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }


class RejectionReason(models.Model):
    _name = 'reject.reason'

    name = fields.Char(string='Name', required=True)
