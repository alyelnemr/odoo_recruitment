# -*- coding: utf-8 -*-
{
    'name' : 'Recruitment',
    'version' : '1.0.5',
    'summary': 'Recruitment Managment',
    'sequence': 30,
    'description': """
Handel recruitment Process
    """,
    'depends': ['base', 'base_setup', 'bus', 'web_tour','hr_recruitment', 'mail','sync_ldap_ads','report_xlsx'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/mail_templates.xml',
        'views/interview_view.xml',
        'views/interview_templates.xml',
        'data/call_result_data.xml',
        'data/interview_data.xml',
        'data/interview_email_templates.xml',
        'data/jobs_data.xml',
        'data/offer_data.xml',
        'views/offer_view.xml',
        'views/applicant_view.xml',
        'views/job_view.xml',
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
