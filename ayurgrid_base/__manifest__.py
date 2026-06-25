{
    'name': 'Ayurgrid Base',
    'version': '19.0.1.0.0',
    'category': 'Healthcare',
    'summary': 'Master data foundation for the Ayurgrid ecosystem.',
    'description': """
Ayurgrid PMS - Phase 1
======================
This module provides the core master data foundation for the Ayurgrid ecosystem.
It includes:
- Admin Setup (Organization, AI Config)
- Hospital Setup (Hospital, Branch, Department, Room)
- Patient Registration (Patient, Ayurveda Assessments)
    """,
    'author': 'Ayurgrid',
    'website': 'https://www.ayurgrid.com',
    'depends': ['base', 'mail', 'contacts'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/organization_views.xml',
        'views/hospital_views.xml',
        'views/branch_views.xml',
        'views/department_views.xml',
        'views/room_views.xml',
        'views/patient_views.xml',
        'views/ai_configuration_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
