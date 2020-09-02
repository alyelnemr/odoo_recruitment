# from odoo.addons.web.controllers import main as report
# from odoo.http import content_disposition, route, request
#
# import json
from odoo import http, tools, _
from odoo.http import request, Controller
from ast import literal_eval

class ApproveCycleController(Controller):

    @http.route(['/approval/cycle/approved'],csrf=False, type='http', methods=['GET'], auth="public", website=True)
    def approval_cycle_approve(self, **kwargs):
        for key in kwargs.keys():
            values = key.split('/')
        data = request.params.copy()
        # x=  literal_eval(values[1])
        approval_cycle = request.env['hr.approval.cycle'].sudo().search([('offer_id','=',int(values[0]))],order='create_date desc',limit=1)
        users = request.env['hr.approval.cycle.users'].sudo().search([('id', 'in', literal_eval(values[1]))],
                                                                        order='create_date desc')
        x = request._cr
        data['applicant_name'] = approval_cycle.application_id.partner_name
        data['approved'] = True
        if len(approval_cycle.users_list_ids) == 1 :
            if approval_cycle.users_list_ids[0].state == 'no_action':
                approval_cycle.users_list_ids[0].state = 'approved'
                approval_cycle.state = 'approved'
        else:
            count = 0
            number_users = len(approval_cycle.users_list_ids)
            for user in approval_cycle.users_list_ids :
                count += 1
                if user.state == 'no_action':
                    user.sudo().write({'state' : 'approved'})
                    if count < number_users:
                        template = request.env.ref('recruitment_ads.approval_cycle_mail_template', False)
                        if template:
                            template= request.env['mail.template'].sudo().browse(template.id)
                            template.email_to = approval_cycle.users_list_ids[count].approval_user_id.email
                            template.send_mail(approval_cycle.id)
                            approval_cycle.users_list_ids[count ].sudo().write({'sent' : True})
                            break;
                    else:
                        approval_cycle.state = 'approved'

        response = request.render('recruitment_ads.hr_approval_cycle_response', data)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @http.route(['/approval/cycle/reject'], csrf=False, type='http', methods=['GET'], auth="public", website=True)
    def approval_cycle_rejected(self, **kwargs):
        values = list(kwargs.keys())
        data = request.params.copy()
        approval_cycle = request.env['hr.approval.cycle'].sudo().search([('offer_id','=',int(values[0]))],order='create_date desc',limit=1)
        data['applicant_name'] = approval_cycle.application_id.partner_name
        data['rejected'] = True

        if len(approval_cycle.users_list_ids) == 1 :
            if approval_cycle.users_list_ids[0].state == 'no_action':
                approval_cycle.users_list_ids[0].state = 'rejected'
                approval_cycle.state = 'rejected'
        else:
            for user in approval_cycle.users_list_ids:
                if user.state == 'no_action':
                    user.sudo().write({'state': 'rejected'})
                    approval_cycle.state = 'rejected'
                    break;

        response = request.render('recruitment_ads.hr_approval_cycle_response', data)
        response.headers['X-Frame-Options'] = 'DENY'
        return response