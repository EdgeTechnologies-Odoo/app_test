# -*- coding: utf-8 -*-

{
    'name' : 'All in One Disable followers App',
    'author': "Edge Technologies",
    'version' : '14.0.1.0',
    'live_test_url':'https://youtu.be/jMmauSrwRvY',
    "images":['static/description/main_screenshot.png'],
    'summary' : 'All Disable follower on Odoo Disable follower on sale disable follower on invoice disable follower on bill disable follower stop subscription stop auto follower stop automatic follower stop follower on order disable follower ',
    'description' : """ Odoo automatically partners customers, vendors, contacts added as the followers. This module disables the partners automatically added as followers.  """,
    "license" : "OPL-1",
    'depends' : ['sale_management','account'],
    'data' : [
        'wizard/res_config_setting_views.xml',
    ],
    'installable' : True,
    'auto_install' : False,
    'price': 15,
    'currency': "EUR",
    'category' : 'Extra Tools',
}
