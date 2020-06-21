# -*- coding: utf-8 -*-
import logging
import re

from odoo import models, fields, api, tools

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = 'res.partner'

    employee = fields.Boolean('Is Employee', default=False)
    GUID = fields.Char('GUID', size=256)

    @api.model
    def get_ldap_employee_data(self, email='*', attrlst=['objectGUID']):
        Ldap = self.env['res.company.ldap']

        employees = []
        res = {}

        for conf in Ldap.get_ldap_dicts():
            _logger.info('Querying ldap {}:{}'.format(conf['ldap_server'], conf.get('ldap_server_port')))
            results = Ldap.paged_query(conf,
                                       u"(&(objectCategory=person)(objectClass=user)(mail={})(!(userAccountControl:1.2.840.113556.1.4.803:=2)))".format(
                                           email),
                                       attrlst, size=100)
            for dn, entry in results:
                # _logger.debug(dn)
                service_account = re.search(r"OU=service(account)?s?", dn,
                                            re.I + re.DOTALL)  # don't take service accounts
                if service_account:
                    continue
                for attr, val in entry.items():
                    if attr == 'objectGUID':
                        res[attr] = val[0].hex()
                    else:
                        res[attr] = tools.ustr(val[0])
                employees.append(res.copy())

        _logger.info('{} employee found in LDAP servers'.format(len(employees)))
        return employees

    @api.model
    def sync_ldap(self):

        def remap_vals(val, mapper):
            mapped_val = {}
            for key in mapper:
                mapped_val[mapper[key]] = val.get(key, '')
            return mapped_val

        employees_data = self.get_ldap_employee_data(attrlst=['objectGUID', 'name', 'mail', 'title'])
        GUIDS = list(map(lambda emp: emp['objectGUID'], employees_data))
        employee_to_update = self.search([('GUID', 'in', GUIDS), '|', ('active', '=', True), ('active', '=', False)])
        GUIDS_to_create_employee = list(set(GUIDS) - set(employee_to_update.mapped('GUID')))
        _logger.info("Searching for employees to update")
        updated = 0
        for emp in employee_to_update:
            values = list(filter(lambda i: i['objectGUID'] == emp.GUID, employees_data))
            attr_map = {'name': 'name', 'mail': 'email', 'title': 'function'}

            for val in values:
                values_hash = val.get('name', '') + '-' + val.get('title', '') + '-' + str(True)
                emp_hash = emp.name + '-' + (emp.function or '') + '-' + str(emp.active)
                if values_hash != emp_hash:
                    vals = remap_vals(val, attr_map)
                    vals['active'] = True
                    emp.with_context({'ldap': True}).write(vals)
                    updated += 1
                    _logger.debug("Employee: %s has been updated because of different hashes %s : %s" % (
                        emp.name, values_hash, emp_hash))
        _logger.info("A total of %s Employees have been updated" % (updated))
        created = 0
        _logger.info("found %s Employees to create" % (len(GUIDS_to_create_employee)))
        for GUID in GUIDS_to_create_employee:
            emp_data = list(filter(lambda i: i['objectGUID'] == GUID, employees_data))[0]
            val = {
                'name': emp_data.get('name', 'Name Not Found'),
                'email': emp_data.get('mail', ''),
                'function': emp_data.get('title', ''),
                'employee': True,
                'company_type': 'person',
                'GUID': GUID,
            }
            self.with_context({'ldap': True}).create(val)
            created += 1
            _logger.debug(" %s of %s Employees has been created" % (created, len(GUIDS_to_create_employee)))
        employee_to_archive = self.search([('GUID', 'not in', GUIDS), ('employee', '=', True)])
        _logger.info("found %s Employees to archive" % (len(employee_to_archive)))
        if employee_to_archive:
            employee_to_archive.write({'active': False})
