# -*- coding: utf-8 -*-
from odoo import models, fields


class PositionGrade(models.Model):
    _name = "position.grade"
    _inherit = ['mail.thread']
    _order = 'sequence asc'

    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(default=10)
