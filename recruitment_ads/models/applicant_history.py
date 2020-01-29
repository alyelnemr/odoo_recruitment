from odoo import models, fields, api
from odoo import tools

AVAILABLE_PRIORITIES = [
    ('0', 'Normal'),
    ('1', 'Low'),
    ('2', 'High'),
    ('3', 'Very High'),
]


class Applicant(models.Model):
    _name = "hr.applicant.history"
    _inherit = 'hr.applicant'
    _auto = False

    # survey_id = fields.Many2one('survey.survey', string="Survey")
    # categ_ids = fields.Many2many('hr.applicant.category', 'hr_applicant_category_hr_applicant_history_rel',
    #                              'hr_applicant_id', 'hr_applicant_category_id',
    #                              string="Tags", readonly=True)
    # tag_ids = fields.Many2many('hr.applicant.category','hr_applicant_category_hr_applicant_history_rel' ,'hr_applicant_id', 'hr_applicant_category_id',  'History',readonly=True)
    # categ_ids = fields.Many2many('hr.applicant.category',readonly=True)
    response_id = fields.Many2one('survey.user_input', "Response", ondelete="set null", oldname="response",
                                  readonly=True)
    campaign_id = fields.Many2one('utm.campaign', string='Campaign', readonly=True)
    medium_id = fields.Many2one('utm.medium', 'Medium', oldname='channel_id', readonly=True)
    message_last_post = fields.Datetime('Last Message Date', readonly=True)
    activity_date_deadline = fields.Date(
        'Next Activity Deadline', related='activity_ids.date_deadline',
        readonly=True,
    )

    # email_from = fields.Char(required=False, readonly=True)
    # partner_phone = fields.Char(readonly=True)
    # partner_mobile = fields.Char(readonly=True)
    #
    # partner_name = fields.Char(readonly=True)
    # job_id = fields.Many2one('hr.job', "Applied Job", readonly=True)
    #
    # partner_id = fields.Many2one('res.partner', "Applicant", readonly=True)
    # # applicant_history_ids = fields.Many2many('hr.applicant', 'applicant_history_rel', 'applicant_id', 'history_id',
    # #                                          string='History', readonly=False)
    # last_activity = fields.Many2one('mail.activity.type', readonly=True)
    # # last_activity_date = fields.Date(readonly=True)
    # # result = fields.Char(readonly=True)
    # source_id = fields.Many2one('utm.source', readonly=True)
    # offer_id = fields.Many2one('hr.offer', string='Offer', readonly=True)
    # cv_matched = fields.Boolean('Matched', default=False, readonly=True)
    # reason_of_rejection = fields.Char('Reason of Rejection', help="Reason why this is applicant not matched",
    #                                   readonly=True)
    # # count_done_interviews = fields.Integer('Done Interviews Count', readonly=True)
    # salary_current = fields.Float("Current Salary", help="Current Salary of Applicant", readonly=True)
    # name = fields.Char("Application Code", readonly=True)
    # serial = fields.Char('serial', readonly=True)
    # active = fields.Boolean("Active", default=True,
    #                         help="If the active field is set to false, it will allow you to hide the case without removing it.")
    # description = fields.Text("Description")
    # email_cc = fields.Text("Watchers Emails", size=252,
    #                        help="These email addresses will be added to the CC field of all inbound and outbound emails for this record before being sent. Separate multiple email addresses with a comma")
    # probability = fields.Float("Probability")
    # create_date = fields.Datetime("Creation Date", readonly=True, index=True)
    # write_date = fields.Datetime("Update Date", readonly=True)
    # stage_id = fields.Many2one('hr.recruitment.stage', 'Stage', readonly=True)
    # last_stage_id = fields.Many2one('hr.recruitment.stage', "Last Stage",
    #                                 help="Stage of the applicant before being in the current stage. Used for lost cases analysis.")
    # # categ_ids = fields.Many2many('hr.applicant.category', string="Tags", readonly=True)
    # company_id = fields.Many2one('res.company', "Company", readonly=True)
    # user_id = fields.Many2one('res.users', "Responsible", readonly=True)
    # date_closed = fields.Datetime("Closed", readonly=True, index=True)
    # # date_open = fields.Datetime("Assigned", readonly=True, index=True)
    # date_last_stage_update = fields.Datetime("Last Stage Update", index=True)
    # priority = fields.Selection(AVAILABLE_PRIORITIES, "Appreciation", default='0')
    #
    # salary_proposed_extra = fields.Char("Proposed Salary Extra",
    #                                     help="Salary Proposed by the Organisation, extra advantages")
    # salary_expected_extra = fields.Char("Expected Salary Extra", help="Salary Expected by Applicant, extra advantages")
    # salary_proposed = fields.Float("Proposed Salary", help="Salary Proposed by the Organisation")
    # salary_expected = fields.Float("Expected Salary", help="Salary Expected by Applicant")
    # availability = fields.Date("Availability",
    #                            help="The date at which the applicant will be available to start working")
    # type_id = fields.Many2one('hr.recruitment.degree', "Degree", readonly=True)
    # department_id = fields.Many2one('hr.department', "Department", readonly=True)
    # reference = fields.Char("Referred By", readonly=True)
    # day_open = fields.Float(string="Days to Open", readonly=True)
    # # day_close = fields.Float(string="Days to Close", readonly=True)
    # delay_close = fields.Float(string='Delay to Close', readonly=True)
    # color = fields.Integer("Color Index")
    # emp_id = fields.Many2one('hr.employee', string="Employee", track_visibility="onchange", readonly=True,
    #                          help="Employee linked to the applicant.")

    # user_email = fields.Char(type="char", string="User Email", readonly=True)
    # attachment_number = fields.Integer(string="Number of Attachments", readonly=True)
    # employee_name = fields.Char(string="Employee Name", readonly=True)
    # attachment_ids = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'hr.applicant')],
    #                                  string='Attachments', readonly=True)

    def _select(self):
        select_str = """
             select id,email_from,partner_phone,partner_mobile,partner_name,job_id,partner_id
             ,source_id,offer_id,cv_matched,reason_of_rejection,
             salary_current,name,serial,active,description,email_cc,probability,create_date,
             write_date,stage_id,last_stage_id,company_id,user_id,date_closed,date_open,
             date_last_stage_update,priority,salary_proposed_extra,salary_expected_extra,salary_proposed,
             salary_expected,availability,type_id,department_id,reference,delay_close,
             color ,emp_id,response_id,campaign_id ,medium_id , message_last_post ,activity_date_deadline  from hr_applicant
        """
        return select_str

    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, 'hr_applicant_history')
        self.env.cr.execute("""CREATE or REPLACE VIEW hr_applicant_history as (
            %s
            )""" % (self._select()))


class HrApplicantCategoryHrApplicantHistoryRel(models.Model):
    _name = "hr.applicant.category.hr_applicant.history.rel"

    hr_applicant_category_id = fields.Integer()
    hr_applicant_history_id = fields.Integer()

