# -*- coding: utf-8 -*-

from itertools import groupby
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang
from odoo.tools import html2plaintext
import odoo.addons.decimal_precision as dp

class WebsiteStoreCategory(models.Model):

	_name = 'store.category'
	_description = 'Store Category'

	name = fields.Char(string="Category name")

	@api.model
	def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
		print("FFFFFFFFFFFFFFFFFFFf")
		# for arg in args:
		#     if arg[0] == 'id':
		#         for n, calendar_id in enumerate(arg[2]):
		#             if isinstance(calendar_id, str):
		#                 arg[2][n] = calendar_id.split('-')[0]
		return super(WebsiteStoreCategory, self)._name_search(name=name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)



class WebsiteStoreLocation(models.Model):
	_inherit = 'store.location'
	
	web_address = fields.Char("Website")
	category_id = fields.Many2many('store.category',string="Category")