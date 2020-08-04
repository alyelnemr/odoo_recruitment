from odoo import models, fields, api
import datetime as datetime_now


class IrAttachmentInherit(models.Model):
    _inherit = 'ir.attachment'

    # attach_name_seq = fields.Char()
    file_name_seq = fields.Char()
    attachment_type = fields.Selection([('cv', 'CV'), ('assessment', 'Assessment')],
                                       string="Attachment Type", required=True, default="cv")
    upload_date = fields.Datetime(string='Upload date')

    @api.depends('res_model', 'res_id')
    @api.onchange('datas_fname', 'attachment_type')
    def _compute_res_name(self):
        res = super(IrAttachmentInherit, self)._compute_res_name()
        for attachment in self:
            if attachment.res_model and attachment.res_id:
                if attachment.res_model == 'hr.applicant':
                    self_write_counter = attachment.with_context({'write_counter': True})
                    record = self.env[attachment.res_model].browse(attachment.res_id)
                    attachment.res_name = record.display_name
                    sequence = ''
                    if self.ids:
                        if attachment.attachment_type == 'cv':
                            sequence = str('(' + str(record.cv_counter) + ')' if record.cv_counter > 0 else '')
                            self_write_counter.name = record.name + sequence
                        elif attachment.attachment_type == 'assessment':
                            sequence = str(
                                '_ASS_' + str(
                                    record.assessment_counter) if record.assessment_counter > 0 else '_ASS')
                            self_write_counter.name = record.name + sequence
                        else:
                            attachment.name = record.display_name
                    else:
                        if attachment.attachment_type == 'cv' and self._origin.attachment_type != 'cv':
                            sequence = str('(' + str(record.cv_counter) + ')' if record.cv_counter > 0 else '')
                            self_write_counter.name = record.name + sequence
                        elif attachment.attachment_type == 'cv' and self._origin.attachment_type == 'cv':
                            self_write_counter.name = self._origin.name
                        elif attachment.attachment_type == 'assessment' and self._origin.attachment_type != 'assessment':
                            sequence = str(
                                '_ASS_' + str(
                                    record.assessment_counter) if record.assessment_counter > 0 else '_ASS')
                            self_write_counter.name = record.name + sequence
                        elif attachment.attachment_type == 'assessment' and self._origin.attachment_type == 'assessment':
                            self_write_counter.name = self._origin.name
                        else:
                            attachment.name = record.display_name
                    if attachment.datas_fname:
                        self_write_counter.upload_date = fields.Datetime.to_string(
                            datetime_now.datetime.now())

                        extension = attachment.datas_fname.split(".")
                        last_item = len(extension) - 1
                        extension = extension[last_item]

                        if self.ids:
                            self_write_counter.datas_fname = record.name + sequence + '.' + extension
                        else:
                            if attachment.attachment_type == 'cv' and self._origin.attachment_type != 'cv':
                                sequence = str('(' + str(record.cv_counter) + ')' if record.cv_counter > 0 else '')
                                self_write_counter.datas_fname = record.name + sequence + '.' + extension
                            elif attachment.attachment_type == 'cv' and self._origin.attachment_type == 'cv':
                                self_write_counter.datas_fname = self._origin.datas_fname
                            elif attachment.attachment_type == 'assessment' and self._origin.attachment_type != 'assessment':
                                sequence = str(
                                    '_ASS_' + str(
                                        record.assessment_counter) if record.assessment_counter > 0 else '_ASS')
                                self_write_counter.datas_fname = record.name + sequence + '.' + extension
                            elif attachment.attachment_type == 'assessment' and self._origin.attachment_type == 'assessment':
                                self_write_counter.datas_fname = self._origin.datas_fname
                            else:
                                attachment.name = record.display_name

        return res

    @api.model
    def create(self, vals):
        res = super(IrAttachmentInherit, self).create(vals)
        if res.res_model == 'hr.applicant':
            if res.attachment_type == 'assessment' and '_ASS' not in res.name:
                res._compute_res_name()

        if res.res_model == 'hr.offer':
            self._cr.execute(" update hr_offer set have_offer = %s where id =  %s ", (True, res.res_id,))
        return res
