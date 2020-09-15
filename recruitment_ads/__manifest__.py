# -*- coding: utf-8 -*-
# noinspection PyStatementEffect
{
    'name': 'Recruitment ADS',
    'version': '2.1.0',
    'summary': 'Recruitment Management',
    'category': 'Employees',
    'author': 'AHBS Odoo Team',
    'website': "http://www.andalusiagroup.net",
    'sequence': 1,
    'description': """
Handle recruitment Process for Andalusia
    """,
    'depends': ['base', 'base_setup', 'bus', 'web_tour', 'hr_recruitment', 'mail', 'sync_ldap_ads', 'report_xlsx',
                'decimal_precision', 'contacts'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/rejected_applicant_mail_template.xml',
        'data/call_result_data.xml',
        'data/interview_data.xml',
        'data/interview_email_templates.xml',
        'data/jobs_data.xml',
        'data/offer_data.xml',
        'data/salary_scale_data.xml',
        'data/position_grade_data.xml',
        'data/hr_policy_offer_and_hire.xml',
        'data/sequence.xml',
        'data/job_mail_template.xml',
        'data/hr_setup_approval_group.xml',
        'data/approval_cycle_mail_template.xml',
        'reports/reports.xml',
        'views/mail_templates.xml',
        'views/interview_view.xml',
        'views/interview_templates.xml',
        'views/offer_view.xml',
        'views/position_grade_view.xml',
        'views/salary_scale_view.xml',
        'views/applicant_view.xml',
        'views/job_view.xml',
        'views/hr_section_view.xml',
        'views/hr_department_view.xml',
        'views/policy.xml',
        'views/res_users_view.xml',
        'views/hr_set_daily_target_view.xml',
        'views/hr_set_montly_target_view.xml',
        'views/hr_setup_approval_cycle_view.xml',
        'views/hr_approval_cycle_view.xml',
        'wizard/recruitment_wizard_view.xml',
        'wizard/offer_wizard_view.xml',
        'wizard/approval_cycle_wizard_view.xml',
        'wizard/interview_mail_compose_message_wizard_view.xml',
        'wizard/generate_daily_target_report_wizard.xml',
        'wizard/generate_monthly_target_report_wizard.xml',
        'wizard/compliance_report_wizard.xml',
        'wizard/generate_rejection_mail_message_view.xml',
        'reports/offer_egypt_template.xml',
        'reports/offer_ksa_template.xml',
        'views/hr_approval_cycle_response.xml',
        'wizard/approval_cycle_mail_message_wizard_view.xml'
    ],

    'qweb': [
        'static/src/xml/activity.xml',
        'static/src/xml/fields.xml',
        'static/src/xml/dialog.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}
