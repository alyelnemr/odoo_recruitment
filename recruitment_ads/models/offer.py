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
    job_id = fields.Many2one('hr.job', string='Job position', related='application_id.job_id')
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
                                       related='application_id.job_id.business_unit_id')
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
    generated_by_bu_id = fields.Many2one('business.unit', string="Generated by", related='create_uid.business_unit_id')
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
        c_p = config['addons_path'].split(',')[-1] + '\\recruitment_ads\\static\\src\\docx\\'
        doc = DocxTemplate(c_p + "egypt-offer.docx")

        context = {
            'name_en': self.application_id.partner_id.name,
            'job': self.job_id.job_title_id.name,
            'level': self.job_id.job_level_id.name,
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

    # @api.multi
    def print_ksa_offer_docx(self):
        document = Document()

        header_1 = document.add_heading('" توظيف عرض  "', 2)
        header_1.style.font.color.rgb = RGBColor(140, 140, 140)
        header_2 = document.add_heading('"Employment Offer"', 2)
        paragraph_format_1 = header_1.paragraph_format
        paragraph_format_2 = header_2.paragraph_format
        paragraph_format_1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph_format_2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        # paragraph_format_1.space_before = Pt(1)
        paragraph_format_2.space_after = Pt(10)

        table = document.add_table(rows=26, cols=6)

        # first Row
        row = table.rows[0]

        t_1_1, t_1_2, t_1_3 = row.cells[:3]
        cell_1 = t_1_1.merge(t_1_3)
        cell_1.text = 'Please note that you have been appointed as follows.'
        t_1_4, t_1_5, t_1_6 = row.cells[3:6]
        cell_1 = t_1_4.merge(t_1_6)

        cell_1.text = "یسرنى إبلاغكم بموافقة الإدارة على توظیفكم حسب البیانات التالیة"
        paragraph = cell_1.paragraphs[0]
        run = paragraph.runs
        cell_1.bold = True
        run[0].font.rtl = True
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        table.rows[0].cells[0]._tc.get_or_add_tcPr().append(shading_elm)
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        table.rows[0].cells[5]._tc.get_or_add_tcPr().append(shading_elm)

        # second Row
        row = table.rows[1].cells[0]
        row.text = "Name"
        row.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        t_2_3, t_2_4, t_2_5, t_2_6 = table.rows[1].cells[1:5]
        row = t_2_3.merge(t_2_6)
        row = row.add_paragraph().add_run()
        row.add_text(str(self.applicant_name))

        row = table.rows[1].cells[5]
        row.text = "الاسم"
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)

        # row 3
        row = table.rows[2].cells[0]
        row.text = "Position:"
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        row = table.rows[2].cells[1]
        row = row.add_paragraph().add_run()
        row.add_text(str(self.job_id.name))

        row = table.rows[2].cells[2]
        row.text = "المسمى الوظيفي "
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        paragraph = row.paragraphs[0]
        run = paragraph.runs
        run[0].font.rtl = True
        row = table.rows[2].cells[3]
        row.text = "Dep’t"
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        # bord_elm = parse_xml(r'<w:tcBorders {} />'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)

        row = table.rows[2].cells[4]
        row = row.add_paragraph().add_run()
        row.add_text(str(self.department_id.name))

        row = table.rows[2].cells[5]
        row.text = " الإدارة"
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        # row 4
        row = table.rows[3].cells[0]
        row.text = "Housing allowance:"
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        row = table.rows[3].cells[1]
        row = row.add_paragraph().add_run()
        row.add_text(str(self.housing_allowance))
        row = table.rows[3].cells[2]
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        row.text = "بدل  سكن :"
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        paragraph = row.paragraphs[0]
        run = paragraph.runs
        run[0].font.rtl = True

        row = table.rows[3].cells[3]
        row.text = "Basic salary:"
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        row = table.rows[3].cells[4]
        if self.offer_type == 'normal_offer':
            row = row.add_paragraph().add_run()
            row.add_text(str(self.fixed_salary))
        else:
            row = row.add_paragraph().add_run()
            row.add_text(str(self.total_salary))
        row = table.rows[3].cells[5]
        row.text = "الراتب الأساسى "
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        paragraph = row.paragraphs[0]
        run = paragraph.runs
        run[0].font.rtl = True
        # row 5
        row = table.rows[4].cells[0]
        row.text = "Total Salary"
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        t_2_3, t_2_4, t_2_5, t_2_6 = table.rows[4].cells[1:5]
        row = t_2_3.merge(t_2_6)
        row = row.add_paragraph().add_run()
        row.add_text(str(self.total_salary))
        row = table.rows[4].cells[5]
        row.text = "اجمالى المرتب "
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        paragraph = row.paragraphs[0]
        run = paragraph.runs
        run[0].font.rtl = True
        # row 6
        row = table.rows[5].cells[0]
        row.text = "Bonus: "
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        row = table.rows[5].cells[1]
        row.text = "according to company policy"
        row = table.rows[5].cells[2]
        row.text = "العلاوة:"
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        paragraph = row.paragraphs[0]
        run = paragraph.runs
        run[0].font.rtl = True
        row = table.rows[5].cells[3]
        row.text = "Vacation"
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        row = table.rows[5].cells[5]
        row.text = "الأجازة"
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        # row 7
        row = table.rows[6].cells[0]
        row.text = "Other Benefits: "
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        row = table.rows[6].cells[1]
        row.text = "تامین طبي لشخصه و المضافین على اقامته "
        paragraph = row.paragraphs[0]
        run = paragraph.runs
        run[0].font.rtl = True
        row = table.rows[6].cells[2]
        row.text = "مزایا أخرى"
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        paragraph = row.paragraphs[0]
        run = paragraph.runs
        run[0].font.rtl = True
        row = table.rows[6].cells[3]
        row.text = "Ticket"
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        row = table.rows[6].cells[4]
        row.text = "تذكرة سفر سنویة لشخصه"
        paragraph = row.paragraphs[0]
        run = paragraph.runs
        run[0].font.rtl = True
        row = table.rows[6].cells[5]
        row.text = "التذاكر"
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        # ROW 8
        row = table.rows[7].cells[0]
        row.text = "Transportation allowens"
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)

        row = table.rows[7].cells[1]
        row = row.add_paragraph().add_run()
        row.add_text(str(self.travel_allowance))
        row = table.rows[7].cells[2]
        row.text = "بدل مواصلات :"
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        paragraph = row.paragraphs[0]
        run = paragraph.runs
        run[0].font.rtl = True
        row = table.rows[7].cells[3]
        row.text = "Service award:"
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        row = table.rows[7].cells[4]
        row.text = "طبقا للنظام"
        paragraph = row.paragraphs[0]
        run = paragraph.runs
        run[0].font.rtl = True
        row = table.rows[7].cells[5]
        row.text = "مكافأة نھایة الخدمة"
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        paragraph = row.paragraphs[0]
        run = paragraph.runs
        run[0].font.rtl = True
        # row 9
        row = table.rows[8].cells[0]
        row.text = "Total: "
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        row = table.rows[8].cells[5]
        row.text = "الاجمالى:"
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        paragraph = row.paragraphs[0]
        run = paragraph.runs
        run[0].font.rtl = True
        t_2_3, t_2_4, t_2_5, t_2_6 = table.rows[8].cells[1:5]
        row = t_2_3.merge(t_2_6)
        row = row.add_paragraph().add_run()
        row.add_text(str(self.total_package))
        # row 10
        t_10_1, t_10_2, t_10_3, t_10_4, t_10_5, t_10_6 = table.rows[9].cells[0:6]
        row = t_10_1.merge(t_10_6)
        row = row.add_paragraph().add_run()
        row.add_text('''
       
         ........  عمل إصابة الإدخار صندوق الإجتماعیة التأمینات  مثل إستقطاعات لأى الراتب  ویخضع     
        
        \n 
        ''')
        row.add_text(
            'Salary is subject to any deduction such as, Social Insurance saving Findwork-related injuries accidents, etc. ......')
        # row 11

        t_11_1, t_11_2 = table.rows[10].cells[:2]
        row = t_11_1.merge(t_11_2)
        row.text = ("Expected date of work:")
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        t_11_3, t_11_4 = table.rows[10].cells[2:4]
        row = t_11_3.merge(t_11_4)
        row.text = ('------')
        t_11_5, t_11_6 = table.rows[10].cells[4:6]
        row = t_11_5.merge(t_11_6)
        row.text = ('التاریخ المطلوب ')
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        paragraph = row.paragraphs[0]
        run = paragraph.runs
        run[0].font.rtl = True
        # row 12
        t_11_1, t_11_2 = table.rows[11].cells[:2]
        row = t_11_1.merge(t_11_2)
        row.text = ('Offer is Valid')
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        t_11_3, t_11_4 = table.rows[11].cells[2:4]
        t_11_3.merge(t_11_4)
        t_11_5, t_11_6 = table.rows[11].cells[4:6]
        row = t_11_5.merge(t_11_6)
        row.text = ('سریان العرض')
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        paragraph = row.paragraphs[0]
        run = paragraph.runs
        run[0].font.rtl = True
        # row 13
        t_1_1, t_1_2, t_1_3 = table.rows[12].cells[:3]
        row = t_1_1.merge(t_1_3)
        # check = parse_xml('''
        # <w:listPr>
        # <w:ilvl w:val="0"/>
        # <w:ilfo w:val="10"/>
        # <wx:t wx:val="¨"/>
        # <wx:font wx:val="Wingdings"/>
        # </w:listPr>
        # <w:spacing w:after="0" w:line="240" w:line-rule="auto"/>
        # <w:jc w:val="center"/>
        # </w:pPr>
        # ''')
        check = parse_xml(r'<w:listPr {} w:val= "1"  w:font= "Wingdings" />'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(check)
        text = '00A8'
        check = text.encode('utf-8')
        # check = str.encode('ascii','ignore')
        # row.add_paragraph('[]')
        row.add_paragraph('''
          [ ] Accept the offer
            [ ] DisAgree
            Name…
            Signature…

        ''')
        # run = row.add_run()

        t_1_4, t_1_5, t_1_6 = table.rows[12].cells[3:6]
        row = t_1_4.merge(t_1_6)
        row = row.add_paragraph().add_run()
        row.add_text('''    [ ] أوافق على العرض
                                   
[ ] أرفض العرض                                          
        التوقیع:........................
         
         الإسم:.........................
        ''')
        row.font.rtl = True
        row.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        t_10_1, t_10_2, t_10_3, t_10_4, t_10_5, t_10_6 = table.rows[13].cells[0:6]
        row = t_10_1.merge(t_10_6)
        # row.width = Inches(4)
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        row = row.add_paragraph().add_run()
        row.add_text(
            'This section is to be filled by Human Resources:                      :- البشریة الموارد إدارة بمعرفة یملاء الجزء ھذا')
        # Row 15
        t_10_1, t_10_2, t_10_3, t_10_4, t_10_5, t_10_6 = table.rows[14].cells[0:6]
        t_10_1.merge(t_10_6)

        # row 16
        t_1_1, t_1_2, t_1_3 = table.rows[15].cells[:3]
        row = t_1_1.merge(t_1_3)
        row.text = ('Don’t Accepts offer [ ] العرض على یوافق لا  ')

        t_1_4, t_1_5, t_1_6 = table.rows[15].cells[3:6]
        row = t_1_4.merge(t_1_6)
        row.text = ('Accepts offer as it is:[ ] الحالیة بصورته العرض على یوافق')

        # row 17
        t_10_1, t_10_2, t_10_3, t_10_4, t_10_5, t_10_6 = table.rows[16].cells[0:6]
        row = t_10_1.merge(t_10_6)
        row.text = ('After doing the following amendments:       [ ]        الآتیة التعدیلات إجراء بعد')
        # row 18
        row = table.rows[17].cells[0]
        row.text = ('Remarks')
        t_2_3, t_2_4, t_2_5, t_2_6 = table.rows[17].cells[1:5]
        t_2_3.merge(t_2_6)
        row = table.rows[17].cells[5]
        row.text = ('ملاحظات:')
        paragraph = row.paragraphs[0]
        run = paragraph.runs
        run[0].font.rtl = True

        # row 19 , 20 , 21
        t_10_1, t_10_2, t_10_3, t_10_4, t_10_5, t_10_6 = table.rows[18].cells[0:6]
        t_10_1.merge(t_10_6)
        t_10_1, t_10_2, t_10_3, t_10_4, t_10_5, t_10_6 = table.rows[19].cells[0:6]
        t_10_1.merge(t_10_6)
        t_10_1, t_10_2, t_10_3, t_10_4, t_10_5, t_10_6 = table.rows[20].cells[0:6]
        t_10_1.merge(t_10_6)

        # row 22
        row = table.rows[21].cells[5]
        row.text = "الدرجة الوظیفیه"
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        paragraph = row.paragraphs[0]
        run = paragraph.runs
        run[0].bold = True
        run[0].font.rtl = True
        row = table.rows[21].cells[4]
        row.text = " الاسم"
        row = table.rows[21].cells[3]
        row.text = " التوقیع"
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        row = table.rows[21].cells[2]
        row.text = "التاریخ"
        row = table.rows[21].cells[1]
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)

        # row 23
        row = table.rows[22].cells[5]
        row.text = "Regional HR Manager"
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        row = table.rows[22].cells[3]
        row.text = " التوقیع"
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        row = table.rows[22].cells[2]
        row.text = "التاریخ"
        row = table.rows[22].cells[1]
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)

        # row 24
        row = table.rows[23].cells[5]
        row.text = "Deputy Group Recruitment Mananger"
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        row = table.rows[23].cells[3]
        row.text = " التوقیع"
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        row = table.rows[23].cells[2]
        row.text = "التاریخ"
        row = table.rows[23].cells[1]
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)

        # row 25
        row = table.rows[24].cells[5]
        row.text = "Regional Financial Manager"
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        row = table.rows[24].cells[3]
        row.text = " التوقیع"
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        row = table.rows[24].cells[2]
        row.text = "التاریخ"
        row = table.rows[24].cells[1]
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)

        # row 26
        row = table.rows[25].cells[5]
        row.text = "Group HR Director"
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        row = table.rows[25].cells[3]
        row.text = " التوقیع"
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        row = table.rows[25].cells[2]
        row.text = "التاریخ"
        row = table.rows[25].cells[1]
        shading_elm = parse_xml(r'<w:shd {} w:fill="FFFFC8"/>'.format(nsdecls('w')))
        row._tc.get_or_add_tcPr().append(shading_elm)
        # p3 = row.add_paragraph('Item B', style='List Continue')
        # style = styles[WD_STYLE.LIST_CONTINUE]

        table.style = ('Table Grid')
        for row in table.rows:
            # row.height =Cm(0.85)
            row.width = Cm(2)
            for cell in row.cells:
                cell.width = 4846320
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                paragraphs = cell.paragraphs
                for paragraph in paragraphs:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in paragraph.runs:
                        font = run.font
                        font.size = Pt(11)
                        font.name = "Times New Roman"
            tbl = table._tbl  # get xml element in table
            for cell in tbl.iter_tcs():
                tcPr = cell.tcPr  # get tcPr element, in which we can define style of borders
                tcBorders = OxmlElement('w:tcBorders')
                top = OxmlElement('w:top')
                top.set(qn('w:sz'), '4')
                top.set(qn('w:val'), 'double')

                left = OxmlElement('w:left')
                left.set(qn('w:val'), 'double')
                left.set(qn('w:sz'), '4')

                bottom = OxmlElement('w:bottom')
                bottom.set(qn('w:val'), 'double')
                bottom.set(qn('w:sz'), '4')
                bottom.set(qn('w:space'), '0')
                bottom.set(qn('w:color'), 'auto')

                right = OxmlElement('w:right')
                right.set(qn('w:val'), 'double')
                right.set(qn('w:sz'), '4')
                tcBorders.append(top)
                tcBorders.append(left)
                tcBorders.append(bottom)
                tcBorders.append(right)
                tcPr.append(tcBorders)

        sequence = self.env.ref('recruitment_ads.sequence_offer_ksa')
        number = sequence.next_by_id()
        file_number = "KSA_Offer_%s.docx" % number
        with osutil.tempdir() as dump_dir:
            file_name = dump_dir
        document.save(file_name)
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
