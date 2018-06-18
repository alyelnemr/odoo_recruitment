# -*- coding: utf-8 -*-
{
    'name' : 'Recruitment',
    'version' : '1.1',
    'summary': 'Recruitment Managment',
    'sequence': 30,
    'description': """
Handel recruitment Process
    """,
    'depends': ['base', 'base_setup', 'bus', 'web_tour','hr_recruitment', 'mail','sync_ldap_ads'],
    'data': [
        'security/groups.xml',
        'views/mail_templates.xml',
        'views/interview_view.xml',
        'views/interview_templates.xml',
        'data/call_result_data.xml',
        'data/interview_data.xml',
        'data/interview_email_templates.xml',
        'wizard/recrutier_activity_wizard_view.xml',
        'reports/reports.xml',

       
    ],
    'qweb': [
        'static/src/xml/activity.xml',
        'static/src/xml/fields.xml',

    ],
   
    'installable': True,
    'application': False,
    'auto_install': False,
}
