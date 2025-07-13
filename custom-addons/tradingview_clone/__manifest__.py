# -*- coding: utf-8 -*-
{
    'name': "TradingView_Clone",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "Moaaz Emam",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','website'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/base_menu.xml',
        'views/symbol_view.xml',
        'views/symbol_website_view.xml',
        'views/market_view.xml',
        'views/ir_cron.xml'
    ],
    'application': True,
}

