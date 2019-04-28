# SaltStack SDB Module for {php}IPAM

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/48f891143bbb41baa8a9da9d33010fb8)](https://www.codacy.com/app/madrisan/saltstack-sdb-phpipam?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=madrisan/saltstack-sdb-phpipam&amp;utm_campaign=Badge_Grade)
[![License](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](https://spdx.org/licenses/Apache-2.0.html)

![](images/phpipam_logo.png?raw=true)

A SaltStack SDB module for interacting with a
[{php}IPAM](https://phpipam.net/), an open-source web IP address management application (IPAM).

This module requires a configuration profile to be configured in either the minion or, as in our implementation, in the master configuration file (`/etc/salt/master.d/phpipam.conf`).

This profile requires very little:

    phpipam:
      auth:
        user: 'read_api_user'
        password: 'xxxxx'
      driver: phpipam
      url: https://ipam.mydomain.com

Where `url` is the URL of the *phpipam* server and `auth.user` and `auth.password` the credential of a user account created in the *phpipam* application. If authentication is successfull, an API token will be received and transparently included in the header of all the API requests.

This Python module should be saved as `salt/_modules/sdb/phpipam.py`.

## API documentation

URL: <https://phpipam.net/api/api_documentation/>

## Usage

### sdb.get

Get the IP address(es) associated to a given *hostname*, by querying the *phpipam* server.

Example of output (`IP:netmask:subnet description:subnet ID`):

    $ sudo salt-run sdb.get sdb://phpipam/HOSTNAME
    10.0.5.18:255.255.255.0:VLAN Front:5
    10.1.7.18:255.255.255.0:VLAN Back:7
