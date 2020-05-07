# -*- coding: utf-8 -*-
# noinspection PyStatementEffect
{
    'name': 'Recruitment ADS',
    'version': '2.1.0',
    'summary': 'Recruitment Management',
    'category': 'Employees',
    'author': 'AHBS Odoo Team',
    'website': "http://www.andalusia.net",
    'sequence': 30,
    'description': """
Handle recruitment Process for Andalusia
    """,
    'depends': ['base', 'base_setup', 'bus', 'web_tour', 'hr_recruitment', 'mail', 'sync_ldap_ads', 'report_xlsx',
                'decimal_precision'],
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
        'data/sequence.xml',
        'views/offer_view.xml',
        'views/applicant_view.xml',
        'views/job_view.xml',
        'views/res_users_view.xml',
        'wizard/recruitment_wizard_view.xml',
        'wizard/offer_wizard_view.xml',
        'wizard/interview_mail_compose_message_wizard_view.xml',
        'reports/reports.xml',
        'wizard/compliance_report_wizard.xml',
    ],

    'qweb': [
        'static/src/xml/activity.xml',
        'static/src/xml/fields.xml',
        'static/src/xml/dialog.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
}
