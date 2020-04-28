# Copyright 2016 Camptocamp SA
# Copyright 2017 Jarsa Sistemas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
import itertools
import json

from odoo import SUPERUSER_ID, _
from odoo.addons.crm.wizard.base_partner_merge import MergePartnerLine, \
    MergePartnerAutomatic
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger('base.partner.merge')


class NoCRMMergePartnerLine(MergePartnerLine):  # noqa
    _module = 'base_partner_merge'


class NoCRMMergePartnerAutomatic(MergePartnerAutomatic):  # noqa
    _module = 'base_partner_merge'

    dst_partner_id = fields.Many2one('res.partner', string='Destination Contact', readonly=True)

    @api.onchange('partner_ids')
    def on_change_partner_ids(self):
        if len(self.partner_ids) < 2:
            raise ValidationError(
                _('You cannot delete a line because merge must have at least 2 lines to do merge.'))
        if self.dst_partner_id not in self.partner_ids:
            raise ValidationError(
                _('You cannot delete a destination contact.'))

    @api.model
    def default_get(self, fields):
        res = super(MergePartnerAutomatic, self).default_get(fields)
        active_ids = self.env.context.get('active_ids')
        if self.env.context.get('active_model') in ('res.partner', 'hr.applicant') and self.env.context.get(
                'partner_ids'):
            active_ids = self.env.context.get('partner_ids')
            res['state'] = 'selection'
            res['partner_ids'] = active_ids
            res['dst_partner_id'] = self.env.context.get('dst_partner_id') or self._get_ordered_partner(active_ids)[
                0].id
        elif self.env.context.get('active_model') == 'res.partner' and active_ids:
            res['state'] = 'selection'
            res['partner_ids'] = active_ids
            res['dst_partner_id'] = self._get_ordered_partner(active_ids)[-1].id
        return res

    def _merge(self, partner_ids, dst_partner=None):
        """ private implementation of merge partner
            :param partner_ids : ids of partner to merge
            :param dst_partner : record of destination res.partner
        """
        Partner = self.env['res.partner']
        partner_ids = Partner.browse(partner_ids).exists()
        if len(partner_ids) < 2:
            return

        # if len(partner_ids) > 3:
        #     raise UserError(_(
        #         "For safety reasons, you cannot merge more than 3 contacts together. You can re-open the wizard several times if needed."))

        # check if the list of partners to merge contains child/parent relation
        child_ids = self.env['res.partner']
        for partner_id in partner_ids:
            child_ids |= Partner.search([('id', 'child_of', [partner_id.id])]) - partner_id
        if partner_ids & child_ids:
            raise UserError(_("You cannot merge a contact with one of his parent."))

        # [stop] check only admin can merge partners with different emails
        # if SUPERUSER_ID != self.env.uid and len(set(partner.email for partner in partner_ids)) > 1:
        #     raise UserError(_(
        #         "All contacts must have the same email. Only the Administrator can merge contacts with different emails."))

        # remove dst_partner from partners to merge
        if dst_partner and dst_partner in partner_ids:
            src_partners = partner_ids - dst_partner
        else:
            ordered_partners = self._get_ordered_partner(partner_ids.ids)
            dst_partner = ordered_partners[-1]
            src_partners = ordered_partners[:-1]
        _logger.info("dst_partner: %s", dst_partner.id)

        # FIXME: is it still required to make an exception for account.move.line since accounting v9.0 ?
        # if SUPERUSER_ID != self.env.uid and 'account.move.line' in self.env and self.env[
        #     'account.move.line'].sudo().search([('partner_id', 'in', [partner.id for partner in src_partners])]):
        #     raise UserError(_(
        #         "Only the destination contact may be linked to existing Journal Items. Please ask the Administrator if you need to merge several contacts linked to existing Journal Items."))

        # call sub methods to do the merge
        self._update_foreign_keys(src_partners, dst_partner)
        self._update_reference_fields(src_partners, dst_partner)
        self._update_values(src_partners, dst_partner)

        _logger.info('(uid = %s) merged the partners %r with %s', self._uid, src_partners.ids, dst_partner.id)
        dst_partner.message_post(body='%s %s' % (_("Merged with the following partners:"), ", ".join(
            '%s <%s> (ID %s)' % (p.name, p.email or 'n/a', p.id) for p in src_partners)))

        # archive source partner, since they are merged
        src_partners.write({'active': False})
        (src_partners + dst_partner).write({'old_data': False})

    @api.multi
    def cancel_merge(self):

        ctx = self._context.copy()
        active_model = ctx.get('active_model')
        action = {'type': 'ir.actions.act_window_close'}
        if ctx.get('new_contact', False) and active_model == 'res.partner':
            self.env[active_model].browse(ctx.get('dst_partner_id')).unlink()
            if not ctx.get('form_dialog'):
                action = self.env.ref('contacts.action_contacts').read()[0]
        elif ctx.get('edit_contact', False) and active_model == 'res.partner':
            edited_contact = self.env[active_model].browse(ctx.get('edit_contact'))
            vals = json.loads(edited_contact.old_data)
            vals['old_data'] = ''
            edited_contact.write(vals)
            if not ctx.get('form_dialog'):
                action = {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }
        elif ctx.get('create_applicant', False) and active_model == 'hr.applicant':
            self.env[active_model].browse(ctx.get('create_applicant')).unlink()
            action = self.env.ref('hr_recruitment.crm_case_categ0_act_job').read()[0]
        elif ctx.get('edit_applicant', False) and active_model == 'res.applicant':
            edit_applicant = self.env[active_model].browse(ctx.get('edit_applicant'))
            vals = json.loads(edit_applicant.old_data)
            vals['old_data'] = ''
            edit_applicant.write(vals)
            action = {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
            return action

    @api.multi
    def _action_next_screen(self):
        """ return the action of the next screen ; this means the wizard is set to treat the
            next wizard line. Each line is a subset of partner that can be merged together.
            If no line left, the end screen will be displayed (but an action is still returned).
        """
        self.invalidate_cache()  # FIXME: is this still necessary?
        values = {}
        if self.line_ids:
            # in this case, we try to find the next record.
            current_line = self.line_ids[0]
            current_partner_ids = literal_eval(current_line.aggr_ids)
            values.update({
                'current_line_id': current_line.id,
                'partner_ids': [(6, 0, current_partner_ids)],
                'dst_partner_id': self._get_ordered_partner(current_partner_ids)[-1].id,
                'state': 'selection',
            })
            self.write(values)
            return {
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }
        else:
            values.update({
                'current_line_id': False,
                'partner_ids': [],
                'state': 'finished',
            })
            self.write(values)
            ctx = self._context
            if ctx.get('active_model') == 'hr.partner':
                return {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }
            else:
                return {'type': 'ir.actions.act_window_close'}
                # view_id = self.env.ref('base.view_partner_form').id
                # action = {
                #     'type': 'ir.actions.act_window',
                #     'res_model': 'res.partner',
                #     'view_type': 'form',
                #     'view_mode': 'form',
                #     'views': [(view_id, 'form')],
                #     'target': 'current',
                #     'res_id': ctx.get('edit_contact'),
                #     'context': ctx,
                # }

    @api.model
    def _update_values(self, src_partners, dst_partner):
        """ Update values of dst_partner with the ones from the src_partners.
            :param src_partners : recordset of source res.partner
            :param dst_partner : record of destination res.partner
        """
        _logger.debug('_update_values for dst_partner: %s for src_partners: %r', dst_partner.id, src_partners.ids)

        model_fields = dst_partner._fields

        def write_serializer(item):
            if isinstance(item, models.BaseModel):
                return item.id
            else:
                return item

        # get all fields that are not computed or x2many
        values = dict()
        for column, field in model_fields.items():
            if field.type not in ('many2many', 'one2many') and field.compute is None:
                for item in itertools.chain(src_partners, [dst_partner]):
                    if item[column]:
                        values[column] = write_serializer(item[column])
        if dst_partner._table == 'res_partner':
            src_partners.write({'active': False})
            # self._cr.commit()
        # remove fields that can not be updated (id and parent_id)
        values.pop('id', None)
        parent_id = values.pop('parent_id', None)
        # src_partners = src_partners.browse(src_partners.ids)
        dst_partner.write(values)
        # try to update the parent_id
        if parent_id and parent_id != dst_partner.id:
            try:
                dst_partner.write({'parent_id': parent_id})
            except ValidationError:
                _logger.info('Skip recursive partner hierarchies for parent_id %s of partner: %s', parent_id,
                             dst_partner.id)
