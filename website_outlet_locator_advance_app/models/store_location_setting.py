# -*- coding: utf-8 -*-


from odoo import fields, models, api, _
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

class StoreSetting(models.Model):
	_name = 'store.setting'
	_description = 'Store Setting'

	name = fields.Char(string='Store Name',size=64,required=False, default="New")

	street = fields.Char()
	street2 = fields.Char()
	zip = fields.Char(change_default=True)
	city = fields.Char()
	state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', country_id)]")
	country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')


	map_center = fields.Selection([
		('auto','Based On Company Address'),
		('manual','Based On Address/Coordinate')], default="auto", required=True, string="Map Center")

	manual_options = fields.Selection([
		('address','Based On Address'),
		('manual','Based On Coordinate')], default="manual", required=True, string="Map Coordinates")

	map_type = fields.Selection([
		('roadmap','Road Map'),
		('satellite','Satellite')], default="roadmap", required=True, string="Map Type")

	latitude = fields.Char(string='Store Latitude')
	longitude = fields.Char(string='Store Longitude')

	google_api_key = fields.Char(
		string='Google Map API Key', required=True, default='Define Google API Key'
	)

	search_radius = fields.Integer(string='Search Radius (In Meters)', default=100) 
	map_zoom = fields.Integer(string='Map Zoom', default=10) 

	website_published = fields.Boolean(
		'Visible in Portal / Website', copy=False, default=False , help="Make this payment acquires available (Customer invoices, etc.)")


	def toggle_website_published(self):
		self.ensure_one()
		self.website_published = not self.website_published
		return True


	@api.constrains('website_published')
	def _check_term_and_condition_unit(self):
		if self.website_published == True :
			terms_ids = self.env['store.setting'].search([])
			for i in terms_ids:
				if i.id == self.id :
					continue
				if i.website_published == True:
					raise ValidationError(_('You Can Only Publish One Google Map Configuration at a Time!!'))