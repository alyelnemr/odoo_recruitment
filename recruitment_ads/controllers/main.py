
from odoo import http, tools, _
from odoo.http import request, Controller


class ApproveCycleController(Controller):

    @http.route(['/approval/cycle/approved'],csrf=False, type='http', methods=['GET'], auth="public", website=True)
    def approval_cycle_approve(self, **kwargs):
        data = request.params.copy()
        user = request.env['hr.approval.cycle.users'].sudo().search([('id', '=', kwargs['t'])])
        approval_cycle = request.env['hr.approval.cycle'].sudo().search([('offer_id','=',int(kwargs['o'])),('id','=',user.approval_cycle_id.id)])
        data['applicant_name'] = approval_cycle.application_id.partner_name
        if len(approval_cycle.users_list_ids) == 1:
            if user.state == 'no_action':
                data['approved'] = True
                user.state = 'approved'
                approval_cycle.state = 'approved'
                if user.email_id.attachment_ids:
                    attachment = request.env['ir.attachment'].search([('id','in',user.email_id.attachment_ids.ids)])
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
                  next_user = request.env['hr.approval.cycle.users'].sudo().search([('sequence', '>', user.sequence),('approval_cycle_id','=',approval_cycle.id)],limit=1)
                  if next_user:
                     approve = user.email_id.body_html.replace(
                          'approval/c'
                          'ycle/approved?o=' + str(int(kwargs['o']) )+ '&amp;t=' + str(user.id),
                                                             'approval/cycle/approved?o=' + str(
                                                                 int(kwargs['o'])) + '&amp;t=' + str(next_user.id))
                     new_body= approve.replace(
                          'approval/cycle/reject?o=' + str(int(kwargs['o']) )+ '&amp;t=' + str(user.id),
                                                             'approval/cycle/reject?o=' + str(
                                                                 int(kwargs['o'])) + '&amp;t=' + str(next_user.id))
                     email_cc =  user.email_id.email_cc +',' + user.approval_user_id.email
                     new_template = template.copy({
                         'email_to': next_user.approval_user_id.email,
                         'body_html' :  new_body,
                         # 'attachment_ids': [attach.id for attach in user.email_id.attachment_ids],
                         'attachment_ids': [(6, 0, user.email_id.attachment_ids.ids)],
                         'email_cc':email_cc,
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
        approval_cycle = request.env['hr.approval.cycle'].sudo().search([('offer_id','=',int(kwargs['o'])),('id','=',user.approval_cycle_id.id)])
        data['applicant_name'] = approval_cycle.application_id.partner_name
        if user.state == 'no_action':
            data['rejected'] = True
            user.state = 'rejected'
            approval_cycle.state = 'rejected'
            if approval_cycle.users_list_ids[0].email_id.attachment_ids:
                attachment = request.env['ir.attachment'].search([('res_model', '=', 'approval.cycle.mail.compose.message')])
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