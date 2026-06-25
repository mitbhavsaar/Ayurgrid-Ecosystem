{
    'name': 'Ayurgrid OPD Module',
    'version': '19.0.1.0.0',
    'category': 'Healthcare',
    'summary': 'Clinical module for Ayurgrid OPD ecosystem.',
    'description': """
Ayurgrid PMS - Phase 2A (OPD)
==============================
This module provides the core clinical engine for Ayurgrid.
Features include:
- Appointment Management
- OPD Consultations (New & Follow-up)
- Therapy Prescriptions & Register
    """,
    'author': 'Ayurgrid',
    'website': 'https://www.ayurgrid.com',
    'depends': ['base', 'mail', 'product', 'ayurgrid_base'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/menus.xml',
        'views/appointment_views.xml',
        'views/consultation_views.xml',
        'views/therapy_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
