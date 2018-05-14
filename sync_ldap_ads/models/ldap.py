# -*- coding: utf-8 -*-

import logging

import ldap
from ldap.controls import SimplePagedResultsControl
from odoo import models, api
from odoo.tools.pycompat import to_native

_logger = logging.getLogger(__name__)


class ResCompanyLDAP(models.Model):
    _inherit = 'res.company.ldap'

    @api.model
    def paged_query(self, conf, filter, retrieve_attributes=None, size=10):
        """
        Query an LDAP server with the filter argument and scope subtree.

        Allow for all authentication methods of the simple authentication
        method:

        - authenticated bind (non-empty binddn + valid password)
        - anonymous bind (empty binddn + empty password)
        - unauthenticated authentication (non-empty binddn + empty password)
        - paged search :data received in chunks to overcome the size limitation set by server

        .. seealso::
           :rfc:`4513#section-5.1` - LDAP: Simple Authentication Method.

        :param dict conf: LDAP configuration
        :param filter: valid LDAP filter
        :param list retrieve_attributes: LDAP attributes to be retrieved. \
        If not specified, return all attributes.
        :param int size: page size to get
        :return: ldap entries
        :rtype: list of tuples (dn, attrs)

        """

        results = []
        pages = 0
        len_records = 0
        SPRC = SimplePagedResultsControl(size=size, cookie='')
        try:
            conn = self.connect(conf)
            ldap_password = conf['ldap_password'] or ''
            ldap_binddn = conf['ldap_binddn'] or ''
            ldap_base = conf['ldap_base'] or ''
            conn.simple_bind_s(to_native(ldap_binddn), to_native(ldap_password), serverctrls=[SPRC])
            msgid = conn.search_ext(to_native(ldap_base), ldap.SCOPE_SUBTREE, filter, retrieve_attributes,
                                    serverctrls=[SPRC], timeout=60)
            while True:
                pages += 1
                rtype, rdata, rmsgid, rctrls = conn.result3(msgid, all=1, timeout=60)
                results.extend(rdata)
                len_records += len(rdata)
                pctrls = [
                    c
                    for c in rctrls
                    if c.controlType == SimplePagedResultsControl.controlType
                ]
                if pctrls:
                    if pctrls[0].cookie:
                        # Copy cookie from response control to request control
                        SPRC.cookie = pctrls[0].cookie
                        msgid = conn.search_ext(to_native(ldap_base), ldap.SCOPE_SUBTREE, filter, retrieve_attributes,
                                                serverctrls=[SPRC], timeout=60)
                    else:
                        break
            conn.unbind()
        except ldap.INVALID_CREDENTIALS:
            _logger.error('LDAP bind failed.')
        except ldap.LDAPError as e:
            _logger.error('An LDAP exception occurred: %s', e)
        _logger.info("LDAP Sync Found  %s entries in %s pages" % (len_records, pages))
        return results
