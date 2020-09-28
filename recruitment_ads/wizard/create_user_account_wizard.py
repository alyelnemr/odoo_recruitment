import base64
from odoo import models, fields, api
from odoo.tools import pycompat


class CreateUserAccountComposeMessage(models.TransientModel):
    _name = 'create.user.account.mail.compose.message'
    _inherit = 'mail.compose.message'
    _description = 'Create User Account Mail wizard'

    approval_user = fields.Many2many('res.partner', 'create_user_mail_to_compose_message_res_partner_rel', 'wizard_id',
                                     'partner_id', string='To', required=True, domain=[('applicant', '=', False)])
    recruiter_id = fields.Many2many('res.partner', 'create_user_mail_cc_compose_message_res_partner_rel', 'wizard_id',
                                    'partner_id', string='CC', domain=[('applicant', '=', False)])
    attachment_ids = fields.Many2many('ir.attachment', 'create_user_mail_compose_message_ir_attachments_rel',
                                      'wizard_id',
                                      'attachment_id', string='Attachments')
    website_published = fields.Boolean(string='Published', help="Visible on the website as a comment", copy=False)
    hr_request_id = fields.Many2one('hr.request')

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
            email_cc = email_to = ''
            if xml_ids[0] == 'recruitment_ads.create_user_account_mail_template':
                email_to = ','.join([p.email for p in self.approval_user])
                email_cc = ','.join([p.email for p in self.recruiter_id])
                # else:
                #     email_to = ','.join([p.email for p in self.partner_ids])
                #     email_cc = ','.join([p.email for p in self.follower_ids])

                body = """        

            <style>
            td,th  {
              border: 1px solid black;
              border-collapse: collapse;
            }
            
            #job{
              border-collapse: collapse;
               width: 100%;
               text-align: center;
            }
            
           #td1_job , #td2_job {
                border: 0px solid #FFFFE0;
           }

            </style>""" + self.body

            mail_values = {
                'subject': self.subject,
                'body_html': body or '',
                'parent_id': self.parent_id and self.parent_id.id,
                'partner_ids': [],
                'email_to': email_to or False,
                'email_cc': email_cc or False,
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

    @api.multi
    def send_mail(self, auto_commit=False):
        """ Process the wizard content and proceed with sending the related
            email(s), rendering any template patterns on the fly if needed. """

        for wizard in self:
            # Duplicate attachments linked to the email.template.
            # Indeed, basic mail.compose.message wizard duplicates attachments in mass
            # mailing mode. But in 'single post' mode, attachments of an email template
            # also have to be duplicated to avoid changing their ownership.
            if wizard.attachment_ids and wizard.composition_mode != 'mass_mail' and wizard.template_id:
                new_attachment_ids = []
                for attachment in wizard.attachment_ids:
                    if attachment in wizard.template_id.attachment_ids:
                        new_attachment_ids.append(
                            attachment.copy({'res_model': 'mail.compose.message', 'res_id': wizard.id}).id)
                    else:
                        new_attachment_ids.append(attachment.id)
                    wizard.write({'attachment_ids': [(6, 0, new_attachment_ids)]})

            Mail = self.env['mail.mail']
            if wizard.template_id:
                Mail = Mail.with_context(mail_notify_user_signature=True)

            res_ids = [wizard.res_id]

            batch_size = int(self.env['ir.config_parameter'].sudo().get_param('mail.batch_size')) or self._batch_size
            sliced_res_ids = [res_ids[i:i + batch_size] for i in range(0, len(res_ids), batch_size)]
            record = self.env['hr.request'].browse(wizard.res_id)
            if record:
                record.create_account = True
            for res_ids in sliced_res_ids:
                batch_mails = Mail
                all_mail_values = wizard.get_mail_values(res_ids)
                for res_id, mail_values in all_mail_values.items():
                    batch_mails |= Mail.create(mail_values)
                batch_mails.send(auto_commit=auto_commit)

            recruitment_ticket = self.env['recruitment.tickets'].create({
                'applicant_code': wizard.hr_request_id.applicant_code,
                'applicant_name': wizard.hr_request_id.applicant_name,
                'business_unit_id': wizard.hr_request_id.business_unit_id.id,
                'job_id': wizard.hr_request_id.job_id.id,
                'department_id': wizard.hr_request_id.department_id.id,
                'section_id': wizard.hr_request_id.section_id.id
            })

        return {'type': 'ir.actions.act_window_close'}
