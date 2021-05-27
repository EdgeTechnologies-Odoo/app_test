# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SaleOrder(models.Model):
	_inherit = 'sale.order'

	def action_confirm(self):
		if self._get_forbidden_state_confirm() & set(self.mapped('state')):
			raise UserError(_(
				'It is not allowed to confirm an order in the following states: %s'
			) % (', '.join(self._get_forbidden_state_confirm())))
		followers_id = self.env['ir.config_parameter'].sudo().get_param('all_in_one_disable_followers_app.disable_follower_sale_order')
		if not followers_id:
			for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
				order.message_subscribe([order.partner_id.id])
		self.write({
			'state': 'sale',
			'date_order': fields.Datetime.now()
		})
		self._action_confirm()
		if self.env.user.has_group('sale.group_auto_done_setting'):
			self.action_done()
		return True	