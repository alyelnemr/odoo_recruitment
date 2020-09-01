# from odoo.addons.web.controllers import main as report
# from odoo.http import content_disposition, route, request
#
# import json
from odoo import http, tools, _
from odoo.http import request, Controller
# import erppeek
class ApproveCycleController(Controller):

    @http.route(['/approval/cycle/approved'],csrf=False, type='http', methods=['GET'], auth="public", website=True)
    def approval_cycle_approve(self, **kwargs):
        # client = erppeek.Client('http://10.24.105.44:8069', 'recruitment_aly', 'admin', 'admin')
        values = list(kwargs.keys())
        data = request.params.copy()
        approval_cycle = request.env['hr.approval.cycle'].sudo().search([('offer_id','=',int(values[0]))],order='create_date desc',limit=1)
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
                # if user.state == 'no_action':
                #     user.sudo().write({'state' : 'approved'})
                #     if count < number_users:
                #         template = request.env.ref('recruitment_ads.approval_cycle_mail_template', False)
                #         if template:
                #             template= request.env['mail.template'].sudo().browse(template.id)
                #             template.email_to = approval_cycle.users_list_ids[count].approval_user_id.email
                #             template.send_mail(approval_cycle.id)
                #             approval_cycle.users_list_ids[count ].sudo().write({'sent' : True})
                #             break;
                #     else:
                #         approval_cycle.state = 'approved'

        response = request.render('auth_signup.signup', data)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @http.route(['/approval/cycle/reject'], csrf=False, type='http', methods=['GET'], auth="public", website=True)
    def approval_cycle_rejected(self, **kwargs):
        # client = erppeek.Client('http://10.24.105.44:8069', 'recruitment_aly', 'admin', 'admin')
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

        response = request.render('auth_signup.signup', data)
        response.headers['X-Frame-Options'] = 'DENY'
        return response