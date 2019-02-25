from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError


class Offer(models.Model):
    _name = 'hr.offer'
    _description = 'Offers'
    _inherit = ['mail.thread']

    @api.depends('application_id', 'application_id.job_id', 'application_id.partner_name',
                 'application_id.department_id')
    def _offer_name(self):
        for offer in self:
            name = []
            if offer.application_id.department_id.name:
                name.append(offer.application_id.department_id.name)
            if offer.application_id.job_id.name:
                name.append(offer.application_id.job_id.name)
            if offer.application_id.partner_name:
                name.append(offer.application_id.partner_name)
            name = ' / '.join(name)
            offer.name = name
            offer.offer_name = "Create Offer / " + name

    @api.depends('fixed_salary', 'variable_salary', 'housing_allowance', 'travel_allowance', 'mobile_allowance',
                 'shifts_no', 'hour_rate', 'offer_type')
    def _compute_total_package(self):
        for offer in self:
            if offer.offer_type == "normal_offer":
                total_package = offer.fixed_salary + offer.variable_salary + \
                                offer.housing_allowance + offer.travel_allowance + offer.mobile_allowance
                offer.total_package = total_package
            elif offer.offer_type == "nursing_offer":
                total_package = offer.hour_rate * offer.shifts_no * offer.shift_hours + \
                                offer.housing_allowance + offer.travel_allowance + offer.mobile_allowance
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
    travel_allowance = fields.Float(string='Travel Allowance', track_visibility='onchange',
                                    digits=dp.get_precision('Offer Salary'))
    mobile_allowance = fields.Float(string='Mobile Allowance', track_visibility='onchange',
                                    digits=dp.get_precision('Offer Salary'))
    total_package = fields.Float(string='Total Package', compute=_compute_total_package, store=True,
                                 digits=dp.get_precision('Offer Salary'))
    business_unit_id = fields.Many2one('business.unit', string='Business Unit',
                                       related='application_id.job_id.business_unit_id')
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
    comment = fields.Text(string='Notes')
    reject_reason = fields.Many2one('reject.reason', string='Rejection Reason')
    offer_type = fields.Selection([('normal_offer', 'Normal Offer'),
                                   ('nursing_offer', 'Nursing Offer'), ],
                                  string="Offer Type", default="normal_offer", required=True)
    shifts_no = fields.Integer('No. of Shifts/Month', required=False)
    shift_hours = fields.Float('No. of hours/Shift', required=False, default=12)
    hour_rate = fields.Float('Hour Rate', required=False)

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


class RejectionReason(models.Model):
    _name = 'reject.reason'

    name = fields.Char(string='Name', required=True)
