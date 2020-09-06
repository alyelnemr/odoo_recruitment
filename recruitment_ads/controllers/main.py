
from odoo import http, tools, _
from odoo.http import request, Controller


class ApproveCycleController(Controller):

    @http.route(['/approval/cycle/approved'],csrf=False, type='http', methods=['GET'], auth="public", website=True)
    def approval_cycle_approve(self, **kwargs):
        data = request.params.copy()
        user = request.env['hr.approval.cycle.users'].sudo().search([('token', '=', kwargs['t'])])
        approval_cycle = request.env['hr.approval.cycle'].sudo().search([('offer_id','=',int(kwargs['o'])),('id','=',user.approval_cycle_id.id)])
        data['applicant_name'] = approval_cycle.application_id.partner_name
        if len(approval_cycle.users_list_ids) == 1:
            if user.state == 'no_action':
                data['approved'] = True
                user.state = 'approved'
                approval_cycle.state = 'approved'
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
                  next_user = request.env['hr.approval.cycle.users'].sudo().search([('sequence', '>', user.sequence),('approval_cycle_id','=',approval_cycle.id)],limit=1)
                  if next_user:
                     template.email_to = next_user.approval_user_id.email
                     template.send_mail(next_user.id)
                     next_user.sent = True
                  else:
                      approval_cycle.state = 'approved'
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
        user = request.env['hr.approval.cycle.users'].sudo().search([('token', '=', kwargs['t'])])
        approval_cycle = request.env['hr.approval.cycle'].sudo().search([('offer_id','=',int(kwargs['o'])),('id','=',user.approval_cycle_id.id)])
        data['applicant_name'] = approval_cycle.application_id.partner_name
        if user.state == 'no_action':
            data['rejected'] = True
            user.state = 'rejected'
            approval_cycle.state = 'rejected'
        else:
            if user.state == 'approved':
                data['approved_before'] = True
            else:
                data['rejected_before'] = True


        response = request.render('recruitment_ads.hr_approval_cycle_response', data)
        response.headers['X-Frame-Options'] = 'DENY'
        return response