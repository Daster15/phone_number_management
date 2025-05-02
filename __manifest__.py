{
    'name': "Phone Number Management",
    'version': '17.0.1.0.0',
    'category': 'Telecommunications',
    'summary': 'Management of phone numbers pool, ported and removed numbers',
    'description': """
        Comprehensive management of telephone numbers including:
        - Number pool with status tracking
        - Ported numbers history
        - Removed numbers registry
        - Bulk operations and imports
    """,
    'author': "POXBOX",
    'website': "https://poxbox.pl",
    'depends': ['base', 'mail'],
    'data': [
        'security/security_rules.xml',
        'security/ir.model.access.csv',
        'views/number_pool_views.xml',
        'views/ported_numbers_views.xml',
        'views/removed_numbers_views.xml',
        'views/menu_views.xml',
        'data/import_templates.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}