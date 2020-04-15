# Copyright 2016 Camptocamp SA
# Copyright 2017 Jarsa Sistemas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.crm.wizard.base_partner_merge import MergePartnerLine, \
    MergePartnerAutomatic
from odoo import api
from odoo.exceptions import ValidationError


class NoCRMMergePartnerLine(MergePartnerLine):  # noqa
    _module = 'base_partner_merge'


class NoCRMMergePartnerAutomatic(MergePartnerAutomatic):  # noqa
    _module = 'base_partner_merge'

    @api.model
    def default_get(self, fields):
        res = super(MergePartnerAutomatic, self).default_get(fields)
        active_ids = self.env.context.get('active_ids')
        if self.env.context.get('active_model') in ('res.partner', 'hr.applicant') and self.env.context.get(
                'partner_ids'):
            active_ids = self.env.context.get('partner_ids')
            res['state'] = 'selection'
            res['partner_ids'] = active_ids
            res['dst_partner_id'] = self._get_ordered_partner(active_ids)[-1].id
        elif self.env.context.get('active_model') == 'res.partner' and active_ids:
            res['state'] = 'selection'
            res['partner_ids'] = active_ids
            res['dst_partner_id'] = self._get_ordered_partner(active_ids)[-1].id
        return res
