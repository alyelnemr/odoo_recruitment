from odoo import models, fields, api
import datetime as datetime_now


class IrAttachmentInherit(models.Model):
    _inherit = 'ir.attachment'

    # attach_name_seq = fields.Char()
    file_name_seq = fields.Char()
    attachment_type = fields.Selection([('cv', 'CV'), ('assessment', 'Assessment')],
                                       string="Attachment Type", required=True, default="cv")
    upload_date = fields.Datetime(string='Upload date')

    @api.model
    def default_get(self, fields):
        result = super(IrAttachmentInherit, self).default_get(fields)
        if self._context.get('default_res_model', False) == 'hr.applicant' and self._context.get('default_res_id',
                                                                                                 False):
            applicant = self.env['hr.applicant'].browse(self._context.get('default_res_id', False))
            applicant.with_context({'write_counter': True}).cv_counter += 1
        return result

    @api.onchange('datas_fname')
    def _onchange_datas_fname(self):
        if self.datas_fname and self.res_model == 'hr.applicant':
            self_write_counter = self.with_context({'write_counter': True})
            # (datetime_now.datetime.now()-fields.Datetime.from_string(self.upload_date))
            self_write_counter.upload_date = fields.Datetime.to_string(
                datetime_now.datetime.now())
            # attach_no = self.search([('res_id', '=', self.res_id)])
            application = self.env['hr.applicant'].browse(self.res_id)

            extension = self.datas_fname.split(".")
            last_item = len(extension) - 1
            extension = extension[last_item]

            if self.attachment_type == 'cv':
                cv_seq = str('(' + str(application.cv_counter - 1) + ')' if application.cv_counter > 1 else '')
                self_write_counter.datas_fname = application.name + cv_seq + '.' + extension
                self_write_counter.name = application.name + cv_seq
            elif self.attachment_type == 'assessment':
                ass_seq = str(
                    '_ASS_' + str(
                        application.assessment_counter - 1) if application.assessment_counter > 1 else '_ASS')
                self_write_counter.datas_fname = application.name + ass_seq + '.' + extension
                self_write_counter.name = application.name + ass_seq

    @api.onchange('attachment_type')
    def _onchange_attachment_type(self):
        if self.datas_fname and self.res_model == 'hr.applicant':
            self_write_counter = self.with_context({'write_counter': True})
            self_write_counter.upload_date = fields.Datetime.to_string(
                datetime_now.datetime.now())
            # attach_no = self.search([('res_id', '=', self.res_id)])
            application = self.env['hr.applicant'].browse(self.res_id).with_context({'write_counter': True})

            extension = self.datas_fname.split(".")
            last_item = len(extension) - 1
            extension = extension[last_item]

            if self.attachment_type == 'cv':
                application.cv_counter += 1
                if application.assessment_counter >= 1:
                    application.assessment_counter -= 1
                cv_seq = str('(' + str(application.cv_counter - 1) + ')' if application.cv_counter > 1 else '')
                self_write_counter.datas_fname = application.name + cv_seq + '.' + extension
                self_write_counter.name = application.name + cv_seq
            elif self.attachment_type == 'assessment':
                application.assessment_counter += 1
                if application.cv_counter >= 1:
                    application.cv_counter -= 1
                ass_seq = str(
                    '_ASS_' + str(
                        application.assessment_counter - 1) if application.assessment_counter > 1 else '_ASS')
                self_write_counter.datas_fname = application.name + ass_seq + '.' + extension
                self_write_counter.name = application.name + ass_seq

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
        if res.res_model == 'hr.applicant':
            if res.attachment_type == 'assessment' and '_ASS' not in res.name:
                res._onchange_datas_fname()

        if res.res_model == 'hr.offer':
            self._cr.execute(" update hr_offer set have_offer = %s where id =  %s ", (True, res.res_id,))
        return res
