# -*- coding: utf-8 -*-

import werkzeug
import json
import base64
import googlemaps
import odoo.http as http
import urllib.parse
import requests
import urllib
from odoo.http import request
from odoo import SUPERUSER_ID
from datetime import datetime, timedelta, time
from odoo.addons.http_routing.models.ir_http import slug
import odoo.http as http


PPG = 20  # Products Per Page
PPR = 4   # Products Per Row

class DynamicController(http.Controller):

    @http.route(['/store/vals'] , type='json', auth="public", website=True)
    def location_vals(self, **post):
        store_id = request.env['store.setting'].sudo().search([('website_published','=',True)],order="id desc", limit=1)
        data = {}
        latitude = False
        longitude = False
        map_zoom = False
        map_type = False
        map_search_radius = False
        geocode_result = None
        api = False
        address = ''

        if store_id.google_api_key:
            gmaps = googlemaps.Client(key=str(store_id.google_api_key))
            api = True
        
        if store_id.map_center == 'auto':   
            company = request.env.user.company_id    
            address += str(company.street) + ' ' + str(company.street2) + ' ' + str(company.state_id.name) + ' ' + str(company.country_id.name)
            try:
                geocode_result = gmaps.geocode(address)
            except ValueError as error_message:
                pass
            latitude = geocode_result[0]['geometry']['location']['lat']
            longitude = geocode_result[0]['geometry']['location']['lng']
        elif store_id.map_center == 'manual':
            if store_id.manual_options == 'manual':
                latitude = store_id.latitude
                longitude = store_id.longitude
            if store_id.manual_options == 'address':
                address += store_id.street + ' ' + store_id.street2 + ' ' + store_id.state_id.name + ' ' + store_id.country_id.name
                geocode_result = gmaps.geocode(address)
                try:
                    geocode_result = gmaps.geocode(address)
                except ValueError as error_message:
                    print("Error: geocode failed on input %s with message %s" % (address, error_message))
                latitude = geocode_result[0]['geometry']['location']['lat']
                longitude = geocode_result[0]['geometry']['location']['lng']

        location_ids = request.env['store.location'].sudo().search([('website_published','=',True)])
    
        location = {}
        for location_id in location_ids:
            if location_id.image:
                src = '/web/image/store.location/'+ str(location_id.id) +'/image'
            else:
                src = ''
            address = ''
            if location_id.street:
                address += """ %s \n""" % location_id.street
            if location_id.street2:
                address += """ %s \n""" % location_id.street2
            if location_id.city:
                address += """ %s \t""" % location_id.city
            if location_id.state_id:
                address += """ %s \t""" % location_id.state_id.name
            if location_id.zip:
                address += """ %s \n""" % location_id.zip
            if location_id.country_id:
                address += """ %s \n""" % location_id.country_id.name

            store_latitude  = False
            store_longitude = False

            if location_id.map_coordinates == 'manual':
                store_latitude = location_id.latitude
                store_longitude = location_id.longitude
            if location_id.map_coordinates == 'address':
                geocode_result = gmaps.geocode(address)
                try:
                    geocode_result = gmaps.geocode(address)
                except ValueError as error_message:
                    print("Error: geocode failed on input %s with message %s" % (address, error_message))
                store_latitude = geocode_result[0]['geometry']['location']['lat']
                store_longitude = geocode_result[0]['geometry']['location']['lng']

            location.update({
                location_id.id : {
                    'name' : location_id.name,
                    'contact' : location_id.contact,
                    'image' : src, 
                    'email' : location_id.email,
                    'address' : address,
                    'latitude' : store_latitude,
                    'longitude' : store_longitude, 
                    'store_id' : location_id.id,
                    'map_search_radius' : store_id.search_radius,
                }
            })

        map_search_radius = store_id.search_radius
        map_zoom = store_id.map_zoom
        map_type = store_id.map_type


        final_val = {}
        data = {}
        map_stores_data = {}
        final_val.update({
            'latitude' : latitude,
            'longitude' : longitude,
            'map_zoom' : map_zoom,
            'map_type' : map_type,
            'map_search_radius' : map_search_radius,
        })

        data.update({
            'api': api,
            'map_init' :final_val,
            'map_stores_data' : location,
            })


        return json.dumps(data)   


    @http.route(['/store/locater'] , type='http', auth="public", website=True)
    def store_locator(self, **post):

        return request.render('website_outlet_locator_app.layout_logo_show')  


    @http.route(['/search/vals'] , type='json', auth="public", website=True)
    def search_vals(self, **post):
        store_id = request.env['store.setting'].sudo().search([],order="id desc", limit=1)
        data = {}
        latitude = False
        longitude = False
        map_zoom = False
        map_type = False
        map_search_radius = False
        geocode_result = None
        address = ''

        gmaps = googlemaps.Client(key=str(store_id.google_api_key))
        
        if store_id.map_center == 'auto':   
            company = request.env.user.company_id    
            address += str(company.street) + ' ' + str(company.street2) + ' ' + str(company.state_id.name) + ' ' + str(company.country_id.name)
            try:
                geocode_result = gmaps.geocode(address)
            except ValueError as error_message:
                print("Error: geocode failed on input %s with message %s" % (address, error_message))
            latitude = geocode_result[0]['geometry']['location']['lat']
            longitude = geocode_result[0]['geometry']['location']['lng']
        elif store_id.map_center == 'manual':
            if store_id.manual_options == 'manual':
                latitude = store_id.latitude
                longitude = store_id.longitude
            if store_id.manual_options == 'address':
                address += store_id.street + ' ' + store_id.street2 + ' ' + store_id.state_id.name + ' ' + store_id.country_id.name
                geocode_result = gmaps.geocode(address)
                try:
                    geocode_result = gmaps.geocode(address)
                except ValueError as error_message:
                    print("Error: geocode failed on input %s with message %s" % (address, error_message))
                latitude = geocode_result[0]['geometry']['location']['lat']
                longitude = geocode_result[0]['geometry']['location']['lng']

        location_ids = request.env['store.location'].sudo().search([('website_published','=',True)])
    
        location = {}
        for location_id in location_ids:
            if location_id.image:
                src = '/web/image/store.location/'+ str(location_id.id) +'/image'
            else:
                src = ''
            address = ''
            if location_id.street:
                address += """ %s \n""" % location_id.street
            if location_id.street2:
                address += """ %s \n""" % location_id.street2
            if location_id.city:
                address += """ %s \t""" % location_id.city
            if location_id.state_id:
                address += """ %s \t""" % location_id.state_id.name
            if location_id.zip:
                address += """ %s \n""" % location_id.zip
            if location_id.country_id:
                address += """ %s \n""" % location_id.country_id.name

            store_latitude  = False
            store_longitude = False

            if location_id.map_coordinates == 'manual':
                store_latitude = location_id.latitude
                store_longitude = location_id.longitude
            if location_id.map_coordinates == 'address':
                geocode_result = gmaps.geocode(address)
                try:
                    geocode_result = gmaps.geocode(address)
                except ValueError as error_message:
                    print("Error: geocode failed on input %s with message %s" % (address, error_message))
                store_latitude = geocode_result[0]['geometry']['location']['lat']
                store_longitude = geocode_result[0]['geometry']['location']['lng']
            if post['search_string'] in location_id.name.lower():
                location.update({
                    location_id.id : {
                        'name' : location_id.name,
                        'contact' : location_id.contact,
                        'image' : src, 
                        'email' : location_id.email,
                        'address' : address,
                        'latitude' : store_latitude,
                        'longitude' : store_longitude, 
                        'store_id' : location_id.id,
                        'map_search_radius' : store_id.search_radius,
                        'found' : True,
                    }
                })
            else:
                location.update({
                    location_id.id : {
                        'name' : location_id.name,
                        'contact' : location_id.contact,
                        'image' : src, 
                        'email' : location_id.email,
                        'address' : address,
                        'latitude' : store_latitude,
                        'longitude' : store_longitude, 
                        'store_id' : location_id.id,
                        'map_search_radius' : store_id.search_radius,
                        'found' : False,
                    }
                })

        map_search_radius = store_id.search_radius
        map_zoom = store_id.map_zoom
        map_type = store_id.map_type


        final_val = {}
        data = {}
        map_stores_data = {}
        final_val.update({
            'latitude' : latitude,
            'longitude' : longitude,
            'map_zoom' : map_zoom,
            'map_type' : map_type,
            'map_search_radius' : map_search_radius,
        })

        data.update({
            'map_init' :final_val,
            'map_stores_data' : location,
            })

        return json.dumps(data)   

        