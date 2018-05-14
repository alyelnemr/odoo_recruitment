# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, tools

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = 'res.partner'

    employee = fields.Boolean('Is Employee', default=False)

    @api.model
    def get_ldap_employee_data(self, email='*', attrlst=['mail']):
        Ldap = self.env['res.company.ldap']

        employees = []
        res ={}

        for conf in Ldap.get_ldap_dicts():
            _logger.info('Querying ldap {}:{}'.format(conf['ldap_server'], conf.get('ldap_server_port')))
            results = Ldap.paged_query(conf,
                                       u"(&(objectCategory=person)(objectClass=user)(mail={})(!(userAccountControl:1.2.840.113556.1.4.803:=2)))".format(
                                           email),
                                       attrlst, size=100)
            for dn, entry in results:
                for attr,val in entry.items():
                    res[attr] = tools.ustr(val[0])
                employees.append(res.copy())

        _logger.info('{} employee found in LDAP servers'.format(len(employees)))
        return employees

    @api.model
    def sync_ldap(self):

        def remap_vals(val,mapper):
            mapped_val ={}
            for key in val:
                mapped_val[mapper[key]]=val[key]
            return mapped_val

        employees_data = self.get_ldap_employee_data(attrlst=['name','mail','title'])
        mails = list(map(lambda emp:emp['mail'],employees_data))
        employee_to_update = self.search([('email','in',mails)])
        mails_to_create_employee = list(set(mails) - set(employee_to_update.mapped('email')))
        _logger.info("Searching for employees to update")
        updated = 0
        for emp in employee_to_update:
            values = list(filter(lambda i:i['mail'] == emp.email,employees_data))
            attr_map = {'name':'name','mail':'email','title':'function'}

            for val in values:
                values_hash = val.get('name','') + '-' + val.get('title','')
                emp_hash = emp.name + '-' + emp.function or ''
                if values_hash != emp_hash:
                    emp.write(remap_vals(val,attr_map))
                    updated +=1
                    _logger.debug(" %s  Employees has been updated" % (updated))
        created= 0
        _logger.info("found %s Employees to create" % (len(mails_to_create_employee)))
        for mail in mails_to_create_employee:
            emp_data = list(filter(lambda i:i['mail'] == mail,employees_data))[0]
            val = {
                'name':emp_data.get('name',mail),
                'email':mail,
                'function':emp_data.get('title',''),
                'employee':True,
                'company_type':'person',
            }
            self.create(val)
            created += 1
            _logger.debug(" %s of %s Employees has been created" % (created,len(mails_to_create_employee)))
        employee_to_archive = self.search([('email','not in',mails),('employee','=',True)])
        _logger.info("found %s Employees to archive" % (len(employee_to_archive)))
        # if employee_to_archive:
        #     employee_to_archive.write({'active':False})






