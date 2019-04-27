# -*- coding: utf-8 -*-
'''
SDB module for {php}IPAM
Copyright (C) 2019 Davide Madrisan <davide.madrisan@gmail.com>

Like all sdb modules, the PHPIPAM module requires a configuration profile to be
configured in either the minion or, as in our implementation, in the master
configuration file (/etc/salt/master.d/phpipam.conf).

This profile requires very little:

.. code-block:: yaml

    phpipam:
      driver: phpipam
      url: https://ipam.mydomain.com
      auth:
        user: 'read_api_user'
        password: 'xxxxx'

The `driver` refers to the phpipam module.

This file should be saved as salt/_sdb/phpipam.py

.. code-block:: yaml

    ipaddr: sdb://phpipam/MACHINE_HOSTNAME

CLI Example:

    .. code-block:: bash

        salt-run sdb.get sdb://phpipam/MACHINE_HOSTNAME
'''

# Import Python libs
import logging
import os
import requests

# Import Salt libs
import salt.config
from salt.exceptions import CommandExecutionError

log = logging.getLogger(__name__)

class Api(object):
    '''
    Class for managing the {php}IPAM token for successive queries
    '''
    def __init__(self, debug=False):
        self.debug = debug

        phpipam_config = self._config()
        try:
            self._phpipam_url = phpipam_config['url']
            auth = phpipam_config['auth']
            self._user = auth['user']
            self._password = auth['password']
        except KeyError as err:
            log.error('Failed to get the {php}IPAM configuration! %s: %s',
                      type(err).__name__, err)
            raise salt.exceptions.CommandExecutionError(
                "Cannot find the {php}IPAM configuration!")

        self._api_url = '{0}/api/lookup/'.format(self._phpipam_url)
        self._verify = phpipam_config.get('verify',
                                          '/etc/ssl/certs/ca-certificates.crt')
        self._token = self._get_token()

    def _config(self):
        '''
        Return the SaltStack configuration for {php}IPAM
        '''
        try:
            master_opts = salt.config.client_config('/etc/salt/master')
        except Exception as err:
            log.error('Failed to read configuration for {php}IPAM! %s: %s',
                      type(err).__name__, err)
            raise salt.exceptions.CommandExecutionError(err)

        phpipam_config = master_opts.get('phpipam', {})
        return phpipam_config

    def _get_token(self):
        '''
        Get an {php}IPAM for future queries
        '''
        resource = 'user'
        url = "{0}/{1}".format(self._api_url, resource)
        response = requests.request('POST',
                                    url,
                                    auth=(self._user, self._password),
                                    verify=self._verify)

        if response.status_code != requests.codes.ok:
            response.raise_for_status()

        token = response.json()['data']['token']
        return token

    def token(self):
        '''
        Return the current API token
        '''
        return self._token

    def query(self, resource):
        '''
        Perform a query directly against the {php}IPAM REST API
        '''
        url = "{0}/{1}".format(self._api_url, resource)
        headers = {
            'token': self._token,
            'Content-Type': 'application/json'
        }
        response = requests.request('GET',
                                    url,
                                    headers=headers,
                                    verify=self._verify)
        if response.status_code != requests.codes.ok:
            response.raise_for_status()

        json = response.json()
        if 'data' in json:
            return json['data']

        if 'message' in json:
            log.debug('Failed to get data from {php}IPAM: %s: %s',
                      url, json['message'])
        return {}

def get(key):
    '''
    Get the IP address(es) associated to a given hostname by querying the {php}IPAM server.

    Example of output (IP:netmask:subnet description:subnet ID):
        10.100.15.20:255.255.255.0:PV Backwww:27
        10.100.7.20:255.255.255.0:PV Frontwww:19
    '''
    api = Api()
    resource = 'addresses/search_hostname_partial'
    res = api.query("{0}/{1}".format(resource, key))

    # the hostname has not been found in {php}IPAM
    if not res:
        return ''

    ipaddrs = []
    for entry in res:
        ipaddr   = entry.get('ip', None)
        hostname = entry.get('hostname', None)
        subnetId = entry.get('subnetId', None)
        if ipaddr and subnetId and hostname == key:
            res_subnet = api.query('subnets/{0}'.format(subnetId))
            if not res_subnet:
                continue
            subnet_netmask = (
                res_subnet.get('calculation', {}).get('Subnet netmask'))
            subnet_description = res_subnet.get('description')
            ipaddrs.append('{0}:{1}:{2}:{3}'.format(
                ipaddr,
                subnet_netmask,
                subnet_description,
                subnetId))

    return os.linesep.join(ipaddrs)
