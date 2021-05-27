# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import float_compare
from datetime import datetime, timedelta

class AccountMove(models.Model):
	_inherit = 'account.move'

	def action_post(self):
		for move in self:
			if not move.line_ids.filtered(lambda line: not line.display_type):
				raise UserError(_('You need to add a line before posting.'))
			if move.auto_post and move.date > fields.Date.today():
				date_msg = move.date.strftime(self.env['res.lang']._lang_get(self.env.user.lang).date_format)
				raise UserError(_("This move is configured to be auto-posted on %s" % date_msg))

			if not move.partner_id:
				if move.is_sale_document():
					raise UserError(_("The field 'Customer' is required, please complete it to validate the Customer Invoice."))
				elif move.is_purchase_document():
					raise UserError(_("The field 'Vendor' is required, please complete it to validate the Vendor Bill."))

			if move.is_invoice(include_receipts=True) and float_compare(move.amount_total, 0.0, precision_rounding=move.currency_id.rounding) < 0:
				raise UserError(_("You cannot validate an invoice with a negative total amount. You should create a credit note instead. Use the action menu to transform it into a credit note or refund."))
			
			if not move.invoice_date and move.is_invoice(include_receipts=True):
				move.invoice_date = fields.Date.context_today(self)
				move.with_context(check_move_validity=False)._onchange_invoice_date()
			
			if (move.company_id.tax_lock_date and move.date <= move.company_id.tax_lock_date) and (move.line_ids.tax_ids or move.line_ids.tag_ids):
				move.date = move.company_id.tax_lock_date + timedelta(days=1)
				move.with_context(check_move_validity=False)._onchange_currency()
		# Create the analytic lines in batch is faster as it leads to less cache invalidation.
		self.mapped('line_ids').create_analytic_lines()
		for move in self:
			if move.auto_post and move.date > fields.Date.today():
				raise UserError(_("This move is configured to be auto-posted on {}".format(move.date.strftime(self.env['res.lang']._lang_get(self.env.user.lang).date_format))))
			followers_id = self.env['ir.config_parameter'].sudo().get_param('all_in_one_disable_followers_app.disable_follower_invoice_bill')
			if not followers_id:
				move.message_subscribe([p.id for p in [move.partner_id, move.commercial_partner_id] if p not in move.sudo().message_partner_ids])

			to_write = {'state': 'posted'}
			move.write(to_write)