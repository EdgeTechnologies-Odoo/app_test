# -*- coding: utf-8 -*-
{
    'name': 'Website Shop/Outlet Location On Google Map',
    "author": "Edge Technologies",
    'version': '13.0.1.3',
    'live_test_url': "https://youtu.be/806_8NUqstw",
    "images":['static/description/main_screenshot.png'],
    'summary': "Website store locator on google map website store location finder website Share store location shop locator google store locator google locator website shop finder shop location finder Website Outlet Location On Google Map Website Location On Google Map",
    'description': """ Website Shop/Outlet locater module used to locate all your offline Shops/Outlets on Google Map on your website with shop address, email and contact details.

store locator in Odoo
odoo store location finder
Website Store Locator
Store Locator Share store location shop locator google store locator google locator gmaps store lotaction, show location finder
shop location finder, shop locator shop finder website shop finder google shop location google maps shop location on google
outlet location finder
outlet locater branch locater on website eCommerce store location with google map webshop location eCommerce store locator webshop locator with google map 

    """,
    "license" : "OPL-1",
    'depends': ['base','web','website','base_geolocalize'],
    'external_dependencies' : {
        'python' : ['googlemaps'],
    },
    'data': [
        'security/store_security.xml',
        'security/ir.model.access.csv',
        'wizard/store_location_setting_view.xml',
        'views/store_configuration_views.xml',
        'views/store_template.xml',
        ],
    'installable': True,
    'auto_install': False,
    'price': 45,
    'currency': "EUR",
    'category': 'eCommerce',
}
