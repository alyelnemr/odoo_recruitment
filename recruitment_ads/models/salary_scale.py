# -*- coding: utf-8 -*-
from odoo import models, fields


class SalaryScale(models.Model):
    _name = "salary.scale"
    _inherit = ['mail.thread']

    name = fields.Char(string='Name', required=True)
