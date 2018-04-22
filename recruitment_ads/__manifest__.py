# -*- coding: utf-8 -*-
{
    'name' : 'Recruitment',
    'version' : '1.1',
    'summary': 'Recruitment Managment',
    'sequence': 30,
    'description': """
Handel recruitment Process
    """,
    'depends': ['base', 'base_setup', 'bus', 'web_tour','hr_recruitment', 'mail'],
    'data': [
        'views/mail_templates.xml',
        'views/interview_view.xml',
        'data/call_result_data.xml',
        'data/interview_data.xml',

       
    ],
    'qweb': [
        'static/src/xml/activity.xml',

    ],
   
    'installable': True,
    'application': False,
    'auto_install': False,
}
