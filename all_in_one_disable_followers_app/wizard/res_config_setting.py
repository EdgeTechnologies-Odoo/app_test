# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResConfigSetting(models.TransientModel):
	_inherit = 'res.config.settings'

	disable_follower_send_mail = fields.Boolean("Disable to add followers by Send by Email")
	disable_follower_sale_order = fields.Boolean("Disable to add followers by Confirm Sale")
	disable_follower_invoice_bill = fields.Boolean("Disable to add followers by Validate Invoice/Bill")

	@api.model
	def get_values(self):
		res = super(ResConfigSetting, self).get_values()
		res['disable_follower_send_mail'] = (self.env['ir.config_parameter'].sudo().get_param('all_in_one_disable_followers_app.disable_follower_send_mail', default=0))
		res['disable_follower_sale_order'] = (self.env['ir.config_parameter'].sudo().get_param('all_in_one_disable_followers_app.disable_follower_sale_order', default=0))
		res['disable_follower_invoice_bill'] = (self.env['ir.config_parameter'].sudo().get_param('all_in_one_disable_followers_app.disable_follower_invoice_bill', default=0))
		return res

	
	def set_values(self):		
		self.env['ir.config_parameter'].sudo().set_param('all_in_one_disable_followers_app.disable_follower_send_mail', self.disable_follower_send_mail)
		self.env['ir.config_parameter'].sudo().set_param('all_in_one_disable_followers_app.disable_follower_sale_order', self.disable_follower_sale_order)
		self.env['ir.config_parameter'].sudo().set_param('all_in_one_disable_followers_app.disable_follower_invoice_bill', self.disable_follower_invoice_bill)
		super(ResConfigSetting, self).set_values()

class MailComposeMessage(models.TransientModel):
	_inherit = 'mail.compose.message'

	def get_mail_values(self, res_ids):
		res = super(MailComposeMessage,self).get_mail_values(res_ids)
		followers_id = self.env['ir.config_parameter'].sudo().get_param('all_in_one_disable_followers_app.disable_follower_send_mail')
		if followers_id:
			for key,value in res.items():
				del value['partner_ids']
		return res