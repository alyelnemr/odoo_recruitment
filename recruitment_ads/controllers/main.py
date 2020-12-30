# -*- coding: utf-8 -*-
import json
from odoo import http, tools, _
from odoo.http import request, Controller
from odoo.addons.website_form.controllers.main import WebsiteForm
from odoo.exceptions import ValidationError
from psycopg2 import IntegrityError


class ApproveCycleController(Controller):

    @http.route(['/approval/cycle/approved'], csrf=False, type='http', methods=['GET'], auth="public", website=True)
    def approval_cycle_approve(self, **kwargs):
        data = request.params.copy()
        user = request.env['hr.approval.cycle.users'].sudo().search([('id', '=', kwargs['t'])])
        approval_cycle = request.env['hr.approval.cycle'].sudo().search(
            [('offer_id', '=', int(kwargs['o'])), ('id', '=', user.approval_cycle_id.id)])
        data['applicant_name'] = approval_cycle.application_id.partner_name
        if len(approval_cycle.users_list_ids) == 1:
            if user.state == 'no_action':
                data['approved'] = True
                user.state = 'approved'
                approval_cycle.state = 'approved'
                if user.email_id.attachment_ids:
                    attachment = request.env['ir.attachment'].search([('id', 'in', user.email_id.attachment_ids.ids)])
                    for attach in attachment:
                        attach.unlink()
            else:
                if user.state == 'approved':
                    data['approved_before'] = True
                else:
                    data['rejected_before'] = True

        else:
            if user.state == 'no_action':
                data['approved'] = True
                user.state = 'approved'
                template = request.env.ref('recruitment_ads.approval_cycle_mail_template', False)
                if template:
                    template = request.env['mail.template'].sudo().browse(template.id)
                    next_user = request.env['hr.approval.cycle.users'].sudo().search(
                        [('sequence', '>', user.sequence), ('approval_cycle_id', '=', approval_cycle.id)], limit=1)
                    if next_user:
                        approve = user.email_id.body_html.replace(
                            'approval/c'
                            'ycle/approved?o=' + str(int(kwargs['o'])) + '&amp;t=' + str(user.id),
                            'approval/cycle/approved?o=' + str(
                                int(kwargs['o'])) + '&amp;t=' + str(next_user.id))
                        new_body = approve.replace(
                            'approval/cycle/reject?o=' + str(int(kwargs['o'])) + '&amp;t=' + str(user.id),
                            'approval/cycle/reject?o=' + str(
                                int(kwargs['o'])) + '&amp;t=' + str(next_user.id))
                        email_cc = user.email_id.email_cc + ',' + user.approval_user_id.email
                        new_template = template.copy({
                            'email_to': next_user.approval_user_id.email,
                            'body_html': new_body,
                            # 'attachment_ids': [attach.id for attach in user.email_id.attachment_ids],
                            'attachment_ids': [(6, 0, user.email_id.attachment_ids.ids)],
                            'email_cc': email_cc,
                        })
                        x = new_template.send_mail(next_user.id)
                        email = request.env['mail.mail'].browse(x)
                        next_user.email_id = email.id
                        email.auto_delete = False
                        # x.auto_delete = False
                        # obj=request.env['mail.mail'].browse(x)
                        # next_user.write({
                        #     'email_id': x
                        # })

                        next_user.sent = True
                        new_template.unlink()
                    else:
                        approval_cycle.state = 'approved'
                        if approval_cycle.users_list_ids[0].email_id.attachment_ids:
                            attachment = request.env['ir.attachment'].search(
                                [('res_model', '=', 'approval.cycle.mail.compose.message')])
                            if attachment:
                                for attach in attachment:
                                    attach.unlink()
                            # attachment = request.env['ir.attachment'].search(
                            #     [('id', 'in', approval_cycle.users_list_ids[0].email_id.attachment_ids.ids)])
                            # for attach in attachment:
                            #     attach.unlink()
            else:
                if user.state == 'approved':
                    data['approved_before'] = True
                else:
                    data['rejected_before'] = True

        response = request.render('recruitment_ads.hr_approval_cycle_response', data)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @http.route(['/approval/cycle/reject'], csrf=False, type='http', methods=['GET'], auth="public", website=True)
    def approval_cycle_rejected(self, **kwargs):
        data = request.params.copy()
        user = request.env['hr.approval.cycle.users'].sudo().search([('id', '=', kwargs['t'])])
        approval_cycle = request.env['hr.approval.cycle'].sudo().search(
            [('offer_id', '=', int(kwargs['o'])), ('id', '=', user.approval_cycle_id.id)])
        data['applicant_name'] = approval_cycle.application_id.partner_name
        if user.state == 'no_action':
            data['rejected'] = True
            user.state = 'rejected'
            approval_cycle.state = 'rejected'
            if approval_cycle.users_list_ids[0].email_id.attachment_ids:
                attachment = request.env['ir.attachment'].search(
                    [('res_model', '=', 'approval.cycle.mail.compose.message')])
                if attachment:
                    for attach in attachment:
                        attach.unlink()
        else:
            if user.state == 'approved':
                data['approved_before'] = True
            else:
                data['rejected_before'] = True

        response = request.render('recruitment_ads.hr_approval_cycle_response', data)
        response.headers['X-Frame-Options'] = 'DENY'
        return response


class JobForm(WebsiteForm):

    # Check and insert values from the form on the model <model>
    @http.route('/website_form/<string:model_name>', type='http', auth="public", methods=['POST'], website=True)
    def website_form(self, model_name, **kwargs):
        model_record = request.env['ir.model'].sudo().search(
            [('model', '=', model_name), ('website_form_access', '=', True)])
        if not model_record:
            return json.dumps(False)

        try:
            data = self.extract_data(model_record, request.params)
        # If we encounter an issue while extracting data
        except ValidationError as e:
            # I couldn't find a cleaner way to pass data to an exception
            return json.dumps({'error_fields': e.args[0]})

        try:
            website_user_id = False
            if model_name == 'hr.applicant':
                data['record']['source_id'] = request.env.ref('recruitment_ads.utm_source_website', False).id
                data['record']['medium_id'] = request.env.ref('utm.utm_medium_website', False).id
                data['record']['cv_matched'] = True
                data['record']['source_resp'] = request.env.ref('recruitment_ads.website_user_root', False).id
                email = data['record'].get('email_from', False).strip().lower()
                phone = data['record'].get('partner_phone', False)
                partner = request.env['res.partner'].search(
                    ['|', '|', ('email', '=', email), ('phone', '=', phone), ('mobile', '=', phone)], limit=1)
                if not partner:
                    partner = request.env['res.partner'].create(
                        {'name': data['record']['partner_name'],
                         'email': data['record']['email_from'],
                         'phone': data['record']['partner_phone'],
                         'mobile': data['record']['partner_phone'],
                         'customer': True})
                data['record']['partner_id'] = partner.id
            id_record = self.insert_record(request, model_record, data['record'], data['custom'], data.get('meta'))
            if id_record:
                self.insert_attachment(model_record, id_record, data['attachments'])

        # Some fields have additional SQL constraints that we can't check generically
        # Ex: crm.lead.probability which is a float between 0 and 1
        # TODO: How to get the name of the erroneous field ?
        except IntegrityError:
            return json.dumps(False)

        request.session['form_builder_model_model'] = model_record.model
        request.session['form_builder_model'] = model_record.name
        request.session['form_builder_id'] = id_record

        return json.dumps({'id': id_record})
