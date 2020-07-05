# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.tools import osutil, config
from odoo.exceptions import ValidationError
from datetime import date, datetime
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import RGBColor
from docx.enum.table import WD_ALIGN_VERTICAL
# from docx.enum.table impor WD_ALIGN_VERTICAL_Enumeration
import unicodedata

from docx.oxml.shared import OxmlElement, qn
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml
from docx.enum.style import WD_STYLE
from docx.shared import Cm
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
            if offer.offer_type == "normal_offer":
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
    applicant_name = fields.Char(string='Applicant Name', related='application_id.partner_name')
    job_id = fields.Many2one('hr.job', string='Job position', related='application_id.job_id' , store=True)
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
                                       related='application_id.job_id.business_unit_id' , store=True)
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
                                   ('nursing_offer', 'Medical/Nursing Offer'), ],
                                  string="Offer Type", default="normal_offer", required=True)
    shifts_no = fields.Integer('No. of Shifts/Month', required=False)
    shift_hours = fields.Float('No. of hours/Shift', required=False, default=12)
    hour_rate = fields.Float('Hour Rate', required=False)
    generated_by_bu_id = fields.Many2one('business.unit', string="Generated by", related='create_uid.business_unit_id' , store=True)
    have_offer = fields.Boolean(default=False, store=True)

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
        return super(Offer, self).write(vals)

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
                self.fixed_salary) + ' ' + self.currency_id.symbol if self.offer_type == 'normal_offer' else str(
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
                self.fixed_salary) + ' ' + self.currency_id.symbol if self.offer_type == 'normal_offer' else str(
                self.total_salary) + ' ' + self.currency_id.symbol,
            'total_salary': str(self.total_salary) + ' ' + self.currency_id.symbol,
            'package_salary': str(self.total_package) + ' ' + self.currency_id.symbol,
            'house_allowance': str(self.housing_allowance)+ ' ' + self.currency_id.symbol,
            'travel_allowance' : str(self.travel_allowance) + ' ' + self.currency_id.symbol,
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


class RejectionReason(models.Model):
    _name = 'reject.reason'

    name = fields.Char(string='Name', required=True)
