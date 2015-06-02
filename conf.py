#!/usr/bin/env python
# encoding: utf-8

import sys
from neutron.common import config as common_config
from neutron import context
from neutron.agent import rpc as agent_rpc
from ncclient import manager

class ConnTor(object):
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        try:
            self.conn = manager.connect_ssh(host = self.host,
                                        username = self.username,
                                        password = self.password,
                                        hostkey_verify = False,
                                        look_for_keys=False)
        except:
            self.conn = None
            raise ValueError("Tor Connection Init Failed.")

    def __enter__(self):
        if self.conn is None:
            raise ValueError("Tor Connection Error.")
        return self.conn

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_tb:
            self.conn = None

class OVSPluginApi(agent_rpc.PluginApi):
    pass

if __name__ == "__main__":
    common_config.init(sys.argv[1:])

    #with ConnTor('sw2', 'sinanp', 'sinanp') as m:
    #            print m.get_config(source='running')
    rpc = OVSPluginApi("q-plugin")
    c = context.get_admin_context_without_session()
    print rpc.tunnel_sync(c, "192.168.2.11", "vxlan")
