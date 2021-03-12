# -*- coding: utf-8 -*-

{
    'name' : 'Recurring Invoice Subscription odoo',
    'author': "Edge Technologies",
    'version' : '14.0.1.0',
    'live_test_url':'https://youtu.be/8GkPVucbUZk',
    "images":["static/description/main_screenshot.png"],
    'summary' : 'Apps for Invoice Recurring orders invoice subscription Recurring invoice Recurring subscription customer invoice subscription process subscription on invoice Recurring customer subscription on invoice subscription recurring process subscription management',
    'description' : """
        User can make recurring invoice manually or automatically as per duration configured.
    """,
    "license" : "OPL-1",
    'depends' : ['base','account'],
    'data': [
            'security/ir.model.access.csv',
            'data/email_template.xml',
            'data/ir_cron.xml',
            'views/invoice_view.xml',
            'wizard/recurring_invoice.xml',
            'views/recurring_invoice_view.xml',
            ],
    'qweb' : [],
    'demo' : [],
    'installable' : True,
    'auto_install' : False,
    'price': 18,
    'category' : 'Accounting',
    'currency': "EUR",
}
