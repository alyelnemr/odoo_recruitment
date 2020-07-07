from odoo import models, fields, api
import datetime as datetime_now


class IrAttachmentInherit(models.Model):
    _inherit = 'ir.attachment'

    # attach_name_seq = fields.Char()
    file_name_seq = fields.Char()
    attachment_type = fields.Selection([('cv', 'CV'), ('assessment', 'Assessment')],
                                       string="Attachment Type", required=True, default="cv")
    upload_date = fields.Datetime(string='Upload date')

    @api.onchange('datas_fname', 'attachment_type')
    def _get_attach_name(self):
        if self.datas_fname and self.res_model == 'hr.applicant':
            self.upload_date = fields.Datetime.to_string(datetime_now.datetime.now())
            attach_no = self.search([('res_id', '=', self.res_id)])
            application = self.env['hr.applicant'].browse(self.res_id)

            extension = self.datas_fname.split(".")
            last_item = len(extension) - 1
            extension = extension[last_item]

            cv_attach = []
            ass_attach = []
            if attach_no:
                for attach in attach_no:
                    if attach.attachment_type == 'cv':
                        cv_attach.append(attach)
                    elif attach.attachment_type == 'assessment':
                        ass_attach.append(attach)

                cv_seq = str('(' + str(len(cv_attach) + 1) + ')' if len(cv_attach) >= 1 else '')
                ass_seq = str('_ASS_' + str(len(ass_attach) + 1) if len(ass_attach) >= 1 else '_ASS')
                if self.attachment_type == 'cv':
                    self.datas_fname = application.name + cv_seq + '.' + extension
                    self.name = application.name + cv_seq
                elif self.attachment_type == 'assessment':
                    self.datas_fname = application.name + ass_seq + '.' + extension
                    self.name = application.name + ass_seq

    @api.depends('res_model', 'res_id')
    def _compute_res_name(self):
        res = super(IrAttachmentInherit, self)._compute_res_name()
        for attachment in self:
            if attachment.res_model and attachment.res_id:
                if attachment.res_model == 'hr.applicant':
                    record = self.env[attachment.res_model].browse(attachment.res_id)
                    attachment.res_name = record.display_name
                    attachment.name = record.display_name
        return res

    @api.model
    def create(self, vals):
        res = super(IrAttachmentInherit, self).create(vals)
        if res.res_model == 'hr.offer':
            self._cr.execute(" update hr_offer set have_offer = %s where id =  %s ", (True, res.res_id,))
        return res
