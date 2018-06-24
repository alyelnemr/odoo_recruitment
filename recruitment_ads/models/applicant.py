from odoo import models, fields, api


class Applicant(models.Model):
    _inherit = "hr.applicant"

    partner_id = fields.Many2one('res.partner', "Contact", required=True)
    applicant_history_ids = fields.Many2many('hr.applicant', 'applicant_history_rel','applicant_id','history_id',string='history', readonly=True)

    @api.depends('activity_ids')
    def _get_last_activity(self):
        for record in self:
            if record.activity_ids:
                last_activity = record.activity_ids.sorted('create_date')[-1]
                record.last_activity = last_activity.activity_type_id
                record.last_activity_date = last_activity.date_deadline
                if last_activity.activity_category == 'interview':
                    record.result = last_activity.interview_result
                else:
                    record.result = last_activity.call_result_id
    last_activity = fields.Many2one('mail.activity.type', compute='_get_last_activity')
    last_activity_date= fields.Date(compute='_get_last_activity')
    result = fields.Char(compute='_get_last_activity')

    def _get_history_data(self, applicant_id):
        if applicant_id == False:
            return self.env['hr.applicant']
        domain = [('partner_id', '=', applicant_id)]
        return self.search(domain)

    @api.onchange('partner_id')
    def onchange_hr_applicant(self):
        history = self._get_history_data(self.partner_id.id)
        self.applicant_history_ids = [(6,0,history.ids)]

