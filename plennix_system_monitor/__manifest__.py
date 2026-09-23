# -*- coding: utf-8 -*-
{
    'name': 'System Monitor',
    'version': '19.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Records every error users hit in Odoo and emails it, with full details, to selected staff.',
    'description': """
Plennix Technologies — System Monitor
=====================================

Whenever a user or an integration gets an error in Odoo, the error is recorded
with who hit it, what they were doing and the full technical details, and it is
emailed as a spreadsheet to the staff chosen in Settings. Support teams learn about
problems as soon as they happen and can investigate them without asking users for
screenshots or needing server access.

Key Features
------------
* Every error shown to a user is recorded automatically with its full details
* Chosen staff receive each error by email, with a spreadsheet attached
* Optional daily email with all of the day's errors
* Searchable error list for administrators, grouped by error, model, action or user

Developed by Plennix Technologies — https://www.plennix.com
""",
    'author': 'Plennix Technologies',
    'company': 'Plennix Technologies',
    'maintainer': 'Plennix Technologies',
    'website': 'https://www.plennix.com',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/system_monitor_log_views.xml',
        'data/ir_cron.xml',
        'data/template.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
