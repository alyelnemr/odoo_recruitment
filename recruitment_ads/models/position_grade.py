# -*- coding: utf-8 -*-
from odoo import models, fields


class PositionGrade(models.Model):
    _name = "position.grade"
    _inherit = ['mail.thread']

    name = fields.Char(string='Name', required=True)
