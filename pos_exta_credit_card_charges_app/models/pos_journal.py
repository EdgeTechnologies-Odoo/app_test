# -*- coding: utf-8 -*-

from itertools import groupby
from datetime import datetime, timedelta
import logging
import psycopg2
import pytz
from collections import defaultdict
from odoo import api, fields, models,tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang
from odoo.tools import html2plaintext
import odoo.addons.decimal_precision as dp
_logger = logging.getLogger(__name__)


class AccountJournalInherit(models.Model):
	_inherit = "pos.payment.method"

	is_credit = fields.Boolean(string="Is credit card")


class AccountInvoiceInherit(models.Model):
	_inherit = "account.move"

	credit_charges = fields.Float(string = "Credit Card Charges")


class PosConfigInherit(models.Model):
	_inherit = "pos.config"

	default_credit_account_id = fields.Many2one('account.account' ,string = "Default Credit Account")
	credit_charge = fields.Float(string='Credit Card Charges')
	charges_type = fields.Selection([('per','Percentage'),('fix','Fixed')] , string = "Credit Charges")
	enable_credit_charges = fields.Boolean(string = "Enable Credit Charges")

class PosSessionInherit(models.Model):
	_inherit = 'pos.session'

	def _accumulate_amounts(self, data):
		# Accumulate the amounts for each accounting lines group
		# Each dict maps `key` -> `amounts`, where `key` is the group key.
		# E.g. `combine_receivables` is derived from pos.payment records
		# in the self.order_ids with group key of the `payment_method_id`
		# field of the pos.payment record.
		amounts = lambda: {'amount': 0.0, 'amount_converted': 0.0}
		tax_amounts = lambda: {'amount': 0.0, 'amount_converted': 0.0, 'base_amount': 0.0, 'base_amount_converted': 0.0}
		split_receivables = defaultdict(amounts)
		split_receivables_cash = defaultdict(amounts)
		combine_receivables = defaultdict(amounts)
		combine_receivables_cash = defaultdict(amounts)
		invoice_receivables = defaultdict(amounts)
		sales = defaultdict(amounts)
		taxes = defaultdict(tax_amounts)
		stock_expense = defaultdict(amounts)
		stock_return = defaultdict(amounts)
		stock_output = defaultdict(amounts)
		rounding_difference = {'amount': 0.0, 'amount_converted': 0.0}
		# Track the receivable lines of the invoiced orders' account moves for reconciliation
		# These receivable lines are reconciled to the corresponding invoice receivable lines
		# of this session's move_id.
		order_account_move_receivable_lines = defaultdict(lambda: self.env['account.move.line'])
		rounded_globally = self.company_id.tax_calculation_rounding_method == 'round_globally'
		for order in self.order_ids:
			# Combine pos receivable lines
			# Separate cash payments for cash reconciliation later.
			for payment in order.payment_ids:
				amount, date = payment.amount, payment.payment_date
				if payment.payment_method_id.split_transactions:
					if payment.payment_method_id.is_cash_count:
						split_receivables_cash[payment] = self._update_amounts(split_receivables_cash[payment], {'amount': amount}, date)
					else:
						split_receivables[payment] = self._update_amounts(split_receivables[payment], {'amount': amount}, date)
				else:
					key = payment.payment_method_id
					if payment.payment_method_id.is_cash_count:
						combine_receivables_cash[key] = self._update_amounts(combine_receivables_cash[key], {'amount': amount}, date)
					else:
						combine_receivables[key] = self._update_amounts(combine_receivables[key], {'amount': amount}, date)

			if order.is_invoiced:
				# Combine invoice receivable lines
				key = order.partner_id.property_account_receivable_id.id
				if self.config_id.cash_rounding:
					invoice_receivables[key] = self._update_amounts(invoice_receivables[key], {'amount': order.amount_paid}, order.date_order)
				else:
					invoice_receivables[key] = self._update_amounts(invoice_receivables[key], {'amount': order.amount_total}, order.date_order)
				# side loop to gather receivable lines by account for reconciliation
				for move_line in order.account_move.line_ids.filtered(lambda aml: aml.account_id.internal_type == 'receivable' and not aml.reconciled):
					order_account_move_receivable_lines[move_line.account_id.id] |= move_line
			else:
				order_taxes = defaultdict(tax_amounts)
				for order_line in order.lines:
					line = self._prepare_line(order_line)
					# Combine sales/refund lines
					sale_key = (
						# account
						line['income_account_id'],
						# sign
						-1 if line['amount'] < 0 else 1,
						# for taxes
						tuple((tax['id'], tax['account_id'], tax['tax_repartition_line_id']) for tax in line['taxes']),
						line['base_tags'],
					)
					sales[sale_key] = self._update_amounts(sales[sale_key], {'amount': line['amount']}, line['date_order'])
					# Combine tax lines
					for tax in line['taxes']:
						tax_key = (tax['account_id'], tax['tax_repartition_line_id'], tax['id'], tuple(tax['tag_ids']))
						order_taxes[tax_key] = self._update_amounts(
							order_taxes[tax_key],
							{'amount': tax['amount'], 'base_amount': tax['base']},
							tax['date_order'],
							round=not rounded_globally
						)
				for tax_key, amounts in order_taxes.items():
					if rounded_globally:
						amounts = self._round_amounts(amounts)
					for amount_key, amount in amounts.items():
						taxes[tax_key][amount_key] += amount

				if self.company_id.anglo_saxon_accounting and order.picking_ids.ids:
					# Combine stock lines
					stock_moves = self.env['stock.move'].sudo().search([
						('picking_id', 'in', order.picking_ids.ids),
						('company_id.anglo_saxon_accounting', '=', True),
						('product_id.categ_id.property_valuation', '=', 'real_time')
					])
					for move in stock_moves:
						exp_key = move.product_id._get_product_accounts()['expense']
						out_key = move.product_id.categ_id.property_stock_account_output_categ_id
						amount = -sum(move.sudo().stock_valuation_layer_ids.mapped('value'))
						stock_expense[exp_key] = self._update_amounts(stock_expense[exp_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)
						if move.location_id.usage == 'customer':
							stock_return[out_key] = self._update_amounts(stock_return[out_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)
						else:
							stock_output[out_key] = self._update_amounts(stock_output[out_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)

				if self.config_id.cash_rounding:
					diff = order.amount_paid - order.amount_total
					rounding_difference = self._update_amounts(rounding_difference, {'amount': diff}, order.date_order)

				# Increasing current partner's customer_rank
				partners = (order.partner_id | order.partner_id.commercial_partner_id)
				partners._increase_rank('customer_rank')

		if self.company_id.anglo_saxon_accounting:
			global_session_pickings = self.picking_ids.filtered(lambda p: not p.pos_order_id)
			if global_session_pickings:
				stock_moves = self.env['stock.move'].sudo().search([
					('picking_id', 'in', global_session_pickings.ids),
					('company_id.anglo_saxon_accounting', '=', True),
					('product_id.categ_id.property_valuation', '=', 'real_time'),
				])
				for move in stock_moves:
					exp_key = move.product_id._get_product_accounts()['expense']
					out_key = move.product_id.categ_id.property_stock_account_output_categ_id
					amount = -sum(move.stock_valuation_layer_ids.mapped('value'))
					stock_expense[exp_key] = self._update_amounts(stock_expense[exp_key], {'amount': amount}, move.picking_id.date)
					if move.location_id.usage == 'customer':
						stock_return[out_key] = self._update_amounts(stock_return[out_key], {'amount': amount}, move.picking_id.date)
					else:
						stock_output[out_key] = self._update_amounts(stock_output[out_key], {'amount': amount}, move.picking_id.date)
		MoveLine = self.env['account.move.line'].with_context(check_move_validity=False)

		data.update({
			'taxes':                               taxes,
			'sales':                               sales,
			'stock_expense':                       stock_expense,
			'split_receivables':                   split_receivables,
			'combine_receivables':                 combine_receivables,
			'split_receivables_cash':              split_receivables_cash,
			'combine_receivables_cash':            combine_receivables_cash,
			'invoice_receivables':                 invoice_receivables,
			'stock_return':                        stock_return,
			'stock_output':                        stock_output,
			'order_account_move_receivable_lines': order_account_move_receivable_lines,
			'rounding_difference':                 rounding_difference,
			'MoveLine':                            MoveLine
		})
		return data

	def _prepare_balancing_line_vals(self, imbalance_amount, move):
		account = self._get_balancing_account()
		account = self.config_id.default_credit_account_id
		partial_vals = {
			'name': _('Difference at closing PoS session'),
			'account_id': account.id,
			'move_id': move.id,
			'partner_id': False,
		}
		# `imbalance_amount` is already in terms of company currency so it is the amount_converted
		# param when calling `_credit_amounts`. amount param will be the converted value of
		# `imbalance_amount` from company currency to the session currency.
		imbalance_amount_session = 0
		if (not self.is_in_company_currency):
			imbalance_amount_session = self.company_id.currency_id._convert(imbalance_amount, self.currency_id, self.company_id, fields.Date.context_today(self))
		return self._credit_amounts(partial_vals, imbalance_amount_session, imbalance_amount)

class PosOrderInherit(models.Model):
	_inherit = "pos.order"

	credit_charges = fields.Float(string = "Credit Card Charges")

	def action_pos_order_invoice(self):
		moves = self.env['account.move']

		for order in self:
			# Force company for all SUPERUSER_ID action
			if order.account_move:
				moves += order.account_move
				continue

			if not order.partner_id:
				raise UserError(_('Please provide a partner for the sale.'))

			move_vals = order._prepare_invoice_vals()
			new_move = moves.sudo()\
							.with_company(order.company_id)\
							.with_context(default_move_type=move_vals['move_type'])\
							.create(move_vals)
			message = _("This invoice has been created from the point of sale session: <a href=# data-oe-model=pos.order data-oe-id=%d>%s</a>") % (order.id, order.name)
			new_move.message_post(body=message)
			order.write({'account_move': new_move.id, 'state': 'invoiced'})
			new_move.sudo().with_company(order.company_id)._post()
			moves += new_move

			if order.session_id.config_id.enable_credit_charges:
				if order.credit_charges > 0:
					MoveLine = self.env['account.move.line']
					move_line = {
								'move_id': new_move.id,
								'quantity': 1,
								'analytic_account_id': False,
								'account_id': order.session_id.config_id.default_credit_account_id.id,
								'name': 'Credit Charges',
							}
					move_lines = MoveLine.sudo().new(move_line)
					move_line = move_lines._convert_to_write({name: move_lines[name] for name in move_lines._cache})
					move_line.update(price_unit=order.credit_charges)
					MoveLine.sudo().create(move_line)

		if not moves:
			return {}

		return {
			'name': _('Customer Invoice'),
			'view_mode': 'form',
			'view_id': self.env.ref('account.view_move_form').id,
			'res_model': 'account.move',
			'context': "{'move_type':'out_invoice'}",
			'type': 'ir.actions.act_window',
			'nodestroy': True,
			'target': 'current',
			'res_id': moves and moves.ids[0] or False,
		}

	def _prepare_invoice_vals(self):
		self.ensure_one()
		timezone = pytz.timezone(self._context.get('tz') or self.env.user.tz or 'UTC')
		vals = {
			'payment_reference': self.name,
			'invoice_origin': self.name,
			'journal_id': self.session_id.config_id.invoice_journal_id.id,
			'move_type': 'out_invoice' if self.amount_total >= 0 else 'out_refund',
			'ref': self.name,
			'partner_id': self.partner_id.id,
			'narration': self.note or '',
			'credit_charges' : self.credit_charges,
			# considering partner's sale pricelist's currency
			'currency_id': self.pricelist_id.currency_id.id,
			'invoice_user_id': self.user_id.id,
			'invoice_date': self.date_order.astimezone(timezone).date(),
			'fiscal_position_id': self.fiscal_position_id.id,
			'invoice_line_ids': [(0, None, self._prepare_invoice_line(line)) for line in self.lines],
			'invoice_cash_rounding_id': self.config_id.rounding_method.id if self.config_id.cash_rounding else False
		}
		return vals

	@api.onchange('payment_ids', 'lines')
	def _compute_amount_all(self):
		for order in self:
			order.amount_paid = order.amount_return = order.amount_tax = 0.0
			currency = order.pricelist_id.currency_id
			order.amount_paid = sum(payment.amount for payment in order.statement_ids)
			order.amount_return = sum(payment.amount < 0 and payment.amount or 0 for payment in order.statement_ids)
			order.amount_tax = currency.round(sum(self._amount_line_tax(line, order.fiscal_position_id) for line in order.lines))
			amount_untaxed = currency.round(sum(line.price_subtotal for line in order.lines))
			order.amount_total = order.amount_tax + amount_untaxed + order.credit_charges


	@api.model
	def create_from_ui(self, orders, draft=False):
		order_ids = []
		for order in orders:
			existing_order = False
			if 'server_id' in order['data']:
				existing_order = self.env['pos.order'].search([('id', '=', order['data']['server_id'])], limit=1) 	
				
			order_ids.append(self._process_order(order, draft, existing_order))
			for order_id in order_ids:
				pos_order_id = self.browse(order_id)
				if pos_order_id:
					ref_order = [o['data'] for o in orders if o['data'].get('name') == pos_order_id.pos_reference]
					for order in ref_order:
						pos_order_id.update({'credit_charges': order.get('credit_charge')})
		return self.env['pos.order'].search_read(domain = [('id', 'in', order_ids)], fields = ['id', 'pos_reference'])