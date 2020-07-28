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

    last_activity = fields.Many2one('mail.activity.type', readonly=True, compute=False)
    last_activity_date = fields.Date(readonly=True, compute=False)
    result = fields.Char(readonly=True, compute=False)
    response_id = fields.Many2one('survey.user_input', "Response", ondelete="set null", oldname="response",
                                  readonly=True)
    campaign_id = fields.Many2one('utm.campaign', string='Campaign', readonly=True)
    medium_id = fields.Many2one('utm.medium', 'Medium', oldname='channel_id', readonly=True)
    message_last_post = fields.Datetime('Last Message Date', readonly=True)
    activity_date_deadline = fields.Date(
        'Next Activity Deadline', related='activity_ids.date_deadline',
        readonly=True,
    )

    def _select(self):
        select_str = """select hr_applicant.id,email_from,partner_phone,partner_mobile,partner_name,job_id,partner_id ,source_id,
        offer_id,cv_matched,reason_of_rejection, salary_current,hr_applicant.name,serial,hr_applicant.active,description,email_cc,probability,
        hr_applicant.create_date, hr_applicant.write_date,stage_id,last_stage_id,hr_applicant.company_id,hr_applicant.user_id,date_closed,date_open, 
        date_last_stage_update,priority,salary_proposed_extra,salary_expected_extra,salary_proposed, salary_expected,
        availability,type_id,department_id,section_id,allow_call,reference,delay_close, hr_applicant.color ,emp_id,response_id,
        campaign_id ,medium_id , hr_applicant.message_last_post ,hr_applicant.activity_date_deadline ,last_activity, last_activity_date, 
        result , res_partner.face_book ,res_partner.linkedin,have_cv ,source_resp,hr_applicant.old_data , tooltip_icon , have_assessment  from 
        hr_applicant join res_partner on res_partner.id = hr_applicant.partner_id"""
        return select_str

    def column_exists(self):
        """ Return whether the given column exists. """
        query = """SELECT column_name FROM information_schema.columns WHERE table_name=%s AND  (column_name = %s or 
        column_name = %s or column_name = %s or column_name = %s or column_name = %s or column_name = %s or 
        column_name = %s  or column_name = %s or column_name = %s or column_name = %s ) """
        result = self.env.cr.execute(query, (
            'hr_applicant', 'last_activity', 'last_activity_date', 'result', 'face_book', 'linkedin', 'response_id',
            'source_resp', 'have_cv', 'tooltip_icon', 'have_assessment'))
        # return result
        return {row['column_name']: row for row in self.env.cr.dictfetchall()}

    @api.model_cr
    def init(self):
        check_column = self.column_exists()
        if check_column:
            tools.drop_view_if_exists(self.env.cr, 'hr_applicant_history')
            self.env.cr.execute("""CREATE or REPLACE VIEW hr_applicant_history as (
                %s
                )""" % (self._select()))


class HrApplicantCategoryHrApplicantHistoryRel(models.Model):
    _name = "hr.applicant.category.hr_applicant.history.rel"

    hr_applicant_category_id = fields.Integer()
    hr_applicant_history_id = fields.Integer()
