from odoo import models,fields,api

class Interview(models.Model):
    _inherit = 'calendar.event'


    hr_applicant_id = fields.Many2one('hr.applicant','Applicant',compute='_get_applicant')
    type = fields.Selection([('normal', 'Normal'),('interview', 'Interview')],string="Type",default='normal')


    @api.depends('res_id','res_model_id')
    def _get_applicant(self):
        for r in self:
            if r.res_model_id.model == 'hr.applicant':
                r.hr_applicant_id = self.env['hr.applicant'].browse([r.res_id])