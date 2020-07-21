import base64
from odoo import models, fields, api
from odoo.tools import pycompat


class RejectionMailComposeMessage(models.TransientModel):
    _name = 'rejection.mail.compose.message'
    _inherit = 'mail.compose.message'
    _description = 'Rejection Mail wizard'

    candidate_id = fields.Many2one('res.partner', string='Candidate')
    application_id = fields.Many2one('hr.applicant', string='Application')
    partner_ids = fields.Many2many('res.partner', 'rejection_mail_compose_message_res_partner_rel', 'wizard_id',
                                   'partner_id', string='Interviewers', domain=[('applicant', '=', False)])
    attachment_ids = fields.Many2many('ir.attachment', 'interview_mail_compose_message_ir_attachments_rel', 'wizard_id',
                                      'attachment_id', string='Attachments')
    website_published = fields.Boolean(string='Published', help="Visible on the website as a comment", copy=False)

    @api.model
    def generate_email_for_composer(self, template_id, res_ids, fields=None):
        """ Call email_template.generate_email(), get fields relevant for
            mail.compose.message
            override to stop automatic look up of email to and convert it to recipients ids"""
        multi_mode = True
        if isinstance(res_ids, pycompat.integer_types):
            multi_mode = False
            res_ids = [res_ids]

        if fields is None:
            fields = ['subject', 'body_html', 'email_from', 'email_to', 'partner_to', 'email_cc', 'reply_to',
                      'attachment_ids', 'mail_server_id']
        returned_fields = fields + ['partner_ids', 'attachments']
        values = dict.fromkeys(res_ids, False)

        template_values = self.env['mail.template'].browse(template_id).generate_email(res_ids, fields=fields)
        for res_id in res_ids:
            res_id_values = dict((field, template_values[res_id][field]) for field in returned_fields if
                                 template_values[res_id].get(field))
            res_id_values['body'] = res_id_values.pop('body_html', '')
            values[res_id] = res_id_values

        return multi_mode and values or values[res_ids[0]]

    @api.multi
    def get_mail_values(self, res_ids):
        """Generate the values that will be used by send_mail to create mail_messages
        or mail_mails. """
        self.ensure_one()
        results = dict.fromkeys(res_ids, False)
        real_ids, xml_ids = zip(*self.template_id.get_xml_id().items())

        # generate attachment
        template_values = self.generate_email_for_composer(
            self.template_id.id, res_ids,
            fields=['attachment_ids'])

        for res_id in res_ids:
            email_dict = template_values[res_id]
            if xml_ids[0] == 'recruitment_ads.rejected_applicant_email_template':
                email_to = self.application_id.email_from or self.candidate_id.email
                email_cc = ','.join([p.email for p in self.partner_ids])
            else:
                email_to = ','.join([p.email for p in self.partner_ids])
                # email_cc = ','.join([p.email for p in self.follower_ids])

            mail_values = {
                'subject': self.subject,
                'body_html': self.body or '',
                'parent_id': self.parent_id and self.parent_id.id,
                'partner_ids': [],
                'email_to': email_to,
                'email_cc': email_cc,
                'attachment_ids': [attach.id for attach in self.attachment_ids],
                'author_id': self.author_id.id,
                'email_from': self.template_id.email_from,
                'record_name': self.record_name,
                'no_auto_thread': self.no_auto_thread,
                'mail_server_id': self.mail_server_id.id,
                'mail_activity_type_id': self.mail_activity_type_id.id,
                'attachments': [(name, base64.b64decode(enc_cont)) for name, enc_cont in
                                email_dict.pop('attachments', list())],
            }
            # process attachments: should not be encoded before being processed by message_post / mail_mail create
            attachment_ids = []
            for attach_id in mail_values.pop('attachment_ids'):
                new_attach_id = self.env['ir.attachment'].browse(attach_id).copy(
                    {'res_model': self._name, 'res_id': self.id})
                attachment_ids.append(new_attach_id.id)
            mail_values['attachment_ids'] = self.env['mail.thread']._message_preprocess_attachments(
                mail_values.pop('attachments', []),
                attachment_ids, 'mail.message', 0)

            results[res_id] = mail_values
        return results