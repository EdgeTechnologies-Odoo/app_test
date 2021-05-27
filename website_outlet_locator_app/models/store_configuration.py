# -*- coding: utf-8 -*-


from itertools import groupby
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang
from odoo.tools import html2plaintext
import odoo.addons.decimal_precision as dp

class WebsiteStoreLocation(models.Model):
    _name = 'store.location'
    _description = 'Website Store Locations'

    name = fields.Char(string='Store Name',size=64,required=False, default="New")
    image = fields.Binary("Image", attachment=True,
        help="This field holds the image used as avatar for this contact, limited to 1024x1024px",)
    
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')

    contact = fields.Char(
        string='Store Contact',
    )
    mobile = fields.Char(
        string='Store Mobile',
    )
    email = fields.Char(
        string='Store Email',
    )

    website_published = fields.Boolean(
        'Visible in Portal / Website', copy=False, 
         help="Make this payment acquires available (Customer invoices, etc.)")


    map_coordinates =fields.Selection([
        ('address','Based On Address'),
        ('manual','Based On Coordinates')], default="manual", required=True, string="Map Coordinates")

    latitude = fields.Char(
        string='Store Latitude',
    )

    longitude = fields.Char(
        string='Store Longitude',
    )

    def toggle_website_published(self):
        self.ensure_one()
        self.website_published = not self.website_published
        return True


class Website(models.Model):
    _inherit = 'website'

    def map_url(self):
        store_id = self.env['store.setting'].sudo().search([('website_published','=',True)],order="id desc", limit=1)
        script = """https://maps.googleapis.com/maps/api/js?key=%s&libraries=geometry,places""" % (store_id.google_api_key)
        return script